using SparseArrays

@testset "Automatic pricing public round trip" begin
    options = SolverOptions(pricing=:auto, simplex_strategy=:adaptive, verbose=false)
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        converted = SolverOptions(T, options)
        @test converted.pricing == :auto
        @test converted.simplex_strategy == :adaptive
        @test JSimplex._remaining_options(converted; iterations=7).pricing == :auto
    end
    optimizer = JSimplex.Optimizer()
    JSimplex.MOI.set(optimizer, JSimplex.MOI.RawOptimizerAttribute("pricing"), :auto)
    @test JSimplex.MOI.get(optimizer, JSimplex.MOI.RawOptimizerAttribute("pricing")) == :auto
    @test JSimplex._solver_options(optimizer).pricing == :auto
    JSimplex.MOI.empty!(optimizer)
    @test JSimplex.MOI.get(optimizer, JSimplex.MOI.RawOptimizerAttribute("pricing")) == :auto
end

function automatic_pricing_workspace(::Type{T}; algorithm=:primal, pricing=:auto,observer=nothing) where T
    problem = LinearProblem(sparse(T[1 2; 2 1]), T[-3,-2]; row_upper=T[4,4])
    options = SolverOptions(T; algorithm, pricing, simplex_strategy=:adaptive, verbose=false)
    policy = JSimplex.NumericalPolicy(T; simplex_strategy=:adaptive, stagnation_window=2,
                                    refactor_timing=false)
    diagnostics = JSimplex.SimplexDiagnostics(;kernel_timing=true,observer)
    progress = JSimplex.SimplexProgressContext(problem; diagnostics, numerical_policy=policy)
    return JSimplex.initialize_workspace(problem,options;progress), diagnostics
end

@testset "Automatic weights recover before selection" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}), algorithm in (:primal,:dual)
        ws, diagnostics = automatic_pricing_workspace(T;algorithm)
        @test JSimplex._prepare_auto_pricing!(ws,algorithm)
        @test JSimplex._effective_pricing(ws,algorithm) == :steepest_edge
        ws.pricing_weights[2] = T <: AbstractFloat ? T(NaN) : zero(T)
        @test JSimplex._prepare_auto_pricing!(ws,algorithm)
        @test JSimplex._effective_pricing(ws,algorithm) == :devex
        @test all(isone,ws.pricing_weights)
        @test all(ws.devex_reference[j] == (ws.basis.states[j] == JSimplex.BASIC)
                  for j in eachindex(ws.devex_reference))
        @test JSimplex.event_count(diagnostics,:pricing_weight_rejected) == 1
        @test ws.scratch.pricing.framework_valid
    end
end

@testset "Selected weights reuse supplied basis solves" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        ws,diagnostics = automatic_pricing_workspace(T)
        JSimplex._prepare_auto_pricing!(ws,:primal)
        JSimplex._primal_entering(ws,ws.options.dual_tolerance)
        direction = zeros(T,2)
        JSimplex.forward_solve!(direction,ws.factorization,T[1,2])
        calls = copy(diagnostics.kernel_calls)
        @test JSimplex._validate_primal_edge!(ws,1,direction)
        ws.pricing_weights[1] *= 4
        @test !JSimplex._validate_primal_edge!(ws,1,direction)
        @test ws.scratch.pricing.active == :devex
        @test diagnostics.kernel_calls == calls
        @test ws.scratch.pricing.validated_weights == 2

        dual,diagnostics = automatic_pricing_workspace(T;algorithm=:dual)
        JSimplex._prepare_auto_pricing!(dual,:dual)
        row = dual.basis.basic_indices[1]
        rho = T[-1,0]
        @test JSimplex._validate_dual_edge!(dual,row,rho)
        dual.pricing_weights[row] = T(9)
        calls = copy(diagnostics.kernel_calls)
        @test !JSimplex._validate_dual_edge!(dual,row,rho)
        @test dual.scratch.pricing.active == :devex
        @test diagnostics.kernel_calls == calls
    end
end

@testset "Pricing state is owned across staged and cancelled work" begin
    ws,diagnostics = automatic_pricing_workspace(Float64)
    JSimplex._prepare_auto_pricing!(ws,:primal)
    trial = JSimplex._candidate_workspace(ws)
    @test trial.scratch.pricing !== ws.scratch.pricing
    trial.scratch.pricing.active = :dantzig
    @test ws.scratch.pricing.active == :steepest_edge
    JSimplex._copy_pivot_state!(ws,trial)
    @test ws.scratch.pricing.active == :dantzig
    @test trial.scratch.pricing !== ws.scratch.pricing
    JSimplex._reset_auto_pricing!(ws)
    JSimplex._prepare_auto_pricing!(ws,:primal)
    cancelled = Ref(false)
    result = JSimplex._transactional_simplex_step!(ws,()->cancelled[]) do candidate,stop
        candidate.scratch.pricing.active = :devex
        JSimplex._simplex_event!(candidate,:pricing_devex)
        cancelled[] = true
        nothing
    end
    @test result.status == TIME_LIMIT
    @test ws.scratch.pricing.active == :steepest_edge
    @test JSimplex.event_count(diagnostics,:pricing_devex) == 0
end

@testset "Edge quality respects stored weight units" begin
    for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt})
        policy = JSimplex.NumericalPolicy(T)
        @test JSimplex.validate_edge_weight(T(2), T(3), policy)
        @test !JSimplex.validate_edge_weight(T(4), T(9), policy)
        @test !JSimplex.validate_edge_weight(T(2), T(3), policy; square_root=true)
        @test JSimplex.validate_edge_weight(T(3), T(3), policy; square_root=true)
        for bad in (zero(T), -one(T))
            @test !JSimplex.validate_edge_weight(bad, one(T), policy)
            @test !JSimplex.validate_edge_weight(one(T), bad, policy)
        end
        if T <: AbstractFloat
            for bad in (T(NaN), T(Inf))
                @test !JSimplex.validate_edge_weight(bad, one(T), policy)
                @test !JSimplex.validate_edge_weight(one(T), bad, policy)
            end
            @test JSimplex.validate_edge_weight(floatmax(T), floatmax(T), policy; square_root=true)
            @test !JSimplex.validate_edge_weight(nextfloat(zero(T)), floatmax(T), policy)
        end
    end
end

function pricing_observations!(monitor, count)
    for _ in 1:count
        JSimplex.observe_progress!(monitor; objective=1, primal_violation=1,
            dual_violation=0, primal_step=0, dual_step=0)
    end
end

@testset "Pricing quality retains stored BigFloat precision" begin
    stored,actual,policy = setprecision(BigFloat,384) do
        (BigFloat(1),BigFloat(2)+eps(BigFloat(2)),JSimplex.NumericalPolicy(BigFloat))
    end
    setprecision(BigFloat,96) do
        @test !JSimplex.validate_edge_weight(stored,actual,policy)
        @test precision(BigFloat) == 96
    end
    @test precision(stored) == precision(actual) == 384
end

@testset "Automatic pricing requires cooldown and a valid framework" begin
    for T in (Float64, Rational{BigInt})
        policy = JSimplex.NumericalPolicy(T; simplex_strategy=:adaptive, stagnation_window=2)
        monitor = JSimplex.StagnationMonitor{T}(2)
        state = JSimplex.PricingState(T)
        @test state.active == :steepest_edge
        pricing_observations!(monitor, 4)
        @test JSimplex.next_pricing!(state, monitor, policy) == :dantzig
        @test !state.framework_valid
        @test state.cooldown_until == 8
        pricing_observations!(monitor, 2)
        @test JSimplex.next_pricing!(state, monitor, policy) == :dantzig
        pricing_observations!(monitor, 2)
        @test JSimplex.next_pricing!(state, monitor, policy) == :dantzig
        # The caller has now built a new reference at the current basis.
        state.framework_valid = true
        @test JSimplex.next_pricing!(state, monitor, policy) == :devex
        @test state.switches == 2
        @test JSimplex.next_pricing!(state, monitor, policy) == :devex
        state.weight_quality = :unreliable
        @test JSimplex.next_pricing!(state, monitor, policy) == :devex
        @test state.needs_reset
        @test !state.framework_valid
        @test state.cooldown_until >= state.observations + 4

        disabled = JSimplex.NumericalPolicy(T; simplex_strategy=:adaptive,
            adaptive_pricing=false, stagnation_window=2)
        ablation = JSimplex.PricingState(T)
        @test JSimplex.next_pricing!(ablation, monitor, disabled) == :steepest_edge
        ablation.weight_quality = :unreliable
        @test JSimplex.next_pricing!(ablation, monitor, disabled) == :devex
        @test ablation.needs_reset
    end
end
