@testset "Checked solves, pricing, and recomputation use the pipeline" begin
    ws = pipeline_workspace()
    cache = JSimplex._hypersparse_workspace!(ws)
    rhs = JSimplex._pipeline_unit_rhs!(ws,4)
    rho = JSimplex._checked_basis_solve!(ws.scratch.rho,ws,rhs;transposed=true)
    @test JSimplex._pipeline_state(cache,:btran).calls > 0
    JSimplex.price!(ws.scratch.tableau_row,ws,rho)
    @test JSimplex._pipeline_state(cache,:pricing).calls == 1
    @test ws.scratch.tableau_row[4] == -1
    @test ws.scratch.tableau_row[36] == 1
    # Recompute overwrites the same RHS twice, including entries absent before.
    ws.costs[32+7] = 3.0
    JSimplex.recompute!(ws)
    @test ws.scratch.rho[7] == -3
    @test JSimplex._pipeline_vector!(ws,ws.scratch.rho).indices == [7]
    @test JSimplex._pipeline_state(cache,:ftran).calls > 0
end

@testset "Weight RHS preserves sparse support without a dense reconstruction" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        ws = pipeline_workspace(T)
        rhs = JSimplex._pipeline_unit_rhs!(ws,3)
        JSimplex._pipeline_basis_solve!(ws.scratch.row_solution,ws,rhs;kernel_mode=:sparse)
        before = ws.scratch.hypersparse.support_rebuilds
        h = JSimplex._pipeline_weight_rhs!(ws,7,T(2))
        expected = zeros(T,32); expected[3] = expected[7] = T(-1//2)
        @test h == expected
        @test Set(JSimplex._pipeline_vector!(ws,h).indices) == Set([3,7])
        @test ws.scratch.hypersparse.support_rebuilds == before
    end
end

@testset "Accepted refinement invalidates pipeline support" begin
    ws = pipeline_workspace()
    rhs = JSimplex._pipeline_unit_rhs!(ws,4)
    out = ws.scratch.rho
    fill!(out,0.0)
    JSimplex._pipeline_changed!(ws,out)
    @test isempty(JSimplex._pipeline_vector!(ws,out).indices)
    quality = JSimplex.refine_basis_solve!(out,ws,rhs,
        ws.progress.numerical_policy,()->false;transposed=true)
    @test quality.reliable
    @test JSimplex._pipeline_vector!(ws,out).indices == [4]
    JSimplex._pipeline_price!(ws.scratch.tableau_row,ws,out;kernel_mode=:sparse)
    @test ws.scratch.tableau_row[4] == -1
    @test ws.scratch.tableau_row[36] == 1
end
