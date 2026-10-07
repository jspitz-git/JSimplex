using JSimplex,LinearAlgebra,SparseArrays,Serialization,TOML
const JS=JSimplex
function main(directory,output)
    ispath(output) && error("Choose a fresh output")
    paths=filter(p->startswith(basename(p),"pivot-"),readdir(directory;join=true))
    sort!(paths;by=p->parse(Int,match(r"pivot-(\d+)\.bin",p)[1]))
    records=Dict{String,Any}[]
    for path in paths
        d=deserialize(path);n=size(d.problem.A,2);rhs=zeros(size(d.B,1))
        if d.entering<=n
            for p in nzrange(d.problem.A,d.entering);rhs[d.problem.A.rowval[p]]=d.problem.A.nzval[p];end
        else
            rhs[d.entering-n]=-1.0
        end
        record=Dict{String,Any}("snapshot"=>path,"iteration"=>d.iteration,
            "entering"=>d.entering,"row"=>d.row,"pivot"=>d.pivot,"row_pivot"=>d.row_pivot,
            "primal_maximum"=>maximum(abs,d.primal),"direction_maximum"=>maximum(abs,d.direction),
            "primal_step"=>d.primal_step)
        try
            f=JS._factorize_basis(d.B,Val(:markowitz))
            exact=JS._refined_basis_solution(f,d.B,rhs,256,()->false)
            record["reference_converged"]=!isnothing(exact)
            if !isnothing(exact)
                pivot=exact[d.row];record["reference_pivot"]=string(pivot)
                record["pivot_relative_difference"]=Float64(abs(BigFloat(d.pivot)-pivot)/max(abs(pivot),BigFloat(1e-100)))
                record["false_pivot"]=abs(pivot)<BigFloat(1e-7) && abs(d.pivot)>1e-7 && record["pivot_relative_difference"]>1e-3
                if record["false_pivot"]
                    high=JS._refined_basis_solution(f,d.B,rhs,512,()->false)
                    record["reference_512_converged"]=!isnothing(high)
                    !isnothing(high) && (record["reference_pivot_512"]=string(high[d.row]))
                end
            end
        catch e
            record["exception"]=sprint(showerror,e)
        end
        push!(records,record)
        open(output,"w") do io;TOML.print(io,Dict("records"=>records));end
        println(d.iteration," pivot=",d.pivot," reference=",get(record,"reference_pivot",get(record,"exception","inconclusive")));flush(stdout)
        get(record,"false_pivot",false) && break
    end
end
Base.invokelatest(main,ARGS...)
