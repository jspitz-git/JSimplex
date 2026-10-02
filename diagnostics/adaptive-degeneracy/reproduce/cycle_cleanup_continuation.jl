# Continue mandatory cleanup from the saved native cycle failure.
using Test,JSimplex,Serialization,LinearAlgebra
BLAS.set_num_threads(1)
function probe(path)
    ws=deserialize(path)
    JSimplex._install_driver_policy!(ws,ws.progress.numerical_policy;start_ns=time_ns())
    start=time_ns();stop=()->(time_ns()-start)/1e9>90
    @test JSimplex._try_native_cleanup_recompute!(ws,stop)
    @test JSimplex._recomputed_basis_reliable(ws)
    @test !JSimplex._legacy_primal_point_certified(ws)
    terminal=JSimplex._run_basis_terminal!(ws,JSimplex.SimplexRunBudget(ws),ws.progress.numerical_policy,
        stop,Val(true),ws.options.dual_tolerance,false,false,true)
    @test terminal.status==OPTIMAL
    @test JSimplex._legacy_primal_point_certified(ws)
    @test JSimplex._original_optimality_certified(ws,ws.primal[1:size(ws.problem.A,2)])
    println("TERMINAL ",terminal," iteration=",ws.iterations);flush(stdout)
end
@testset "Captured cycle cleanup continuation" begin
    foreach(probe,ARGS)
end
