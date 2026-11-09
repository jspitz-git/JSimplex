# All built-in records retain the model's scalar type. The aggregate history has
# one concrete vector type regardless of the number and kinds of reductions.
const PostsolveStep{T} = Union{PresolveMap{T},SingletonRowStep{T},
    SingletonEqualityStep{T},SparseEqualityStep{T},DoubletonStep{T},BoundPropagationStep{T}}
const _PRESOLVE_PASS_COUNT = 9

function _apply_presolve_pass!(pass::F, problem::LinearProblem{T},
                               steps::Vector{PostsolveStep{T}}, trace) where {F,T}
    next = pass(problem)
    next isa PresolveFailure && return next
    changed = !isempty(next.postsolve_stack)
    if changed
        append!(steps, next.postsolve_stack)
        _advance_propagation_trace!(trace, next)
    end
    return (changed ? next.problem : problem), changed
end

function _apply_propagation_pass!(problem::LinearProblem{T},
                                  steps::Vector{PostsolveStep{T}}, trace) where {T}
    dirty = isnothing(trace.reference) ? trues(size(problem.A, 1)) :
        _changed_propagation_rows(trace.reference, problem,
            trace.row_origin, trace.column_origin, trace.pending)
    changed_columns = falses(size(problem.A, 2))
    next = _propagate_row_bounds(problem, dirty, changed_columns)
    next isa PresolveFailure && return next
    changed = !isempty(next.postsolve_stack)
    changed && append!(steps, next.postsolve_stack)
    _reset_propagation_trace!(trace, next, changed_columns)
    return (changed ? next.problem : problem), changed
end

function _dispatch_presolve_pass!(problem, steps, trace, index::Int)
    index == 1 && return _apply_presolve_pass!(_presolve_basic, problem, steps, trace)
    index == 2 && return _apply_presolve_pass!(reduce_singleton_rows, problem, steps, trace)
    index == 3 && return _apply_presolve_pass!(aggregate_singleton_equalities, problem, steps, trace)
    index == 4 && return _apply_presolve_pass!(aggregate_sparse_equalities, problem, steps, trace)
    index == 5 && return _apply_presolve_pass!(reduce_parallel_rows, problem, steps, trace)
    index == 6 && return _apply_presolve_pass!(reduce_dependent_rows, problem, steps, trace)
    index == 7 && return _apply_presolve_pass!(substitute_free_doubleton, problem, steps, trace)
    index == 8 && return _apply_propagation_pass!(problem, steps, trace)
    index == 9 && return _apply_presolve_pass!(reduce_dual_fixings, problem, steps, trace)
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
    return f(step::BoundPropagationStep{T}, value)
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
