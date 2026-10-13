using JSimplex.SparseArrays

@testset "Legacy Harris selection tolerates each original row bound separately" begin
    for sign in (-1.0, 1.0), update in (:pfi, :bartels_golub)
        # Both row activities are individually feasible within 1e-7. Summing
        # their tolerated errors rejects the unit pivot and picks 1e-14.
        problem = LinearProblem(sparse(sign .* [-7e-8 -1e-14; -7e-8 -1.0]), [0.0, -1.0];
            row_lower=fill(sign > 0 ? 0.0 : -Inf, 2),
            row_upper=fill(sign > 0 ? Inf : 0.0, 2),
            column_lower=[1.0, 0.0], column_upper=[1.0, Inf])
        options = SolverOptions(algorithm=:primal, simplex_strategy=:legacy,
            basis_update=update, verbose=false)
        workspace = JSimplex.initialize_workspace(problem, options)
        @test JSimplex.primal_infeasibility(workspace) == 0.0
        terminal = JSimplex._primal_iteration!(workspace, () -> false, options.dual_tolerance)
        @test isnothing(terminal)
        @test workspace.iterations == 1
        @test workspace.basis.basic_indices[2] == 2
        @test workspace.refactorizations == 0
        @test JSimplex._original_primal_feasible(problem, workspace.primal[1:2], options.primal_tolerance)
    end
end
