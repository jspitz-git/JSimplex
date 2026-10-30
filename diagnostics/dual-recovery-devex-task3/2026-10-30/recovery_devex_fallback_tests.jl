# Task3 prospective ordinary tests; Julia UNEXECUTED during preparation.
# Include after canonical Task1 and Task2 tests in a fresh source overlay.
module RecoveryDevexFallbackTests
using Test, LinearAlgebra, SparseArrays, JSimplex
const J=JSimplex

mutable struct RecoveryFactor{T,F}
    base::F
    updates::Vector{J.PackedEta{T}}
    failed_row::Int
    units::Int
    corrections::Int
    forwards::Int
    backwards::Int
    awaiting_correction::Bool
    injected::Bool
end
wrap(f::F,row::Int) where F=RecoveryFactor{eltype(f.work),F}(f,f.updates,row,0,0,0,0,false,false)
J._factor_storage_count(f::RecoveryFactor)=J._factor_storage_count(f.base)
J._factor_growth_reference(f::RecoveryFactor)=J._factor_growth_reference(f.base)
J._factor_growth_measure(f::RecoveryFactor)=J._factor_growth_measure(f.base)
function J.forward_solve!(dest::Vector{T},f::RecoveryFactor{T},rhs::Vector{T}) where T
    f.forwards+=1
    J._ordinary_forward_solve!(dest,f.base,rhs)
end
function J.transpose_solve!(dest::Vector{T},f::RecoveryFactor{T},rhs::Vector{T}) where T
    f.backwards+=1
    J.transpose_solve!(dest,f.base,rhs)
    if f.awaiting_correction
        f.corrections+=1;f.awaiting_correction=false
        fill!(dest,zero(T))
    elseif count(!iszero,rhs)==1 && any(==(one(T)),rhs)
        f.units+=1
        if f.units==f.failed_row && !f.injected
            dest ./= T(2);f.awaiting_correction=true;f.injected=true
        end
    end
    dest
end
mutable struct Builder{F}
    calls::Int
    failed_row::Int
    last::Union{Nothing,F}
    failure::Union{Nothing,Exception}
end
function (b::Builder{F})(B,options) where F
    b.calls+=1 # before genuine factorization, including throws
    new=wrap(J._basis_factorization(B,options),b.failed_row)
    new isa F || error("test factor type changed")
    b.last=new
    isnothing(b.failure) || throw(b.failure)
    new
end
mutable struct Observe
    calls::Int
    publish_calls::Int
    reasons::NTuple{3,Symbol}
    saw_devex::Bool
    throw_reason::Symbol
    mutate::Symbol
    failure::Exception
end
function (o::Observe)(reason,ws)
    o.calls+=1
    if reason==:correction_attempt
        if o.mutate==:nonfinite_core
            ws.primal[end]=eltype(ws.costs)(Inf)
        elseif o.mutate==:finite_primal
            ws.primal[ws.basis.basic_indices[1]]+=one(eltype(ws.costs))
        elseif o.mutate==:finite_rho
            ws.scratch.rho[1]+=one(eltype(ws.costs))
        elseif o.mutate==:stale_mode
            ws.scratch.pricing.algorithm=:primal
        end
    elseif reason in (:pricing_reset,:repair,:restore_checkpoint,:checkpoint)
        o.publish_calls+=1
        i=o.publish_calls
        i<=3 && (o.reasons=Base.setindex(o.reasons,reason,i))
        o.saw_devex &= J._weight_pricing(ws,:dual)==:devex && all(isone,ws.pricing_weights)
    end
    reason==o.throw_reason && throw(o.failure)
    nothing
end
function fixture(::Type{T}=Float64;failed_row=2,pricing=:auto) where T
    # Zero basic costs distinguish recomputed price RHS from unit weight RHS.
    p=J.LinearProblem(sparse(Matrix{T}(I,2,2)),zeros(T,2);column_lower=fill(nothing,2))
    options=J.SolverOptions(T;verbose=false,time_limit=Inf,pricing)
    policy=J.NumericalPolicy(T;solve_refinement=false,recovery=false,adaptive_refactor=false,
                             refactor_timing=false,hypersparse=false)
    failure=SingularException(43)
    observer=Observe(0,0,(:none,:none,:none),true,:never,:none,failure)
    diagnostics=J.SimplexDiagnostics(;observer,kernel_timing=true)
    progress=J.SimplexProgressContext(p;numerical_policy=policy,diagnostics)
    # One genuine initial factor; trial factory later constructs one more.
    factor=wrap(J._basis_factorization(p.A,options),0)
    states=vcat(fill(J.BASIC,2),fill(J.FREE_NONBASIC,2))
    ws=J.SimplexWorkspace(p,options,progress,zeros(T,4),
        vcat(p.column_lower,p.row_lower),vcat(p.column_upper,p.row_upper),J.Basis([1,2],states),
        zeros(T,4),zeros(T,4),T[9,8,7,6],trues(4),factor,J.SimplexScratch(T,2,4),
        7,0,false,0,false,false,options.refactorization_interval,0,typemax(Int),0,0)
    state=J.PricingState(T);state.algorithm=:dual;state.switches=4;state.rejected_weights=5;state.resets=6
    ws.scratch.pricing=state
    pool=J._pricing_pool!(ws,:dual);append!(pool.indices,[1,2]);pool.valid=true;pool.full_scan=true
    c=J.checkpoint_basis(ws)
    builder=Builder{typeof(factor)}(0,failed_row,nothing,nothing)
    (;ws,c,builder,observer,failure)
end
function snapshot(ws)
    s=ws.scratch.pricing;p=ws.scratch.pricing_pool
    (;factor=ws.factorization,options=ws.options,policy=ws.progress.numerical_policy,
      costs=copy(ws.costs),lower=copy(ws.lower),upper=copy(ws.upper),primal=copy(ws.primal),
      reduced=copy(ws.reduced_costs),weights=copy(ws.pricing_weights),reference=copy(ws.devex_reference),
      basis=copy(ws.basis.basic_indices),states=copy(ws.basis.states),
      flags=(ws.dual_pricing_fallback,ws.dual_devex_fallback),
      pricing=isnothing(s) ? nothing : ntuple(i->getfield(s,i),fieldcount(typeof(s))),
      pool=isnothing(p) ? nothing : (copy(p.indices),p.valid,p.full_scan,p.basis_generation,p.cost_generation),
      history=copy(ws.scratch.checkpoints),
      owners=map(objectid,(ws.costs,ws.lower,ws.upper,ws.primal,ws.reduced_costs,ws.pricing_weights,
                          ws.devex_reference,ws.basis.basic_indices,ws.basis.states)))
end
function construct(f;algorithm=:dual,stop=()->false)
    guard=J._guard_stop_callback(stop)
    J._recovery_trial_with_pricing(f.ws,f.c,guard;algorithm,build_factor=f.builder)
end
function runtests()
    # Missing explicit route must never opt in, even when pricing says dual.
    @testset "Explicit dual retry scope" begin
        for T in (Float32,Float64),algorithm in (:unspecified,:primal,:dual)
            f=fixture(T);before=snapshot(f.ws)
            r=construct(f;algorithm)
            @test snapshot(f.ws)==before && f.ws.refactorizations==1
            @test f.builder.calls==1 && f.builder.last!==f.ws.factorization
            @test (f.builder.last.forwards,f.builder.last.backwards)==(1,4)
            @test (f.builder.last.units,f.builder.last.corrections)==(2,1)
            if algorithm==:dual
                @test r isa J._RecoveryTrialResult && r.devex_fallback && r.failed_weight_row==2
                @test r.workspace.factorization===f.builder.last
                @test r.workspace.pricing_weights==ones(T,4)
                @test J._weight_pricing(r.workspace,:dual)==:devex
                @test r.workspace.scratch.rho==zeros(T,2)
                @test r.workspace.basis.basic_indices!==f.ws.basis.basic_indices
                @test r.workspace.pricing_weights!==f.ws.pricing_weights
                @test r.workspace.devex_reference!==f.ws.devex_reference
                @test r.workspace.scratch.pricing!==f.ws.scratch.pricing
                @test r.workspace.scratch.pricing_pool.indices!==f.ws.scratch.pricing_pool.indices
            else
                @test r===nothing
            end
            @test f.ws.progress.diagnostics.counts[:pricing_devex]==0
            @test f.ws.progress.diagnostics.counts[:pricing_weight_rejected]==0
        end
        for algorithm in (:bad,),api in (:constructor,:repair,:restore)
            f=fixture();before=snapshot(f.ws)
            @test_throws ArgumentError begin
                if api==:constructor
                    construct(f;algorithm)
                elseif api==:repair
                    J.repair_basis!(f.ws,f.ws.progress.numerical_policy,()->false;algorithm)
                else
                    J.restore_checkpoint!(f.ws,f.c,()->false;algorithm)
                end
            end
            @test snapshot(f.ws)==before && f.ws.refactorizations==0
        end
    end
    # Every cancellation/throw is before live adoption, but charged work stays.
    @testset "Cancelled or throwing fallback publication" begin
        f=fixture();before=snapshot(f.ws)
        @test construct(f;stop=()->!isnothing(f.builder.last) && f.builder.last.corrections==1)===nothing
        @test snapshot(f.ws)==before && f.ws.refactorizations==1
        @test f.builder.last.corrections==1
        for mode in (:nonfinite_core,:finite_primal,:finite_rho,:stale_mode)
            f=fixture();f.observer.mutate=mode;before=snapshot(f.ws)
            @test construct(f)===nothing
            @test snapshot(f.ws)==before && f.ws.refactorizations==1
            @test f.builder.last.corrections==1
            @test f.ws.progress.diagnostics.counts[:pricing_devex]==0
        end
        f=fixture();before=snapshot(f.ws)
        guard=J._guard_stop_callback(()->begin
            !isnothing(f.builder.last) && f.builder.last.corrections==1 && throw(f.failure)
            false
        end)
        e=try J._recovery_trial_with_pricing(f.ws,f.c,guard;algorithm=:dual,build_factor=f.builder);nothing catch e;e end
        @test e===f.failure && guard.exception===f.failure
        @test snapshot(f.ws)==before && f.ws.refactorizations==1
        f=fixture();before=snapshot(f.ws);f.observer.throw_reason=:correction_attempt
        e=try construct(f);nothing catch e;e end
        @test e isa J.DiagnosticObserverFailure && e.cause===f.failure
        @test snapshot(f.ws)==before && f.builder.last.corrections==0
        for reason in (:pricing_reset,:repair,:checkpoint)
            f=fixture();before=snapshot(f.ws);r=construct(f)
            @test r!==nothing
            f.observer.throw_reason=reason
            e=try J._publish_recovery!(f.ws,r,:repair,J._guard_stop_callback(()->false));nothing catch e;e end
            @test e isa J.DiagnosticObserverFailure && e.cause===f.failure
            @test snapshot(f.ws)==before && f.ws.refactorizations==1
            @test f.ws.progress.diagnostics.counts[:pricing_devex]==0
            @test f.ws.progress.diagnostics.counts[:pricing_weight_rejected]==0
        end
        f=fixture();before=snapshot(f.ws);r=construct(f)
        @test !J._publish_recovery!(f.ws,r,:repair,J._guard_stop_callback(()->true))
        @test snapshot(f.ws)==before && f.observer.publish_calls==3
        @test f.ws.progress.diagnostics.counts[:repair]==0
        f=fixture();before=snapshot(f.ws);r=construct(f)
        g=J._guard_stop_callback(()->throw(f.failure))
        e=try J._publish_recovery!(f.ws,r,:repair,g);nothing catch e;e end
        @test e===f.failure && g.exception===f.failure
        @test snapshot(f.ws)==before
        f=fixture();before=snapshot(f.ws);f.builder.failure=f.failure
        e=try construct(f);nothing catch e;e end
        @test e===f.failure && snapshot(f.ws)==before
        @test f.builder.calls==1 && f.ws.refactorizations==1
    end
    @testset "Fallback publishes mode with the basis" begin
        for T in (Float32,Float64),reason in (:repair,:restore_checkpoint),pricing in (:steepest_edge,:auto)
            f=fixture(T;pricing);before=snapshot(f.ws);r=construct(f)
            @test J._publish_recovery!(f.ws,r,reason,J._guard_stop_callback(()->false))
            @test f.ws.factorization===f.builder.last && f.ws.factorization!==before.factor
            @test f.ws.pricing_weights==ones(T,4) && f.ws.devex_reference==Bool[true,true,false,false]
            @test J._weight_pricing(f.ws,:dual)==:devex
            @test f.ws.dual_devex_fallback==(pricing!=:auto)
            state=f.ws.scratch.pricing
            @test (state.rejected_weights,state.switches,state.resets)==(6,5,8)
            @test state.framework_valid && !state.needs_reset && state.weight_quality==:valid
            @test f.observer.saw_devex && f.observer.reasons==(:pricing_reset,reason,:checkpoint)
            @test f.observer.calls==4 && f.observer.publish_calls==3
            @test f.ws.iterations==7 && f.ws.refactorizations==1
            @test length(f.ws.scratch.checkpoints)==1
            @test isempty(f.ws.scratch.pricing_pool.indices) && !f.ws.scratch.pricing_pool.valid
            @test f.ws.scratch.recovery_restored==(reason==:restore_checkpoint)
            d=f.ws.progress.diagnostics
            @test (d.counts[:pricing_weight_rejected],d.counts[:pricing_devex],d.counts[:pricing_reset],d.counts[reason],d.counts[:checkpoint])==(1,1,1,1,1)
            @test (f.builder.last.forwards,f.builder.last.backwards)==(1,4)
        end
    end
    @testset "Temporary selection and successful DSE retain their own mode" begin
        f=fixture();state=f.ws.scratch.pricing
        state.active=:dantzig;state.return_mode=:steepest_edge;state.temporary=true
        before=snapshot(f.ws);r=construct(f)
        @test snapshot(f.ws)==before && r.devex_fallback
        @test !r.workspace.scratch.pricing.temporary
        @test r.workspace.scratch.pricing.active==:devex && r.workspace.scratch.pricing.return_mode==:devex
        f=fixture(;failed_row=0);r=construct(f)
        @test r!==nothing && !r.devex_fallback && r.failed_weight_row==0
        @test J._weight_pricing(r.workspace,:dual)==:steepest_edge
        @test (f.builder.last.forwards,f.builder.last.backwards)==(1,3)
        @test J._publish_recovery!(f.ws,r,:repair,J._guard_stop_callback(()->false))
        @test f.ws.progress.diagnostics.counts[:pricing_devex]==0
        @test f.ws.progress.diagnostics.counts[:pricing_weight_rejected]==0
        @test !f.ws.dual_devex_fallback
    end
    @testset "Legacy and precision routes remain strict" begin
        for T in (Float32,Float64,BigFloat,Rational{BigInt})
            p=J.LinearProblem(sparse(T[1;;]),T[0])
            options=J.SolverOptions(T;verbose=false,pricing=:steepest_edge,time_limit=Inf)
            w=J.initialize_workspace(p,options);c=J.checkpoint_basis(w)
            @test J._recovery_trial(w,c,J._guard_stop_callback(()->false)) isa J.SimplexWorkspace
            @test J.restore_checkpoint!(w,c,()->false)
            @test !w.dual_devex_fallback
            @test J.restore_checkpoint!(w,c,()->false;algorithm=:primal)
            @test J.restore_checkpoint!(w,c,()->false;algorithm=:dual)
            @test !w.dual_devex_fallback
            # Reliable ordinary reconstruction remains DSE; no fallback records.
            @test J._weight_pricing(w,:dual)==:steepest_edge
        end
        # Actual public dual retry with genuine ordinary factories; no seam.
        for T in (Float32,Float64)
            p=J.LinearProblem(sparse(T[1 1;1 1]),zeros(T,2);column_lower=T[1,0],row_lower=T[1,2])
            options=J.SolverOptions(T;verbose=false,pricing=:dantzig,simplex_strategy=:adaptive)
            policy=J.NumericalPolicy(T;numerical_profile=:checked,simplex_strategy=:adaptive)
            w=J.initialize_workspace(p,options;progress=J.SimplexProgressContext(p;numerical_policy=policy))
            w.basis.basic_indices.=[1,2]
            w.basis.states.=[J.BASIC,J.BASIC,J.AT_LOWER,J.AT_LOWER]
            w.primal[1]=zero(T)
            result=J._dual_iteration!(w,J._guard_stop_callback(()->false))
            @test result isa J.DualTermination && result.status==J.OPTIMAL
            @test w.basis.basic_indices!=[1,2] && J.primal_infeasibility(w)==zero(T)
        end
    end
end
end
Base.invokelatest(RecoveryDevexFallbackTests.runtests)
