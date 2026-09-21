@testset "Phase-I vectors avoid concatenation scratch" begin
    problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, 1024, 1024), ones(1024))
    JSimplex._primal_phase_one_vectors(problem, 1024)
    # The three final arrays contain about 80 KiB of costs and bounds.
    @test (@allocated JSimplex._primal_phase_one_vectors(problem, 1024)) <= 90_000
end

@testset "Phase-I costs and bounds retain values and own their storage" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for (columns, artificials) in ((3, 2), (0, 2), (3, 0), (0, 0))
            input_lower = [isodd(i) ? Bound{T}(nothing) : Bound(T(-i)) for i in 1:columns]
            input_upper = [iseven(i) ? Bound{T}(nothing) : Bound(T(i)) for i in 1:columns]
            problem = LinearProblem(JSimplex.SparseArrays.spzeros(T, artificials, columns),
                T[-i for i in 1:columns]; column_lower=input_lower, column_upper=input_upper)
            original_objective = copy(problem.objective)
            objective, lower, upper = @inferred JSimplex._primal_phase_one_vectors(problem, artificials)
            @test objective == vcat(zeros(T, columns), ones(T, artificials))
            @test lower == vcat(input_lower, fill(Bound(zero(T)), artificials))
            @test upper == vcat(input_upper, fill(Bound{T}(nothing), artificials))
            @test objective !== problem.objective
            @test lower !== problem.column_lower
            @test upper !== problem.column_upper
            @test lower !== upper
            another = JSimplex._primal_phase_one_vectors(problem, artificials)
            @test all(pair -> first(pair) !== last(pair), zip((objective, lower, upper), another))
            if !isempty(objective)
                objective[1] = T(99)
                lower[1] = Bound(T(-99))
                upper[end] = Bound(T(99))
                @test problem.objective == original_objective
                @test problem.column_lower == input_lower
                @test problem.column_upper == input_upper
                @test another[1] == vcat(zeros(T, columns), ones(T, artificials))
                @test another[2] == vcat(input_lower, fill(Bound(zero(T)), artificials))
                @test another[3] == vcat(input_upper, fill(Bound{T}(nothing), artificials))
            end
        end
    end
end

@testset "Phase-I vectors retain stored BigFloat bounds" begin
    problem = setprecision(BigFloat, 512) do
        stored = BigFloat(1) + BigFloat(2)^(-300)
        LinearProblem(JSimplex.SparseArrays.spzeros(BigFloat, 1, 1), [stored];
                      column_lower=[stored], column_upper=[stored + 1])
    end
    setprecision(BigFloat, 64) do
        objective, lower, upper = JSimplex._primal_phase_one_vectors(problem, 1)
        @test objective == BigFloat[0, 1]
        @test all(value -> precision(value) == 64, objective)
        @test isequal(bound_value(lower[1]), bound_value(problem.column_lower[1]))
        @test isequal(bound_value(upper[1]), bound_value(problem.column_upper[1]))
        @test precision(bound_value(lower[1])) == 512
        @test precision(bound_value(upper[1])) == 512
        @test iszero(bound_value(lower[2])) && precision(bound_value(lower[2])) == 64
        @test !isfinite(upper[2])
    end
end
