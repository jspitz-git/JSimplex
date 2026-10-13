using JSimplex, Test, SparseArrays

function metric_workspace(T, algorithm)
    problem = LinearProblem(sparse(reshape(T[1],1,1)),T[-1];row_upper=T[0])
    policy = JSimplex.NumericalPolicy(T;adaptive_stalling=true,
        adaptive_pricing=true,stagnation_window=4,refactor_timing=false)
    ws = JSimplex.initialize_workspace(problem,
        SolverOptions(T;algorithm,pricing=:steepest_edge,verbose=false);
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
    return ws
end

@testset "Secondary price improvements cannot hide a primal objective plateau" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        ws = metric_workspace(T,:primal)
        JSimplex._prepare_auto_pricing!(ws,:primal)
        for i in 1:12
            ws.iterations = i
            ws.reduced_costs[1] = T(-32+i)
            JSimplex._observe_stagnation!(ws,:primal,zero(T),one(T))
            JSimplex._observe_auto_pricing!(ws,:primal)
        end
        monitor = ws.scratch.stagnation.monitor
        @test monitor.objective_improvement == 0
        @test monitor.dual_improvement > 0
        @test monitor.state == :stalled
        @test JSimplex._effective_pricing(ws,:primal) == :dantzig
        # Actual objective improvement still counts, including an auxiliary
        # objective represented by the workspace's current cost vector.
        for i in 13:16
            ws.iterations = i
            ws.primal[1] = T(i-12)
            JSimplex._observe_stagnation!(ws,:primal,one(T),zero(T))
        end
        @test ws.scratch.stagnation.monitor.state == :progress
    end
end

@testset "Dual progress uses its objective and primal feasibility" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        ws = metric_workspace(T,:dual)
        ws.primal[2] = T(20)
        for i in 1:8
            ws.iterations = i
            ws.reduced_costs[1] = T(-32+i)
            JSimplex._observe_stagnation!(ws,:dual,zero(T),one(T))
        end
        @test ws.scratch.stagnation.monitor.state == :stalled
        # A zero-cost dual phase can make real progress by removing primal
        # violations; ignoring all feasibility metrics would lose this case.
        for i in 9:16
            ws.iterations = i
            ws.primal[2] = T(20-i)
            JSimplex._observe_stagnation!(ws,:dual,one(T),zero(T))
        end
        @test ws.scratch.stagnation.monitor.state == :progress
        @test ws.scratch.stagnation.monitor.primal_improvement > 0
    end
end
