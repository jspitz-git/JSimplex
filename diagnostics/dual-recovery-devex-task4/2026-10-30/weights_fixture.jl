module Task4WeightFixture
using Test, LinearAlgebra, SparseArrays, JSimplex
const J=JSimplex

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
                 limit=3,pricing=:steepest_edge,state_mode=:none,scale=one(T)) where T
    A=sparse(scale*Matrix{T}(I,2,2))
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
end
