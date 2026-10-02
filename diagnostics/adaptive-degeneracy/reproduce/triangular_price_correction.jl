# One native residual correction despite an ordinarily reliable BTRAN.
using JSimplex,Serialization,LinearAlgebra,SparseArrays
BLAS.set_num_threads(1)
function probe(prefix)
    ws=deserialize(prefix*"-rejected.bin");data=deserialize(prefix*"-direction.bin")
    B=JSimplex.basis_matrix(ws);rhs=ws.costs[ws.basis.basic_indices]
    dual=similar(rhs);JSimplex.transpose_solve!(dual,ws.factorization,rhs)
    scratch=JSimplex.SolveQualityScratch(Float64,length(rhs));policy=ws.progress.numerical_policy
    before=JSimplex._compensated_solve_quality!(scratch,B,dual,rhs,policy,true)
    correction=similar(dual);JSimplex.transpose_solve!(correction,ws.factorization,scratch.residual)
    trial=dual+correction
    after=JSimplex._compensated_solve_quality!(scratch,B,trial,rhs,policy,true)
    println("RAW_CORRECTION ",after)
    if !after.reliable
        cutoff=policy.solve_tolerance*maximum(abs,correction)
        JSimplex._clean_homogeneous_terms!(trial,B,rhs,true,zeros(Int,length(rhs)),policy;cutoff)
        after=JSimplex._compensated_solve_quality!(scratch,B,trial,rhs,policy,true)
    end
    exact_residual=transpose(Rational{BigInt}.(B))*Rational{BigInt}.(trial)-Rational{BigInt}.(rhs)
    prices=similar(ws.reduced_costs);JSimplex._recompute_reduced_costs!(prices,ws,trial)
    println("PREFIX ",prefix," before=",before," after=",after," exact=",all(iszero,exact_residual),
        " correction=",maximum(abs,correction)," price=",prices[data.entering])
    copyto!(ws.reduced_costs,prices);copyto!(ws.scratch.rho,trial)
    JSimplex._pipeline_changed!(ws,ws.scratch.rho)
    JSimplex._invalidate_pricing_pool!(ws;basis=false)
    terminal=JSimplex._primal_iteration!(ws,()->false,data.tolerance,true)
    println("CONTINUATION ",terminal," iteration=",ws.iterations,
        " point=",JSimplex._legacy_primal_point_certified(ws));flush(stdout)
end
foreach(probe,ARGS)
