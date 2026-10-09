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

@testset "Bound snapping and retention use per-bound feasibility" begin
    for T in (Float32, Float64), sign in (-1, 1), fixed_leaving in (false, true),
        update in (:pfi, :bartels_golub, :forrest_tomlin, :suhl_suhl)
        # Three structural basic variables lie just outside their bounds.
        # Exchanging the first one snaps its value and moves the entering
        # variable by 7e-8; every individual bound remains within tolerance.
        offset = T(sign) * T(7e-8)
        A = sparse(T[1 0 0 offset 1; 0 1 0 offset 0; 0 0 1 offset 0])
        lower = fill(T(sign > 0 ? 0 : -Inf), 5)
        upper = fill(T(sign > 0 ? Inf : 0), 5)
        lower[4] = upper[4] = one(T)
        # A fixed leaving variable must snap; a nonfixed one may retain its
        # tolerated value. Exercise both contracts on the same equations.
        fixed_leaving && (lower[1] = upper[1] = zero(T))
        problem = LinearProblem(A, T[0, 0, 0, 0, -sign];
            row_lower=zeros(T, 3), row_upper=zeros(T, 3),
            column_lower=lower, column_upper=upper)
        options = SolverOptions(T; algorithm=:primal, simplex_strategy=:legacy,
            basis_update=update, primal_tolerance=T(1e-7), verbose=false)
        workspace = JSimplex.initialize_workspace(problem, options)
        workspace.basis.basic_indices .= 1:3
        workspace.basis.states[1:3] .= JSimplex.BASIC
        workspace.basis.states[6:8] .= JSimplex.AT_LOWER
        JSimplex.recompute!(workspace; refactorize=true)
        @test JSimplex.primal_infeasibility(workspace) == zero(T)
        before = copy(workspace.primal)
        terminal = JSimplex._primal_iteration!(workspace, () -> false,
            options.dual_tolerance)
        @test isnothing(terminal)
        @test workspace.basis.basic_indices == [5, 2, 3]
        if fixed_leaving
            @test workspace.primal[1] == zero(T)
            @test workspace.primal[5] ≈ -offset
        else
            @test workspace.primal == before
        end
        @test JSimplex._original_primal_feasible(problem, workspace.primal[1:5],
            options.primal_tolerance)
        @test JSimplex.primal_infeasibility(workspace) == zero(T)
        @test maximum(abs, A * workspace.primal[1:5]) <= eps(T)
    end
end

function structural_bound_snap_workspace(coefficient; fixed_leaving=true)
    problem = LinearProblem(sparse([1.0 7e-8 coefficient]), [0.0, 0.0, -1.0];
        row_lower=[0.0], row_upper=[0.0], column_lower=[0.0, 1.0, 0.0],
        column_upper=[fixed_leaving ? 0.0 : Inf, 1.0, Inf])
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
    primal_before = copy(workspace.primal)
    terminal = JSimplex._primal_iteration!(workspace, () -> false, workspace.options.dual_tolerance)
    @test terminal.status == NUMERICAL_ERROR
    @test workspace.iterations == 0
    @test workspace.basis.basic_indices == before
    @test workspace.primal == primal_before
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

@testset "Nonfixed structural zero steps preserve a certified point" begin
    for coefficient in (0.01, 1.0)
        workspace = structural_bound_snap_workspace(coefficient; fixed_leaving=false)
        before = copy(workspace.primal)
        terminal = JSimplex._primal_iteration!(workspace, () -> false,
            workspace.options.dual_tolerance)
        @test isnothing(terminal)
        @test workspace.iterations == 1
        @test workspace.basis.basic_indices == [3]
        @test workspace.primal == before
        @test workspace.problem.A * workspace.primal[1:3] == workspace.primal[4:end]
        @test JSimplex._original_primal_feasible(workspace.problem,
            workspace.primal[1:3], workspace.options.primal_tolerance)
    end
end
