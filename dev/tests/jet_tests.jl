using Test
using JET
using JSimplex
using JuMP

const MOI = JuMP.MOI

@testset "JET typed solver kernels" begin
    float_problem = LinearProblem(JSimplex.SparseArrays.sparse([1.0 1.0]),
                                  [-1.0, -2.0]; row_upper=[3.0])
    rational_problem = LinearProblem(
        JSimplex.SparseArrays.sparse(Rational{BigInt}[1 1]),
        Rational{BigInt}[-1, -2]; row_upper=Rational{BigInt}[3],
    )
    float_workspace = JSimplex.initialize_workspace(float_problem, SolverOptions(Float64))
    rational_workspace = JSimplex.initialize_workspace(
        rational_problem, SolverOptions(Rational{BigInt}),
    )

    JET.@test_opt target_modules=(JSimplex,) JSimplex.recompute!(float_workspace)
    JET.@test_opt target_modules=(JSimplex,) JSimplex.recompute!(rational_workspace)
    JET.@test_opt target_modules=(JSimplex,) solve(float_problem)
    JET.@test_opt target_modules=(JSimplex,) solve(rational_problem)
end

@testset "JET typed MOI adapter helpers" begin
    float_optimizer = JSimplex.Optimizer{Float32}()
    float_source = MOI.Utilities.Model{Float32}()
    float_x = MOI.add_variable(float_source)
    MOI.add_constraint(float_source, float_x, MOI.GreaterThan(Float32(1)))
    float_evaluation = JSimplex.MOIScalarEvaluation(
        Int[1], Float32[2], Float32(3),
    )
    rational_evaluation = JSimplex.MOIScalarEvaluation(
        Int[1], Rational{BigInt}[2//3], Rational{BigInt}(1//3),
    )

    @test @inferred(JSimplex._solver_options(float_optimizer)) isa SolverOptions{Float32}
    @test @inferred(JSimplex._evaluate_moi_function(
        float_evaluation,
        Float32[4],
    )) === Float32(11)
    @test @inferred(JSimplex._evaluate_moi_function(
        rational_evaluation,
        Rational{BigInt}[3],
    )) == Rational{BigInt}(7//3)
    JET.@test_opt target_modules=(JSimplex,) JSimplex._solver_options(float_optimizer)
end
