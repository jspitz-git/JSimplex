# Inspect the saved failed original-model cleanup without changing production.
using JSimplex,Serialization,LinearAlgebra
BLAS.set_num_threads(1)
function report(ws,label)
    B=JSimplex.basis_matrix(ws);rhs=JSimplex._basis_primal_rhs(ws)
    basic=ws.primal[ws.basis.basic_indices];dual=copy(ws.scratch.rho)
    policy=ws.progress.numerical_policy
    primal_quality=JSimplex._compensated_solve_quality!(JSimplex.SolveQualityScratch(Float64,length(rhs)),B,basic,rhs,policy,false)
    dual_quality=JSimplex._compensated_solve_quality!(JSimplex.SolveQualityScratch(Float64,length(rhs)),B,dual,ws.costs[ws.basis.basic_indices],policy,true)
    println(label," iteration=",ws.iterations," dimensions=",size(B)," algorithm=",ws.options.algorithm,
        " point=",JSimplex._legacy_primal_point_certified(ws)," basis_quality=",JSimplex._recomputed_basis_reliable(ws),
        " primal_quality=",primal_quality," dual_quality=",dual_quality,
        " pinf=",JSimplex.primal_infeasibility_summary(ws)," dinf=",JSimplex.dual_infeasibility_summary(ws),
        " original_bounds=",JSimplex._original_bounds_active(ws)," original_costs=",JSimplex._original_costs_active(ws))
    flush(stdout)
end
ws=deserialize(ARGS[1]);report(ws,"SAVED")
for method in (:driver,:native_cleanup,:native_phase)
    trial=deepcopy(ws)
    result=method==:driver ? JSimplex._verify_driver_basis!(trial,()->false;refactorize=true) :
        method==:native_cleanup ? JSimplex._try_native_cleanup_recompute!(trial,()->false) :
        JSimplex._complete_native_phase_transfer!(trial,()->false)
    println("METHOD ",method," result=",result);report(trial,"AFTER")
end
