@testset "Solver options and results" begin
    options = SolverOptions()
    @test options.algorithm == :dual
    @test options.iteration_limit == 100_000
    @test options.time_limit == Inf

    limited = SolverOptions(iteration_limit=17, time_limit=2.5)
    @test limited.iteration_limit == 17
    @test limited.time_limit == 2.5

    @test_throws ArgumentError SolverOptions(iteration_limit=-1)
    @test_throws ArgumentError SolverOptions(time_limit=-0.1)
    @test_throws ArgumentError SolverOptions(primal_tolerance=0.0)

    stats = SolveStatistics(iterations=3, elapsed_seconds=0.25,
                            refactorizations=1)
    result = Solution(OPTIMAL, 4.0, [1.0, 2.0], stats, "optimal")
    @test result.status == OPTIMAL
    @test result.objective_value == 4.0
    @test result.primal == [1.0, 2.0]
end
