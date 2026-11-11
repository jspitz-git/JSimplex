# Private work shared only by audited readers in one presolve call. Row entries
# and their CSC snapshot are read-only while cached; there is no cross-solve
# retention and no task may inherit another task's mutable session.
module _PresolveWork

using SparseArrays
const JS = parentmodule(@__MODULE__)
const Q = Rational{BigInt}
const _session_key = gensym(:presolve_work)

mutable struct Session{T}
    exact::Dict{T,Q}
    matrix::Union{Nothing,SparseMatrixCSC{T,Int}}
    rows::Vector{Vector{Tuple{Int,T}}}
    lower::Vector{JS.Bound{T}}
    upper::Vector{JS.Bound{T}}
    costs::Vector{T}
    constant::T
    sense::JS.ObjectiveSense
    policy::Bool
    environment::Tuple
    rejected::Dict{Int,Vector{JS.Bound{T}}}
    qcap::Int
    rcap::Int
    qbytes::Int
    bytecap::Int
end

function Session(::Type{T}, qcap, rcap, bytecap) where {T}
    Session{T}(Dict{T,Q}(), nothing, Vector{Tuple{Int,T}}[],
        JS.Bound{T}[], JS.Bound{T}[], T[], zero(T), JS.MIN_SENSE,
        false, (), Dict{Int,Vector{JS.Bound{T}}}(), qcap, rcap, 0, bytecap)
end

function current(::Type{T}) where {T}
    session = get(task_local_storage(), _session_key, nothing)
    return session isa Session{T} ? session : nothing
end

function with_session(f, ::Type{T}; qcap=100_000, rcap=100_000,
                      bytecap=64 * 1024^2) where {T}
    T in (Float32, Float64, BigFloat) || return f()
    session = Session(T, qcap, rcap, bytecap)
    # Base restores the previous value in finally, including nested exceptions.
    # New Tasks have separate, initially empty task-local storage.
    return task_local_storage(f, _session_key, session)
end

function clear_rejections!()
    session = get(task_local_storage(), _session_key, nothing)
    session isa Session && empty!(session.rejected)
    return nothing
end

# BigFloat is mutable: copy(x) and T(x) need not own its MPFR payload.
owned(x) = copy(x)
owned(x::BigFloat) = deepcopy(x)
owned(x::Array{BigFloat}) = deepcopy(x)
owned(x::Array{JS.Bound{BigFloat}}) = deepcopy(x)
function owned(x::SparseMatrixCSC{T,Int}) where {T}
    k=nnz(x);nr=length(x.rowval);nv=length(x.nzval)
    if nr==k && nv==k
        return SparseMatrixCSC{T,Int}(size(x,1),size(x,2),
            copy(x.colptr),copy(x.rowval),copy(x.nzval))
    end
    # Julia's CSC constructor requires canonical buffer lengths. Construct the
    # logical prefix first, then retain the caller's independent spare tails.
    # Ordinary canonical matrices still copy each buffer exactly once above.
    rowval=Vector{Int}(undef,k);nzval=Vector{T}(undef,k)
    copyto!(rowval,1,x.rowval,1,k);copyto!(nzval,1,x.nzval,1,k)
    result=SparseMatrixCSC{T,Int}(size(x,1),size(x,2),copy(x.colptr),rowval,nzval)
    if nr>k
        resize!(rowval,nr);copyto!(rowval,k+1,x.rowval,k+1,nr-k)
    end
    if nv>k
        resize!(nzval,nv);copyto!(nzval,k+1,x.nzval,k+1,nv-k)
    end
    return result
end
owned(x::SparseMatrixCSC{BigFloat,Int}) = deepcopy(x)

samevalue(a, b) = isequal(a, b)
samevalue(a::BigFloat, b::BigFloat) =
    isequal(a, b) && precision(a) == precision(b)
samevalue(a::JS.Bound{BigFloat}, b::JS.Bound{BigFloat}) =
    isfinite(a) == isfinite(b) && samevalue(a.value, b.value)
samevalues(a, b) = isequal(a, b)
function samevalues(a::AbstractArray{T}, b::AbstractArray{T}) where
        {T<:Union{BigFloat,JS.Bound{BigFloat}}}
    axes(a) == axes(b) || return false
    for i in eachindex(a, b)
        samevalue(a[i], b[i]) || return false
    end
    return true
end

# This deliberately does not call JS._exact_rational: its scalar methods route
# here. Preserve the original conversion's treatment of stored MPFR precision.
original_exact(v) = Q(v)
original_exact(v::BigFloat) =
    setprecision(BigFloat, max(precision(v), precision(BigFloat))) do
        Q(v)
    end

# Native keys are bounded by qcap. Account for the arbitrarily large BigFloat
# key and rational payloads without traversing the whole session.
keybytes(v, q::Q) = 0
keybytes(v::BigFloat, q::Q) = 512 + cld(precision(v), 8) +
    cld(ndigits(numerator(q); base=2), 8) +
    cld(ndigits(denominator(q); base=2), 8)

function exact(v::T) where {T}
    session = current(T)
    isnothing(session) && return original_exact(v)
    # A callback may change DAZ/FTZ during presolve. Never reuse a subnormal's
    # conversion across modes; retain Julia's original result or exception.
    if (T in (Float32, Float64) && issubnormal(v)) ||
            (T === BigFloat && !isfinite(v))
        return original_exact(v)
    end
    cached = get(session.exact, v, nothing)
    isnothing(cached) || return cached
    q = original_exact(v)
    if length(session.exact) < session.qcap
        cost = keybytes(v, q)
        if cost <= session.bytecap - session.qbytes
            session.exact[T === BigFloat ? owned(v) : v] = q
            session.qbytes += cost
        end
    end
    return q
end

same(a::SparseMatrixCSC, b::SparseMatrixCSC) =
    size(a) == size(b) && isequal(a.colptr, b.colptr) &&
    isequal(a.rowval, b.rowval) && samevalues(a.nzval, b.nzval)

function rows(A::SparseMatrixCSC{T,Int}) where {T}
    session = current(T)
    isnothing(session) && return JS._row_entries(A)
    environment = (precision(BigFloat), rounding(BigFloat), rounding(T),
        get_zero_subnormals())
    if isnothing(session.matrix) || !isequal(session.environment, environment) ||
            !same(session.matrix, A)
        # Clear first: every row reader shares this matrix/environment owner.
        # A rows-only reader must not publish data with stale rejections.
        empty!(session.rejected)
        snapshot = owned(A)
        data = JS._row_entries(snapshot)
        session.matrix = snapshot
        session.rows = data
        session.environment = environment
    end
    return session.rows
end

function entries(problem::JS.LinearProblem{T}, policy::Bool) where {T}
    session = current(T)
    isnothing(session) && return JS._row_entries(problem.A)
    data = rows(problem.A)
    lower = samevalues(session.lower, problem.row_lower)
    upper = samevalues(session.upper, problem.row_upper)
    costs = samevalues(session.costs, problem.objective)
    if !lower || !upper || !costs ||
            !samevalue(session.constant, problem.objective_constant) ||
            session.sense != problem.objective_sense || session.policy != policy
        empty!(session.rejected)
        lower || (session.lower = owned(problem.row_lower))
        upper || (session.upper = owned(problem.row_upper))
        costs || (session.costs = owned(problem.objective))
        session.constant = owned(problem.objective_constant)
        session.sense = problem.objective_sense
        session.policy = policy
    end
    return data
end

# entries must establish the matrix and global dependencies before these two
# helpers are used. Bounds are checked only on the columns of this equality.
function rejected(problem::JS.LinearProblem{T}, row, terms) where {T}
    session = current(T)
    isnothing(session) && return false
    bounds = get(session.rejected, row, nothing)
    isnothing(bounds) && return false
    length(bounds) == 2length(terms) || return false
    for k in eachindex(terms)
        j = terms[k][1]
        samevalue(bounds[2k - 1], problem.column_lower[j]) &&
            samevalue(bounds[2k], problem.column_upper[j]) || return false
    end
    return true
end

function remember!(problem::JS.LinearProblem{T}, row, terms) where {T}
    session = current(T)
    isnothing(session) && return nothing
    length(session.rejected) >= session.rcap &&
        !haskey(session.rejected, row) && return nothing
    bounds = Vector{JS.Bound{T}}(undef, 2length(terms))
    for (k, (j, _)) in enumerate(terms)
        bounds[2k - 1] = problem.column_lower[j]
        bounds[2k] = problem.column_upper[j]
    end
    session.rejected[row] = T === BigFloat ? owned(bounds) : bounds
    return nothing
end

end # module _PresolveWork
