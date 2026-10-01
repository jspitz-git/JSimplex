# Exact rank diagnosis after determinant-preserving singleton elimination.
# Higher/exact precision is used only as an independent diagnostic reference.
using JSimplex,Serialization,SparseArrays,LinearAlgebra,TOML
BLAS.set_num_threads(1)
function singleton_core(B)
    rows=collect(axes(B,1));columns=collect(axes(B,2));removed=0
    while !isempty(rows)
        C=B[rows,columns];dropzeros!(C)
        row_counts=zeros(Int,length(rows))
        for r in rowvals(C);row_counts[r]+=1;end
        column_counts=diff(C.colptr)
        r=findfirst(==(1),row_counts)
        if r!==nothing
            c=findfirst(j->any(==(r),view(rowvals(C),nzrange(C,j))),axes(C,2))
        else
            c=findfirst(==(1),column_counts)
            c===nothing && break
            r=only(view(rowvals(C),nzrange(C,c)))
        end
        deleteat!(rows,r);deleteat!(columns,c);removed+=1
    end
    B[rows,columns],removed
end
records=Dict{String,Any}[]
for path in ARGS[2:end]
    data=deserialize(path)
    for (label,B) in (("before",data.B),("after",data.nextB))
        core,removed=singleton_core(B)
        row=Dict{String,Any}("snapshot"=>path,"label"=>label,"iteration"=>data.iteration,
            "core_size"=>size(core,1),"singletons_removed"=>removed,
            "pivot"=>data.direction[data.leaving],"tableau_coefficient"=>data.tableau_coefficient)
        println("CORE ",row);flush(stdout)
        if size(core,1)<=160
            factor=lu(Matrix{Rational{BigInt}}(core);check=false)
            row["exact_nonsingular"]=issuccess(factor)
            row["factorization_info"]=Int(factor.info)
        else
            row["note"]="Exact dense diagnosis skipped above the 160-coordinate bound."
        end
        push!(records,row);println("EXACT ",row);flush(stdout)
        open(ARGS[1],"w") do io;TOML.print(io,Dict("records"=>records));end
    end
end
