# Explicit native Float64 experiment, loaded into JSimplex by diagnostics only.
# P*S*B*E = L*U; the backend represents inv(S)*P'*L, packed upper starts at U.
struct TrialLowerBackend
    lower::SparseMatrixCSC{Float64,Int}
    row_order::Vector{Int}
    scaling::Vector{Float64}
    divide_scaling::Bool
    fallback::Union{Nothing,UMFPACKBackend}
    work::Vector{Float64}
end
_backend_dimension(b::TrialLowerBackend)=length(b.work)
_backend_storage_count(b::TrialLowerBackend)=isnothing(b.fallback) ? nnz(b.lower) : _backend_storage_count(b.fallback)
sparse_solve_view(::TrialLowerBackend)=nothing
function _copy_backend(b::TrialLowerBackend)
    return TrialLowerBackend(b.lower,b.row_order,b.scaling,b.divide_scaling,
        isnothing(b.fallback) ? nothing : _copy_backend(b.fallback),similar(b.work))
end
function _backend_forward_solve!(destination::Vector,b::TrialLowerBackend,rhs::AbstractVector)
    isnothing(b.fallback) || return _backend_forward_solve!(destination,b.fallback,rhs)
    L=b.lower
    for row in eachindex(destination)
        original=b.row_order[row]
        destination[row]=b.divide_scaling ? rhs[original]/b.scaling[original] : rhs[original]*b.scaling[original]
    end
    # Native L is unit lower triangular, diagonal first in each CSC column.
    for column in eachindex(destination)
        value=destination[column]
        @inbounds for slot in (L.colptr[column]+1):(L.colptr[column+1]-1)
            destination[L.rowval[slot]]-=L.nzval[slot]*value
        end
    end
    return destination
end
function _backend_transpose_solve!(destination::Vector,b::TrialLowerBackend,rhs::AbstractVector)
    isnothing(b.fallback) || return _backend_transpose_solve!(destination,b.fallback,rhs)
    L=b.lower;work=b.work
    copyto!(work,rhs)
    for column in reverse(eachindex(work))
        value=work[column]
        @inbounds for slot in (L.colptr[column]+1):(L.colptr[column+1]-1)
            value-=L.nzval[slot]*work[L.rowval[slot]]
        end
        work[column]=value
    end
    for row in eachindex(work)
        original=b.row_order[row]
        destination[original]=b.divide_scaling ? work[row]/b.scaling[original] : work[row]*b.scaling[original]
    end
    return destination
end
function _trial_direct_factor(Factor,B)
    f=Factor(B)
    f.base isa UMFPACKBackend || return f
    n=_backend_dimension(f.base);F=f.base.factorization
    if isnothing(F)
        base=TrialLowerBackend(spzeros(0,0),Int[],Float64[],false,nothing,Float64[])
    else
        L,U,p,q,scaling=F.L,F.U,F.p,F.q,F.Rs
        divide=_umfpack_scale_mode(F,L,U,p,q,scaling)
        valid_lower=all(i->L.colptr[i]<L.colptr[i+1] &&
            L.rowval[L.colptr[i]]==i && L.nzval[L.colptr[i]]==1.0,1:n)
        if isnothing(divide) || !valid_lower
            base=TrialLowerBackend(spzeros(n,n),collect(1:n),ones(n),false,f.base,zeros(n))
        else
            base=TrialLowerBackend(L,p,scaling,divide,nothing,zeros(n))
            for column in 1:n
                packed=f.upper[column]
                empty!(packed.indices);empty!(packed.values)
                for slot in nzrange(U,column)
                    push!(packed.indices,U.rowval[slot]);push!(packed.values,U.nzval[slot])
                end
            end
            copyto!(f.column_order,q);copyto!(f.positions,invperm(q))
            _invalidate_dense_upper!(f)
        end
    end
    values=map(name->getfield(f,name),fieldnames(typeof(f)))
    return Factor{Float64,TrialLowerBackend}(base,Base.tail(values)...)
end
const TrialDirectFactor=Union{ForrestTomlinFactorization{Float64,TrialLowerBackend},
    SuhlSuhlFactorization{Float64,TrialLowerBackend},BartelsGolubFactorization{Float64,TrialLowerBackend}}
function refactorize!(f::TrialDirectFactor,B::AbstractMatrix{Float64})
    Factor=getfield(@__MODULE__,nameof(typeof(f)))
    candidate=_trial_direct_factor(Factor,B)
    # Construct the complete candidate before replacing any live state.
    for name in fieldnames(typeof(f))
        setfield!(f,name,getfield(candidate,name))
    end
    return f
end
function _install_trial_direct!()
    for (mode,Factor) in ((:forrest_tomlin,ForrestTomlinFactorization),
                         (:suhl_suhl,SuhlSuhlFactorization),(:bartels_golub,BartelsGolubFactorization))
        @eval function _basis_factorization(B::AbstractMatrix{Float64},options::SolverOptions{Float64,$(QuoteNode(mode)),:native})
            options.simplex_strategy==:legacy || return $Factor(B)
            return _trial_direct_factor($Factor,B)
        end
    end
    return nothing
end
