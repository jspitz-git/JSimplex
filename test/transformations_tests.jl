function test_typed_transformations(::Type{T}) where {T}
    problem = LinearProblem(JSimplex.SparseArrays.sparse(T[1 1]), T[1, 2];
        column_lower=T[2, 3], column_upper=T[7, 9],
        variable_domains=[SEMI_CONTINUOUS, SEMI_INTEGER])
    relaxed = @inferred JSimplex.relax_integrality(problem)
    presolved = @inferred JSimplex.identity_presolve(relaxed)
    scaling = @inferred JSimplex.identity_scaling(presolved.problem)
    @test relaxed isa LinearProblem{T}
    @test bound_value.(relaxed.column_lower) == T[0, 0]
    @test bound_value.(relaxed.column_upper) == T[7, 9]
    @test presolved.postsolve_stack === ()
    @test (@inferred JSimplex.unscale_primal(scaling, T[1, 2])) == T[1, 2]
    @test (@inferred JSimplex.unscale_dual(scaling, T[3])) == T[3]
    @test (@inferred JSimplex.postsolve_primal(presolved, T[1, 2])) isa Vector{T}
    free = LinearProblem(JSimplex.SparseArrays.spzeros(T, 0, 1), T[1];
        column_lower=[nothing], variable_domains=[SEMI_CONTINUOUS])
    relaxed_free = @inferred JSimplex.relax_integrality(free)
    @test !isfinite(only(relaxed_free.column_lower))
    @test !isfinite(only(relaxed_free.column_upper))
end

@testset "Typed transformations" begin
    foreach(test_typed_transformations, (Float32, Float64, BigFloat, Rational{BigInt}))
end

@testset "Solver transformations" begin
    problem = LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([1.0, 1.0, 1.0, 1.0], 1, 4)), zeros(4);
        column_lower=[0.0, -2.0, 3.0, 2.0],
        column_upper=[1.0, 8.0, 9.0, 7.0],
        variable_domains=[BINARY, INTEGER, SEMI_CONTINUOUS, SEMI_INTEGER],
    )
    relaxed = JSimplex.relax_integrality(problem)
    @test all(==(CONTINUOUS), relaxed.variable_domains)
    @test bound_value.(relaxed.column_lower) == [0.0, -2.0, 0.0, 0.0]
    @test bound_value.(relaxed.column_upper) == [1.0, 8.0, 9.0, 7.0]
    @test problem.variable_domains[1] == BINARY
    @test bound_value(problem.column_lower[3]) == 3.0

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
    basic_indices = [2, 4]
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
