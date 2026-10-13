using Test, JSimplex, SparseArrays, LinearAlgebra

@testset "Small dual pivot certification retains the selected backend" begin
    for manager in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub, :huangfu_hall),
        mode in (:valid, :infeasible, :stop)
        # Native row scaling loses enough relative accuracy in the small Schur
        # complement to exhaust refinement. Unscaled Markowitz preserves it.
        B = [1.0e16 1.0e16; 1.0e16 1.0e16+2.0]
        pivot = 2.0^-20
        cost = mode == :infeasible ? pivot-1.0e-4 : pivot
        problem = LinearProblem(sparse(hcat(B, pivot*B[:,1])), [1.0, 0.0, cost];
            row_lower=zeros(2), row_upper=zeros(2))
        options = SolverOptions(algorithm=:dual, basis_update=manager,
            basis_refactorization=:markowitz, verbose=false)
        ws = JSimplex.initialize_workspace(problem, options)
        ws.basis = JSimplex.Basis([1,2], [JSimplex.BASIC, JSimplex.BASIC,
            JSimplex.AT_LOWER, JSimplex.AT_LOWER, JSimplex.AT_LOWER])
        JSimplex.recompute!(ws; refactorize=true)
        before = deepcopy((ws.primal, ws.costs, ws.basis.basic_indices, ws.basis.states))
        prices = copy(ws.reduced_costs)
        @test JSimplex._stabilize_small_dual_pivot!(ws, 3, pivot, pivot, 1.0,
            () -> mode == :stop) == (mode == :valid)
        @test before == (ws.primal, ws.costs, ws.basis.basic_indices, ws.basis.states)
        if mode == :valid
            @test abs(ws.reduced_costs[3]) <= options.dual_tolerance*pivot/8
        else
            @test ws.reduced_costs == prices
        end
    end
end

@testset "Private Markowitz refinement solves retain orientation and ownership" begin
    B = sparse([4.0 1.0; 2.0 3.0])
    factor = JSimplex._factorize_basis(B, Val(:markowitz))
    rhs = [1.0, 4.0]
    x = JSimplex._refinement_basis_solve(factor, rhs, false)
    y = JSimplex._refinement_basis_solve(factor, rhs, true)
    @test B*x ≈ rhs
    @test transpose(B)*y ≈ rhs
    @test x != y
    @test rhs == [1.0, 4.0]
    saved = copy(x)
    JSimplex._refinement_basis_solve(factor, [-3.0, 7.0], false)
    @test x == saved
end
