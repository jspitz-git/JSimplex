# UNEXECUTED. Existing raw extraction, triangle/permutation helpers and export type unchanged.
function _bgx_checked_basis_lu(L::SparseMatrixCSC{Float64,Int},U::SparseMatrixCSC{Float64,Int},
                           p::Vector{Int},q::Vector{Int},scaling::Vector{Float64},divide::Bool,owner;allocate=_bgx_allocate)
    try
        n=size(L,1)
        _check_export_triangle(L,n,true)
        _check_export_triangle(U,n,false)
        seen=_bgx_scratch!(owner,:seen,n,nnz(L),nnz(U);allocate)
        _check_export_permutation(p,n,seen)
        _check_export_permutation(q,n,seen)
        length(scaling)==n && all(s->isfinite(s) && s>0.0,scaling) ||
            throw(ArgumentError("Export scaling"))
        return BasisLUExport(L,U,p,q,scaling,divide)
    catch
        _bgx_drop!(owner);rethrow()
    end
end

function _bgx_scale_mode(F,L,U,p,q,scaling,owner,n::Int,l::Int,u::Int;allocate=_bgx_allocate)
    try
        all(==(1.0),scaling) && return false
        all(x->isfinite(x) && x>0,scaling) || return _bgx_drop!(owner)
        index=firstindex(scaling);largest=abs(log2(scaling[index]))
        for i in eachindex(scaling)
            magnitude=abs(log2(scaling[i]))
            if magnitude>largest;index=i;largest=magnitude;end
        end
        coefficient=scaling[index];n=length(p)
        b=_bgx_budget(n,l,u);w=_bgx_prepare!(owner,n,b)
        group=isnothing(w) ? nothing : w.orientation
        work=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[1]
        auxiliary=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[2]
        fill!(work,0.0);work[index]=min(1.0,coefficient)
        rhs_value=work[index]
        ldiv!(auxiliary,F,work)
        all(isfinite,auxiliary) && any(!iszero,auxiliary) || return _bgx_drop!(owner)
        # Only these two short-lived vectors are needed in addition to solve scratch.
        permuted=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[3]
        transformed=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[4]
        if isnothing(group) && b.keep_orientation
            complete=(work,auxiliary,permuted,transformed)
            if isnothing(w)
                w=BGExportWorkspace(nothing,complete,n,512+b.orientation_bytes)
                owner.workspace=w
            else
                w.orientation=complete;w.charged_bytes=_bgx_charge(w)
            end
        end
        for i in eachindex(permuted);permuted[i]=auxiliary[q[i]];end
        mul!(work,U,permuted);mul!(transformed,L,work)
        _hh_abs_mul!(work,U,permuted);_hh_abs_mul!(auxiliary,L,work)
        all(isfinite,transformed) && all(isfinite,auxiliary) || return _bgx_drop!(owner)
        target=findfirst(==(index),p)
        multiply,divide=coefficient*rhs_value,rhs_value/coefficient
        function matches(expected)
            isfinite(expected) && expected>0 || return false
            for i in eachindex(transformed)
                reference=i==target ? expected : 0.0
                allowance=64n*eps(Float64)*max(auxiliary[i],abs(reference))
                abs(transformed[i]-reference)<=allowance || return false
            end
            true
        end
        multiplicative,divisive=matches(multiply),matches(divide)
        multiplicative==divisive && return _bgx_drop!(owner)
        divisive
    catch
        _bgx_drop!(owner);rethrow()
    end
end

_bgx_export(backend,owner;allocate=_bgx_allocate)=_bgx_drop!(owner)
function _bgx_export(backend::UMFPACKBackend,owner;allocate=_bgx_allocate)
    try
        F=backend.factorization
        if isnothing(F)
            backend.dimension==0 || throw(ArgumentError("Missing nonempty native factor"))
            _bgx_drop!(owner)
            return _bgx_checked_basis_lu(spzeros(0,0),spzeros(0,0),Int[],Int[],Float64[],false,owner;allocate)
        end
        issuccess(F) || throw(LinearAlgebra.SingularException(0))
        L,U,p,q,s=_hh_extract_parts(F,HHExtractWorkspace())
        _bgx_checked_basis_lu(L,U,p,q,s,false,owner;allocate)
        divide=_bgx_scale_mode(F,L,U,p,q,s,owner,length(p),nnz(L),nnz(U);allocate)
        isnothing(divide) && return _bgx_drop!(owner)
        return BasisLUExport(L,U,p,q,s,divide)
    catch
        _bgx_drop!(owner);rethrow()
    end
end
function _bgx_export(backend::MarkowitzBackend{Float64},owner;allocate=_bgx_allocate)
    try
        L,U,p,q,s=_hh_extract_parts(backend,HHExtractWorkspace())
        return _bgx_checked_basis_lu(L,U,p,q,s,false,owner;allocate)
    catch
        _bgx_drop!(owner);rethrow()
    end
end
