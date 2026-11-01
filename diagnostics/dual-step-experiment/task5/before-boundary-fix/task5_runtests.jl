using JSimplex,Test,LinearAlgebra,SparseArrays
const J=JSimplex
@assert realpath(pathof(J))=="/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl/src/JSimplex.jl"
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
include(joinpath(@__DIR__,"..","ExperimentalDualEngine.jl"));const E=ExperimentalDualEngine
include("driver_fixtures.jl")
if ARGS==["red"]
    @testset "Task5 opt-in complete solve interfaces and actual hook" begin
        for name in (:SolveRecord,:solve_experimental,:PhaseAdapter);@test isdefined(E,name);end
        p=driver_problem();a=copy(p.A);c=copy(p.objective);o=driver_options();r=J.solve(p;options=o)
        @test r.status==J.OPTIMAL
        @test r.objective_value==1.
        @test p.A==a
        @test p.objective==c
        probe=MainHookProbe(0)
        r=try J._solve_diagnosed(p,nothing;options=o,dual_engine=probe) catch ex;ex isa MethodError ? nothing : rethrow() end
        @test r isa J.Solution{Float64}
        @test probe.calls==1
    end
else
    @assert ARGS==["green"]
    include("fixtures.jl");include("state_tests.jl");include("invariant_tests.jl")
    include("kernel_fixtures.jl");include("kernel_tests.jl")
    include("proposal_fixtures.jl");include("ratio_tests.jl");include("proposal_tests.jl")
    include("commit_fixtures.jl");include("commit_tests.jl");include("recovery_tests.jl")
    include("driver_tests.jl")
    for name in ("native_basic_stationarity_tests.jl","native_certificate_recovery_tests.jl","native_terminal_primal_tests.jl","legacy_primal_point_recovery_tests.jl","dual_entry_phase_tests.jl","simplex_driver_tests.jl","solver_tests.jl")
        include(joinpath(@__DIR__,"..","..","..","test",name))
    end
    println("DUAL_ENGINE_TASK5_COMPLETED")
end
