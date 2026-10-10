include("restore.jl")
function quality_report(w,B,x,rhs,transposed)
    s=JS.SolveQualityScratch(Float64,length(rhs));p=w.progress.numerical_policy
    plain=JS.solve_quality!(s,B,x,rhs,p;transposed)
    q=JS._compensated_solve_quality!(s,B,x,rhs,p,transposed)
    bad=findall(i->abs(s.residual[i])>p.solve_tolerance*s.work_scale[i],eachindex(rhs))
    Dict("plain"=>Dict(string(k)=>getfield(plain,k) for k in fieldnames(typeof(plain))),
      "compensated"=>Dict(string(k)=>getfield(q,k) for k in fieldnames(typeof(q))),
      "bad_count"=>length(bad),"bad"=>[Dict("row"=>i,"residual"=>s.residual[i],"scale"=>s.work_scale[i],"rhs"=>rhs[i]) for i in bad[1:min(end,30)]])
end
function main(snapshot,out)
    reports=[]
    for fresh in (false,true)
        w=restore_bg(snapshot;fresh);B=JS.basis_matrix(w);rhs=JS._basis_primal_rhs(w)
        r=summary(w);r["fresh_factor"]=fresh
        r["primal_quality"]=quality_report(w,B,w.primal[w.basis.basic_indices],rhs,false)
        r["dual_quality"]=quality_report(w,B,w.scratch.rho,w.costs[w.basis.basic_indices],true)
        primal=w.primal[1:size(w.problem.A,2)]
        r["original_primal_feasible"]=JS._original_primal_feasible(w.problem,primal,w.options.primal_tolerance)
        r["original_optimality_certified"]=JS._original_optimality_certified(w,primal)
        basic=copy(w.primal[w.basis.basic_indices]);dual=copy(w.scratch.rho)
        r["native_primal_repair"]=JS._native_cleanup_solve!(basic,w,B,rhs,()->false;local_reconstruction=true)
        r["native_dual_repair"]=JS._native_cleanup_solve!(dual,w,B,w.costs[w.basis.basic_indices],()->false;transposed=true,local_reconstruction=true)
        r["primal_after"]=quality_report(w,B,basic,rhs,false)
        r["dual_after"]=quality_report(w,B,dual,w.costs[w.basis.basic_indices],true)
        push!(reports,r)
        open(out,"w") do io;TOML.print(io,Dict("cases"=>reports));end
        println(r);flush(stdout)
    end
end
abspath(PROGRAM_FILE) == (@__FILE__) && Base.invokelatest(main,ARGS...)
