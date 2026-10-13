using SparseArrays

@testset "Dual fixing avoids selections when all movements are blocked" begin
    count = 128
    problem = LinearProblem(sparse(1:count, 1:count, ones(count), count, count), ones(count);
        row_lower=zeros(count), row_upper=ones(count), column_upper=ones(count))
    JSimplex.reduce_dual_fixings(problem)
    @test (@allocated JSimplex.reduce_dual_fixings(problem)) <= 512
    @test JSimplex.reduce_dual_fixings(problem).problem === problem
end

@testset "Lazy dual selections preserve skipped columns and zero-cost preference" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), sense in (MIN_SENSE, MAX_SENSE)
        costs = sense == MIN_SENSE ? T[1, -1, 0, 0] : T[-1, 1, 0, 0]
        problem = LinearProblem(sparse(1:4, 1:4, ones(T, 4), 4, 4), costs;
            objective_sense=sense, objective_constant=T(5),
            row_lower=[T(0), T(0), T(0), nothing],
            row_upper=[T(10), T(10), nothing, nothing],
            column_lower=T[0, 0, 1, -2], column_upper=T[10, 10, 4, 2],
            column_names=["blocked_lower", "blocked_upper", "upper_fallback", "prefer_lower"])
        original = deepcopy(problem)
        result = JSimplex.reduce_dual_fixings(problem)
        step = only(result.postsolve_stack)
        @test step.columns == [1, 2]
        @test step.rows == [1, 2]
        @test step.removed_values == [nothing, nothing, T(4), T(-2)]
        @test step.removed_states == [JSimplex.FREE_NONBASIC, JSimplex.FREE_NONBASIC,
                                     JSimplex.AT_UPPER, JSimplex.AT_LOWER]
        @test result.problem.A == T[1 0; 0 1]
        @test result.problem.objective == costs[1:2]
        @test result.problem.objective_constant == T(5)
        @test result.problem.column_names == ["blocked_lower", "blocked_upper"]
        @test JSimplex.postsolve_primal(result, T[0, 0]) == T[0, 0, 4, -2]
        basis = JSimplex.Basis([3, 4], [JSimplex.AT_LOWER, JSimplex.AT_UPPER,
                                       JSimplex.BASIC, JSimplex.BASIC])
        restored = JSimplex.restore_basis(result, basis)
        @test restored.basic_indices == collect(5:8)
        @test restored.states[1:4] == [JSimplex.AT_LOWER, JSimplex.AT_UPPER,
                                      JSimplex.AT_UPPER, JSimplex.AT_LOWER]
        @test problem.A == original.A
        @test problem.objective == original.objective
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Lazy dual selections retain nonzero contributions and negative coefficients" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(1:3, 1:3, T[1, -1, 1], 3, 3), T[1, -2, 4];
            objective_constant=T(7), row_lower=[T(0), nothing, nothing],
            row_upper=T[10, 0, 10], column_lower=T[0, 0, 2], column_upper=T[10, 3, 5])
        result = JSimplex.reduce_dual_fixings(problem)
        @test only(result.postsolve_stack).columns == [1]
        @test result.problem.objective_constant == T(9)
        @test JSimplex.postsolve_primal(result, T[1]) == T[1, 3, 2]
    end
end

@testset "Dual fixing leaves absent or unbounded candidates unchanged" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for (rows, columns) in ((0, 0), (3, 0), (0, 3), (3, 3))
            problem = LinearProblem(spzeros(T, rows, columns), zeros(T, columns);
                column_lower=fill(nothing, columns))
            @test JSimplex.reduce_dual_fixings(problem).problem === problem
        end
    end
end
