using SparseArrays

@testset "Public solve derives BigFloat policy from stored input precision" begin
    for algorithm in (:primal, :dual), simplex_strategy in (:legacy, :adaptive), rows in (0, 1)
        problem, options = setprecision(BigFloat, 256) do
            p = rows == 0 ? LinearProblem(spzeros(BigFloat, 0, 1), BigFloat[1]; column_upper=BigFloat[1]) :
                LinearProblem(sparse(BigFloat[1;;]), BigFloat[1]; row_lower=BigFloat[1], column_upper=BigFloat[2])
            p, SolverOptions(BigFloat; algorithm, simplex_strategy, verbose=false, presolve=false, scaling=:off)
        end
        setprecision(BigFloat, 8) do
            result = try
                solve(problem; options)
            catch exception
                exception
            end
            @test result isa Solution{BigFloat}
            if result isa Solution
                @test result.status == OPTIMAL
                @test result.primal == BigFloat[rows]
                @test result.objective_value == rows
            end
            @test precision(BigFloat) == 8
            @test precision(options.primal_tolerance) == 256
            @test precision(problem.objective[1]) == 256
        end
    end
    setprecision(BigFloat, 8) do
        @test_throws ArgumentError JSimplex.NumericalPolicy(BigFloat)
    end
end
