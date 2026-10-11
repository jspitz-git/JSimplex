# Frozen extraction reference from production b720674. Do not change.
function original_markowitz_parts(F::JS.MarkowitzBackend{T},::JS.HHExtractWorkspace) where {T}
    n,k=F.dimension,F.sparse_pivots
    core_order=F.core.p
    core_positions=invperm(core_order)
    rows=copy(F.row_order)
    for i in eachindex(core_order)
        rows[k+i]=F.row_order[k+core_order[i]]
    end
    li,lj,lv=collect(1:n),collect(1:n),ones(T,n)
    ui,uj,uv=Int[],Int[],T[]
    for pivot in 1:k
        push!(ui,pivot);push!(uj,pivot);push!(uv,F.diagonal[pivot])
        lower,upper=F.lower[pivot],F.upper[pivot]
        for j in eachindex(lower.indices)
            row=lower.indices[j]
            row>k && (row=k+core_positions[row-k])
            push!(li,row);push!(lj,pivot);push!(lv,lower.values[j])
        end
        for j in eachindex(upper.indices)
            push!(ui,pivot);push!(uj,upper.indices[j]);push!(uv,upper.values[j])
        end
    end
    # Read the existing dense LU storage, without forming another dense matrix.
    core=F.core.factors
    for j in axes(core,2), i in axes(core,1)
        value=core[i,j]
        iszero(value) && continue
        if i>j
            push!(li,k+i);push!(lj,k+j);push!(lv,value)
        else
            push!(ui,k+i);push!(uj,k+j);push!(uv,value)
        end
    end
    return sparse(li,lj,lv,n,n),sparse(ui,uj,uv,n,n),rows,copy(F.column_order),ones(T,n)
end
