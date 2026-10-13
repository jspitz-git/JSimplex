using SparseArrays

@testset "Propagation reuses one exact zero across rows" begin
    count = 128
    problem = LinearProblem(sparse(ones(count, 2)), ones(2);
        row_lower=zeros(count), row_upper=zeros(count), column_upper=zeros(2))
    JSimplex.propagate_row_bounds(problem)
    measured = @timed JSimplex.propagate_row_bounds(problem)
    @test Base.gc_alloc_count(measured.gcstats) <= 7_200
    result = JSimplex.propagate_row_bounds(problem)
    @test size(result.problem.A) == (0, 2)
    @test bound_value.(problem.column_lower) == [0.0, 0.0]
    @test bound_value.(problem.column_upper) == [0.0, 0.0]
end

@testset "Shared zero initialization keeps row activities independent" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(1:3, 1:3, ones(T, 3), 3, 3), ones(T, 3);
            row_lower=T[1, 0, -3], row_upper=T[2, 0, -1],
            column_lower=T[1, 0, -3], column_upper=T[2, 0, -1])
        original = deepcopy(problem)
        result = JSimplex.propagate_row_bounds(problem)
        @test size(result.problem.A) == (0, 3)
        @test JSimplex.postsolve_primal(result, T[1, 0, -2]) == T[1, 0, -2]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper
        @test problem.row_lower == original.row_lower
        @test problem.row_upper == original.row_upper
    end
end

@testset "Zero initialization follows empty and inactive rows" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(sparse(T[0 0 0; 1 0 0; 0 1 0; 0 0 1]), ones(T, 3);
            row_lower=T[0, 2, 2, -6], row_upper=T[0, 6, 6, -2],
            column_lower=T[0, 0, -10], column_upper=T[10, 10, 0])
        original = deepcopy(problem)
        active, changed = BitVector([true, false, true, true]), falses(3)
        result = JSimplex._propagate_row_bounds(problem, active, changed)
        @test bound_value.(result.problem.column_lower) == T[0, 2, -6]
        @test bound_value.(result.problem.column_upper) == T[10, 6, -2]
        @test changed == [false, true, true]
        @test active == [true, false, true, true]
        @test problem.column_lower == original.column_lower
        @test problem.column_upper == original.column_upper

        @test JSimplex._propagate_row_bounds(problem, falses(4)).problem === problem
        empty = LinearProblem(spzeros(T, 4, 3), ones(T, 3);
            row_lower=zeros(T, 4), row_upper=zeros(T, 4))
        @test JSimplex.propagate_row_bounds(empty).problem === empty
    end
end
