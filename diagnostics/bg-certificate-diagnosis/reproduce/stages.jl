include("probe.jl")
function stages(snapshot,out)
    reports=[]
    for original in (false,true)
        w=restore_bg(snapshot);B=JS.basis_matrix(w);p=w.progress.numerical_policy
        if original
            JS._restore_original_costs!(w)
            JS.recompute!(w;refactorize=false)
        end
        rhs=w.costs[w.basis.basic_indices];x=copy(w.scratch.rho)
        s=JS.SolveQualityScratch(Float64,length(rhs))
        JS._compensated_solve_quality!(s,B,x,rhs,p,true)
        delta=similar(x);JS.transpose_solve!(delta,w.factorization,s.residual)
        cutoff=p.solve_tolerance*maximum(abs,delta)
        trial=x+delta
        r=Dict{String,Any}("original_costs"=>original,"tolerance"=>p.solve_tolerance,
            "correction_norm"=>maximum(abs,delta),"cutoff"=>cutoff,
            "initial"=>quality_report(w,B,x,rhs,true),
            "corrected"=>quality_report(w,B,trial,rhs,true))
        JS._clean_homogeneous_terms!(trial,B,rhs,true,zeros(Int,length(rhs)),p;cutoff)
        r["homogeneous"]=quality_report(w,B,trial,rhs,true)
        trial=x+delta
        r["local_success"]=JS._native_phase_local_rows!(trial,copy(transpose(B)),rhs,p,cutoff,()->false)
        r["local"]=quality_report(w,B,trial,rhs,true)
        # Diagnostic second correction only: no production changes.
        JS._compensated_solve_quality!(s,B,trial,rhs,p,true)
        JS.transpose_solve!(delta,w.factorization,s.residual)
        trial .+= delta
        r["second_correction"]=quality_report(w,B,trial,rhs,true)
        r["native_recompute"]=JS._try_native_cleanup_recompute!(w,()->false)
        r["summary"]=summary(w)
        push!(reports,r)
    end
    open(out,"w") do io; TOML.print(io,Dict("cases"=>reports));end
end
Base.invokelatest(stages,ARGS...)
