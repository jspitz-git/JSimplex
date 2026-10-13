using Test, JSimplex, SparseArrays

@testset "Unscaling without presolve reductions repairs original feasibility" begin
    for T in (Float32, Float64), algorithm in (:dual, :primal)
        coefficient = T(2)^24
        problem = LinearProblem(sparse(reshape(T[coefficient], 1, 1)), T[1];
            row_lower=T[1])
        original = deepcopy(problem)
        options = SolverOptions(T; algorithm, presolve=false, scaling=:on,
            simplex_strategy=:legacy, verbose=false)
        # Zero is feasible within the scaled row tolerance, but violates the
        # original row by one. Empty postsolve stacks still need this recovery.
        scaled, _ = JSimplex.scale_problem(problem)
        @test JSimplex._original_primal_feasible(scaled, T[0], options.primal_tolerance)
        @test !JSimplex._original_primal_feasible(problem, T[0], options.primal_tolerance)
        result = solve(problem; options)
        @test result.status == OPTIMAL
        @test result.primal !== nothing &&
            JSimplex._original_primal_feasible(problem, result.primal, options.primal_tolerance)
        @test result.objective_value !== nothing && result.objective_value ≈ inv(coefficient)
        @test problem.A == original.A && problem.row_lower == original.row_lower
        @test problem.objective == original.objective
    end
end

@testset "Unscaled cleanup keeps budgets and does not accept original infeasibility" begin
    for algorithm in (:dual, :primal)
        problem = LinearProblem(sparse([1.0 0; 0 2.0^24]), [1.0,1.0];
            row_lower=[1.0,1.0])
        limited = solve(problem; options=SolverOptions(; algorithm, presolve=false,
            iteration_limit=1, verbose=false))
        @test limited.status == ITERATION_LIMIT
        @test limited.statistics.iterations <= 1
        @test limited.primal === nothing
        timed = solve(problem; options=SolverOptions(; algorithm, presolve=false,
            time_limit=0.0, verbose=false))
        @test timed.status == TIME_LIMIT
        @test timed.statistics.iterations == 0
        impossible = LinearProblem(sparse(reshape([2.0^24],1,1)),[1.0];
            row_lower=[1.0], column_upper=[0.0])
        rejected = solve(impossible; options=SolverOptions(; algorithm,
            presolve=false, verbose=false))
        # This control checks rejection, not availability of an infeasibility
        # certificate for the original ill-scaled model.
        @test rejected.status in (INFEASIBLE, NUMERICAL_ERROR)
        @test rejected.primal === nothing
    end
end

@testset "Feasible unscaled points avoid unnecessary cleanup" begin
    for algorithm in (:dual,:primal), scaling in (:on,:off)
        problem=LinearProblem(sparse(reshape([1.0],1,1)),[1.0];row_lower=[1.0])
        io=IOBuffer()
        result=JSimplex.Logging.with_logger(JSimplex.Logging.SimpleLogger(io)) do
            solve(problem;options=SolverOptions(;algorithm,scaling,presolve=false,verbose=true))
        end
        @test result.status==OPTIMAL
        @test result.primal==[1.0]
        @test !occursin("Starting postsolve cleanup",String(take!(io)))
    end
end
