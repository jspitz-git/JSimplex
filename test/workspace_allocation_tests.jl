@testset "Workspace initialization avoids temporary copies" begin
    problem = read_mps(joinpath(@__DIR__, "fixtures", "solver", "netlib", "adlittle.mps"))
    options = SolverOptions(verbose=false)
    JSimplex.initialize_workspace(problem, options)
    @test (@allocated JSimplex.initialize_workspace(problem, options)) <= 63_000
end

@testset "Workspace costs and bounds own their storage" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(JSimplex.SparseArrays.spzeros(T, 2, 3), T[3, -2, 0];
            column_lower=[T(1), nothing, nothing], column_upper=[T(4), T(5), nothing],
            row_lower=T[2, 3], row_upper=[T(7), nothing])
        options = SolverOptions(T;verbose=false)
        workspace = @inferred JSimplex.initialize_workspace(problem, options)
        @test workspace.costs == T[3, -2, 0, 0, 0]
        @test workspace.basis.basic_indices == [4, 5]
        @test workspace.basis.states == [JSimplex.AT_LOWER, JSimplex.AT_UPPER,
            JSimplex.FREE_NONBASIC, JSimplex.BASIC, JSimplex.BASIC]
        @test workspace.lower == [Bound(T(1)), Bound{T}(nothing), Bound{T}(nothing),
                                 Bound(T(2)), Bound(T(3))]
        @test workspace.upper == [Bound(T(4)), Bound(T(5)), Bound{T}(nothing),
                                 Bound(T(7)), Bound{T}(nothing)]
        workspace.costs[1] = T(9)
        workspace.lower[1] = Bound(T(-99))
        workspace.lower[4] = Bound(T(-98))
        workspace.upper[2] = Bound(T(88))
        workspace.upper[4] = Bound(T(87))
        @test problem.objective == T[3, -2, 0]
        @test bound_value(problem.column_lower[1]) == T(1)
        @test bound_value(problem.row_lower[1]) == T(2)
        @test bound_value(problem.column_upper[2]) == T(5)
        @test bound_value(problem.row_upper[1]) == T(7)
        @test workspace.progress.objective == T[3, -2, 0]
        another = JSimplex.initialize_workspace(problem, options)
        @test another.costs == T[3, -2, 0, 0, 0]
    end
end

@testset "Workspace initialization handles empty dimensions" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), (rows, columns) in ((0, 0), (0, 3), (3, 0))
        problem = LinearProblem(JSimplex.SparseArrays.spzeros(T, rows, columns), ones(T, columns))
        workspace = @inferred JSimplex.initialize_workspace(problem, SolverOptions(T;verbose=false))
        @test length(workspace.costs) == rows + columns
        @test all(isone, workspace.costs[1:columns])
        @test all(iszero, workspace.costs[columns+1:end])
        @test length(workspace.basis.basic_indices) == rows
    end
end

@testset "Workspace retains stored BigFloat objective precision" begin
    problem = setprecision(BigFloat, 512) do
        LinearProblem(JSimplex.SparseArrays.spzeros(BigFloat, 0, 1),
                      [BigFloat(1) + BigFloat(2)^(-300)])
    end
    setprecision(BigFloat, 64) do
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(BigFloat;verbose=false))
        @test isequal(workspace.costs[1], problem.objective[1])
        @test precision(workspace.costs[1]) == 512
    end
end
