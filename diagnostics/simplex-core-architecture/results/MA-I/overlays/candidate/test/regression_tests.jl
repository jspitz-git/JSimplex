@testset "AFIRO regression" begin
    path = joinpath(@__DIR__, "fixtures", "solver", "afiro.mps")
    problem = read_mps(path)
    result = solve(problem)
    @test result.status == OPTIMAL
    @test result.objective_value ≈ -464.7531428571429 atol=1.0e-6 rtol=1.0e-8
    @test length(result.primal) == size(problem.A, 2)
end

@testset "AFIRO scaling modes preserve original optimum" begin
    problem = read_mps(joinpath(@__DIR__, "fixtures", "solver", "afiro.mps"))
    for algorithm in (:dual, :primal)
        scaled = solve(problem;
            options=SolverOptions(; algorithm, scaling=:auto, verbose=false))
        plain = solve(problem;
            options=SolverOptions(; algorithm, scaling=:off, verbose=false))
        @test scaled.status == OPTIMAL
        @test plain.status == OPTIMAL
        @test isapprox(scaled.objective_value, -464.7531428571429;
                       atol=1e-6, rtol=1e-8)
        @test isapprox(scaled.objective_value, plain.objective_value; atol=1e-6)
        @test JSimplex._original_primal_feasible(
            problem, something(scaled.primal), 1e-7)
    end
end
