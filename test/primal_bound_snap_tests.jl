using JSimplex.SparseArrays

@testset "Legacy primal pivots preserve feasibility when a leaving bound is snapped" begin
    for update in (:pfi, :bartels_golub, :forrest_tomlin, :suhl_suhl),
        free_entering in (false, true), entering_sign in (1.0, -1.0),
        row_sign in (1.0, -1.0)
        # The fixed first column places row 1 just below its lower bound.
        # Snapping it exactly to zero would force x2 = -7e-6. Retain its
        # tolerated value or choose another safe zero-step Harris candidate.
        A = free_entering ? [-7e-8 -0.01; 0.0 -0.009; 0.0 1.0] :
                            [-7e-8 -0.01; 0.0 -0.009]
        A[:, 2] .*= entering_sign
        A .*= row_sign
        problem = LinearProblem(sparse(A), [0.0, -entering_sign];
            row_lower=fill(row_sign > 0 ? 0.0 : -Inf, size(A, 1)),
            row_upper=fill(row_sign > 0 ? Inf : 0.0, size(A, 1)),
            column_lower=[1.0, free_entering || entering_sign < 0 ? -Inf : 0.0],
            column_upper=[1.0, free_entering || entering_sign > 0 ? Inf : 0.0])
        options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy,
            pricing=:steepest_edge, basis_update=update,
            basis_refactorization=:native, refactorization_interval=80,
            primal_tolerance=1e-7, verbose=false)
        workspace = JSimplex.initialize_workspace(problem, options)
        @test JSimplex.primal_infeasibility(workspace) == 0.0
        terminal = JSimplex._primal_iteration!(workspace, () -> false,
            options.dual_tolerance)
        @test isnothing(terminal)
        @test workspace.iterations == 1
        @test JSimplex.primal_infeasibility(workspace) <= options.primal_tolerance
        @test abs(workspace.primal[2]) <= options.primal_tolerance
        @test workspace.refactorizations == 0
    end
end

function structural_bound_snap_workspace(coefficient)
    problem = LinearProblem(sparse([1.0 7e-8 coefficient]), [0.0, 0.0, -1.0];
        row_lower=[0.0], row_upper=[0.0], column_lower=[0.0, 1.0, 0.0],
        column_upper=[Inf, 1.0, Inf])
    options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy, verbose=false)
    workspace = JSimplex.initialize_workspace(problem, options)
    workspace.basis.basic_indices[1] = 1
    workspace.basis.states[1] = JSimplex.BASIC
    workspace.basis.states[4] = JSimplex.AT_LOWER
    JSimplex.recompute!(workspace; refactorize=true)
    workspace.refactorizations = 0
    return workspace
end

@testset "Legacy primal rejects an unsafe sole pivot without mutating the basis" begin
    workspace = structural_bound_snap_workspace(0.01)
    before = copy(workspace.basis.basic_indices)
    terminal = JSimplex._primal_iteration!(workspace, () -> false, workspace.options.dual_tolerance)
    @test terminal.status == NUMERICAL_ERROR
    @test workspace.iterations == 0
    @test workspace.basis.basic_indices == before
    @test JSimplex.primal_infeasibility(workspace) == 0.0
end

@testset "Legacy primal accepts a tolerated bound snap that stays feasible" begin
    workspace = structural_bound_snap_workspace(1.0)
    terminal = JSimplex._primal_iteration!(workspace, () -> false, workspace.options.dual_tolerance)
    @test isnothing(terminal)
    @test workspace.iterations == 1
    @test workspace.primal[3] ≈ -7e-8
    @test JSimplex.primal_infeasibility(workspace) == 0.0
end
