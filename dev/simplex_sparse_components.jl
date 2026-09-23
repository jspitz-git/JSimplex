module JSimplexSparseComponents
using JSimplex, SparseArrays

"""Probe an already extracted block only; never create a basis or solve an LP."""
function probe(A)
    m,n = size(A)
    m <= 256 && n <= 256 && nnz(A) <= 50000 ||
        throw(ArgumentError("Sparse component exceeds the bounded extraction contract"))
    indexed = @timed JSimplex.RowAccess(A)
    rows = indexed.value
    rho = JSimplex.IndexedVector{eltype(A)}(m)
    out = JSimplex.IndexedVector{eltype(A)}(m+n)
    ordered = Int[]
    profiles = Dict{String,Any}[]
    for name in ("unit","quarter","dense")
        values = zeros(eltype(A),m)
        support = name == "unit" ? (1:min(1,m)) : name == "quarter" ? (1:4:m) : (1:m)
        for row in support
            values[row] = isodd(row) ? one(eltype(A)) : -one(eltype(A))
        end
        # Include discovery of dense RHS support and clearing previous output.
        JSimplex.load_indexed!(rho,values)
        JSimplex.sparse_price!(out,A,rho,rows;ordered_rows=ordered)
        measured = @timed begin
            JSimplex.load_indexed!(rho,values)
            JSimplex.sparse_price!(out,A,rho,rows;ordered_rows=ordered)
        end
        verified = setprecision(BigFloat,256) do
            for column in 1:n
                total,scale = BigFloat(0),BigFloat(0)
                terms = 0
                for p in nzrange(A,column)
                    product = BigFloat(values[A.rowval[p]])*BigFloat(A.nzval[p])
                    total += product
                    scale += abs(product)
                    terms += 1
                end
                allowance = BigFloat(2terms)*BigFloat(eps(eltype(A)))*scale
                abs(BigFloat(out.values[column])-total) <= allowance || return false
            end
            return out.values[n+1:n+m] == -values
        end
        verified || error("Sparse component pricing failed its reference bound")
        push!(profiles,Dict("name"=>name,"rhs_support"=>count(!iszero,values),
            "result_support"=>length(out.indices),"seconds"=>measured.time,
            "allocated_bytes"=>measured.bytes,"reference_verified"=>verified))
    end
    cancellation = JSimplex.IndexedVector{eltype(A)}(max(m,1))
    for _ in 1:32, row in eachindex(cancellation.values)
        JSimplex.add_entry!(cancellation,row,one(eltype(A)))
        JSimplex.add_entry!(cancellation,row,-one(eltype(A)))
    end
    JSimplex.compact_support!(cancellation)
    isempty(cancellation.indices) || error("Cancelled sparse support was retained")
    JSimplex.add_entry!(cancellation,1,one(eltype(A)))
    cancellation.indices == [1] || error("Cancelled support could not be reinserted")
    return Dict("row_index_seconds"=>indexed.time,"row_index_allocated_bytes"=>indexed.bytes,
        "row_index_bytes"=>sizeof(rows.rowptr)+sizeof(rows.columns)+sizeof(rows.positions),
        "indexed_scratch_bytes"=>sizeof(rho.values)+sizeof(rho.membership)+sizeof(out.values)+
            sizeof(out.membership)+sizeof(rho.indices)+sizeof(out.indices)+sizeof(ordered),
        "pricing_profiles"=>profiles,"cancellation_verified"=>true,
        "full_sized_factorization"=>false,"simplex_solve"=>false)
end
end
