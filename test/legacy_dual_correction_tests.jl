using JSimplex.SparseArrays

@testset "Legacy dual corrects mild updated solve errors before refactorization" begin
    for T in (Float32, Float64),
        update in (:pfi, :bartels_golub, :forrest_tomlin, :suhl_suhl),
        transposed in (true, false)
        T === Float32 && update != :pfi && continue
        problem = LinearProblem(sparse(T[1 0; 0 1]), T[1, 10];
            row_lower=T[1, -Inf])
        options = SolverOptions(T; algorithm=:dual, simplex_strategy=:legacy,
            basis_update=update, refactorization_interval=80, verbose=false)
        workspace = JSimplex.initialize_workspace(problem, options)
        # Simulate roundoff in an updated factor with a small triangular error.
        # The actual basis remains -I; the exact row and column are [-1, 0].
        delta = T === Float32 ? T(1e-3) : T(1e-5)
        stale = transposed ? T[-1 delta; 0 -1] : T[-1 0; delta -1]
        workspace.factorization.base = JSimplex._factorize_basis(sparse(stale))
        JSimplex.replace_column!(workspace.factorization, T[1, 0], 1)
        JSimplex.recompute!(workspace)
        terminal = JSimplex.dual_iteration!(workspace, () -> false)
        @test isnothing(terminal)
        @test workspace.iterations == 1
        @test workspace.basis.basic_indices == [1, 4]
        @test workspace.primal[1] ≈ 1.0
        @test abs(workspace.primal[4]) <= options.primal_tolerance
        @test workspace.refactorizations == 0
        @test workspace.dual_refactorization_interval == 80
        @test eltype(workspace.scratch.pivot_quality_cache.rhs) === T
    end
end

@testset "Native direction correction preserves a candidate when its pivot disagrees" begin
    problem = LinearProblem(sparse([1.0 0.0; 0.0 1.0]), [1.0, 10.0]; row_lower=[1.0, -Inf])
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
    workspace.factorization.base = JSimplex._factorize_basis(sparse([-1.0 0.0; 1e-5 -1.0]))
    direction = JSimplex.forward_solve(workspace.factorization, [1.0, 0.0])
    before = copy(direction)
    # A corrected FTRAN pivot of -1 cannot validate a ratio decision made
    # from a tableau coefficient of +1, even with an exact direction residual.
    workspace.scratch.tableau_row[1] = 1.0
    @test !JSimplex._try_native_dual_correction!(workspace, direction, 1, 1, () -> false)
    @test direction == before
end
