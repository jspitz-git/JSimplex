using JSimplex.SparseArrays

function unsafe_structural_candidates(count; safe=true)
    columns = 2 + count + Int(safe)
    A = zeros(2, columns)
    A[1, 1:2] = [1.0, 7e-8]
    A[1, 3:2+count] .= 0.01
    safe && (A[:, end] = [-1.0, -1.0])
    costs = [0.0; 0.0; fill(-2.0, count); safe ? [-1.0] : Float64[]]
    problem = LinearProblem(sparse(A), costs; row_lower=[0.0, 0.0],
        row_upper=[0.0, Inf], column_lower=[0.0; 1.0; zeros(columns-2)],
        column_upper=[Inf; 1.0; fill(Inf, columns-2)])
    options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy,
        basis_update=:bartels_golub, pricing=:steepest_edge, verbose=false)
    workspace = JSimplex.initialize_workspace(problem, options)
    workspace.basis.basic_indices[1] = 1
    workspace.basis.states[1] = JSimplex.BASIC
    workspace.basis.states[columns+1] = JSimplex.AT_LOWER
    JSimplex.recompute!(workspace; refactorize=true)
    workspace.refactorizations = 0
    return workspace
end

@testset "Legacy primal tries another entering variable before failing a ratio test" begin
    workspace = unsafe_structural_candidates(1)
    terminal = JSimplex._primal_iteration!(workspace, () -> false, workspace.options.dual_tolerance)
    @test isnothing(terminal)
    @test workspace.iterations == 1
    @test 4 in workspace.basis.basic_indices
    @test workspace.primal[3] == 0.0
    @test JSimplex.primal_infeasibility(workspace) == 0.0
    @test workspace.refactorizations == 0
    @test isempty(workspace.scratch.rejected_entering)
end

@testset "Legacy primal candidate retry honors cancellation and clears rejections" begin
    workspace = unsafe_structural_candidates(1)
    calls = Ref(0)
    stop = () -> (calls[] += 1; calls[] >= 2)
    terminal = JSimplex._primal_iteration!(workspace, stop, workspace.options.dual_tolerance)
    @test terminal.status == TIME_LIMIT
    @test workspace.iterations == 0
    @test workspace.basis.basic_indices == [1, 6]
    @test isempty(workspace.scratch.rejected_entering)
    @test isnothing(JSimplex._primal_iteration!(workspace, () -> false, workspace.options.dual_tolerance))
    @test workspace.iterations == 1
end

@testset "Legacy primal does not report optimality after exhausting unsafe candidates" begin
    workspace = unsafe_structural_candidates(2; safe=false)
    terminal = JSimplex._primal_iteration!(workspace, () -> false, workspace.options.dual_tolerance)
    @test terminal.status == NUMERICAL_ERROR
    @test workspace.iterations == 0
    @test workspace.basis.basic_indices == [1, 6]
    @test isempty(workspace.scratch.rejected_entering)
end

@testset "Legacy primal searches beyond eight unsafe entering candidates" begin
    workspace = unsafe_structural_candidates(9)
    terminal = JSimplex._primal_iteration!(workspace, () -> false, workspace.options.dual_tolerance)
    @test isnothing(terminal)
    @test workspace.iterations == 1
    @test 12 in workspace.basis.basic_indices
    @test isempty(workspace.scratch.rejected_entering)
end

@testset "Legacy primal skips tiny pivots after a single basis refresh" begin
    problem = LinearProblem(sparse([1e-14 0.0 0.0; 0.0 2e-14 0.0; 0.0 0.0 1.0]),
        [-3.0, -2.0, -1.0]; row_upper=[1e-20, 1e-20, 1.0])
    options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy, verbose=false)
    workspace = JSimplex.initialize_workspace(problem, options)
    terminal = JSimplex._primal_iteration!(workspace, () -> false, options.dual_tolerance)
    @test isnothing(terminal)
    @test workspace.iterations == 1
    @test workspace.primal[3] ≈ 1.0
    @test workspace.refactorizations == 1
    @test isempty(workspace.scratch.rejected_entering)
end
