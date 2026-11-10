# A history belongs to one optimization, never to the infeasibility proof LP.
# No workspace/factorization/model is retained; column snapshots are owned.
mutable struct _PostsolveHistory{T}
    metadata::Vector{_PostsolveLift.Metadata{T}}
    propagation::Vector{Union{Nothing,_PropagationHistory.Group{T}}}
end
_PostsolveHistory(::Type{T}) where T = _PostsolveHistory(
    _PostsolveLift.Metadata{T}[], Union{Nothing,_PropagationHistory.Group{T}}[])
_history_mark(::Nothing) = 0
_history_mark(h::_PostsolveHistory) = length(h.metadata)
_restore_history_mark!(::Nothing, mark) = nothing
function _restore_history_mark!(h::_PostsolveHistory, mark)
    resize!(h.metadata, mark)
    resize!(h.propagation, mark)
    return nothing
end
_record_presolve!(::Nothing, p, next, group=nothing) = nothing
function _record_presolve!(h::_PostsolveHistory, p, next, group=nothing)
    (next isa PresolveFailure || isempty(next.postsolve_stack)) && return nothing
    push!(h.metadata, _PostsolveLift.metadata(p, next, 0))
    push!(h.propagation, group)
    return nothing
end

# Discard all speculative metadata if a pass fails or the tolerance envelope
# causes the original model to be retained. Proof calls receive history=nothing.
function _history_transaction(f, history)
    mark = _history_mark(history)
    try
        result = f()
        if result isa PresolveFailure || isempty(result.postsolve_stack)
            _restore_history_mark!(history, mark)
        end
        return result
    catch
        _restore_history_mark!(history, mark)
        rethrow()
    end
end

function _postsolve_with_dual(history::_PostsolveHistory, presolved, scaling, run, options)
    x = unscale_primal(scaling, run.primal)
    if isempty(presolved.postsolve_stack) || isnothing(run.basis)
        return run.basis, postsolve_primal(presolved, x)
    end
    try
        length(history.metadata) == length(presolved.postsolve_stack) &&
            all(m.step === s for (m,s) in zip(history.metadata,presolved.postsolve_stack)) ||
            throw(ArgumentError("incomplete postsolve metadata"))
        isnothing(run.dual) && throw(ArgumentError("no reduced dual witness"))
        y = unscale_dual(scaling, run.dual)
        basis, _, primal = _PropagationHistory.chain(history.metadata,history.propagation,
            run.basis,y,x,options)
        return basis,primal
    catch exception
        exception isa ArgumentError || rethrow()
        # This is a basis hint. Inconclusive reconstruction keeps the original
        # restoration and certified original-model cleanup, without a new solve.
        return restore_basis(presolved,run.basis), postsolve_primal(presolved,x)
    finally
        _restore_history_mark!(history,0)
    end
end
function _postsolve_with_dual(::Nothing, presolved, scaling, run, options)
    x=postsolve_primal(presolved,unscale_primal(scaling,run.primal))
    b=isnothing(run.basis) || isempty(presolved.postsolve_stack) ? run.basis : restore_basis(presolved,run.basis)
    return b,x
end
