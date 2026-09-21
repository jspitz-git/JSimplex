using SparseArrays

@testset "Singleton detection avoids complete row-entry vectors" begin
    problem = LinearProblem(sparse(ones(128, 128)), ones(128))
    JSimplex.reduce_singleton_rows(problem)
    @test (@allocated JSimplex.reduce_singleton_rows(problem)) <= 30_000
end

@testset "Singleton positions ignore zeros and preserve multiple-entry rows" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        matrix = SparseMatrixCSC(5, 4, [1, 4, 6, 8, 10],
            [1, 2, 3, 3, 4, 3, 5, 2, 5], T[2, 0, 3, 4, -2, 5, 0, 0, -0.0])
        push!(matrix.rowval, 1)
        push!(matrix.nzval, T(99))
        positions = @inferred JSimplex._singleton_row_positions(matrix)
        @test positions == [(1, 1), (0, 0), (-1, 0), (2, 5), (0, 0)]
        @test positions isa Vector{Tuple{Int,Int}}
        @test matrix.colptr == [1, 4, 6, 8, 10]
        @test matrix.rowval == [1, 2, 3, 3, 4, 3, 5, 2, 5, 1]
        @test isequal(matrix.nzval, T[2, 0, 3, 4, -2, 5, 0, 0, -0.0, 99])
        positions[2] = (1, 2)
        @test positions[5] == (0, 0)
        @test JSimplex._singleton_row_positions(matrix)[2] == (0, 0)
    end
end

@testset "Singleton scan retains bound sources and basis restoration" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[2 0; 0 -2; 1 1; 0 0]), T[1, 2];
            row_lower=T[4, -10, -100, 0], row_upper=T[8, -6, 100, 0],
            column_upper=T[10, 10], row_names=["positive", "negative", "pair", "empty"])
        result = JSimplex.reduce_singleton_rows(problem)
        step = only(result.postsolve_stack)
        @test result.problem.A == T[1 1; 0 0]
        @test result.problem.row_names == ["pair", "empty"]
        @test bound_value.(result.problem.column_lower) == T[2, 3]
        @test bound_value.(result.problem.column_upper) == T[4, 5]
        @test step.map.rows == [3, 4]
        @test step.lower_sources == [(1, JSimplex.AT_LOWER), (2, JSimplex.AT_UPPER)]
        @test step.upper_sources == [(1, JSimplex.AT_UPPER), (2, JSimplex.AT_LOWER)]
        @test JSimplex.postsolve_primal(result, T[2, 5]) == T[2, 5]
        basis = JSimplex.Basis([3, 4], [JSimplex.AT_LOWER, JSimplex.AT_UPPER,
                                      JSimplex.BASIC, JSimplex.BASIC])
        restored = JSimplex.restore_basis(result, basis)
        @test restored.basic_indices == [1, 2, 5, 6]
        @test restored.states == [JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_LOWER,
                                  JSimplex.AT_LOWER, JSimplex.BASIC, JSimplex.BASIC]
        @test bound_value.(problem.column_lower) == T[0, 0]
        @test bound_value.(problem.column_upper) == T[10, 10]
        @test problem.A == T[2 0; 0 -2; 1 1; 0 0]
        result.problem.column_lower[1] = Bound(T(-1))
        @test bound_value(problem.column_lower[1]) == T(0)
    end
end

@testset "Singleton scan preserves rejection and failure paths" begin
    for T in (Float32, Float64)
        inexact = LinearProblem(sparse(reshape(T[3], 1, 1)), T[1]; row_lower=T[1], row_upper=T[2])
        @test JSimplex.reduce_singleton_rows(inexact).problem === inexact
    end
    infeasible = LinearProblem(sparse([1.0 0.0; 1.0 1.0]), [1.0, 1.0];
        row_lower=[2.0, 0.0], column_upper=[1.0, 1.0])
    failure = JSimplex.reduce_singleton_rows(infeasible)
    @test failure.status == INFEASIBLE
    @test (failure.rows, failure.columns, failure.nonzeros) == (1, 2, 2)
    @test bound_value.(infeasible.column_lower) == [0.0, 0.0]
end

@testset "Singleton scan supports empty dimensions" begin
    for (rows, columns) in ((0, 0), (0, 3), (3, 0), (3, 4))
        problem = LinearProblem(spzeros(rows, columns), zeros(columns))
        @test JSimplex._singleton_row_positions(problem.A) == fill((0, 0), rows)
        @test JSimplex.reduce_singleton_rows(problem).problem === problem
    end
end
