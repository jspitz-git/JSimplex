# UNEXECUTED. Existing raw extraction, triangle/permutation helpers and export type unchanged.
@inline function _bgxsp_checked_basis_lu(L::SparseMatrixCSC{Float64,Int},U::SparseMatrixCSC{Float64,Int},
                           p::Vector{Int},q::Vector{Int},scaling::Vector{Float64},divide::Bool,owner;allocate=_bgxsp_allocate)
    _bgxsp_checked_basis_lu_core(L,U,p,q,scaling,divide,owner,allocate)
end

function _bgxsp_checked_basis_lu_core(L::SparseMatrixCSC{Float64,Int},U::SparseMatrixCSC{Float64,Int},p::Vector{Int},q::Vector{Int},scaling::Vector{Float64},divide::Bool,owner::O,allocate::A) where {O,A}
    try
        n=size(L,1)
        _bgxsp_count!(:triangle_checks);_check_export_triangle(L,n,true)
        _bgxsp_count!(:triangle_checks);_check_export_triangle(U,n,false)
        seen=_bgxsp_scratch!(owner,:seen,n,nnz(L),nnz(U);allocate)
        _bgxsp_count!(:permutation_checks);_check_export_permutation(p,n,seen)
        _bgxsp_count!(:permutation_checks);_check_export_permutation(q,n,seen)
        length(scaling)==n && all(s->isfinite(s) && s>0.0,scaling) ||
            throw(ArgumentError("Export scaling"))
        return BasisLUExport(L,U,p,q,scaling,divide)
    catch
        _bgxsp_drop!(owner);rethrow()
    end
end

@inline function _bgxsp_scale_mode(F,L,U,p,q,scaling,owner,n::Int,l::Int,u::Int;allocate=_bgxsp_allocate)
    _bgxsp_scale_mode_core(F,L,U,p,q,scaling,owner,n,l,u,allocate)
end

function _bgxsp_scale_mode_core(F::FT,L::LT,U::UT,p::PT,q::QT,scaling::ST,owner::O,n::Int,l::Int,u::Int,allocate::A) where {FT,LT,UT,PT,QT,ST,O,A}
    try
        all(==(1.0),scaling) && return false
        all(x->isfinite(x) && x>0,scaling) || return _bgxsp_drop!(owner)
        index=firstindex(scaling);largest=abs(log2(scaling[index]))
        for i in eachindex(scaling)
            magnitude=abs(log2(scaling[i]))
            if magnitude>largest;index=i;largest=magnitude;end
        end
        coefficient=scaling[index];n=length(p)
        b=_bgxsp_budget(n,l,u);w=_bgxsp_prepare!(owner,n,b)
        group=isnothing(w) ? nothing : w.orientation
        work=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[1]
        auxiliary=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[2]
        fill!(work,0.0);work[index]=min(1.0,coefficient)
        rhs_value=work[index]
        _bgxsp_count!(:orientation_solves);ldiv!(auxiliary,F,work)
        all(isfinite,auxiliary) && any(!iszero,auxiliary) || return _bgxsp_drop!(owner)
        # Only these two short-lived vectors are needed in addition to solve scratch.
        permuted=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[3]
        transformed=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[4]
        if isnothing(group) && b.keep_orientation
            complete=(work,auxiliary,permuted,transformed)
            if isnothing(w)
                w=BGSpecializedProbeExportWorkspace(nothing,complete,n,512+b.orientation_bytes)
                owner.workspace=w
            else
                w.orientation=complete;w.charged_bytes=_bgxsp_charge(w)
            end
        end
        for i in eachindex(permuted);permuted[i]=auxiliary[q[i]];end
        _bgxsp_count!(:orientation_products);mul!(work,U,permuted);_bgxsp_count!(:orientation_products);mul!(transformed,L,work)
        _bgxsp_count!(:orientation_products);_hh_abs_mul!(work,U,permuted);_bgxsp_count!(:orientation_products);_hh_abs_mul!(auxiliary,L,work)
        all(isfinite,transformed) && all(isfinite,auxiliary) || return _bgxsp_drop!(owner)
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
        multiplicative==divisive && return _bgxsp_drop!(owner)
        divisive
    catch
        _bgxsp_drop!(owner);rethrow()
    end
end

@inline _bgxsp_export(backend,owner;allocate=_bgxsp_allocate)=_bgxsp_export_core(backend,owner,allocate)
_bgxsp_export_core(backend::B,owner::O,allocate::A) where {B,O,A}=_bgxsp_drop!(owner)
@inline function _bgxsp_export(backend::UMFPACKBackend,owner;allocate=_bgxsp_allocate)
    _bgxsp_export_core(backend,owner,allocate)
end

function _bgxsp_export_core(backend::B,owner::O,allocate::A) where {B<:UMFPACKBackend,O,A}
    try
        F=backend.factorization
        if isnothing(F)
            backend.dimension==0 || throw(ArgumentError("Missing nonempty native factor"))
            _bgxsp_drop!(owner)
            return _bgxsp_checked_basis_lu(spzeros(0,0),spzeros(0,0),Int[],Int[],Float64[],false,owner;allocate)
        end
        issuccess(F) || throw(LinearAlgebra.SingularException(0))
        _bgxsp_count!(:extractions);L,U,p,q,s=_hh_extract_parts(F,HHExtractWorkspace())
        _bgxsp_checked_basis_lu(L,U,p,q,s,false,owner;allocate)
        divide=_bgxsp_scale_mode(F,L,U,p,q,s,owner,length(p),nnz(L),nnz(U);allocate)
        isnothing(divide) && return _bgxsp_drop!(owner)
        return BasisLUExport(L,U,p,q,s,divide)
    catch
        _bgxsp_drop!(owner);rethrow()
    end
end
@inline function _bgxsp_export(backend::MarkowitzBackend{Float64},owner;allocate=_bgxsp_allocate)
    _bgxsp_export_core(backend,owner,allocate)
end

function _bgxsp_export_core(backend::B,owner::O,allocate::A) where {B<:MarkowitzBackend{Float64},O,A}
    try
        _bgxsp_count!(:extractions);L,U,p,q,s=_hh_extract_parts(backend,HHExtractWorkspace())
        return _bgxsp_checked_basis_lu(L,U,p,q,s,false,owner;allocate)
    catch
        _bgxsp_drop!(owner);rethrow()
    end
end
