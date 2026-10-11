# Private S2 control fixtures. No source rewriting or incremental flags.
# Includes are safe only in a serial guarded Julia job. No timing claim is made.
module PrimalFlipFixtures
using JSimplex, SparseArrays, LinearAlgebra
const JS = JSimplex
const MANAGERS = (:pfi, :huangfu_hall, :forrest_tomlin, :suhl_suhl, :bartels_golub)
const BACKENDS = (:native, :markowitz)
const KINDS = (:flip_then_pivot, :flip_chain, :flip_then_unbounded, :scheduled_flip)

function problem(::Type{T}, kind::Symbol) where T
    if kind == :flip_then_pivot
        return JS.LinearProblem(sparse(reshape(T[1, 1], 1, 2)), T[-2, -1];
            row_upper=T[5], column_upper=T[1, 10])
    elseif kind == :flip_chain
        return JS.LinearProblem(sparse(ones(T, 1, 4)), T[-4, -3, -2, -1];
            row_upper=T[5], column_upper=ones(T, 4))
    elseif kind == :flip_then_unbounded
        return JS.LinearProblem(sparse(reshape(T[1, 0], 1, 2)), T[-2, -1];
            row_upper=T[2], column_upper=[one(T), nothing])
    elseif kind == :scheduled_flip
        # A real first pivot leaves a nonempty history. The second variable flips.
        return JS.LinearProblem(sparse(Matrix{T}(I, 2, 2)), T[-3, -2];
            row_upper=T[1, 3], column_upper=[nothing, one(T)])
    end
    error("Unknown fixture: $kind")
end

function deadline(ws, diagnostics)
    context = JS.SolveContext(time_ns(), Inf, diagnostics, ws.progress.numerical_policy)
    return JS._guard_stop_callback(JS._SolveDeadline(context))
end

function workspace(::Type{T}, kind; manager=:pfi, backend=:native) where T
    p = problem(T, kind)
    options = JS.SolverOptions(T; algorithm=:primal, pricing=:dantzig,
        simplex_strategy=:legacy, presolve=false, partial_pricing=false,
        basis_update=manager, basis_refactorization=backend,
        refactorization_interval=160, iteration_limit=100, time_limit=Inf,
        verbose=false)
    policy = JS.NumericalPolicy(T, options)
    @assert !policy.incremental_primal && !policy.incremental_primal_pivots
    @assert !policy.adaptive_refactor
    # Tiny characterization only: scalar trace records, no retained workspace.
    events = NamedTuple[]
    observer = function (event, ws)
        event in (:flip_completed, :pivot_completed) || return nothing
        push!(events, (event=string(event), iteration=ws.iterations,
            selected_row=ws.scratch.selected_row,
            step=string(ws.scratch.last_primal_step),
            updates=length(ws.factorization.updates), refactors=ws.refactorizations))
        return nothing
    end
    diagnostics = JS.SimplexDiagnostics(; observer, kernel_timing=true)
    ws = JS.initialize_workspace(p, options; progress=JS.SimplexProgressContext(p;
        numerical_policy=policy, diagnostics))
    @assert JS._primal_feasible(ws)
    preparation = NamedTuple[]
    if kind == :scheduled_flip
        terminal = JS._primal_iteration!(ws, deadline(ws, diagnostics), options.dual_tolerance)
        @assert isnothing(terminal)
        @assert length(events) == 1 && only(events).event == "pivot_completed"
        @assert length(ws.factorization.updates) == 1
        append!(preparation, events)
        empty!(events)
        # Owned fixture setup before invocation, never an observer mutation.
        ws.dual_refactorization_interval = 1
        @assert JS._scheduled_refactor_reason(ws, :primal) == :limit
    end
    for key in keys(diagnostics.kernel_calls)
        diagnostics.kernel_calls[key] = 0
        diagnostics.kernel_nanoseconds[key] = 0
    end
    for key in keys(diagnostics.counts)
        diagnostics.counts[key] = 0
    end
    empty!(diagnostics.events)
    diagnostics.next_event = 1
    return (; problem=p, ws, diagnostics, events, preparation)
end
end
