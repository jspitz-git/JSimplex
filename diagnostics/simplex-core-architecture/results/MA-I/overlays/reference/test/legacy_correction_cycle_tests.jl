using JSimplex.SparseArrays
using JSimplex.LinearAlgebra

@testset "A corrected legacy cycle does not justify a longer update chain" begin
    rows = 8
    problem = LinearProblem(sparse(Matrix{Float64}(I, rows, rows)), collect(1.0:rows);
        row_lower=ones(rows))
    options = SolverOptions(basis_update=:bartels_golub,
        refactorization_interval=2, verbose=false)
    diagnostics = JSimplex.SimplexDiagnostics()
    progress = JSimplex.SimplexProgressContext(problem; diagnostics)
    workspace = JSimplex.initialize_workspace(problem, options; progress)
    stale = -Matrix{Float64}(I, rows, rows)
    stale[1, 2] = 1e-5
    workspace.factorization.base = JSimplex._factorize_basis(sparse(stale))
    JSimplex.replace_column!(workspace.factorization, [1.0; zeros(rows - 1)], 1)
    workspace.dual_nonzero_steps_since_refactorization = 1
    workspace.dual_stable_refactorizations = 2
    JSimplex.recompute!(workspace)
    @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    @test JSimplex.event_count(diagnostics, :correction) >= 1
    @test workspace.refactorizations == 1
    @test workspace.dual_refactorization_interval == 2
    # Clean cycles do not grow beyond the configured legacy ceiling.
    for _ in 2:7
        @test isnothing(JSimplex.dual_iteration!(workspace, () -> false))
    end
    @test workspace.dual_refactorization_interval == 2
end

@testset "Native correction also protects adaptive refactorization" begin
    problem = LinearProblem(sparse([1.0 0.0; 0.0 1.0]), [1.0, 10.0]; row_lower=[1.0, -Inf])
    options = SolverOptions(verbose=false)
    policy = JSimplex.NumericalPolicy(Float64; adaptive_refactor=true)
    progress = JSimplex.SimplexProgressContext(problem; numerical_policy=policy)
    workspace = JSimplex.initialize_workspace(problem, options; progress)
    workspace.factorization.base = JSimplex._factorize_basis(sparse([-1.0 0.0; 1e-5 -1.0]))
    direction = JSimplex.forward_solve(workspace.factorization, [1.0, 0.0])
    before = copy(direction)
    workspace.scratch.tableau_row[1] = -1.0
    @test JSimplex._try_native_dual_correction!(workspace, direction, 1, 1, () -> false)
    @test direction != before
    @test direction ≈ [-1.0, 0.0]
    @test workspace.scratch.refactorization.residual_bad
end
