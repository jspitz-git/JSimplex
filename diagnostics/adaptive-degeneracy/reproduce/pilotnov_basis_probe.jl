# Inspect captured post-failure bases independently of incremental factors.
using JSimplex,Serialization,LinearAlgebra,SparseArrays,TOML
BLAS.set_num_threads(1)
output=ARGS[1]
records=Dict{String,Any}[]
for path in ARGS[2:end]
    ws=deserialize(path);B=JSimplex.basis_matrix(ws)
    row=Dict{String,Any}("snapshot"=>path,"iteration"=>ws.iterations,
        "refactorizations"=>ws.refactorizations,"rows"=>size(B,1),"nonzeros"=>nnz(B),
        "unique_basic_indices"=>length(unique(ws.basis.basic_indices)),
        "updates"=>length(ws.factorization.updates),"selected_row"=>ws.scratch.selected_row,
        "selected_entering"=>ws.scratch.selected_entering,
        "last_primal_step"=>ws.scratch.last_primal_step,"last_dual_step"=>ws.scratch.last_dual_step)
    row["native_factorization"]=try
        JSimplex._factorize_basis(B,Val(:native));"success"
    catch e
        sprint(showerror,e)
    end
    values=svdvals(Matrix(B))
    row["largest_singular_value"]=maximum(values)
    row["smallest_singular_value"]=minimum(values)
    row["small_singular_values"]=sort(values)[1:min(5,length(values))]
    push!(records,row);println(row);flush(stdout)
end
open(output,"w") do io;TOML.print(io,Dict("records"=>records));end
