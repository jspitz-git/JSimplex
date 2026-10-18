from pathlib import Path
R=Path.cwd();C=R/'diagnostics/direct-bg-export-workspace/reproduce'
workspace=r'''# UNEXECUTED separate candidate. Loaded only after the frozen direct-BG stage.
mutable struct BGExportWorkspace
    seen::Union{Nothing,BitVector}
    orientation::Union{Nothing,NTuple{4,Vector{Float64}}}
    dimension::Int
    charged_bytes::Int
end
_bgx_allocate(::Type{T},n::Int) where T = Vector{T}(undef,n)
_bgx_allocate(::Type{Bool},n::Int) = falses(n)
_bgx_drop!(owner) = (owner.workspace=nothing; nothing)
function _bgx_budget(n::Int,l::Int,u::Int)
    n>=0 && l>=0 && u>=0 || throw(ArgumentError("Negative export size"))
    add=Base.Checked.checked_add;mul=Base.Checked.checked_mul
    payload=add(mul(16,add(l,u)),mul(8,add(n,1)))
    # Avoid n+63 overflow: quotient plus remainder accounts for bit chunks.
    seen_bytes=mul(8,add(div(n,64),Int(rem(n,64)!=0)))
    orientation_bytes=mul(32,n)
    limit=min(1048576,fld(payload,16))
    seen_charge=add(512,seen_bytes)
    full_charge=add(seen_charge,orientation_bytes)
    keep_seen=n>0 && seen_charge<=limit
    return (;limit,seen_bytes,orientation_bytes,keep_seen,
             keep_orientation=keep_seen && full_charge<=limit)
end
function _bgx_charge(w::BGExportWorkspace)
    512+(isnothing(w.seen) ? 0 : 8*cld(w.dimension,64))+
        (isnothing(w.orientation) ? 0 : 32*w.dimension)
end
# Private cache invariants originate here. No arbitrary caller-owned buffers.
function _bgx_prepare!(owner,n::Int,b)
    w=owner.workspace
    if !b.keep_seen || (!isnothing(w) && w.dimension!=n)
        _bgx_drop!(owner);return nothing
    end
    if !isnothing(w) && !b.keep_orientation
        w.orientation=nothing
        if isnothing(w.seen)
            _bgx_drop!(owner);return nothing
        end
        w.charged_bytes=_bgx_charge(w)
    end
    return owner.workspace
end
function _bgx_scratch!(owner,role::Symbol,n::Int,l::Int,u::Int;allocate=_bgx_allocate)
    role===:seen || throw(ArgumentError("Unsupported export scratch role"))
    try
        b=_bgx_budget(n,l,u);w=_bgx_prepare!(owner,n,b)
        !isnothing(w) && !isnothing(w.seen) && return w.seen
        seen=allocate(Bool,n)::BitVector
        if b.keep_seen
            if isnothing(w)
                w=BGExportWorkspace(seen,nothing,n,512+b.seen_bytes)
                owner.workspace=w
            else
                w.seen=seen;w.charged_bytes=_bgx_charge(w)
            end
        end
        return seen
    catch
        _bgx_drop!(owner);rethrow()
    end
end
'''
(C/'workspace.jl').write_text(workspace)
raw=(R/'diagnostics/direct-lu-policy-adapters/reproduce/factor-export.jl').read_text()
# Retain existing validated structures/helpers; add only private distinct methods.
checked=raw[raw.index('function _checked_basis_lu('):raw.index('\n_export_basis_lu(backend)')]
checked=checked.replace('_checked_basis_lu(', '_bgx_checked_basis_lu(').replace('scaling::Vector{Float64},divide::Bool)', 'scaling::Vector{Float64},divide::Bool,owner;allocate=_bgx_allocate)').replace('seen=falses(n)','seen=_bgx_scratch!(owner,:seen,n,nnz(L),nnz(U);allocate)')
# Enclose validation so malformed export cannot retain previous cache.
lines=checked.splitlines();idx=next(i for i,s in enumerate(lines) if 'n=size(L,1)' in s)
checked='\n'.join(lines[:idx])+ '\n    try\n'+'\n'.join('    '+s for s in lines[idx:-1])+ '\n    catch\n        _bgx_drop!(owner);rethrow()\n    end\nend\n'
hh=(R/'.superpowers/sdd/2026-10-16-direct-lu-policy-adapters/driver-stages/green/src/huangfu_hall_factorization.jl').read_text()
original=hh[hh.index('function _hh_scale_mode('):hh.index('\nfunction _hh_extract_parts(F::LinearAlgebra.LU')].rstrip()
body=original.splitlines()[1:-1]
# Body changes only: staged acquisitions/retention and failure cleanup. Arithmetic exact.
body='\n'.join(body)
body=body.replace('    coefficient=scaling[index];n=length(p)', '''    coefficient=scaling[index];n=length(p)
    b=_bgx_budget(n,l,u);w=_bgx_prepare!(owner,n,b)
    group=isnothing(w) ? nothing : w.orientation
    work=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[1]
    auxiliary=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[2]''')
body=body.replace('    permuted=Vector{Float64}(undef,n);transformed=similar(permuted)', '''    permuted=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[3]
    transformed=isnothing(group) ? allocate(Float64,n)::Vector{Float64} : group[4]
    if isnothing(group) && b.keep_orientation
        complete=(work,auxiliary,permuted,transformed)
        if isnothing(w)
            w=BGExportWorkspace(nothing,complete,n,512+b.orientation_bytes)
            owner.workspace=w
        else
            w.orientation=complete;w.charged_bytes=_bgx_charge(w)
        end
    end''')
# All early fallback outcomes release cache; all-unit remains successful false.
body=body.replace('|| return nothing','|| return _bgx_drop!(owner)').replace('multiplicative==divisive && return nothing','multiplicative==divisive && return _bgx_drop!(owner)')
scale='function _bgx_scale_mode(F,L,U,p,q,scaling,owner,n::Int,l::Int,u::Int;allocate=_bgx_allocate)\n    try\n'+'\n'.join('    '+s for s in body.splitlines())+'\n    catch\n        _bgx_drop!(owner);rethrow()\n    end\nend\n'
exports=r'''
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
'''
(C/'export.jl').write_text('# UNEXECUTED. Existing raw extraction, triangle/permutation helpers and export type unchanged.\n'+checked+'\n'+scale+exports)
imports=r'''# UNEXECUTED. Precondition: canonical validated Float64/Int upper CSC.
# Standalone diagonal-ineligibility tests also allowed; arbitrary malformed CSC
# must first pass _bgx_checked_basis_lu, as in the reference export boundary.
function _bgx_import_upper(U::SparseMatrixCSC{Float64,Int},normalize::Bool;allocate=_bgx_allocate)
    n=size(U,1)
    D=nothing
    if normalize
        D=allocate(Float64,n)::Vector{Float64}
        for col in 1:n
            D[col]=U[col,col]
            if !(isfinite(D[col]) && !iszero(D[col]))
                D=nothing
                break
            end
        end
    end
    # Same owned maps/output types as _direct_packed_upper; allocation seam is
    # cold, local and not retained. No actual source methods are replaced.
    order_ids=allocate(Int,n)::Vector{Int}
    positions=allocate(Int,n)::Vector{Int}
    for i in 1:n;order_ids[i]=i;positions[i]=i;end
    order=UpperRowOrder(order_ids,positions)
    upper=allocate(PackedUpperColumn{Float64,UpperRowIndices},n)::Vector{PackedUpperColumn{Float64,UpperRowIndices}}
    rejected=false
    for col in 1:n
        first,last=U.colptr[col],U.colptr[col+1]-1
        count=last-first+1
        ids=allocate(Int,count)::Vector{Int}
        values=allocate(Float64,count)::Vector{Float64}
        for k in 1:count
            slot=first+k-1
            row=U.rowval[slot];ids[k]=row
            old=U.nzval[slot]
            if !isnothing(D) && !rejected
                value=old/D[row]
                if !isfinite(value) || (!iszero(old) && iszero(value))
                    rejected=true
                else
                    values[k]=value
                end
            elseif !rejected
                values[k]=old
            end
        end
        upper[col]=PackedUpperColumn{Float64}(UpperRowIndices(ids,order),values)
    end
    if rejected
        # Fill every final slot, including not-yet-initialized slots. No new
        # output allocation, no arithmetic retry, and no mutation of raw U.
        for col in 1:n
            values=upper[col].values;first=U.colptr[col]
            for k in eachindex(values);values[k]=U.nzval[first+k-1];end
        end
        D=nothing
    end
    return upper,D
end
'''
(C/'import.jl').write_text(imports)
print('Wrote3 UNEXECUTED candidate sources; tests already present; no Julia')
