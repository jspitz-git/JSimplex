using SparseArrays

@testset "Basic presolve reuses staged row changes" begin
    count = 256
    for kind in (:fixed, :empty)
        A = kind == :fixed ?
            hcat(sparse(1:count, 1:count, ones(count), count, count), sparse(ones(count, 1))) :
            sparse([1], [count + 1], [1.0], 1, count + 1)
        rows = size(A, 1)
        problem = LinearProblem(A, ones(count + 1);
            row_lower=zeros(rows), row_upper=ones(rows),
            column_lower=zeros(count + 1), column_upper=[zeros(count); 2.0])
        JSimplex._presolve_basic(problem)
        if kind == :fixed
            @test (@allocated JSimplex._presolve_basic(problem)) <= 490_000
        else
            # Counts distinguish the removed empty vectors from byte variability
            # in exact arithmetic across runs.
            measured = @timed JSimplex._presolve_basic(problem)
            @test Base.gc_alloc_count(measured.gcstats) <= 7_350
        end
    end
end

@testset "Reused basic scratch preserves cumulative shifts of varying lengths" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[2 0 1 1; 1 3 0 1; 0 1 0 1]), T[2, 3, 4, 1];
            objective_constant=T(7), row_lower=T[3, 0, 1], row_upper=T[6, 4, 5],
            column_lower=T[1, -1, 0.5, 0], column_upper=[T(1), T(-1), T(0.5), nothing])
        original = deepcopy(problem)
        result = JSimplex._presolve_basic(problem)
        @test result.problem.A == ones(T, 3, 1)
        @test result.problem.objective == T[1]
        @test result.problem.objective_constant == T(8)
        @test bound_value.(result.problem.row_lower) == T[0.5, 2, 2]
        @test bound_value.(result.problem.row_upper) == T[3.5, 6, 6]
        @test only(result.postsolve_stack).columns == [4]
        @test JSimplex.postsolve_primal(result, T[2]) == T[1, -1, 0.5, 2]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Rejected basic changes cannot leak through an empty column" begin
    for T in (Float32, Float64), accepted_first in (false, true)
        # Candidate 2 stages a shift for row 2, then fails on row 3. Candidate 3
        # has no row entries and must not commit the abandoned shift.
        problem = LinearProblem(sparse(T[1 0 0 1; 0 2 0 1; 0 0.1 0 1]), T[3, 0, 0, 1];
            objective_constant=T(5), row_lower=T[2, 2, 1], row_upper=T[4, 4, 2],
            column_lower=T[1, 0.5, 0, 0],
            column_upper=[accepted_first ? T(1) : nothing, T(0.5), nothing, nothing])
        original = deepcopy(problem)
        result = JSimplex._presolve_basic(problem)
        @test only(result.postsolve_stack).columns == (accepted_first ? [2, 4] : [1, 2, 4])
        @test bound_value.(result.problem.row_lower) == (accepted_first ? T[1, 2, 1] : T[2, 2, 1])
        @test bound_value.(result.problem.row_upper) == (accepted_first ? T[3, 4, 2] : T[4, 4, 2])
        @test result.problem.objective_constant == T(accepted_first ? 8 : 5)
        primal = accepted_first ? T[0.5, 1] : T[1, 0.5, 1]
        @test JSimplex.postsolve_primal(result, primal) == T[1, 0.5, 0, 1]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end
