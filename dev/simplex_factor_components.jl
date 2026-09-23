module JSimplexFactorComponents
using JSimplex,SparseArrays,LinearAlgebra

"""Select at most 64 occupied rows/columns, inspecting at most 50000 entries."""
function extract(A)
    rows,columns = Int[],Int[]
    positions = Dict{Int,Int}()
    ii,jj,vv = Int[],Int[],eltype(A)[]
    scanned = 0
    for column in axes(A,2)
        local_column = length(columns)+1
        recorded = false
        for p in nzrange(A,column)
            scanned == 50000 && break
            scanned += 1
            row,value = A.rowval[p],A.nzval[p]
            iszero(value) && continue
            if !haskey(positions,row)
                length(rows) == 64 && continue
                push!(rows,row); positions[row] = length(rows)
            end
            if !recorded
                push!(columns,column); recorded = true
            end
            push!(ii,positions[row]); push!(jj,local_column); push!(vv,value)
        end
        (scanned == 50000 || length(columns) == 64) && break
    end
    block = sparse(ii,jj,vv,length(rows),length(columns))
    return block,Dict("selected_rows"=>rows,"selected_columns"=>columns,
        "scanned_stored_entries"=>scanned,"scan_limit"=>50000,"dimension_limit"=>64,
        "recipe"=>"First encountered occupied rows/columns, restricted to 64 each and 50000 scanned stored entries")
end

"""Build a bounded, strictly row-diagonally-dominant synthetic factor component."""
function component_basis(block)
    all(size(block) .<= 64) || throw(ArgumentError("Factor component exceeds 64x64"))
    all(isfinite,nonzeros(block)) || throw(ArgumentError("Factor component must be finite"))
    n = min(size(block)...)
    B = Matrix(block[1:n,1:n])
    for row in 1:n
        largest = max(1.0,maximum(abs,@view(B[row,:]);init=0.0))
        for column in 1:n
            B[row,column] /= largest
        end
        B[row,row] += 1+sum(abs,@view(B[row,:]))
    end
    return sparse(B)
end

function probe(block)
    B = component_basis(block)
    n = size(B,1)
    backends = Dict{String,Any}[]
    for kind in (:native,:markowitz)
        built = @timed JSimplex._factorize_basis(B,Val(kind))
        adapted = @timed JSimplex.sparse_solve_view(built.value)
        view = adapted.value
        profiles = Dict{String,Any}[]
        verified = true
        for support in (1,4,0), transposed in (false,true)
            values = zeros(n)
            if support == 0
                values .= 1.0
            else
                for i in 1:support:n
                    support == 1 && i > 1 && break
                    values[i] = isodd(i) ? 1.0 : -1.0
                end
            end
            rhs,dest = JSimplex.IndexedVector{Float64}(n),JSimplex.IndexedVector{Float64}(n)
            JSimplex.load_indexed!(rhs,values)
            operation = transposed ? JSimplex.hypersparse_transpose_solve! : JSimplex.hypersparse_forward_solve!
            dense = zeros(n)
            dense_operation = transposed ? JSimplex._backend_transpose_solve! : JSimplex._backend_forward_solve!
            dense_operation(dense,built.value,values)
            if isnothing(view)
                measured = @timed begin
                    dense_operation(dense,built.value,values)
                    JSimplex.load_indexed!(dest,dense)
                end
                seconds,bytes = measured.time,measured.bytes
            else
                operation(dest,view,rhs)
                measured = @timed operation(dest,view,rhs)
                seconds,bytes = measured.time,measured.bytes
            end
            matrix = transposed ? transpose(B) : B
            reference = setprecision(BigFloat,256) do
                Matrix{BigFloat}(matrix) \ BigFloat.(values)
            end
            residual = maximum(abs,BigFloat.(dest.values)-reference;init=BigFloat(0))
            allowance = 256eps(Float64)*max(BigFloat(1),maximum(abs,reference;init=BigFloat(0)))
            valid = residual <= allowance && isapprox(dest.values,dense;atol=256eps(Float64),rtol=256eps(Float64))
            valid || error("Bounded factor component failed its independent reference")
            verified &= valid
            push!(profiles,Dict("rhs_support"=>count(!iszero,values),"result_support"=>length(dest.indices),
                "transposed"=>transposed,"seconds"=>seconds,"allocated_bytes"=>bytes,
                "reference_verified"=>valid,"path"=>isnothing(view) ? "dense_fallback" : "hypersparse"))
        end
        push!(backends,Dict("backend"=>string(kind),"fresh_lu_seconds"=>built.time,
            "fresh_lu_allocated_bytes"=>built.bytes,"adapter_seconds"=>adapted.time,
            "adapter_allocated_bytes"=>adapted.bytes,"adapter_available"=>!isnothing(view),
            "adapter_storage_bytes"=>Base.summarysize(view),"profiles"=>profiles,
            "reference_verified"=>verified))
    end
    return Dict("basis_dimension"=>n,"basis_nonzeros"=>nnz(B),
        "basis_recipe"=>"Leading square of occupied block, each row divided by max(1,maxabs), then diagonal += 1 + row absolute sum",
        "full_sized_factorization"=>false,"simplex_solve"=>false,"backends"=>backends)
end
end
