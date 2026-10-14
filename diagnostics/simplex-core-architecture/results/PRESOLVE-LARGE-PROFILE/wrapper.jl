function profile_large_dispatch(current, steps, trace, index, round, observer)
    observer(:start, round, index, current, nothing)
    timed = @timed _dispatch_presolve_pass!(current, steps, trace, index)
    observer(:finish, round, index, current, timed)
    return timed.value
end
