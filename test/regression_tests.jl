@testset "AFIRO regression" begin
    path = joinpath(@__DIR__, "fixtures", "solver", "afiro.mps")
    problem = read_mps(path)
    result = solve(problem)
    @test result.status == OPTIMAL
    @test result.objective_value ≈ -464.7531428571429 atol=1.0e-6 rtol=1.0e-8
    @test length(result.primal) == size(problem.A, 2)
end
