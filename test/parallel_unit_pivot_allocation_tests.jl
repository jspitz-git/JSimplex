using SparseArrays

@testset "Parallel rows avoid division by one allocations" begin
    terms = [(column, 1.0) for column in 1:64]
    JSimplex._parallel_signature(terms)
    @test (@allocated JSimplex._parallel_signature(terms)) <= 35_000

    problem = LinearProblem(sparse(ones(1, 1)), [0.0]; row_lower=[2.0], row_upper=[6.0])
    pivot = big(1)//1
    JSimplex._normalized_interval(problem, 1, pivot)
    @test (@allocated JSimplex._normalized_interval(problem, 1, pivot)) <= 1_000

    repeated = LinearProblem(sparse(repeat([1.0 2.0 -1.0], 128, 1)), zeros(3);
        row_lower=zeros(128), row_upper=fill(6.0, 128), column_lower=fill(nothing, 3))
    JSimplex.reduce_parallel_rows(repeated)
    @test (@allocated JSimplex.reduce_parallel_rows(repeated)) <= 500_000
end

@testset "Parallel normalization preserves signs and unbounded endpoints" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(ones(T, 4, 1)), zeros(T, 1);
            row_lower=[T(0), nothing, T(0), nothing],
            row_upper=[T(6), T(6), nothing, nothing])
        original = deepcopy(problem)
        for (scale, expected) in
            ((1, ((0, 6), (nothing, 6), (0, nothing), (nothing, nothing))),
             (-1, ((-6, 0), (-6, nothing), (nothing, 0), (nothing, nothing))),
             (2, ((0, 3), (nothing, 3), (0, nothing), (nothing, nothing))),
             (1//2, ((0, 12), (nothing, 12), (0, nothing), (nothing, nothing))))
            terms = [(2, T(scale)), (4, T(2scale)), (7, T(-3scale))]
            saved = deepcopy(terms)
            @test JSimplex._parallel_signature(terms) == [big(1)//1, big(2)//1, -big(3)//1]
            @test terms == saved
            for row in 1:4
                @test JSimplex._normalized_interval(problem, row, Rational{BigInt}(scale)) == expected[row]
            end
        end
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Parallel groups preserve tightened and overlapping intervals" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 2 -1; 2 4 -2; -1 -2 1; 1 2 -1; 1 1 -1; 1 2 -1]),
            zeros(T, 3); row_lower=T[0, 2, -4, 3, 0, -1], row_upper=T[6, 10, -2, 7, 6, 8],
            row_names=["wide", "scaled", "negative", "overlap", "different", "duplicate"])
        original = deepcopy(problem)
        result = JSimplex.reduce_parallel_rows(problem)
        @test only(result.postsolve_stack).rows == [3, 4, 5]
        @test result.problem.A == T[-1 -2 1; 1 2 -1; 1 1 -1]
        @test bound_value.(result.problem.row_lower) == T[-4, 3, 0]
        @test bound_value.(result.problem.row_upper) == T[-2, 7, 6]
        @test result.problem.row_names == ["negative", "overlap", "different"]
        @test JSimplex.postsolve_primal(result, T[3, 0, 0]) == T[3, 0, 0]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[6] = Bound(T(5))
        problem.row_upper[6] = Bound(T(6))
        failure = JSimplex.reduce_parallel_rows(problem)
        @test failure isa JSimplex.PresolveFailure
        @test failure.status == INFEASIBLE
        @test problem.A == original.A
        @test bound_value(problem.row_lower[6]) == T(5)
    end
end
