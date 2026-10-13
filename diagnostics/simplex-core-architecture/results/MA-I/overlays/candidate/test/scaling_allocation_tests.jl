@testset "Scaling avoids separate maxima buffers" begin
    for (rows, columns, budget) in ((1, 1024, 112_000), (1024, 1, 87_000))
        problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, rows, columns), ones(columns))
        JSimplex.scale_problem(problem)
        @test (@allocated JSimplex.scale_problem(problem)) <= budget
    end
end

@testset "Scaling keeps independent column maxima and owned factor arrays" begin
    for T in (Float32, Float64, BigFloat)
        problem = LinearProblem(JSimplex.SparseArrays.sparse(T[8 2 1 0; 0 0 0 0]),
            T[4, 1, 2, 0]; variable_domains=[CONTINUOUS, CONTINUOUS, INTEGER, CONTINUOUS])
        scaled, factors = @inferred JSimplex.scale_problem(problem)
        again, again_factors = JSimplex.scale_problem(problem)
        @test factors.row_factors == T[8, 1]
        @test factors.column_factors == T[1, 1//4, 1, 1]
        @test scaled.A == JSimplex.SparseArrays.sparse(T[1 1 1//8 0; 0 0 0 0])
        @test scaled.objective == T[4, 4, 2, 0]
        @test scaled.variable_domains == problem.variable_domains
        @test factors.row_factors !== again_factors.row_factors
        @test factors.column_factors !== again_factors.column_factors
        factors.row_factors[1] = T(99)
        factors.column_factors[2] = T(99)
        scaled.A.nzval[1] = T(99)
        scaled.objective[1] = T(99)
        @test again_factors.row_factors == T[8, 1]
        @test again_factors.column_factors == T[1, 1//4, 1, 1]
        @test again.A[1, 1] == one(T)
        @test again.objective == T[4, 4, 2, 0]
        @test problem.A == JSimplex.SparseArrays.sparse(T[8 2 1 0; 0 0 0 0])
        @test problem.objective == T[4, 1, 2, 0]
    end
end

@testset "Reused row maxima reset invalid and empty rows to unit factors" begin
    for T in (Float32, Float64)
        problem = LinearProblem(JSimplex.SparseArrays.sparse(T[8 0; 0 1//8; 0 0]), zeros(T, 2);
            row_upper=[nothing, floatmax(T), nothing])
        scaled, factors = JSimplex.scale_problem(problem)
        @test factors.row_factors == T[8, 1, 1]
        @test factors.column_factors == T[1, 1//8]
        @test scaled.A == JSimplex.SparseArrays.sparse(T[1 0; 0 1; 0 0])
        @test bound_value(scaled.row_upper[2]) == floatmax(T)
    end
end

@testset "Scaling maxima handle empty dimensions" begin
    for T in (Float32, Float64, BigFloat), (rows, columns) in ((0, 0), (0, 3), (3, 0))
        problem = LinearProblem(JSimplex.SparseArrays.spzeros(T, rows, columns), ones(T, columns))
        scaled, factors = @inferred JSimplex.scale_problem(problem)
        @test size(scaled.A) == (rows, columns)
        @test scaled.objective == problem.objective
        @test factors.row_factors == ones(T, rows)
        @test factors.column_factors == ones(T, columns)
    end
end

@testset "Column maxima preserve stored BigFloat precision" begin
    problem = setprecision(BigFloat, 512) do
        stored = BigFloat(8) + BigFloat(2)^(-300)
        LinearProblem(JSimplex.SparseArrays.sparse(reshape([stored, BigFloat(2), BigFloat(0)], 1, 3)),
                      BigFloat[4, 1, 0])
    end
    setprecision(BigFloat, 64) do
        scaled, factors = JSimplex.scale_problem(problem)
        @test factors.row_factors == BigFloat[8]
        @test factors.column_factors == BigFloat[1, 1//4, 1]
        @test Rational{BigInt}(scaled.A[1, 1]) == Rational{BigInt}(problem.A[1, 1]) / 8
        @test precision(scaled.A[1, 1]) >= 512
        @test scaled.A[1, 2] == BigFloat(1)
        @test scaled.objective == BigFloat[4, 4, 0]
    end
end
