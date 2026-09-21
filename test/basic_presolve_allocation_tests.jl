using SparseArrays

@testset "Basic presolve avoids an intermediate matrix" begin
    unchanged = LinearProblem(sparse(ones(128, 128)), ones(128))
    reduced = LinearProblem(sparse([ones(127, 127) zeros(127); zeros(1, 128)]), ones(128))
    for (problem, budget) in ((unchanged, 60_000), (reduced, 650_000))
        JSimplex._presolve_basic(problem)
        @test (@allocated JSimplex._presolve_basic(problem)) <= budget
    end
end

@testset "Basic presolve selects rows and columns and preserves stored zeros" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        matrix = SparseMatrixCSC(4, 4, [1, 2, 5, 5, 7], [1, 2, 3, 4, 2, 4], T[3, 1, 0, 0, 2, -1])
        problem = LinearProblem(matrix, T[5, 2, 0, 3]; objective_constant=T(7),
            row_lower=T[6, 1, 0, -3], row_upper=T[6, 9, 0, 5],
            column_lower=T[2, 0, 0, 0], column_upper=[T(2), T(10), nothing, T(10)],
            row_names=["r1", "r2", "r3", "r4"], column_names=["c1", "c2", "c3", "c4"])
        result = JSimplex._presolve_basic(problem)
        reduced = result.problem
        step = only(result.postsolve_stack)
        @test size(reduced.A) == (2, 2)
        @test reduced.A.colptr == [1, 3, 5]
        @test reduced.A.rowval == [1, 2, 1, 2]
        @test reduced.A.nzval == T[1, 0, 2, -1]
        @test reduced.objective == T[2, 3]
        @test reduced.objective_constant == T(17)
        @test bound_value.(reduced.row_lower) == T[1, -3]
        @test bound_value.(reduced.row_upper) == T[9, 5]
        @test bound_value.(reduced.column_lower) == T[0, 0]
        @test bound_value.(reduced.column_upper) == T[10, 10]
        @test reduced.row_names == ["r2", "r4"]
        @test reduced.column_names == ["c2", "c4"]
        @test step.rows == [2, 4]
        @test step.columns == [2, 4]
        @test JSimplex.postsolve_primal(result, T[3, 4]) == T[2, 3, 0, 4]
        @test problem.A.colptr == [1, 2, 5, 5, 7]
        @test problem.A.rowval == [1, 2, 3, 4, 2, 4]
        @test problem.A.nzval == T[3, 1, 0, 0, 2, -1]
        @test bound_value.(problem.row_lower) == T[6, 1, 0, -3]
        reduced.A.nzval[1] = T(20)
        @test problem.A.nzval[2] == T(1)

        # Row 1 becomes infeasible only after eliminating the fixed column.
        problem.row_lower[1] = Bound(T(7))
        problem.row_upper[1] = Bound(T(7))
        failure = JSimplex._presolve_basic(problem)
        @test failure.status == INFEASIBLE
        @test failure.rows == 2
        @test failure.columns == 2
        @test failure.nonzeros == 3
        @test occursin("row 1", failure.message)
    end
end

@testset "Basic presolve handles unchanged and empty matrix shapes" begin
    unchanged = LinearProblem(SparseMatrixCSC(2, 2, [1, 3, 4], [1, 2, 2], [1.0, 0.0, 2.0]), [1.0, 1.0])
    # Spare CSC storage is not an active coefficient.
    push!(unchanged.A.rowval, 1)
    push!(unchanged.A.nzval, 42.0)
    identity = JSimplex._presolve_basic(unchanged)
    @test identity.problem === unchanged
    @test isempty(identity.postsolve_stack)
    @test unchanged.A.nzval == [1.0, 0.0, 2.0, 42.0]

    for (rows, columns) in ((0, 0), (0, 3), (3, 0))
        problem = LinearProblem(spzeros(rows, columns), zeros(columns))
        result = JSimplex._presolve_basic(problem)
        @test size(result.problem.A) == (0, 0)
        @test result.original_column_count == columns
        @test JSimplex.postsolve_primal(result, Float64[]) == zeros(columns)
    end

    rows_only = LinearProblem(sparse([1.0 2.0; 0.0 0.0]), [1.0, 1.0])
    result = JSimplex._presolve_basic(rows_only)
    @test result.problem.A == [1.0 2.0]
    @test only(result.postsolve_stack).columns == [1, 2]
    columns_only = LinearProblem(sparse([1.0 0.0; 2.0 0.0]), [1.0, 0.0])
    result = JSimplex._presolve_basic(columns_only)
    @test result.problem.A == reshape([1.0, 2.0], 2, 1)
    @test only(result.postsolve_stack).rows == [1, 2]
end
