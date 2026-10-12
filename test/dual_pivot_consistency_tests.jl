using JSimplex,Test,SparseArrays,LinearAlgebra

function duplicate_dual_column_workspace(;strategy=:legacy,manager=:pfi,
        policy=nothing,diagnostics=nothing)
    # Independent four-row fixture: column 5 duplicates basic column 1, so
    # exchanging column 2 for column 5 has an exactly zero pivot.
    B=[0.7976562684646633 0.7976562684649653 0.0015056776313773224 0.6327753077629599;
       0.5177335268477845 0.5177335268478244 0.6443667761825296 0.6858186366935533;
       0.8652657188641331 0.8652657188642626 0.8354165933982676 0.5692906556126978;
       0.3498039507903441 0.3498039507907107 0.9287063361318404 0.8119167116587698]
    p=LinearProblem(sparse(hcat(B,B[:,1])),zeros(5);row_lower=-B[:,2],row_upper=-B[:,2])
    options=SolverOptions(algorithm=:dual,simplex_strategy=strategy,basis_update=manager,
        pricing=:dantzig,verbose=false)
    if isnothing(policy)
        adaptive=strategy==:adaptive
        policy=JSimplex.NumericalPolicy(Float64;adaptive_stalling=adaptive,
            adaptive_pricing=adaptive,adaptive_primal_perturbation=adaptive,
            adaptive_dual_perturbation=adaptive,phase_one=adaptive)
    end
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
    ws.basis.basic_indices .= 1:4
    ws.basis.states[1:4] .= JSimplex.BASIC
    ws.basis.states[6:9] .= JSimplex.AT_LOWER
    JSimplex.recompute!(ws;refactorize=true)
    return ws
end


# Deterministic recovery boundary; the native roundoff fixture above stays intact.
# The candidate shares this factor. Only two genuine unit solves are perturbed;
# every later attempt is still counted, including failures before delegation returns.
mutable struct DualRecoveryFactor{F}
    inner::F
    ftran::Int
    prepared::Int
    ordinary::Int
    btran::Int
    unit::Int
    correction::Int
    cost::Int
    metadata::Int
    invalidations::Int
    refactors::Int
    updates_attempted::Int
    copies::Int
    hits::Int
    correction_events::Int
    rejection_events::Int
    refresh_events::Int
    observer_ok::Bool
    staged_seen::Bool
end
DualRecoveryFactor(inner)=DualRecoveryFactor(inner,ntuple(_->0,16)...,true,false)
Base.getproperty(f::DualRecoveryFactor,k::Symbol)=k in fieldnames(typeof(f)) ?
    getfield(f,k) : getproperty(getfield(f,:inner),k)
dual_recovery_unit()=(0.0,1.0,0.0,0.0)
dual_recovery_rho()=(-4194303.5,4194304.0,0.0,0.0)
dual_recovery_correction()=(2.0^-22,2.0^-22,0.0,0.0)
dual_recovery_duplicate()=(1.0,1.0-2.0^-23,0.0,0.0)
dual_recovery_primal_rhs()=(-1.0,-1.0-2.0^-23,0.0,0.0)
function JSimplex._unit_transpose_rhs(f::DualRecoveryFactor,rhs,row::Int)
    f.metadata+=1
    @assert row==2 && Tuple(rhs)==dual_recovery_unit()
    return JSimplex._unit_transpose_rhs(f.inner,rhs,row)
end
function JSimplex.transpose_solve!(d::Vector{Float64},f::DualRecoveryFactor,r::AbstractVector)
    f.btran+=1
    rhs=Tuple(r)
    if rhs==dual_recovery_unit()
        f.unit+=1
        JSimplex.transpose_solve!(d,f.inner,r)
        @assert Tuple(d)==dual_recovery_rho()
        if f.hits<2
            d[1]-=2.0^-22
            f.hits+=1
        end
    elseif rhs==dual_recovery_correction()
        f.correction+=1
        JSimplex.transpose_solve!(d,f.inner,r)
        @assert Tuple(d)==(2.0^-22,0.0,0.0,0.0)
    elseif rhs==(0.0,0.0,0.0,0.0)
        f.cost+=1
        JSimplex.transpose_solve!(d,f.inner,r)
        @assert all(iszero,d)
    else
        error("Unexpected recovery BTRAN RHS")
    end
    return d
end
function JSimplex.forward_solve!(d::Vector{Float64},f::DualRecoveryFactor,r::AbstractVector)
    f.ftran+=1;f.prepared+=1
    @assert Tuple(r)==dual_recovery_duplicate()
    JSimplex.forward_solve!(d,f.inner,r)
    @assert Tuple(d)==(1.0,0.0,0.0,0.0)
    return d
end
function JSimplex._ordinary_forward_solve!(d::Vector{Float64},f::DualRecoveryFactor,r::AbstractVector)
    f.ftran+=1;f.ordinary+=1
    @assert Tuple(r)==dual_recovery_primal_rhs()
    JSimplex._ordinary_forward_solve!(d,f.inner,r)
    @assert Tuple(d)==(0.0,-1.0,0.0,0.0)
    return d
end
function JSimplex._invalidate_prepared_destination!(f::DualRecoveryFactor,d)
    f.invalidations+=1
    return JSimplex._invalidate_prepared_destination!(f.inner,d)
end
JSimplex._finite_updated_factor(f::DualRecoveryFactor)=JSimplex._finite_updated_factor(f.inner)
function JSimplex.refactorize!(f::DualRecoveryFactor,B::AbstractMatrix)
    f.refactors+=1
    @assert size(B)==(4,4)
    @assert all(B[i,j]==(i<=2 && j<=2 ? (i==1 ? 1.0 : 1.0+(j==1 ? -2.0^-23 : 2.0^-23)) : Float64(i==j)) for i in 1:4,j in 1:4)
    JSimplex.refactorize!(f.inner,B)
    return f
end
function JSimplex.replace_column!(f::DualRecoveryFactor,d::AbstractVector,row::Integer;kwargs...)
    f.updates_attempted+=1
    error("Unexpected recovery factor update")
end
function JSimplex.copy_basis_factorization(f::DualRecoveryFactor)
    f.copies+=1
    error("Unexpected recovery factor copy")
end
function dual_recovery_observer(original,factor_ref)
    return (event,ws)->begin
        f=factor_ref[]
        if !isnothing(f)
            f.observer_ok &= ws.factorization===f
            f.staged_seen |= JSimplex._is_staged_workspace(ws)
            if event==:correction_attempt
                f.correction_events+=1
                f.observer_ok &= f.rejection_events==0
            elseif event==:pivot_rejected
                f.rejection_events+=1
                f.observer_ok &= f.correction_events==1
            elseif event==:refactor_pivot
                f.refresh_events+=1
                f.observer_ok &= (f.ftran,f.btran,f.refactors,f.invalidations)==(2,3,1,4)
            end
        end
        original(event,ws)
    end
end
function dual_recovery_budget_workspace(;manager,policy=nothing,diagnostics)
    B=[1.0 1.0 0.0 0.0;1.0-2.0^-23 1.0+2.0^-23 0.0 0.0;
       0.0 0.0 1.0 0.0;0.0 0.0 0.0 1.0]
    p=LinearProblem(sparse(hcat(B,B[:,1])),zeros(5);row_lower=-B[:,2],row_upper=-B[:,2])
    options=SolverOptions(algorithm=:dual,simplex_strategy=:legacy,basis_update=manager,
        pricing=:dantzig,verbose=false)
    isnothing(policy) && (policy=JSimplex.NumericalPolicy(Float64))
    @assert !policy.hypersparse && !policy.solve_refinement && !policy.recovery && !policy.pivot_validation
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
    ws.basis.basic_indices .= 1:4
    ws.basis.states[1:4] .= JSimplex.BASIC
    ws.basis.states[6:9] .= JSimplex.AT_LOWER
    JSimplex.recompute!(ws;refactorize=true)
    factor=DualRecoveryFactor(ws.factorization)
    return JSimplex.SimplexWorkspace((k==:factorization ? factor : getfield(ws,k) for k in fieldnames(typeof(ws)))...)
end
dual_recovery_kernels(d)=ntuple(i->d.kernel_calls[(:ftran,:btran,:refactorization)[i]],3)
function check_dual_recovery_work(ws,diagnostics,kernels_before;refresh=false)
    f=ws.factorization
    @test (f.ftran,f.prepared,f.ordinary)==(2+refresh,2,Int(refresh))
    @test (f.btran,f.unit,f.correction,f.cost)==(3+refresh,2,1,Int(refresh))
    @test (f.refactors,f.invalidations,f.metadata,f.hits,f.copies,f.updates_attempted)==(Int(refresh),4+2refresh,2,2,0,0)
    @test dual_recovery_kernels(diagnostics).-kernels_before==(2+refresh,3+refresh,Int(refresh))
    @test f.observer_ok && f.staged_seen
    @test (f.correction_events,f.rejection_events,f.refresh_events)==(1,1,Int(refresh))
    @test get(diagnostics.counts,:pivot_completed,0)==get(diagnostics.counts,:bound_flipped,0)==0
end

@testset "Dual cannot exchange a basic column for its exact duplicate" begin
    for strategy in (:legacy,:adaptive), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws=duplicate_dual_column_workspace(;strategy,manager)
        @test issuccess(lu(Matrix{Rational{BigInt}}(JSimplex.basis_matrix(ws));check=false))
        @test ws.primal[2] < -0.9
        before=copy(ws.basis.basic_indices)
        terminal=JSimplex.dual_iteration!(ws,()->false)
        @test ws.basis.basic_indices == before
        @test ws.iterations == 0
        @test issuccess(lu(Matrix{Rational{BigInt}}(JSimplex.basis_matrix(ws));check=false))
        @test !isnothing(terminal) && terminal.status==JSimplex.NUMERICAL_ERROR
    end
end

@testset "Failed dual pivot recovery remains bounded and unpublished" begin
    for mode in (:exhausted,:cancelled,:callback_error,:numerical_callback_error), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        rejected=Ref(0);cancelled=Ref(false)
        observer=(event,ws)->begin
            if event==:pivot_rejected
                rejected[]+=1
                mode==:cancelled && (cancelled[]=true)
                mode==:callback_error && error("rejected pivot observer")
                mode==:numerical_callback_error && throw(SingularException(7))
            end
            nothing
        end
        policy=JSimplex.NumericalPolicy(Float64;max_pivot_candidates=mode==:cancelled ? 2 : 1,max_recovery_rounds=0)
        factor_ref=Ref{Any}(nothing)
        diagnostics=JSimplex.SimplexDiagnostics(;observer=dual_recovery_observer(observer,factor_ref),kernel_timing=true)
        ws=dual_recovery_budget_workspace(;manager,policy,diagnostics)
        factor_ref[]=ws.factorization
        kernels_before=dual_recovery_kernels(diagnostics)
        before=(copy(ws.primal),copy(ws.costs),copy(ws.reduced_costs),copy(ws.basis.states),
                copy(ws.basis.basic_indices),ws.iterations,ws.refactorizations)
        if mode==:callback_error
            @test_throws JSimplex.DiagnosticObserverFailure{ErrorException} JSimplex.dual_iteration!(ws,()->cancelled[])
        elseif mode==:numerical_callback_error
            @test_throws JSimplex.DiagnosticObserverFailure{SingularException} JSimplex.dual_iteration!(ws,()->cancelled[])
        else
            terminal=JSimplex.dual_iteration!(ws,()->cancelled[])
            @test terminal.status==(mode==:cancelled ? JSimplex.TIME_LIMIT : JSimplex.NUMERICAL_ERROR)
        end
        @test rejected[]==1
        @test before==(ws.primal,ws.costs,ws.reduced_costs,ws.basis.states,
                       ws.basis.basic_indices,ws.iterations,ws.refactorizations)
        @test isempty(ws.scratch.rejected_rows) && isempty(ws.scratch.rejected_entering)
        @test isempty(ws.factorization.updates)
        check_dual_recovery_work(ws,diagnostics,kernels_before;refresh=false)
    end
end

@testset "Consistent small dual pivots retain the direct path" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        T in (BigFloat,Rational{BigInt}) && manager!=:pfi && continue
        coefficient=T(1//1000000)
        p=LinearProblem(sparse(reshape(T[coefficient],1,1)),T[0];row_lower=T[1])
        diagnostics=JSimplex.SimplexDiagnostics()
        options=SolverOptions(T;algorithm=:dual,basis_update=manager,pricing=:dantzig,verbose=false)
        ws=JSimplex.initialize_workspace(p,options;progress=JSimplex.SimplexProgressContext(p;diagnostics))
        @test isnothing(JSimplex.dual_iteration!(ws,()->false))
        @test ws.basis.basic_indices==[1]
        @test ws.primal[1]≈T(1000000)
        @test ws.refactorizations==0
        @test get(diagnostics.counts,:pivot_rejected,0)==0
        @test eltype(ws.primal)===T
    end
end

@testset "Cancellation after dual refresh cannot publish a pivot" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        cancelled=Ref(false)
        observer=(event,ws)->(event==:refactor_pivot && (cancelled[]=true);nothing)
        factor_ref=Ref{Any}(nothing)
        diagnostics=JSimplex.SimplexDiagnostics(;observer=dual_recovery_observer(observer,factor_ref),kernel_timing=true)
        ws=dual_recovery_budget_workspace(;manager,diagnostics)
        factor_ref[]=ws.factorization
        kernels_before=dual_recovery_kernels(diagnostics)
        before=(copy(ws.primal),copy(ws.costs),copy(ws.reduced_costs),
                copy(ws.basis.states),copy(ws.basis.basic_indices))
        refs=ws.refactorizations
        terminal=JSimplex.dual_iteration!(ws,()->cancelled[])
        @test terminal.status==JSimplex.TIME_LIMIT
        @test before==(ws.primal,ws.costs,ws.reduced_costs,ws.basis.states,ws.basis.basic_indices)
        @test ws.iterations==0
        @test ws.refactorizations==refs+1
        @test get(diagnostics.counts,:pivot_completed,0)==0
        @test get(diagnostics.counts,:bound_flipped,0)==0
        @test isempty(ws.scratch.rejected_rows) && isempty(ws.scratch.rejected_entering)
        check_dual_recovery_work(ws,diagnostics,kernels_before;refresh=true)
    end
end
