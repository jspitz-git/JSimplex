# Prospective ordinary Task2 tests. Julia syntax/runtime UNEXECUTED.
# Include after canonical Task1 refinement_outcome_tests-reviewed.jl.
module RecoveryWeightTests
using Test, LinearAlgebra, SparseArrays, JSimplex
using ..RefinementOutcomeTests
const J=JSimplex
const R=RefinementOutcomeTests

# Real delegated solves precede declarations. These faults test classification,
# not numerical accuracy of a native backend. No production methods overwritten.
mutable struct WeightProbe{T,F}
    factor::F
    updates::Vector{J.PackedEta{T}}
    failed_row::Int
    initial::Symbol
    correction::Symbol
    unit_calls::Int
    correction_calls::Int
    awaiting_correction::Bool
    failure::Exception
end
function J.transpose_solve!(dest::Vector{T},f::WeightProbe{T},rhs::Vector{T}) where T
    correction=f.awaiting_correction
    correction ? (f.correction_calls+=1) : (f.unit_calls+=1)
    ldiv!(dest,transpose(f.factor),rhs)
    mode=correction ? f.correction : f.unit_calls==f.failed_row ? f.initial : :real
    if mode==:half
        dest ./= T(2)
    elseif mode==:negative
        dest .*= -one(T)
    elseif mode==:zero
        fill!(dest,zero(T))
    elseif mode==:tiny
        fill!(dest,zero(T));dest[1]=nextfloat(zero(T))
    elseif mode==:huge
        fill!(dest,zero(T));dest[1]=ldexp(one(T),T===Float32 ? 127 : 1023)
    elseif mode==:inf
        fill!(dest,T(Inf))
    elseif mode==:nan
        fill!(dest,T(NaN))
    elseif mode==:throw
        throw(f.failure)
    end
    f.awaiting_correction=correction || mode!=:real
    dest
end
mutable struct Guard
    calls::Int
    true_at::Int
    throw_at::Int
    failure::Exception
end
function (g::Guard)()
    g.calls+=1
    g.calls==g.throw_at && throw(g.failure)
    g.calls==g.true_at
end
mutable struct Observer
    calls::Int
end
(o::Observer)(reason,ws)=(o.calls+=1;nothing)

function fixture(::Type{T}=Float64;failed_row=1,initial=:half,correction=:zero,
                 limit=3,pricing=:steepest_edge,state_mode=:none) where T
    A=sparse(Matrix{T}(I,2,2))
    p=J.LinearProblem(A,zeros(T,2);column_lower=fill(nothing,2))
    options=J.SolverOptions(T;verbose=false,time_limit=Inf,pricing)
    policy=J.NumericalPolicy(T;solve_refinement=false,max_refinements=limit,
                             adaptive_refactor=true,refactor_timing=false)
    observer=Observer(0);diag=J.SimplexDiagnostics(;observer)
    context=J.SimplexProgressContext(p;numerical_policy=policy,diagnostics=diag)
    native=lu(Matrix(A));failure=SingularException(37)
    factor=WeightProbe{T,typeof(native)}(native,J.PackedEta{T}[],failed_row,
        initial,correction,0,0,false,failure)
    states=vcat(fill(J.BASIC,2),fill(J.FREE_NONBASIC,2))
    ws=J.SimplexWorkspace(p,options,context,zeros(T,4),
        vcat(p.column_lower,p.row_lower),vcat(p.column_upper,p.row_upper),
        J.Basis([1,2],states),zeros(T,4),zeros(T,4),T[9,8,7,6],trues(4),factor,
        J.SimplexScratch(T,2,4),0,0,false,0,false,false,options.refactorization_interval,0,typemax(Int),0,0)
    ws.scratch.recovery_active=true
    fill!(ws.scratch.rho,T(3));fill!(ws.scratch.steepest_valid,true)
    ws.scratch.steepest_initialized=true
    if state_mode!=:none
        state=J.PricingState(T);state.algorithm=state_mode==:stale ? :primal : :dual
        state.switches=4;state.rejected_weights=5;state.resets=6;state.observations=7
        state.trial_until=11;state.progress_windows=2
        if state_mode==:temporary
            state.active=:dantzig;state.return_mode=:steepest_edge;state.temporary=true
        end
        ws.scratch.pricing=state
    end
    pool=J._pricing_pool!(ws,:dual);append!(pool.indices,[1,2]);pool.valid=true;pool.full_scan=true
    J._basis_matrix!(ws);J._pivot_quality_buffers(ws)
    guard=Guard(0,0,0,failure)
    (;ws,guard,factor,observer)
end
fields(r)=(r.ok,r.fallback_ready,r.failed_row,r.reason,r.refinement_cause)
function untouched_payload(ws)
    (copy(ws.primal),copy(ws.reduced_costs),copy(ws.costs),copy(ws.lower),copy(ws.upper),
     copy(ws.basis.basic_indices),copy(ws.basis.states),copy(ws.scratch.rho),ws.options,ws.factorization)
end
function owner_ids(ws)
    map(objectid,(ws.pricing_weights,ws.devex_reference,ws.basis.basic_indices,ws.basis.states,
                  ws.scratch.rho,ws.scratch.steepest_valid,ws.scratch.pricing_pool.indices))
end
function runtests()
    # Catches accepting a partial DSE rebuild, continuing past a failed row,
    # classifying unsafe provenance as finite inconclusive, and legacy opt-in.
    @testset "Recovery weight failure classification" begin
        for T in (Float32,Float64),row in (1,2)
            f=fixture(T;failed_row=row);before=untouched_payload(f.ws)
            result=J._rebuild_recovery_weights_result!(f.ws,f.guard;algorithm=:dual)
            @test fields(result)==(false,true,row,J._weight_finite_inconclusive,J._refine_unchanged)
            @test (f.factor.unit_calls,f.factor.correction_calls)==(row,1)
            @test f.guard.calls==row+1 # row stops plus one refinement stop, no classifier stop
            @test untouched_payload(f.ws)==before
            @test f.ws.pricing_weights[1:2]==(row==1 ? T[9,8] : T[1,8])
            @test !f.ws.dual_devex_fallback
            @test f.ws.scratch.pricing===nothing
            for mode in (:negative,:half)
                g=fixture(T;failed_row=row,correction=mode,limit=1)
                r=J._rebuild_recovery_weights_result!(g.ws,g.guard;algorithm=:dual)
                @test r.fallback_ready && r.failed_row==row
                @test r.refinement_cause==(mode==:negative ? J._refine_not_improved : J._refine_limit)
                @test (g.factor.unit_calls,g.factor.correction_calls)==(row,1)
            end
            h=fixture(T;failed_row=row,limit=0)
            r=J._rebuild_recovery_weights_result!(h.ws,h.guard;algorithm=:dual)
            @test r.fallback_ready && r.refinement_cause==J._refine_limit
            @test (h.factor.unit_calls,h.factor.correction_calls)==(row,0)
        end
        for T in (Float32,Float64)
            f=fixture(T;failed_row=0)
            r=J._rebuild_recovery_weights_result!(f.ws,f.guard;algorithm=:dual)
            @test r.ok && !r.fallback_ready && r.failed_row==0 && r.reason==J._weight_complete
            @test f.ws.pricing_weights==T[1,1,7,6]
            @test (f.factor.unit_calls,f.factor.correction_calls,f.guard.calls)==(2,0,2)
            @test !f.ws.dual_devex_fallback
        end
    end
    # Catches resetting only the failed row/prefix or mutating live-owned state.
    @testset "Partial DSE prefix is discarded" begin
        for T in (Float32,Float64)
            f=fixture(T;failed_row=2);live=fixture(T;failed_row=0)
            before=untouched_payload(f.ws);live_weights=copy(live.ws.pricing_weights)
            ids=owner_ids(f.ws);pool=f.ws.scratch.pricing_pool
            r=J._rebuild_recovery_weights_result!(f.ws,f.guard;algorithm=:dual)
            @test r.fallback_ready && f.ws.pricing_weights==T[1,8,7,6]
            calls=(f.factor.unit_calls,f.factor.correction_calls,f.guard.calls)
            @test J._prepare_recovery_devex!(f.ws)===nothing
            @test f.ws.pricing_weights==ones(T,4)
            @test f.ws.devex_reference==Bool[true,true,false,false]
            @test f.ws.dual_devex_fallback && J._weight_pricing(f.ws,:dual)==:devex
            @test untouched_payload(f.ws)==before && owner_ids(f.ws)==ids
            @test f.ws.scratch.pricing_pool===pool && isempty(pool.indices) && !pool.valid && !pool.full_scan
            @test (pool.basis_generation,pool.cost_generation)==(UInt(0),UInt(0))
            @test (f.factor.unit_calls,f.factor.correction_calls,f.guard.calls)==calls
            @test f.observer.calls==1 # only original correction_attempt; no reset callback
            @test J.recent_events(f.ws.progress.diagnostics)==[:correction_attempt]
            @test live.ws.pricing_weights==live_weights && !live.ws.dual_devex_fallback
        end
    end
    # Catches stale temporary Dantzig / wrong algorithm, double counter updates,
    # lost fixed-mode flag, or an auto-without-state that never becomes Devex.
    @testset "Fixed auto and temporary pricing transitions" begin
        for pricing in (:steepest_edge,:auto),mode in (:none,:fixed,:temporary)
            f=fixture(;pricing,state_mode=mode);ids=owner_ids(f.ws)
            state=f.ws.scratch.pricing;events=J.recent_events(f.ws.progress.diagnostics)
            @test J._prepare_recovery_devex!(f.ws)===nothing
            @test owner_ids(f.ws)==ids && f.observer.calls==0
            @test J.recent_events(f.ws.progress.diagnostics)==events
            @test J._effective_pricing(f.ws,:dual)==:devex
            @test f.ws.pricing_weights==ones(4) && f.ws.devex_reference==Bool[true,true,false,false]
            @test f.ws.dual_devex_fallback==(pricing!=:auto)
            current=f.ws.scratch.pricing
            if mode!=:none || pricing==:auto
                @test current.algorithm==:dual && current.active==:devex && current.return_mode==:devex
                @test !current.temporary && current.framework_valid && !current.needs_reset
                @test current.weight_quality==:valid && current.progress_windows==0
                @test (current.rejected_weights,current.switches,current.resets)==(mode==:none ? (1,1,1) : (6,5,7))
                @test !any(f.ws.scratch.steepest_valid) && !f.ws.scratch.steepest_initialized
                if mode!=:none
                    @test current===state && current.observations==7 && current.trial_until==11
                end
            else
                @test current===nothing
            end
        end
        for mode in (:stale,),active in (false,true)
            f=fixture(;state_mode=mode);f.ws.scratch.recovery_active=active
            weights=copy(f.ws.pricing_weights);state=f.ws.scratch.pricing
            @test_throws ArgumentError J._prepare_recovery_devex!(f.ws)
            @test f.ws.pricing_weights==weights && state.active==:steepest_edge
            @test f.observer.calls==0
        end
        f=fixture();f.ws.scratch.recovery_active=false
        @test_throws ArgumentError J._prepare_recovery_devex!(f.ws)
        @test f.ws.pricing_weights==[9,8,7,6] && !f.ws.dual_devex_fallback
    end
    @testset "Unknown route and unsafe work stay strict" begin
        for T in (Float32,Float64),algorithm in (:unspecified,:primal,:unknown)
            f=fixture(T)
            r=J._rebuild_recovery_weights_result!(f.ws,f.guard;algorithm)
            @test !r.ok && !r.fallback_ready && r.reason==J._weight_ineligible
            @test r.refinement_cause==J._refine_not_observed
            g=fixture(T)
            @test J._rebuild_recovery_weights!(g.ws,g.guard)===false
            @test (f.factor.unit_calls,f.factor.correction_calls)==(g.factor.unit_calls,g.factor.correction_calls)
            @test f.ws.pricing_weights==g.ws.pricing_weights && f.guard.calls==g.guard.calls
        end
        for T in (BigFloat,Rational{BigInt})
            f=fixture(T)
            r=J._rebuild_recovery_weights_result!(f.ws,f.guard;algorithm=:dual)
            @test !r.ok && !r.fallback_ready && r.refinement_cause==J._refine_not_observed
        end
        for T in (Float32,Float64),mode in (:zero,:tiny,:huge)
            f=fixture(T;initial=mode)
            r=J._rebuild_recovery_weights_result!(f.ws,f.guard;algorithm=:dual)
            @test !r.ok && !r.fallback_ready && r.reason==J._weight_invalid_norm
            @test f.factor.unit_calls==1 && f.factor.correction_calls==1
        end
        for T in (Float32,Float64),mode in (:inf,:nan)
            f=fixture(T;initial=mode)
            r=J._rebuild_recovery_weights_result!(f.ws,f.guard;algorithm=:dual)
            @test !r.fallback_ready && r.reason==J._weight_nonfinite_attempt
            @test r.refinement_cause==J._refine_nonfinite_initial_quality
            @test (f.factor.unit_calls,f.factor.correction_calls)==(1,0)
        end
        for T in (Float32,Float64)
            f=fixture(T;correction=:inf)
            r=J._rebuild_recovery_weights_result!(f.ws,f.guard;algorithm=:dual)
            @test !r.fallback_ready && r.reason==J._weight_nonfinite_attempt
            @test r.refinement_cause==J._refine_nonfinite_correction
            g=fixture(T);g.guard.true_at=2
            r=J._rebuild_recovery_weights_result!(g.ws,g.guard;algorithm=:dual)
            @test !r.fallback_ready && r.reason==J._weight_stopped && r.refinement_cause==J._refine_stopped
            @test (g.factor.unit_calls,g.factor.correction_calls,g.guard.calls)==(1,0,2)
            h=fixture(T);h.guard.true_at=1
            r=J._rebuild_recovery_weights_result!(h.ws,h.guard;algorithm=:dual)
            @test r.reason==J._weight_stopped && r.refinement_cause==J._refine_not_observed
            @test h.factor.unit_calls==0
        end
        for where_throw in (:initial,:correction,:stop)
            f=fixture(;initial=where_throw==:initial ? :throw : :half,
                      correction=where_throw==:correction ? :throw : :zero)
            where_throw==:stop && (f.guard.throw_at=2)
            caught=try J._rebuild_recovery_weights_result!(f.ws,f.guard;algorithm=:dual);nothing catch e;e end
            @test caught===f.factor.failure
            @test !f.ws.dual_devex_fallback
        end
        f=fixture(;state_mode=:stale)
        @test !J._rebuild_recovery_weights_result!(f.ws,f.guard;algorithm=:dual).fallback_ready
        for pricing in (:devex,:dantzig)
            f=fixture(;pricing)
            r=J._rebuild_recovery_weights_result!(f.ws,f.guard;algorithm=:dual)
            @test r.ok && r.reason==J._weight_not_needed && !r.fallback_ready
            @test f.factor.unit_calls==0 && f.guard.calls==0
        end
        # Component contract catches unknown metadata and invalid proposal erased
        # by a final finite quality. Task1 separately exercises actual provenance.
        for cause in (J._refine_not_observed,J._refine_reliable)
            f=fixture();q=J.SolveQuality(1.0,1/3,true,false)
            out=J._BasisRefinementOutcome(q,cause,false)
            r=J._failed_recovery_weight(f.ws,[0.5,0.0],out,1,:dual)
            @test !r.fallback_ready && r.reason==J._weight_ineligible
        end
        for T in (Float32,Float64)
            sc=R.scenario(:discarded_nonfinite_cleanup,T);f=R.fixture(sc,true)
            out=J._refine_basis_solve_outcome!(f.point,f.ws,f.rhs,f.policy,f.stop;transposed=true)
            @test out.quality.finite && out.invalid_seen
            r=J._failed_recovery_weight(f.ws,f.point,out,1,:dual)
            @test !r.fallback_ready && r.reason==J._weight_nonfinite_attempt
        end
    end
end
end
Base.invokelatest(RecoveryWeightTests.runtests)
