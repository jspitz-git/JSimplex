using SparseArrays

@testset "Propagation avoids bounds copies when no tightening is possible" begin
    problem = LinearProblem(sparse([1, 1], [1, 2], [1.0, 1.0], 1, 4096), zeros(4096);
        column_lower=fill(nothing, 4096), row_lower=[0.0], row_upper=[1.0])
    JSimplex.propagate_row_bounds(problem)
    @test (@allocated JSimplex.propagate_row_bounds(problem)) <= 100_000
    @test JSimplex.propagate_row_bounds(problem).problem === problem
end

@testset "Lazy propagation bounds preserve incremental updates and original bounds" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for lower_first in (false, true)
            problem = LinearProblem(sparse(lower_first ? T[-1 0; 1 1] : T[1 0; 1 1]), T[1, 1];
                row_lower=lower_first ? [nothing, nothing] : [nothing, T(7)],
                row_upper=lower_first ? T[-3, 7] : [T(3), nothing], column_upper=T[10, 10])
            active, changed = BitVector([true, false]), falses(2)
            result = JSimplex._propagate_row_bounds(problem, active, changed)
            @test bound_value.(result.problem.column_lower) == (lower_first ? T[3, 0] : T[0, 4])
            @test bound_value.(result.problem.column_upper) == (lower_first ? T[7, 4] : T[3, 10])
            @test changed == [true, true]
            @test active == [true, false]
            step = only(result.postsolve_stack)
            @test bound_value.(step.old_lower) == T[0, 0]
            @test bound_value.(step.old_upper) == T[10, 10]
            @test result.problem.column_lower !== problem.column_lower
            @test result.problem.column_upper !== problem.column_upper
            result.problem.column_lower[1] = Bound(T(-1))
            result.problem.column_upper[1] = Bound(T(20))
            @test bound_value.(problem.column_lower) == T[0, 0]
            @test bound_value.(problem.column_upper) == T[10, 10]
        end
    end
end

@testset "Propagation failure after tightening preserves the source" begin
    problem = LinearProblem(sparse([1.0 0.0; 1.0 1.0]), [1.0, 1.0];
        row_lower=[nothing, 15.0], row_upper=[3.0, nothing], column_upper=[10.0, 10.0])
    changed = falses(2)
    failure = JSimplex._propagate_row_bounds(problem, BitVector([true, false]), changed)
    @test failure.status == INFEASIBLE
    @test changed == [true, false]
    @test bound_value.(problem.column_lower) == [0.0, 0.0]
    @test bound_value.(problem.column_upper) == [10.0, 10.0]
end
