@testset "Factor accounting includes lazy coefficient snapshots" begin
    for method in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws = pipeline_workspace(;basis_update=method)
        before = JSimplex._factor_storage_count(ws.factorization)
        rhs = JSimplex._pipeline_unit_rhs!(ws,1)
        JSimplex._pipeline_basis_solve!(ws.scratch.row_solution,ws,rhs;kernel_mode=:sparse)
        after = JSimplex._factor_storage_count(ws.factorization)
        @test after > before
        JSimplex._refresh_refactor_metrics!(ws;force=true)
        @test ws.scratch.refactorization.stored_elements == after
        @test JSimplex.refactor_reason(ws.scratch.refactorization,ws.progress.numerical_policy) == :none
        ws.scratch.refactorization.residual_bad = true
        @test JSimplex.refactor_reason(ws.scratch.refactorization,ws.progress.numerical_policy) == :residual
        JSimplex.refactorize!(ws.factorization,JSimplex.basis_matrix(ws))
        @test JSimplex._factor_storage_count(ws.factorization) == before
    end
end

@testset "Pipeline diagnostics include preparation, conversion, and rejected work" begin
    p = LinearProblem(spdiagm(0=>ones(32)),zeros(32);row_lower=zeros(32))
    diagnostics = JSimplex.SimplexDiagnostics(kernel_timing=true)
    policy = JSimplex.NumericalPolicy(Float64;hypersparse=true)
    ws = JSimplex.initialize_workspace(p,SolverOptions(verbose=false,basis_update=:forrest_tomlin);
        progress=JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=policy))
    rhs = JSimplex._pipeline_unit_rhs!(ws,1)
    for _ in 1:2
        JSimplex._pipeline_basis_solve!(ws.scratch.rho,ws,rhs;transposed=true,kernel_mode=:sparse)
        JSimplex._pipeline_price!(ws.scratch.tableau_row,ws,ws.scratch.rho;kernel_mode=:sparse)
    end
    @test get(diagnostics.kernel_calls,:hypersparse_setup,0) == 1
    @test get(diagnostics.kernel_calls,:hypersparse_base_graph,0) == 1
    @test get(diagnostics.kernel_calls,:hypersparse_upper_graph,0) == 1
    @test get(diagnostics.kernel_calls,:hypersparse_btran_sparse,0) == 2
    @test get(diagnostics.kernel_calls,:hypersparse_pricing_sparse,0) == 2
    @test get(diagnostics.kernel_nanoseconds,:hypersparse_btran_sparse,0) > 0
    rhs[4] = 3.0
    JSimplex._pipeline_changed!(ws,rhs)
    before = get(diagnostics.kernel_calls,:hypersparse_support,0)
    JSimplex._pipeline_basis_solve!(ws.scratch.row_solution,ws,rhs;kernel_mode=:sparse)
    @test get(diagnostics.kernel_calls,:hypersparse_support,0) == before+1
    candidate = JSimplex._candidate_workspace(ws)
    unit = JSimplex._pipeline_unit_rhs!(candidate,6)
    before = get(diagnostics.kernel_calls,:hypersparse_ftran_sparse,0)
    JSimplex._pipeline_basis_solve!(candidate.scratch.row_solution,candidate,unit;kernel_mode=:sparse)
    @test get(diagnostics.kernel_calls,:hypersparse_ftran_sparse,0) == before+1
    @test ws.scratch.row_solution[6] == 0
end
