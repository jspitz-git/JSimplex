using SparseArrays

@testset "Parallel signatures reuse one for repeated pivot coefficients" begin
    count = 128
    for (kind, limit) in ((:positive, 11_500), (:negative, 11_500), (:unit, 8_500),
                           (:unequal, 15_500), (:unit_unequal, 10_900))
        pivot = kind in (:unit, :unit_unequal) ? 1.0 : kind == :negative ? -2.0 : 2.0
        row = kind in (:unequal, :unit_unequal) ? [pivot 2pivot -pivot] : fill(pivot, 1, 3)
        problem = LinearProblem(sparse(repeat(row, count, 1)), zeros(3);
            row_lower=fill(min(0.0, 6pivot), count), row_upper=fill(max(0.0, 6pivot), count),
            column_lower=fill(nothing, 3))
        JSimplex.reduce_parallel_rows(problem)
        measured = @timed JSimplex.reduce_parallel_rows(problem)
        @test Base.gc_alloc_count(measured.gcstats) <= limit
        @test only(JSimplex.reduce_parallel_rows(problem).postsolve_stack).rows == [1]
    end
end

@testset "Repeated pivot signatures preserve unequal and opposite coefficients" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), pivot in (1, 2, -2, 1//2, -1//2)
        s = T(pivot)
        terms = [(5, s), (9, s), (12, 2s), (15, -s), (20, s), (25, T(0))]
        original = deepcopy(terms)
        expected = Rational{BigInt}[1, 1, 2, -1, 1, 0]
        @test JSimplex._parallel_signature(terms) == expected
        @test JSimplex._parallel_signature(Tuple(terms)) == expected
        @test JSimplex._parallel_signature([(7, s)]) == Rational{BigInt}[1]
        @test terms == original
    end
end

@testset "Repeated coefficients preserve parallel representatives and contradictions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[2 2 2; -2 -2 -2; 1 1 1; 2 2 3]), zeros(T, 3);
            row_lower=T[0, -10, 1, 0], row_upper=T[12, 0, 4, 12],
            column_lower=fill(nothing, 3))
        original = deepcopy(problem)
        result = JSimplex.reduce_parallel_rows(problem)
        @test only(result.postsolve_stack).rows == [3, 4]
        @test result.problem.A == T[1 1 1; 2 2 3]
        @test JSimplex.postsolve_primal(result, T[1, 1, 0]) == T[1, 1, 0]
        @test problem.A == original.A
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper

        problem.row_lower[3] = Bound(T(7))
        problem.row_upper[3] = Bound(T(8))
        @test JSimplex.reduce_parallel_rows(problem).status == INFEASIBLE
        @test problem.A == original.A
    end
end

@testset "Signature equality compares stored BigFloat values exactly" begin
    pivot = setprecision(BigFloat, 192) do
        BigFloat(2) + BigFloat(2)^(-100)
    end
    same = setprecision(BigFloat, 256) do
        BigFloat(pivot)
    end
    different = setprecision(BigFloat, 320) do
        BigFloat(pivot) + BigFloat(2)^(-120)
    end
    terms = [(5, pivot), (9, same), (12, different)]
    original = deepcopy(terms)
    expected = Rational{BigInt}[1, 1, Rational{BigInt}(different) / Rational{BigInt}(pivot)]
    setprecision(BigFloat, 64) do
        @test JSimplex._parallel_signature(terms) == expected
        @test terms == original
        @test precision.(last.(terms)) == [192, 256, 320]
        @test precision(BigFloat) == 64
    end
end
