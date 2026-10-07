using JSimplex,LinearAlgebra,SparseArrays,Serialization,TOML
const JS=JSimplex
struct ProbeFactor{F}
    value::F
    transposed::Bool
end
Base.transpose(f::ProbeFactor)=ProbeFactor(f.value,!f.transposed)
Base.:(\)(f::ProbeFactor,rhs)=f.transposed ? JS.transpose_solve(f.value,rhs) : JS.forward_solve(f.value,rhs)
source=read(joinpath(dirname(pathof(JS)),"simplex_recovery.jl"),String)
start=findfirst("function _refined_basis_solution(",source).start
# This function ends the source file at the pinned baseline.
body=source[start:end]
occursin("function ",body[findnext("\nend",body,1).stop:end]) && error("Inspect function extraction")
body=replace(body,"_refined_basis_solution("=>"_probe_refined_basis_solution(")
body=replace(body,"isfinite(error) || return nothing"=>"push!(Main.ERRORS,Float64(error)); isfinite(error) || return nothing")
Base.include_string(JS,body,"instrumented-refinement")
const ERRORS=Float64[]
function main(snapshot,out)
    ispath(out) && error("Choose a fresh report")
    d=deserialize(snapshot);rhs=d.costs[d.basis.basic_indices];B=d.B
    records=Dict{String,Any}[]
    for backend in (:native,:markowitz)
        f=backend==:native ? lu(B) : ProbeFactor(JS.PFIFactorization(B,Val(:markowitz)),false)
        for bits in (256,512)
            empty!(ERRORS)
            elapsed=@elapsed y=Base.invokelatest(JS._probe_refined_basis_solution,f,B,rhs,bits,()->false;transposed=true)
            record=Dict{String,Any}("backend"=>string(backend),"bits"=>bits,"seconds"=>elapsed,
                "converged"=>!isnothing(y),"errors"=>copy(ERRORS))
            if !isnothing(y)
                j=d.entering;n=size(d.problem.A,2)
                price=setprecision(BigFloat,bits) do
                    j<=n ? BigFloat(d.costs[j])-sum(BigFloat(d.problem.A.nzval[k])*y[d.problem.A.rowval[k]] for k in nzrange(d.problem.A,j);init=BigFloat(0)) : BigFloat(d.costs[j])+y[j-n]
                end
                record["entering_price"]=string(price)
            end
            push!(records,record)
            println(backend," ",bits," converged=",record["converged"]," errors=",ERRORS);flush(stdout)
        end
    end
    open(out,"w") do io;TOML.print(io,Dict("iteration"=>d.iteration,"pivot"=>d.pivot,"checks"=>records));end
end
Base.invokelatest(main,ARGS...)
