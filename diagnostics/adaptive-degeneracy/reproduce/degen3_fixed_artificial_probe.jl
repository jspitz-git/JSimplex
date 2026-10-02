# Diagnostic feasibility reoptimization with artificials fixed to exact zero.
using JSimplex,Serialization,LinearAlgebra
BLAS.set_num_threads(1)
function probe(prefix)
    phase=deserialize(prefix*"-phase.bin");map=deserialize(prefix*"-map.bin")
    original=deserialize(prefix*"-original.bin")
    println("PREFIX ",prefix);flush(stdout)
    opts=phase.options
    phase.options=SolverOptions(algorithm=:dual,basis_update=:pfi,basis_refactorization=:native,
        pricing=:steepest_edge,refactorization_interval=80,time_limit=90.0,
        iteration_limit=phase.iterations+5000,verbose=false)
    policy=JSimplex.NumericalPolicy(Float64)
    JSimplex._install_driver_policy!(phase,policy;start_ns=time_ns())
    for j in map.artificial_columns
        phase.upper[j]=phase.problem.column_upper[j]=JSimplex.Bound(0.0)
    end
    fill!(phase.costs,0.0);fill!(phase.problem.objective,0.0)
    start=time_ns();stop=()->(time_ns()-start)/1e9>90
    JSimplex._phase_refactor!(phase,original,stop)
    println("START point=",JSimplex._legacy_primal_point_certified(phase)," quality=",JSimplex._recomputed_basis_reliable(phase),
        " pinf=",JSimplex.primal_infeasibility_summary(phase));flush(stdout)
    terminal=JSimplex._dual_optimize!(phase,stop;perturb_degenerate=false)
    println("TERMINAL ",terminal," iteration=",phase.iterations," point=",JSimplex._original_primal_feasible(phase,phase.primal[1:size(phase.problem.A,2)]),
        " maxart=",maximum(abs,phase.primal[map.artificial_columns]));flush(stdout)
    if terminal.status==JSimplex.OPTIMAL
        phase.options=opts
        println("REMOVAL ",JSimplex.remove_artificials!(phase,map,original,policy,stop),
            " iteration=",original.iterations," original_point=",JSimplex._legacy_primal_point_certified(original));flush(stdout)
    end
end
foreach(probe,ARGS)
