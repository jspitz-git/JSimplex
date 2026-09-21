using SparseArrays

@testset "Free pivot bounds need no exact activity allocations" begin
    for bounded_peers in (false, true)
        problem = LinearProblem(sparse(ones(1, 8)), zeros(8);
            row_lower=[6.0], row_upper=[6.0],
            column_lower=[nothing; fill(bounded_peers ? 0.0 : nothing, 7)],
            column_upper=[nothing; fill(bounded_peers ? 1.0 : nothing, 7)])
        terms = [(column, 1.0) for column in 1:8]
        pivot, rhs = big(1)//1, big(6)//1
        JSimplex._equality_implies_column_bounds(problem, terms, 1, pivot, rhs)
        @test (@allocated JSimplex._equality_implies_column_bounds(problem, terms, 1, pivot, rhs)) <= 64
    end
end

@testset "Only free pivots bypass the column bound proof" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for (pivot, low, high, too_low, too_high) in
            ((1, 2, 4, 3, 3), (-1, -4, -2, -3, -3),
             (2, 1, 2, 1.5, 1.5), (-2, -2, -1, -1.5, -1.5))
            for (peer_lower, peer_upper, lower, upper, expected) in
                ((2, 4, nothing, nothing, true),
                 (nothing, nothing, nothing, nothing, true),
                 (2, 4, low, high, true),
                 (2, 4, too_low, high, false),
                 (2, 4, low, too_high, false),
                 (2, 4, low, nothing, true),
                 (2, 4, nothing, high, true),
                 (nothing, nothing, low, nothing, false),
                 (nothing, nothing, nothing, high, false),
                 (2, nothing, low, high, false),
                 (nothing, 4, low, high, false))
                problem = LinearProblem(sparse(reshape(T[pivot, 1], 1, 2)), zeros(T, 2);
                    row_lower=T[6], row_upper=T[6],
                    column_lower=[lower, peer_lower], column_upper=[upper, peer_upper])
                terms = [(1, T(pivot)), (2, one(T))]
                @test JSimplex._equality_implies_column_bounds(problem, terms, 1,
                    big(pivot)//1, big(6)//1) == expected
            end
        end
    end
end

@testset "Free pivot aggregation preserves model and postsolve data" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 1; 1 -1]), T[2, 1];
            row_lower=[T(4), nothing], row_upper=T[4, 0],
            column_lower=[nothing, T(0)], column_upper=[nothing, T(3)])
        original = deepcopy(problem)
        result = JSimplex.aggregate_sparse_equalities(problem)
        @test result.problem.A == reshape(T[-2], 1, 1)
        @test result.problem.objective == T[-1]
        @test result.problem.objective_constant == T(8)
        @test bound_value.(result.problem.row_upper) == T[-4]
        @test only(result.postsolve_stack).map.rows == [2]
        @test only(result.postsolve_stack).map.columns == [2]
        @test JSimplex.postsolve_primal(result, T[3]) == T[1, 3]
        basis = JSimplex.Basis([2], JSimplex.VariableState[JSimplex.AT_UPPER, JSimplex.BASIC])
        restored = JSimplex.restore_basis(result, basis)
        @test restored.basic_indices == [1, 4]
        @test restored.states == JSimplex.VariableState[
            JSimplex.BASIC, JSimplex.AT_UPPER, JSimplex.AT_LOWER, JSimplex.BASIC]
        @test problem.A == original.A
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
    end
end
