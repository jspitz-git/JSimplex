using Test, JSimplex, SparseArrays

function cost_history_workspace(T; pricing=true)
    problem = LinearProblem(sparse(reshape(T[1],1,1)),T[1];
        row_lower=T[10],column_lower=T[1])
    policy = JSimplex.NumericalPolicy(T;adaptive_stalling=true,
        adaptive_pricing=pricing,stagnation_window=4,refactor_timing=false)
    ws = JSimplex.initialize_workspace(problem,
        SolverOptions(T;algorithm=:dual,basis_refactorization=:native,verbose=false);
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
    JSimplex._prepare_auto_pricing!(ws,:dual)
    return ws
end

function repair_cost_and_observe!(ws,i)
    T = eltype(ws.costs)
    # Exercise the core's real nonbasic-price repair at an unchanged point.
    ws.reduced_costs[1] = -one(T)
    JSimplex.update_duals!(ws,zeros(T,2),2,2,zero(T))
    ws.iterations = i
    JSimplex._observe_stagnation!(ws,:dual,zero(T),zero(T))
    JSimplex._observe_auto_pricing!(ws,:dual)
end

@testset "Cost repairs cannot repeatedly erase dual feasibility stagnation" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        ws = cost_history_workspace(T)
        point = copy(ws.primal)
        for i in 1:8
            repair_cost_and_observe!(ws,i)
        end
        @test ws.costs[1] == T(9)
        @test ws.primal == point
        @test ws.scratch.stagnation.monitor.observations == 8
        @test ws.scratch.stagnation.monitor.state == :stalled
        @test ws.scratch.stagnation.monitor.objective_improvement == 0
        @test JSimplex._effective_pricing(ws,:dual) == :dantzig
        # A failed pricing trial still expires when each pivot repairs a cost.
        for i in 9:24
            repair_cost_and_observe!(ws,i)
        end
        @test !ws.scratch.pricing.temporary
        @test ws.scratch.pricing.last_transition == :trial_limit
        @test JSimplex._effective_pricing(ws,:dual) == :steepest_edge
    end
end

@testset "Cost repair preserves genuine feasibility gains and the phase reset" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        ws = cost_history_workspace(T)
        for i in 1:8
            ws.primal[2] = T(i)
            repair_cost_and_observe!(ws,i)
        end
        @test ws.scratch.stagnation.monitor.observations == 8
        @test ws.scratch.stagnation.monitor.state == :progress
        @test ws.scratch.stagnation.monitor.primal_improvement > 0
        @test !ws.scratch.pricing.temporary
        JSimplex._reset_auto_pricing!(ws)
        repair_cost_and_observe!(ws,9)
        @test ws.scratch.stagnation.monitor.observations == 1
        @test ws.scratch.stagnation.monitor.state == :progress
    end
end

@testset "Explicit adaptive cost perturbation still resets feasibility history" begin
    ws = cost_history_workspace(Float64;pricing=false)
    for i in 1:8
        repair_cost_and_observe!(ws,i)
    end
    m = ws.scratch.stagnation.monitor
    old_best = m.best_primal
    journal = JSimplex.PerturbationJournal(ws)
    policy = JSimplex.NumericalPolicy(Float64;adaptive_stalling=true,
        adaptive_dual_perturbation=true,stagnation_window=4,refactor_timing=false)
    @test JSimplex.perturb_dual_costs!(ws,m,journal,policy) > 0
    @test !m.initialized
    ws.primal[2] = -10.0
    ws.iterations = 9
    JSimplex._observe_stagnation!(ws,:dual,0.0,0.0)
    @test m.state == :progress
    @test m.window_count == 1
    @test m.best_primal > old_best
end

@testset "Local recovery after deterioration is not a new feasibility record" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        ws = cost_history_workspace(T;pricing=false)
        for i in 1:8
            repair_cost_and_observe!(ws,i)
        end
        best = ws.scratch.stagnation.monitor.best_primal
        # Violation first rises, then falls, but remains above its old record.
        for i in 9:16
            ws.primal[2] = T(i-30)
            repair_cost_and_observe!(ws,i)
            i % 4 == 0 && @test ws.scratch.stagnation.monitor.state == :stalled
        end
        @test ws.scratch.stagnation.monitor.best_primal == best
        @test ws.scratch.stagnation.monitor.primal_improvement < 0
    end
end
