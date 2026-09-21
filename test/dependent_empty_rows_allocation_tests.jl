using SparseArrays

@testset "Dependent reduction skips dictionaries for empty rows" begin
    count = 128
    for A in (spzeros(count, 3), sparse(collect(1:count), ones(Int, count), zeros(count), count, 3))
        problem = LinearProblem(A, zeros(3); row_lower=zeros(count), row_upper=zeros(count))
        JSimplex.reduce_dependent_rows(problem)
        measured = @timed JSimplex.reduce_dependent_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= 200
        @test JSimplex.reduce_dependent_rows(problem).problem === problem
    end
end

@testset "Empty dependent rows preserve identity and stored zeros" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), count in (0, 5, 257)
        A = sparse(collect(1:count), ones(Int, count), zeros(T, count), count, 3)
        # This pass leaves empty-row feasibility to the dedicated reduction.
        problem = LinearProblem(A, zeros(T, 3); row_lower=ones(T, count), row_upper=ones(T, count))
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test result.problem === problem
        @test problem.A.colptr == original.A.colptr
        @test problem.A.rowval == original.A.rowval
        @test problem.A.nzval == original.A.nzval
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Empty rows preserve dependency proofs and row maps" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        A = sparse(T[0 0; 2 4; 0 0; 2 4; 0 0])
        problem = LinearProblem(A, zeros(T, 2); row_lower=T[0, 6, 0, 6, 0],
            row_upper=T[0, 6, 0, 6, 0], column_lower=fill(nothing, 2))
        original = deepcopy(problem)
        result = JSimplex.reduce_dependent_rows(problem)
        @test only(result.postsolve_stack).rows == [1, 2, 3, 5]
        @test result.problem.A == T[0 0; 2 4; 0 0; 0 0]
        @test bound_value.(result.problem.row_lower) == T[0, 6, 0, 0]
        @test bound_value.(result.problem.row_upper) == T[0, 6, 0, 0]
        @test JSimplex.postsolve_primal(result, T[1, 1]) == T[1, 1]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[4] = Bound(T(7))
        problem.row_upper[4] = Bound(T(7))
        @test JSimplex.reduce_dependent_rows(problem).status == INFEASIBLE
    end
end
