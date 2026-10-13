using JSimplex.SparseArrays
using JSimplex.LinearAlgebra

@testset "Legacy primal rejects a spurious nonsingular-looking pivot" begin
    for update in (:pfi, :bartels_golub), pricing in (:dantzig, :steepest_edge)
        problem = LinearProblem(sparse(reshape([0.0, 1.0], 2, 1)), [-1.0];
            row_upper=[0.0, 1.0])
        options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy,
            basis_update=update, pricing=pricing, refactorization_interval=80, verbose=false)
        workspace = JSimplex.initialize_workspace(problem, options)
        workspace.factorization.base = JSimplex._factorize_basis(sparse([-1.0 1.0; 0.0 -1.0]))
        JSimplex.replace_column!(workspace.factorization, [1.0, 0.0], 1)
        # The stale forward solve offers a unit pivot in row 1, where the
        # actual entering column is zero. Its forward residual looks harmless
        # in ill-conditioned examples; the transpose row must also be valid.
        terminal = JSimplex._primal_iteration!(workspace, () -> false, options.dual_tolerance)
        @test isnothing(terminal)
        @test workspace.basis.basic_indices == [2, 1]
        @test workspace.primal[1] ≈ 1.0
        @test workspace.refactorizations == 1
        @test JSimplex._original_primal_feasible(problem, workspace.primal[1:1], options.primal_tolerance)
        @test_nowarn JSimplex.recompute!(workspace; refactorize=true)
    end
end

@testset "Legacy primal corrects a row without unnecessary refactorization" begin
    problem = LinearProblem(sparse(reshape([1.0, 0.0], 2, 1)), [-1.0]; row_upper=[1.0, 1.0])
    options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy,
        basis_update=:bartels_golub, pricing=:steepest_edge,
        refactorization_interval=80, verbose=false)
    diagnostics = JSimplex.SimplexDiagnostics()
    progress = JSimplex.SimplexProgressContext(problem; diagnostics)
    workspace = JSimplex.initialize_workspace(problem, options; progress)
    workspace.factorization.base = JSimplex._factorize_basis(sparse([-1.0 1e-5; 0.0 -1.0]))
    JSimplex.replace_column!(workspace.factorization, [1.0, 0.0], 1)
    @test isnothing(JSimplex._primal_iteration!(workspace, () -> false, options.dual_tolerance))
    @test workspace.primal[1] ≈ 1.0
    @test workspace.refactorizations == 0
    @test JSimplex.event_count(diagnostics, :correction) == 1
end
