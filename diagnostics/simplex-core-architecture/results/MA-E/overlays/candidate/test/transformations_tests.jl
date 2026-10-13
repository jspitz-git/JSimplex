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

@testset "Power-of-two row and column scaling preserves model meaning" begin
    for T in (Float32, Float64, BigFloat)
        problem = LinearProblem(
            JSimplex.SparseArrays.sparse(T[8 2 0; 16 1//2 0; 0 0 0]),
            T[4, 1, 0]; objective_constant=T(3), objective_sense=MAX_SENSE,
            row_lower=[T(4), nothing, T(0)], row_upper=[T(8), T(2), nothing],
            column_lower=[T(0), nothing, nothing],
            column_upper=[T(2), T(4), nothing],
            row_names=["first", "second", "empty"],
            column_names=["x", "y", "free"],
        )
        original = deepcopy(problem)
        scaled, factors = JSimplex.scale_problem(problem)
        @test factors.row_factors == T[8, 16, 1]
        @test factors.column_factors == T[1, 1//4, 1]
        @test scaled.A == JSimplex.SparseArrays.sparse(T[1 1 0; 1 1//8 0; 0 0 0])
        @test scaled.objective == T[4, 4, 0]
        @test scaled.objective_constant == T(3)
        @test scaled.objective_sense == MAX_SENSE
        @test bound_value(scaled.row_lower[1]) == T(1//2)
        @test !isfinite(scaled.row_lower[2])
        @test bound_value(scaled.row_lower[3]) == zero(T)
        @test bound_value(scaled.row_upper[1]) == one(T)
        @test bound_value(scaled.row_upper[2]) == T(1//8)
        @test !isfinite(scaled.row_upper[3])
        @test bound_value(scaled.column_upper[2]) == one(T)
        @test !isfinite(scaled.column_lower[2])
        @test !isfinite(scaled.column_upper[3])
        @test scaled.row_names == problem.row_names
        @test scaled.column_names == problem.column_names
        @test JSimplex.unscale_primal(factors, T[2, 2, 0]) == T[2, 8, 0]
        @test JSimplex.unscale_dual(factors, T[8, 16, 0]) == T[1, 1, 0]
        @test problem.A == original.A
        @test problem.objective == original.objective
        @test problem.row_lower == original.row_lower
        @test problem.column_upper == original.column_upper
    end
end

@testset "Unsafe scaling factors keep original row or column units" begin
    T = Float64
    tiny = nextfloat(zero(T))
    wide = LinearProblem(JSimplex.SparseArrays.sparse(reshape(T[2.0^100, tiny], 1, 2)),
        T[0, 0])
    _, wide_factors = JSimplex.scale_problem(wide)
    @test wide_factors.row_factors == T[1]

    bounded = LinearProblem(JSimplex.SparseArrays.sparse(reshape(T[2.0^-100], 1, 1)),
        T[0]; row_upper=T[floatmax(T)])
    _, bounded_factors = JSimplex.scale_problem(bounded)
    @test bounded_factors.row_factors == T[1]

    costly = LinearProblem(JSimplex.SparseArrays.sparse(reshape(T[1, 2.0^-100], 1, 2)),
        T[0, floatmax(T)])
    _, costly_factors = JSimplex.scale_problem(costly)
    @test costly_factors.column_factors == T[1, 1]

    narrow = LinearProblem(JSimplex.SparseArrays.sparse(reshape(T[1, 2.0^-100], 1, 2)),
        T[0, 0]; column_upper=[nothing, tiny])
    _, narrow_factors = JSimplex.scale_problem(narrow)
    @test narrow_factors.column_factors == T[1, 1]
end

@testset "Direct scaling keeps discrete columns in their original units" begin
    problem = LinearProblem(
        JSimplex.SparseArrays.sparse(reshape([8.0, 2.0, 1.0], 1, 3)),
        [1.0, 1.0, 1.0]; variable_domains=[CONTINUOUS, BINARY, INTEGER],
        column_upper=[nothing, 1.0, 3.0],
    )
    scaled, factors = JSimplex.scale_problem(problem)
    @test factors.column_factors == [1.0, 1.0, 1.0]
    @test scaled.variable_domains == problem.variable_domains
    @test bound_value(scaled.column_upper[2]) == 1.0
    @test bound_value(scaled.column_upper[3]) == 3.0
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
