@testset "Workspace pools retain owned indices and invalidate changed costs" begin
    ws,policy,_ = partial_pricing_workspace(Float64)
    ws.costs[1] = ws.reduced_costs[1] = -1.0
    pool = JSimplex._pricing_pool!(ws,:primal)
    @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 1
    candidate = JSimplex._candidate_workspace(ws)
    copy_pool = candidate.scratch.pricing_pool
    @test copy_pool !== pool
    @test copy_pool.indices !== pool.indices
    @test copy_pool.indices == pool.indices
    copy_pool.scan_position = 129
    empty!(copy_pool.indices)
    @test pool.scan_position == 65
    @test pool.indices == [1]
    generation = pool.cost_generation
    ws.costs[1] = 0.0
    ws.costs[129] = -1.0
    JSimplex.recompute!(ws)
    @test !pool.valid
    @test pool.cost_generation > generation
    @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 129
    generation = pool.basis_generation
    JSimplex._invalidate_pricing_pool!(ws;basis=true,costs=false)
    @test pool.basis_generation > generation
    @test !pool.valid
    JSimplex._restore_original_costs!(ws)
    @test !pool.valid
    JSimplex.recompute!(ws)
    @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 0
    @test pool.full_scan
end

@testset "Both solver selection paths use partial pricing only when enabled" begin
    for enabled in (false,true), algorithm in (:primal,:dual)
        ws,policy,diagnostics = partial_pricing_workspace(Float64;algorithm,enabled)
        if algorithm == :primal
            ws.reduced_costs[1] = -1.0
            ws.reduced_costs[129] = -10.0
            chosen,_ = JSimplex._primal_entering(ws,ws.options.dual_tolerance)
        else
            ws.primal[ws.basis.basic_indices[1]] = -2.0
            ws.primal[ws.basis.basic_indices[129]] = -11.0
            chosen = JSimplex.dual_edge_selection(ws)
        end
        @test chosen == (enabled ? 1 : 129)
        @test isnothing(ws.scratch.pricing_pool) == !enabled
        if enabled
            @test ws.scratch.pricing_pool.scanned_entries == 64
            @test JSimplex.event_count(diagnostics,:pricing_block_scan) == 1
            @test JSimplex.event_count(diagnostics,:pricing_full_scan) == 0
        end
    end
end

@testset "Last-block candidates and full current terminal scans reach the loops" begin
    for T in (Float64,Rational{BigInt})
        ws,policy,_ = partial_pricing_workspace(T)
        ws.costs[129] = ws.reduced_costs[129] = -one(T)
        result = JSimplex._primal_optimize!(ws,()->false,ws.options.dual_tolerance)
        @test result.status == OPTIMAL
        @test ws.primal[129] == one(T)
        @test ws.iterations == 1
        @test ws.scratch.pricing_pool.full_scan

        ws,policy,diagnostics = partial_pricing_workspace(T;algorithm=:dual)
        ws.lower[ws.basis.basic_indices[1]] = Bound(one(T))
        result = JSimplex.dual_iteration!(ws,()->false)
        @test result.status == INFEASIBLE
        @test ws.iterations == 0
        @test ws.scratch.pricing_pool.full_scan
        @test JSimplex.event_count(diagnostics,:pricing_full_scan) > 0
    end
end

@testset "Dual working-cost shifts invalidate cached candidates" begin
    ws,policy,_ = partial_pricing_workspace(Float64)
    pool = JSimplex._pricing_pool!(ws,:primal)
    ws.reduced_costs[2] = -1.0
    @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 2
    generation = pool.cost_generation
    JSimplex.update_duals!(ws,zeros(length(ws.costs)),130,1,0.0)
    @test ws.costs[2] == 1.0
    @test !pool.valid
    @test pool.cost_generation > generation
end

@testset "Wide bound flips save pricing scans without changing the optimum" begin
    for enabled in (false,true)
        ws,policy,diagnostics = partial_pricing_workspace(Float64;enabled)
        ws.costs[1:129] .= -1.0
        JSimplex.recompute!(ws)
        result = JSimplex._primal_optimize!(ws,()->false,ws.options.dual_tolerance)
        @test result.status == OPTIMAL
        @test ws.iterations == 129
        @test ws.primal[1:129] == ones(129)
        @test JSimplex.event_count(diagnostics,:pricing_full_scan) > 0
        if enabled
            @test JSimplex.event_count(diagnostics,:pricing_pool_hit) > 100
            @test JSimplex.event_count(diagnostics,:pricing_scanned_entries) < 2000
        else
            @test JSimplex.event_count(diagnostics,:pricing_scanned_entries) >= 129*130
        end
    end
end
