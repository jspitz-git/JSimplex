# Restoring an activated upper inequality must also relabel its slack on the
# ordinary (no-dual-witness) fallback path.
struct InequalityActivationStep{T<:Real} <: AbstractPostsolveStep
    columns::Int
    rows::Int
    sides::Vector{Tuple{Int,Bool}}
end
function postsolve_primal(step::InequalityActivationStep, x)
    length(x)==step.columns || throw(ArgumentError("activation primal dimensions"))
    return x
end
function restore_basis(step::InequalityActivationStep, basis::Basis)
    restored=Basis(basis.basic_indices,basis.states)
    n=step.columns
    length(basis.states)==n+step.rows && length(basis.basic_indices)==step.rows ||
        throw(ArgumentError("activation basis dimensions"))
    for (row,upper) in step.sides
        restored.states[n+row] == BASIC && continue
        restored.states[n+row] = upper ? AT_UPPER : AT_LOWER
    end
    return restored
end

# All built-in records retain the model's scalar type. The aggregate history has
# one concrete vector type regardless of the number and kinds of reductions.
const PostsolveStep{T} = Union{PresolveMap{T},SingletonRowStep{T},
    SingletonEqualityStep{T},SparseEqualityStep{T},DoubletonStep{T},BoundPropagationStep{T},InequalityActivationStep{T}}
const _PRESOLVE_PASS_COUNT = 9

function _apply_presolve_pass!(pass::F, problem::LinearProblem{T},
                               steps::Vector{PostsolveStep{T}}, trace, history=nothing) where {F,T}
    next = pass(problem)
    next isa PresolveFailure && return next
    _record_presolve!(history,problem,next)
    changed = !isempty(next.postsolve_stack)
    if changed
        append!(steps, next.postsolve_stack)
        _advance_propagation_trace!(trace, next)
    end
    return (changed ? next.problem : problem), changed
end

function _apply_propagation_pass!(problem::LinearProblem{T},
                                  steps::Vector{PostsolveStep{T}}, trace,
                                  directed_bounds::Bool=true, history=nothing) where {T}
    dirty = isnothing(trace.reference) ? trues(size(problem.A, 1)) :
        _changed_propagation_rows(trace.reference, problem,
            trace.row_origin, trace.column_origin, trace.pending)
    changed_columns = falses(size(problem.A, 2))
    builder = isnothing(history) ? nothing : _PropagationHistory.Builder(T)
    next = _propagate_row_bounds(problem, dirty, changed_columns; directed_bounds, history=builder)
    next isa PresolveFailure && return next
    changed = !isempty(next.postsolve_stack)
    if changed
        group = isnothing(builder) ? nothing : _PropagationHistory.finish!(builder,problem)
        _record_presolve!(history,problem,next,group)
        append!(steps,next.postsolve_stack)
    end
    _reset_propagation_trace!(trace, next, changed_columns)
    return (changed ? next.problem : problem), changed
end

function _dispatch_presolve_pass!(problem, steps, trace, index::Int,
                                  directed_bounds::Bool=true, history=nothing,
                                  rounded_costs::Bool=false, dependent_cache=nothing, strict_objective::Bool=false)
    index == 1 && return _apply_presolve_pass!(_presolve_basic, problem, steps, trace, history)
    index == 2 && return _apply_presolve_pass!(reduce_singleton_rows, problem, steps, trace, history)
    index == 3 && return _apply_presolve_pass!(p -> aggregate_singleton_equalities(p;rounded_costs=!strict_objective), problem, steps, trace, history)
    index == 4 && return _apply_presolve_pass!(p -> aggregate_sparse_equalities(p;rounded_costs), problem, steps, trace, history)
    index == 5 && return _apply_presolve_pass!(reduce_parallel_rows, problem, steps, trace, history)
    index == 6 && return _apply_presolve_pass!(p -> _cached_dependent_rows!(dependent_cache,p), problem, steps, trace, history)
    index == 7 && return _apply_presolve_pass!(p -> substitute_free_doubleton(p;rounded_costs), problem, steps, trace, history)
    index == 8 && return _apply_propagation_pass!(problem, steps, trace, directed_bounds, history)
    index == 9 && return _apply_presolve_pass!(reduce_dual_fixings, problem, steps, trace, history)
    throw(ArgumentError("unknown presolve pass: $index"))
end

# Split the finite record union explicitly, including when its size exceeds the
# compiler's automatic union-splitting limit. Both restoration paths use this.
function _apply_postsolve_step(f::F, step::PostsolveStep{T}, value) where {F,T}
    step isa PresolveMap{T} && return f(step, value)
    step isa SingletonRowStep{T} && return f(step, value)
    step isa SingletonEqualityStep{T} && return f(step, value)
    step isa SparseEqualityStep{T} && return f(step, value)
    step isa DoubletonStep{T} && return f(step, value)
    step isa BoundPropagationStep{T} && return f(step, value)
    return f(step::InequalityActivationStep{T}, value)
end

function _postsolve_primal(steps::Vector{PostsolveStep{T}}, x) where {T}
    for index in reverse(eachindex(steps))
        x = _apply_postsolve_step(postsolve_primal, steps[index], x)
    end
    return x
end

function _restore_basis(steps::Vector{PostsolveStep{T}}, basis::Basis) where {T}
    restored = Basis(basis.basic_indices, basis.states)
    for index in reverse(eachindex(steps))
        restored = _apply_postsolve_step(restore_basis, steps[index], restored)
    end
    return restored
end
