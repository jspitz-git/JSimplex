@testset "Solver transformations" begin
    problem = LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0, 1.0, 1.0, 1.0], 1, 4)), zeros(4);
        column_lower=[0.0, -2.0, 3.0, 2.0],
        column_upper=[1.0, 8.0, 9.0, 7.0],
        variable_domains=[BINARY, INTEGER, SEMI_CONTINUOUS, SEMI_INTEGER],
    )
    relaxed = JSimplex.relax_integrality(problem)
    @test all(==(CONTINUOUS), relaxed.variable_domains)
    @test relaxed.column_lower == [0.0, -2.0, 0.0, 0.0]
    @test relaxed.column_upper == [1.0, 8.0, 9.0, 7.0]
    @test problem.variable_domains[1] == BINARY
    @test problem.column_lower[3] == 3.0

    relaxed.objective[1] = 99.0
    relaxed.A[1, 1] = 99.0
    @test problem.objective[1] == 0.0
    @test problem.A[1, 1] == 1.0

    presolved = JSimplex.identity_presolve(relaxed)
    scaling = JSimplex.identity_scaling(presolved.problem)
    x = [0.25, 1.0, 4.0, 3.0]
    @test JSimplex.unscale_primal(scaling, x) == x
    @test JSimplex.unscale_dual(scaling, [2.0]) == [2.0]
    @test JSimplex.postsolve_primal(presolved, x) == x
end

@testset "Basis boundary" begin
    basic_indices = Int32[2, 4]
    states = JSimplex.VariableState[
        JSimplex.BASIC,
        JSimplex.AT_LOWER,
        JSimplex.AT_UPPER,
        JSimplex.FREE_NONBASIC,
    ]
    basis = JSimplex.Basis(basic_indices, states)
    basic_indices[1] = 1
    states[1] = JSimplex.AT_LOWER
    @test basis.basic_indices == [2, 4]
    @test basis.states == [
        JSimplex.BASIC,
        JSimplex.AT_LOWER,
        JSimplex.AT_UPPER,
        JSimplex.FREE_NONBASIC,
    ]
end
