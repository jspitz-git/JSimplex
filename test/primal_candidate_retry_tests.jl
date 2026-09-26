using JSimplex.SparseArrays

@testset "Legacy primal tries another entering variable before failing a ratio test" begin
    problem = LinearProblem(sparse([-7e-8 -0.01 1.0; 0.0 0.0 -1.0]), [0.0, -2.0, -1.0];
        row_lower=[0.0, 0.0], column_lower=[1.0, 0.0, 0.0],
        column_upper=[1.0, Inf, Inf])
    options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy,
        basis_update=:bartels_golub, pricing=:steepest_edge, verbose=false)
    workspace = JSimplex.initialize_workspace(problem, options)
    terminal = JSimplex._primal_iteration!(workspace, () -> false, options.dual_tolerance)
    @test isnothing(terminal)
    @test workspace.iterations == 1
    @test 3 in workspace.basis.basic_indices
    @test workspace.primal[2] == 0.0
    @test JSimplex.primal_infeasibility(workspace) == 0.0
    @test workspace.refactorizations == 0
    @test isempty(workspace.scratch.rejected_entering)
end

@testset "Legacy primal candidate retry honors cancellation and clears rejections" begin
    problem = LinearProblem(sparse([-7e-8 -0.01 1.0; 0.0 0.0 -1.0]), [0.0, -2.0, -1.0];
        row_lower=[0.0, 0.0], column_lower=[1.0, 0.0, 0.0],
        column_upper=[1.0, Inf, Inf])
    options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy, verbose=false)
    workspace = JSimplex.initialize_workspace(problem, options)
    calls = Ref(0)
    stop = () -> (calls[] += 1; calls[] >= 2)
    terminal = JSimplex._primal_iteration!(workspace, stop, options.dual_tolerance)
    @test terminal.status == TIME_LIMIT
    @test workspace.iterations == 0
    @test workspace.basis.basic_indices == [4, 5]
    @test isempty(workspace.scratch.rejected_entering)
    # Cancellation must not exclude the useful candidate in a subsequent call.
    @test isnothing(JSimplex._primal_iteration!(workspace, () -> false, options.dual_tolerance))
    @test workspace.iterations == 1
end

@testset "Legacy primal does not report optimality after exhausting unsafe candidates" begin
    problem = LinearProblem(sparse([-7e-8 -0.01 -0.02]), [0.0, -2.0, -1.0];
        row_lower=[0.0], column_lower=[1.0, 0.0, 0.0], column_upper=[1.0, Inf, Inf])
    options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy, verbose=false)
    workspace = JSimplex.initialize_workspace(problem, options)
    terminal = JSimplex._primal_iteration!(workspace, () -> false, options.dual_tolerance)
    @test terminal.status == NUMERICAL_ERROR
    @test workspace.iterations == 0
    @test workspace.basis.basic_indices == [4]
    @test isempty(workspace.scratch.rejected_entering)
end

@testset "Legacy primal searches beyond eight unsafe entering candidates" begin
    # Nine identically unsafe improving columns precede a valid zero-step pivot.
    A = zeros(2, 11)
    A[1, 1] = -7e-8
    A[1, 2:10] .= -0.01
    A[:, 11] = [1.0, -1.0]
    problem = LinearProblem(sparse(A), [0.0; fill(-2.0, 9); -1.0];
        row_lower=[0.0, 0.0], column_lower=[1.0; zeros(10)],
        column_upper=[1.0; fill(Inf, 10)])
    options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy, verbose=false)
    workspace = JSimplex.initialize_workspace(problem, options)
    terminal = JSimplex._primal_iteration!(workspace, () -> false, options.dual_tolerance)
    @test isnothing(terminal)
    @test workspace.iterations == 1
    @test 11 in workspace.basis.basic_indices
    @test isempty(workspace.scratch.rejected_entering)
end
