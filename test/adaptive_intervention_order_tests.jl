using JSimplex, Test, SparseArrays

function intervention_workspace(T, algorithm; pricing=true, rule=:steepest_edge)
    problem = algorithm == :primal ?
        LinearProblem(sparse(reshape(T[1],1,1)),T[-1];row_upper=T[0]) :
        LinearProblem(sparse(reshape(T[1],1,1)),T[0];row_lower=T[1])
    policy = JSimplex.NumericalPolicy(T;adaptive_stalling=true,
        adaptive_pricing=pricing,adaptive_primal_perturbation=true,
        adaptive_dual_perturbation=true,stagnation_window=2,refactor_timing=false)
    events = NamedTuple[]
    observer = (event,ws)->begin
        state = ws.scratch.pricing
        push!(events,(;event,iteration=ws.iterations,
            temporary=!isnothing(state) && state.temporary))
    end
    ws = JSimplex.initialize_workspace(problem,
        SolverOptions(T;algorithm,pricing=rule,verbose=false);
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy,
            diagnostics=JSimplex.SimplexDiagnostics(;observer)))
    JSimplex._prepare_auto_pricing!(ws,algorithm)
    return ws,events
end

# Drive the same completed-observation order as both optimization loops. The
# fixed point deliberately stays stalled so trial expiry and shifting are visible.
function intervention_observation!(ws, algorithm; stop=()->false)
    ws.iterations += 1
    JSimplex._observe_stagnation!(ws,algorithm,zero(eltype(ws.costs)),zero(eltype(ws.costs)))
    JSimplex._observe_auto_pricing!(ws,algorithm)
    return algorithm == :primal ? JSimplex._maybe_perturb_primal_bounds!(ws,stop) :
        JSimplex._maybe_perturb_dual_costs!(ws,stop)
end

@testset "Pricing trials defer new shifts without consuming perturbation levels" begin
    for T in (Float32,Float64,BigFloat), algorithm in (:primal,:dual)
        ws,events = intervention_workspace(T,algorithm)
        original = (copy(ws.costs),copy(ws.lower),copy(ws.upper))
        for _ in 1:11
            @test intervention_observation!(ws,algorithm) == 0
            @test isnothing(ws.scratch.perturbations)
        end
        @test ws.scratch.pricing.temporary
        @test isequal(original,(ws.costs,ws.lower,ws.upper))
        @test intervention_observation!(ws,algorithm) > 0
        @test !ws.scratch.pricing.temporary
        @test JSimplex._effective_pricing(ws,algorithm) == :steepest_edge
        journal = ws.scratch.perturbations
        @test algorithm == :primal ? journal.bounds.level == 1 : journal.level == 1
        @test !ws.scratch.stagnation.monitor.initialized
        @test [(x.event,x.iteration) for x in events if x.event in
            (:pricing_dantzig,:pricing_trial_expired,:perturbation)] ==
            [(:pricing_dantzig,4),(:pricing_trial_expired,12),(:perturbation,12)]
        # The unchanged perturbation can stay active during a later trial.
        # No new shift is introduced during its two-window assessment interval.
        for _ in 1:4
            @test intervention_observation!(ws,algorithm) == 0
        end
        @test ws.scratch.pricing.temporary
        @test algorithm == :primal ? journal.bounds.level == 1 : journal.level == 1
        @test all(!x.temporary for x in events if x.event == :perturbation)
    end
end

@testset "Perturbation-only and explicit Dantzig need no pricing trial" begin
    for algorithm in (:primal,:dual), (pricing,rule) in ((false,:steepest_edge),(true,:dantzig))
        ws,events = intervention_workspace(Float64,algorithm;pricing,rule)
        for _ in 1:3
            @test intervention_observation!(ws,algorithm) == 0
        end
        @test intervention_observation!(ws,algorithm) > 0
        @test !any(x.event == :pricing_dantzig for x in events)
        @test count(x.event == :perturbation for x in events) == 1
    end
end

@testset "A productive pricing trial ends without starting perturbation" begin
    for algorithm in (:primal,:dual)
        ws,events = intervention_workspace(Float64,algorithm)
        for _ in 1:4
            intervention_observation!(ws,algorithm)
        end
        for i in 1:4
            if algorithm == :primal
                ws.primal[1] = Float64(i)
            else
                ws.primal[2] = i/8
            end
            @test intervention_observation!(ws,algorithm) == 0
        end
        @test !ws.scratch.pricing.temporary
        @test isnothing(ws.scratch.perturbations)
        @test any(x.event == :pricing_progress_return for x in events)
    end
end

@testset "Cancellation between trial expiry and a shift leaves the LP untouched" begin
    for algorithm in (:primal,:dual)
        ws,events = intervention_workspace(Float64,algorithm)
        original = (copy(ws.costs),copy(ws.lower),copy(ws.upper))
        for _ in 1:11
            intervention_observation!(ws,algorithm)
        end
        @test intervention_observation!(ws,algorithm;stop=()->true) == -1
        @test isequal(original,(ws.costs,ws.lower,ws.upper))
        @test isnothing(ws.scratch.perturbations)
        @test !any(x.event == :perturbation for x in events)
    end
end
