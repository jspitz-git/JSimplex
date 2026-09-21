@testset "Restoring original costs avoids temporary vectors" begin
    problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, 1, 1024), ones(1024))
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    JSimplex._restore_original_costs!(workspace)
    fill!(workspace.costs, 99.0)
    @test (@allocated JSimplex._restore_original_costs!(workspace)) == 0
    @test workspace.costs == vcat(ones(1024), 0.0)
end

@testset "Cost restoration preserves storage and original coefficients" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        for (rows, columns) in ((2, 3), (0, 0), (0, 3), (3, 0))
            objective = T[-i for i in 1:columns]
            problem = LinearProblem(JSimplex.SparseArrays.spzeros(T, rows, columns), objective)
            workspace = JSimplex.initialize_workspace(problem, SolverOptions(T;verbose=false))
            costs = workspace.costs
            primal, prices = copy(workspace.primal), copy(workspace.reduced_costs)
            fill!(costs, T(99))
            @test (@inferred JSimplex._restore_original_costs!(workspace)) === nothing
            @test workspace.costs === costs
            @test costs == vcat(objective, zeros(T, rows))
            @test problem.objective == objective
            @test workspace.primal == primal
            @test workspace.reduced_costs == prices
            if columns > 0
                problem.objective[1] = T(17)
                JSimplex._restore_original_costs!(workspace)
                @test costs[1] == T(17)
                costs[1] = T(23)
                @test problem.objective[1] == T(17)
            end
        end
    end
end

@testset "Cost restoration includes phase-I artificial columns" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        problem = LinearProblem(JSimplex.SparseArrays.sparse(T[1 1]), T[4, -5];
            row_lower=T[1], row_upper=T[1])
        options = SolverOptions(T;verbose=false, algorithm=:primal)
        workspace, artificial_count, _ = JSimplex._primal_phase_one(
            problem, options, JSimplex.SimplexProgressContext(problem), () -> false)
        @test artificial_count == 1
        workspace.problem.objective .= T[4, -5, 0]
        fill!(workspace.costs, T(99))
        JSimplex._restore_original_costs!(workspace)
        @test workspace.costs == T[4, -5, 0, 0]
        @test problem.objective == T[4, -5]
    end
end

@testset "Restored costs retain signed zeros and BigFloat precision" begin
    problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, 1, 1), [-0.0])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    fill!(workspace.costs, 99.0)
    JSimplex._restore_original_costs!(workspace)
    @test isequal(workspace.costs, [-0.0, 0.0])

    problem = setprecision(BigFloat, 512) do
        LinearProblem(JSimplex.SparseArrays.spzeros(BigFloat, 1, 1),
                      [BigFloat(1) + BigFloat(2)^(-300)])
    end
    setprecision(BigFloat, 64) do
        workspace = JSimplex.initialize_workspace(problem, SolverOptions(BigFloat;verbose=false))
        fill!(workspace.costs, BigFloat(99))
        JSimplex._restore_original_costs!(workspace)
        @test isequal(workspace.costs[1], problem.objective[1])
        @test precision(workspace.costs[1]) == 512
        @test iszero(workspace.costs[2]) && precision(workspace.costs[2]) == 64
    end
end
