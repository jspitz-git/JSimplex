using SparseArrays

@testset "Propagation avoids converting unchanged candidate bounds" begin
    count = 128
    problem = LinearProblem(sparse(ones(count, 2)), ones(2);
        row_lower=fill(10.0, count), row_upper=fill(10.0, count), column_upper=fill(10.0, 2))
    JSimplex.propagate_row_bounds(problem)
    measured = @timed JSimplex.propagate_row_bounds(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 24_000
    @test JSimplex.propagate_row_bounds(problem).problem === problem
end

@testset "Equal candidates preserve existing bounds and change flags" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), coefficient in (1, -1, 2, 1//2)
        problem = LinearProblem(sparse(fill(T(coefficient), 1, 2)), ones(T, 2);
            row_lower=T[10coefficient], row_upper=T[10coefficient], column_upper=T[10, 10])
        original = deepcopy(problem)
        active, changed = trues(1), BitVector([true, false])
        result = JSimplex._propagate_row_bounds(problem, active, changed)
        @test result.problem === problem
        @test changed == [true, false]
        @test active == [true]
        @test isempty(result.postsolve_stack)
        @test JSimplex.postsolve_primal(result, T[4, 6]) == T[4, 6]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
    end
end

@testset "Equal candidates use the latest accepted cache values" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[1 0; 1 1]), ones(T, 2);
            row_lower=[nothing, T(6)], row_upper=T[6, 6], column_upper=T[10, 10])
        original = deepcopy(problem)
        active, changed = BitVector([true, false]), falses(2)
        result = JSimplex._propagate_row_bounds(problem, active, changed)
        @test bound_value.(result.problem.column_lower) == T[0, 0]
        @test bound_value.(result.problem.column_upper) == T[6, 6]
        @test changed == [true, true]
        @test active == [true, false]
        @test JSimplex.postsolve_primal(result, T[2, 4]) == T[2, 4]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
    end
end

@testset "Equal candidates retain stored zero signs and BigFloat precision" begin
    for T in (Float32, Float64, BigFloat)
        problem = LinearProblem(sparse(ones(T, 1, 2)), ones(T, 2);
            row_lower=T[10], row_upper=T[10], column_lower=fill(-zero(T), 2), column_upper=T[10, 10])
        result = JSimplex.propagate_row_bounds(problem)
        @test result.problem === problem
        @test all(signbit, bound_value.(result.problem.column_lower))
    end
    problem = setprecision(BigFloat, 256) do
        value = BigFloat(1) + BigFloat(2)^(-100)
        LinearProblem(sparse(ones(BigFloat, 1, 2)), ones(BigFloat, 2);
            row_lower=[value], row_upper=[value], column_upper=[value, value])
    end
    original = deepcopy(problem)
    setprecision(BigFloat, 64) do
        changed = falses(2)
        result = JSimplex._propagate_row_bounds(problem, trues(1), changed)
        @test result.problem === problem
        @test !any(changed)
        @test result.problem.column_upper == original.column_upper
        @test all(value -> precision(bound_value(value)) == 256, result.problem.column_upper)
        @test precision(BigFloat) == 64
    end
end
