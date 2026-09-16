@testset "Solver options and results" begin
    options = SolverOptions()
    @test options.algorithm == :dual
    @test options.pricing == :steepest_edge
    @test options.verbose
    @test options.iteration_limit == 100_000
    @test options.time_limit == Inf

    limited = SolverOptions(iteration_limit=17, time_limit=2.5, verbose=false)
    @test limited.iteration_limit == 17
    @test limited.time_limit == 2.5
    @test !limited.verbose

    @test_throws ArgumentError SolverOptions(iteration_limit=-1)
    @test_throws ArgumentError SolverOptions(time_limit=-0.1)
    @test_throws ArgumentError SolverOptions(primal_tolerance=0.0)
    @test_throws ArgumentError SolverOptions(pricing=:unknown)

    stats = SolveStatistics(iterations=3, elapsed_seconds=0.25,
                            refactorizations=1)
    result = Solution(OPTIMAL, 4.0, [1.0, 2.0], stats, "optimal")
    @test result.status == OPTIMAL
    @test result.objective_value == 4.0
    @test result.primal == [1.0, 2.0]
end

@testset "Time limits are validated before Float64 conversion" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        @test_throws ArgumentError SolverOptions(T; time_limit=big"-1e-400")
        @test_throws ArgumentError SolverOptions(T; time_limit=-1 // big(10)^400)
        @test_throws ArgumentError SolverOptions(T; time_limit=big"-Inf")
        @test_throws ArgumentError SolverOptions(T; time_limit=big"NaN")
        @test SolverOptions(T; time_limit=big"Inf").time_limit === Inf
        @test SolverOptions(T; time_limit=big"1e-400").time_limit === 0.0
        @test SolverOptions(T; time_limit=big"-0.0").time_limit === -0.0
        @test SolverOptions(T; time_limit=big"2.5").time_limit === 2.5
    end
end

@testset "Parametric solver options and results" begin
    @test @inferred(SolverOptions()) isa SolverOptions{Float64}
    options32 = @inferred SolverOptions(Float32)
    @test options32.primal_tolerance isa Float32
    @test options32.primal_tolerance > 0.0f0
    @test SolverOptions(Float16).zero_tolerance == nextfloat(zero(Float16))

    exact = @inferred SolverOptions(Rational{BigInt})
    @test exact.primal_tolerance == 0
    @test exact.dual_tolerance == 0
    @test exact.zero_tolerance == 0

    converted = @inferred SolverOptions(
        Rational{BigInt}, SolverOptions(time_limit=2.5, verbose=false),
    )
    @test converted isa SolverOptions{Rational{BigInt}}
    @test converted.time_limit === 2.5
    @test !converted.verbose
    @test SolverOptions(Float32, SolverOptions(pricing=:devex)).pricing == :devex
    @test_throws ArgumentError SolverOptions(Int)
    for T in (ComplexF64, String)
        @test_throws ArgumentError SolverOptions(T)
        @test_throws ArgumentError SolverOptions(T, SolverOptions())
    end

    stats = SolveStatistics()
    optimal = @inferred Solution(OPTIMAL, 3.0f0, Float32[1], stats, "optimal")
    stopped = @inferred Solution{Float32}(TIME_LIMIT, nothing, nothing, stats, "stopped")
    @test optimal isa Solution{Float32}
    @test stopped isa Solution{Float32}
end
