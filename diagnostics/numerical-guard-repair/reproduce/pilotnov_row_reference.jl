using JSimplex,LinearAlgebra,SparseArrays,Serialization,TOML
const JS=JSimplex
function main(snapshot,output)
    ispath(output) && error("Choose a fresh report")
    d=deserialize(snapshot);ws=JS.initialize_workspace(d.problem,d.options);ws.basis=d.basis
    policy=ws.progress.numerical_policy;m=size(d.B,1);rhs=zeros(m);rhs[d.row]=1
    scratch=JS.SolveQualityScratch(Float64,m);records=[]
    for backend in (:stored,:native,:markowitz)
        factor=backend==:stored ? d.factor : backend==:native ? lu(d.B) : JS._factorize_basis(d.B,Val(:markowitz))
        solve=backend==:stored ? b->JS.transpose_solve(factor,b) : b->JS._refinement_basis_solve(factor,b,true)
        x=backend==:stored ? copy(d.rho) : solve(rhs)
        trace=[]
        for k in 0:12
            q=JS._compensated_solve_quality!(scratch,d.B,x,rhs,policy,true)
            push!(trace,Dict("correction"=>k,"ratio"=>JS._dual_row_residual_ratio(ws,x,d.row),
                "absolute_error"=>q.absolute_error,"maximum"=>maximum(abs,x)))
            k<12 && (x .+= solve(scratch.residual))
        end
        push!(records,Dict("backend"=>string(backend),"trace"=>trace))
    end
    f=JS._factorize_basis(d.B,Val(:markowitz))
    exact=JS._refined_basis_solution(f,d.B,rhs,256,()->false;transposed=true)
    report=Dict{String,Any}("row"=>d.row,"iteration"=>d.iteration,"message"=>d.message,
        "stored_updates"=>length(d.factor.updates),"records"=>records,"reference_converged"=>!isnothing(exact))
    if !isnothing(exact)
        report["rounded_reference_ratio"]=JS._dual_row_residual_ratio(ws,Float64.(exact),d.row)
        report["reference_maximum"]=Float64(maximum(abs,exact))
    end
    open(output,"w") do io;TOML.print(io,report);end
    println(report)
end
Base.invokelatest(main,ARGS...)
