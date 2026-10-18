# UNEXECUTED. Precondition: canonical validated Float64/Int upper CSC.
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
