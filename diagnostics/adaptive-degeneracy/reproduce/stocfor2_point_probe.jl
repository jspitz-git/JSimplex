using JSimplex,Serialization,LinearAlgebra
BLAS.set_num_threads(1)
for path in ARGS
    ws=deserialize(path);m,n=size(ws.problem.A)
    println("STATE ",path," shape=",(m,n)," iter=",ws.iterations," refs=",ws.refactorizations,
        " pinf=",JSimplex.primal_infeasibility_summary(ws)," dinf=",JSimplex.dual_infeasibility_summary(ws),
        " obj=",dot(ws.costs,ws.primal)," bounds=",JSimplex._original_bounds_active(ws),
        " costs=",JSimplex._original_costs_active(ws)," point=",JSimplex._legacy_primal_point_certified(ws),
        " basis_hash=",hash(ws.basis.basic_indices)," problem_hash=",hash((ws.problem.A.colptr,ws.problem.A.rowval,ws.problem.A.nzval)))
    offenders=sort([(max(JSimplex._lower_violation(ws.lower[i],ws.primal[i]),
        JSimplex._upper_violation(ws.upper[i],ws.primal[i])),i) for i in eachindex(ws.primal)];rev=true)
    println("TOP ",offenders[1:min(8,length(offenders))]);flush(stdout)
end
