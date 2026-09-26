using JSimplex.SparseArrays

@testset "Corrected dual repricing rejects overflow before changing the basis" begin
    huge = (floatmax(Float64) / 2) * (1 + 1e-12)
    problem = LinearProblem(sparse([0.5 1.0 -huge]), [0.0, 1.0, 1.0];
        row_lower=[1.0], row_upper=[1.0],
        column_lower=zeros(3), column_upper=[1.0, Inf, Inf])
    options = SolverOptions(algorithm=:dual, simplex_strategy=:legacy,
        pricing=:dantzig, verbose=false)
    workspace = JSimplex.initialize_workspace(problem, options)
    workspace.basis.basic_indices[1] = 1
    workspace.basis.states[1] = JSimplex.BASIC
    workspace.basis.states[4] = JSimplex.AT_LOWER
    JSimplex.recompute!(workspace; refactorize=true)
    workspace.factorization.base = JSimplex._factorize_basis(sparse(reshape([0.5 * (1 + 1e-10)], 1, 1)))
    JSimplex.replace_column!(workspace.factorization, [1.0], 1)
    JSimplex.recompute!(workspace)
    before = copy(workspace.basis.basic_indices)
    terminal = JSimplex.dual_iteration!(workspace, () -> false)
    @test terminal.status == NUMERICAL_ERROR
    @test workspace.iterations == 0
    @test workspace.basis.basic_indices == before
    @test all(isfinite, workspace.reduced_costs)
end

@testset "Legacy primal reconsiders stale rejections after a basis refresh" begin
    problem = LinearProblem(sparse([1.0 7e-8 -1.0 1e-14; 0.0 0.0 -1.0 0.0]),
        [0.0, 0.0, -2.0, -1.0]; row_lower=[0.0, 0.0], row_upper=[0.0, Inf],
        column_lower=[0.0, 1.0, 0.0, 0.0], column_upper=[Inf, 1.0, Inf, Inf])
    options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy,
        pricing=:dantzig, verbose=false)
    workspace = JSimplex.initialize_workspace(problem, options)
    workspace.basis.basic_indices[1] = 1
    workspace.basis.states[1] = JSimplex.BASIC
    workspace.basis.states[5] = JSimplex.AT_LOWER
    JSimplex.recompute!(workspace; refactorize=true)
    workspace.refactorizations = 0
    # Column3 looks unsafe with the stale factor. Column4 then triggers a
    # refresh, after which column3 has a safe unit pivot on the second row.
    workspace.factorization.base = JSimplex._factorize_basis(sparse([-128.0 0.0; -128.0 -1.0]))
    terminal = JSimplex._primal_iteration!(workspace, () -> false, options.dual_tolerance)
    @test isnothing(terminal)
    @test workspace.iterations == 1
    @test workspace.basis.basic_indices == [1, 3]
    @test workspace.refactorizations == 1
    @test isempty(workspace.scratch.rejected_entering)
    @test JSimplex._original_primal_feasible(problem, workspace.primal[1:4], options.primal_tolerance)
end
