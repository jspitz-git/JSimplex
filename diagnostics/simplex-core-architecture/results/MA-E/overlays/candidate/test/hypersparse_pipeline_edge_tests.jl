using LinearAlgebra

@testset "Pipeline observes dense reachability and sparse recovery" begin
    ws = pipeline_workspace()
    B = spdiagm(0=>ones(32),-1=>fill(-1.0,31))
    JSimplex.refactorize!(ws.factorization,B)
    cache = JSimplex._hypersparse_workspace!(ws)
    state = JSimplex._pipeline_state(cache,:ftran)
    state.mode = :sparse
    state.output_density = 0.0
    rhs = JSimplex._pipeline_unit_rhs!(ws,1)
    out = ws.scratch.row_solution
    for _ in 1:3
        JSimplex._pipeline_basis_solve!(out,ws,rhs)
        @test out == ones(32)
        @test state.output_density == 1.0
    end
    @test state.mode == :dense
    @test state.sparse_calls > 0 && state.dense_calls > 0
    # Sparse output observations allow a return without discarding old entries.
    rhs = JSimplex._pipeline_unit_rhs!(ws,32)
    for _ in 1:3
        JSimplex._pipeline_basis_solve!(out,ws,rhs)
        @test out == Float64[i==32 for i in 1:32]
    end
    @test JSimplex._pipeline_vector!(ws,out).indices == [32]
end

@testset "Mode probes measure one complete call and keep state independent" begin
    ws = pipeline_workspace()
    cache = JSimplex._hypersparse_workspace!(ws)
    cache.modes = ntuple(_->JSimplex.KernelModeState(),6)
    state = JSimplex._pipeline_state(cache,:ftran)
    ticks = Ref(UInt64(0))
    clock = ()->(ticks[] += UInt64(1000))
    rhs = JSimplex._pipeline_unit_rhs!(ws,1)
    for _ in 1:64
        JSimplex._pipeline_basis_solve!(ws.scratch.row_solution,ws,rhs;clock)
    end
    @test state.calls == 64
    @test state.probes == 2
    @test state.dense_calls+state.sparse_calls == 64
    @test state.dense_samples+state.sparse_samples == 64
    @test state.sparse_total_seconds+state.dense_total_seconds ≈ 64e-6
    @test JSimplex._pipeline_state(cache,:btran).calls == 0
    @test JSimplex._pipeline_state(cache,:bfrt).calls == 0
    @test JSimplex._pipeline_state(cache,:weight_ftran).calls == 0
end

@testset "Pipeline numerical failure preserves reusable support" begin
    for mode in (:sparse,:dense)
        ws = pipeline_workspace()
        JSimplex.refactorize!(ws.factorization,spdiagm(0=>fill(1e-200,32)))
        rhs = JSimplex._pipeline_unit_rhs!(ws,2)
        JSimplex._pipeline_add!(ws,rhs,2,1e200)
        @test_throws JSimplex._UnreliableBasisSolve JSimplex._pipeline_basis_solve!(
            ws.scratch.row_solution,ws,rhs;kernel_mode=mode)
        rhs = JSimplex._pipeline_unit_rhs!(ws,3)
        JSimplex._pipeline_basis_solve!(ws.scratch.row_solution,ws,rhs;kernel_mode=mode)
        @test isfinite(ws.scratch.row_solution[3])
        @test JSimplex._pipeline_vector!(ws,ws.scratch.row_solution).indices == [3]
        # A dense numerical producer can fail before the next kernel starts.
        rhs[4] = Inf
        JSimplex._pipeline_changed!(ws,rhs)
        @test_throws JSimplex._UnreliableBasisSolve JSimplex._pipeline_basis_solve!(
            ws.scratch.rho,ws,rhs;kernel_mode=mode)
    end
    ws = pipeline_workspace()
    rhs = JSimplex._pipeline_rhs_buffer!(ws)
    @test_throws JSimplex._UnreliableBasisSolve JSimplex._add_pipeline_rhs!(rhs,1,Inf)
    JSimplex._add_pipeline_rhs!(rhs,2,floatmax(Float64))
    @test_throws JSimplex._UnreliableBasisSolve JSimplex._add_pipeline_rhs!(rhs,2,floatmax(Float64))
end

@testset "Empty pipeline and dimension guards" begin
    ws = pipeline_workspace(;n=0)
    rhs = JSimplex._pipeline_rhs_values(JSimplex._pipeline_rhs_buffer!(ws))
    JSimplex._pipeline_basis_solve!(ws.scratch.rho,ws,rhs)
    JSimplex._pipeline_price!(ws.scratch.tableau_row,ws,ws.scratch.rho)
    @test isempty(ws.scratch.rho) && isempty(ws.scratch.tableau_row)
    @test JSimplex._pipeline_state(ws.scratch.hypersparse,:ftran).last_mode == :empty
    @test_throws DimensionMismatch JSimplex._pipeline_basis_solve!(ones(1),ws,rhs)
    @test_throws DimensionMismatch JSimplex._pipeline_price!(ones(1),ws,rhs)
    @test_throws ArgumentError JSimplex._pipeline_basis_solve!(rhs,ws,rhs;kernel_mode=:invalid)
end
