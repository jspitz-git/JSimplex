function profile_large_presolve(problem::LinearProblem{T}, observer) where {T}
    # Individual passes retain their small tuple results. The complete history
    # has runtime length, so accumulate it without changing the result's type.
    steps = PostsolveStep{T}[]
    current = problem
    propagation_trace = PropagationTrace{T}()
    last_relevant_pass = _PRESOLVE_PASS_COUNT
    for round in 1:12
        last_changed_pass = 0
        for index in 1:_PRESOLVE_PASS_COUNT
            index > last_relevant_pass && break
            next = profile_large_dispatch(current, steps, propagation_trace, index, round, observer)
            next isa PresolveFailure && return next
            current, changed = next
            if changed
                last_changed_pass = index
                last_relevant_pass = _PRESOLVE_PASS_COUNT
            end
        end
        last_changed_pass == 0 && break
        # Later passes already saw the final model in this round. Revisit them
        # only if an earlier pass changes that model in the next round.
        last_relevant_pass = last_changed_pass
    end
    return PresolveResult(current, steps, size(problem.A, 2))
end
