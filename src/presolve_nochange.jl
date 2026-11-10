struct _DependentRowsSnapshot{T<:Real}
    A::SparseMatrixCSC{T,Int}
    row_lower::Vector{Bound{T}}
    row_upper::Vector{Bound{T}}
end

mutable struct _DependentRowsCache{T<:Real}
    snapshot::Union{Nothing,_DependentRowsSnapshot{T}}
end

_DependentRowsCache{T}() where {T<:Real} = _DependentRowsCache{T}(nothing)

function _cached_dependent_rows!(cache::_DependentRowsCache{T},
                                 problem::LinearProblem{T}) where {T}
    A = problem.A
    m, n = size(A)
    eligible = (T === Float32 || T === Float64) &&
        m <= 256 && n <= 10_000 && length(A.nzval) <= 10_000
    snapshot = cache.snapshot
    if eligible && !isnothing(snapshot) &&
       size(snapshot.A) == (m, n) &&
       isequal(snapshot.A.colptr, A.colptr) &&
       isequal(snapshot.A.rowval, A.rowval) &&
       isequal(snapshot.A.nzval, A.nzval) &&
       isequal(snapshot.row_lower, problem.row_lower) &&
       isequal(snapshot.row_upper, problem.row_upper)
        return identity_presolve(problem)
    end

    # Only an unchanged result can populate the cache. Clear the old key
    # before calling the pass, including when the model exceeds the cap.
    cache.snapshot = nothing
    result = reduce_dependent_rows(problem)
    if eligible && result isa PresolveResult &&
       result.problem === problem && isempty(result.postsolve_stack)
        cache.snapshot = _DependentRowsSnapshot(copy(A), copy(problem.row_lower),
                                               copy(problem.row_upper))
    end
    return result
end

_cached_dependent_rows!(::Nothing, p) = reduce_dependent_rows(p)
