using JET
using JSimplex

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
