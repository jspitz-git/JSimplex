using SparseArrays

@testset "Bound-only presolve avoids intermediate row slices" begin
    problem = LinearProblem(sparse(ones(128, 128)), ones(128))
    rows = collect(1:128)
    lower = copy(problem.column_lower)
    lower[1] = Bound(1.0)
    JSimplex._row_result(problem, rows; column_lower=lower)
    @test (@allocated JSimplex._row_result(problem, rows; column_lower=lower)) <= 350_000
end

@testset "Bound-only results retain independent model arrays" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        matrix = SparseMatrixCSC(2, 2, [1, 3, 4], [1, 2, 2], T[2, 0, -3])
        problem = LinearProblem(matrix, T[1, 4]; objective_constant=T(7),
            objective_sense=MAX_SENSE, row_lower=T[-2, -4], row_upper=T[6, 9],
            column_lower=T[0, 0], column_upper=T[10, 12],
            name="bound change", row_names=["first", "second"], column_names=["x", "y"])
        lower, upper = copy(problem.column_lower), copy(problem.column_upper)
        lower[1], upper[2] = Bound(T(1)), Bound(T(8))
        result = JSimplex._row_result(problem, [1, 2]; column_lower=lower, column_upper=upper)
        reduced = result.problem
        @test reduced !== problem
        @test reduced.A.colptr == [1, 3, 4]
        @test reduced.A.rowval == [1, 2, 2]
        @test reduced.A.nzval == T[2, 0, -3]
        @test reduced.objective == T[1, 4]
        @test reduced.objective_constant == T(7)
        @test reduced.objective_sense == MAX_SENSE
        @test bound_value.(reduced.row_lower) == T[-2, -4]
        @test bound_value.(reduced.row_upper) == T[6, 9]
        @test bound_value.(reduced.column_lower) == T[1, 0]
        @test bound_value.(reduced.column_upper) == T[10, 8]
        @test reduced.name == "bound change"
        @test reduced.row_names == ["first", "second"]
        @test reduced.column_names == ["x", "y"]
        @test only(result.postsolve_stack).rows == [1, 2]
        @test only(result.postsolve_stack).columns == [1, 2]
        @test JSimplex.postsolve_primal(result, T[2, 3]) == T[2, 3]
        for field in (:colptr, :rowval, :nzval)
            @test getfield(reduced.A, field) !== getfield(problem.A, field)
        end
        for field in (:objective, :row_lower, :row_upper, :column_lower, :column_upper,
                      :variable_domains, :row_names, :column_names)
            @test getfield(reduced, field) !== getfield(problem, field)
        end
        reduced.A.nzval[1] = T(20)
        reduced.row_lower[1] = Bound(T(-20))
        reduced.row_upper[1] = Bound(T(30))
        reduced.row_names[1] = "changed"
        reduced.column_lower[1] = Bound(T(5))
        reduced.column_upper[2] = Bound(T(6))
        @test problem.A.nzval == T[2, 0, -3]
        @test bound_value.(problem.row_lower) == T[-2, -4]
        @test bound_value.(problem.row_upper) == T[6, 9]
        @test problem.row_names == ["first", "second"]
        @test bound_value.(lower) == T[1, 0]
        @test bound_value.(upper) == T[10, 8]

        # Equal row count alone does not imply an identity selection.
        permuted = JSimplex._row_result(problem, [2, 1]; column_lower=lower).problem
        @test permuted.A == T[0 -3; 2 0]
        @test bound_value.(permuted.row_lower) == T[-4, -2]
        @test bound_value.(permuted.row_upper) == T[9, 6]
        @test permuted.row_names == ["second", "first"]
        subset = JSimplex._row_result(problem, [2]).problem
        @test subset.A == T[0 -3]
        @test bound_value.(subset.row_lower) == T[-4]
        @test subset.row_names == ["second"]
        identity = JSimplex._row_result(problem, [1, 2])
        @test identity.problem === problem
        @test isempty(identity.postsolve_stack)
    end
end

@testset "Bound-only results handle unnamed and empty rows" begin
    for rows in (0, 3)
        problem = LinearProblem(spzeros(rows, 2), zeros(2))
        lower = Bound.([1.0, 0.0])
        result = JSimplex._row_result(problem, collect(1:rows); column_lower=lower)
        @test size(result.problem.A) == (rows, 2)
        @test isempty(result.problem.row_names)
        @test result.problem.A !== problem.A
        @test result.problem.row_lower !== problem.row_lower
        @test result.problem.column_lower !== lower
        @test bound_value.(result.problem.column_lower) == [1.0, 0.0]
    end
    empty = LinearProblem(spzeros(0, 0), Float64[])
    @test JSimplex._row_result(empty, Int[]).problem === empty
end

@testset "Bound-only copies preserve stored BigFloat values" begin
    problem = setprecision(BigFloat, 256) do
        value = BigFloat(1) / 3
        LinearProblem(sparse(reshape([value], 1, 1)), [value];
            row_lower=[value], row_upper=[BigFloat(2)], row_names=["row"])
    end
    result = setprecision(BigFloat, 64) do
        JSimplex._row_result(problem, [1]; column_lower=[Bound(BigFloat(1))])
    end
    @test result.problem.A.nzval[1] === problem.A.nzval[1]
    @test bound_value(result.problem.row_lower[1]) === bound_value(problem.row_lower[1])
    @test precision(result.problem.A.nzval[1]) == 256
end

@testset "Bound-only results exclude spare CSC storage" begin
    problem = LinearProblem(SparseMatrixCSC(2, 2, [1, 3, 4], [1, 2, 2], [2.0, 0.0, -3.0]), [1.0, 4.0])
    push!(problem.A.rowval, 1)
    push!(problem.A.nzval, 99.0)
    result = JSimplex._row_result(problem, [1, 2]; column_lower=Bound.([1.0, 0.0]))
    @test result.problem.A.colptr == [1, 3, 4]
    @test result.problem.A.rowval == [1, 2, 2]
    @test result.problem.A.nzval == [2.0, 0.0, -3.0]
    @test problem.A.nzval == [2.0, 0.0, -3.0, 99.0]
end
