using SparseArrays

@testset "Doubleton detection avoids complete row-entry vectors" begin
    count = 128
    for (kind, budget) in ((:wide, 10_000), (:inequalities, 8_000))
        A = kind == :wide ? sparse(ones(count, count)) :
            sparse(repeat(collect(1:count), inner=2), collect(1:2count), ones(2count), count, 2count)
        problem = LinearProblem(A, ones(size(A, 2)); row_upper=ones(count),
            column_lower=fill(nothing, size(A, 2)))
        JSimplex.substitute_free_doubleton(problem)
        @test (@allocated JSimplex.substitute_free_doubleton(problem)) <= budget
        @test JSimplex.substitute_free_doubleton(problem).problem === problem
    end
end

@testset "Doubleton scan ignores zeros and preserves longer rows" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        A = SparseMatrixCSC(6, 5, [1, 5, 7, 10, 12, 13],
            [1, 3, 4, 5, 3, 4, 3, 4, 5, 2, 5, 6],
            T[0, 1, 2, 1, 2, -0.0, 3, -1, 1, 2, 1, 0])
        problem = LinearProblem(A, T[2, 3, 4, 5, 0]; objective_constant=T(7),
            row_lower=[T(0), T(0), T(6), T(4), nothing, T(0)],
            row_upper=T[0, 4, 6, 4, 10, 0], column_lower=fill(nothing, 5),
            row_names=["empty", "single", "triple", "pair", "other", "zero"])
        original = deepcopy(problem)
        result = JSimplex.substitute_free_doubleton(problem)
        step = only(result.postsolve_stack)
        @test step.equality_row == 4
        @test (step.eliminated, step.retained) == (1, 3)
        @test (step.alpha, step.beta) == (T(2), T(0.5))
        @test step.map.rows == [1, 2, 3, 5, 6]
        @test step.map.columns == [2, 3, 4, 5]
        @test result.problem.A == T[0 0 0 0; 0 0 2 0; 2 3.5 0 0; 0 1.5 1 0; 0 0 0 0]
        @test all(!iszero, result.problem.A.nzval)
        @test result.problem.objective == T[3, 5, 5, 0]
        @test result.problem.objective_constant == T(11)
        @test bound_value.(result.problem.row_upper) == T[0, 4, 4, 8, 0]
        @test result.problem.row_names == ["empty", "single", "triple", "other", "zero"]
        @test JSimplex.postsolve_primal(result, T[2, 0, 0, 0]) == T[2, 2, 0, 0, 0]
        basis = JSimplex.Basis(collect(5:9),
            [fill(JSimplex.FREE_NONBASIC, 4); fill(JSimplex.BASIC, 5)])
        @test JSimplex.restore_basis(result, basis).basic_indices == [6, 7, 8, 1, 10, 11]
        @test isequal(problem.A.nzval, original.A.nzval)
        @test problem.A.colptr == original.A.colptr
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Doubleton scan tries the second candidate after rejection" begin
    for T in (Float32, Float64, BigFloat), free_first in (false, true)
        problem = LinearProblem(sparse(T[3 1; 0 1]), zeros(T, 2);
            row_lower=[T(1), nothing], row_upper=T[1, 4],
            column_lower=[free_first ? nothing : T(0), nothing])
        result = JSimplex.substitute_free_doubleton(problem)
        step = only(result.postsolve_stack)
        @test (step.eliminated, step.retained) == (2, 1)
        @test (step.alpha, step.beta) == (T(1), T(-3))
        @test result.problem.A == reshape(T[-3], 1, 1)
        @test bound_value.(result.problem.row_upper) == T[3]
        @test JSimplex.postsolve_primal(result, T[0]) == T[0, 1]
    end
end

@testset "Doubleton scan respects active storage and empty shapes" begin
    padded = LinearProblem(sparse(ones(3, 3)), ones(3);
        row_lower=ones(3), row_upper=ones(3), column_lower=fill(nothing, 3))
    push!(padded.A.rowval, 999)
    push!(padded.A.nzval, 42.0)
    @test JSimplex.substitute_free_doubleton(padded).problem === padded
    @test padded.A.rowval[end] == 999
    @test padded.A.nzval[end] == 42.0
    for (rows, columns) in ((0, 0), (0, 3), (3, 0), (3, 3))
        problem = LinearProblem(spzeros(rows, columns), zeros(columns))
        @test JSimplex.substitute_free_doubleton(problem).problem === problem
    end
    bounded = LinearProblem(sparse([1.0 1.0]), ones(2); row_lower=[2.0], row_upper=[2.0])
    @test JSimplex.substitute_free_doubleton(bounded).problem === bounded
end

@testset "Duplicate CSC entries cannot substitute a column into itself" begin
    # A raw CSC constructor permits duplicate entries. Preserve the previous
    # rejection instead of constructing a self-referential postsolve step.
    problem = LinearProblem(SparseMatrixCSC(2, 1, [1, 3], [1, 1], [1.0, 1.0]), [1.0];
        row_lower=[2.0, 0.0], row_upper=[2.0, 0.0], column_lower=[nothing])
    @test_throws ArgumentError JSimplex.substitute_free_doubleton(problem)
    problem.column_lower[1] = Bound(0.0)
    @test JSimplex.substitute_free_doubleton(problem).problem === problem
end
