using Test, JSimplex, SparseArrays, LinearAlgebra

function precision_recovery_fixture(; policy=JSimplex.NumericalPolicy(Float64;
        simplex_strategy=:adaptive, precision_boosting=true, refactor_timing=false),
        diagnostics=nothing)
    A = sparse([1e16 1.0; nextfloat(1e16) 1.0])
    rhs = A * [0.5, 1.0]
    problem = LinearProblem(A, zeros(2); row_lower=rhs, row_upper=rhs,
        column_lower=fill(nothing, 2), column_upper=fill(nothing, 2))
    options = SolverOptions(; verbose=false, presolve=false, scaling=:off,
        primal_tolerance=1e-10, dual_tolerance=1e-10)
    progress = JSimplex.SimplexProgressContext(problem; diagnostics, numerical_policy=policy)
    basis = JSimplex.Basis([1, 2],
        [JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.AT_LOWER])
    return JSimplex.initialize_from_basis(problem, basis, options; policy, progress)
end
