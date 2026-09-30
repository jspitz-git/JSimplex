using SparseArrays, LinearAlgebra

function isolated_pricing_policy(::Type{T}=Float64; enabled=true, window=2) where T
    # All unrelated adaptive mechanisms remain disabled.
    return JSimplex.NumericalPolicy(T; adaptive_stalling=true, adaptive_pricing=enabled,
        stagnation_window=window, refactor_timing=false)
end

function pricing_window!(state, monitor, policy; objective=1)
    for _ in 1:monitor.window
        JSimplex.observe_progress!(monitor; objective, primal_violation=1,
            dual_violation=0, primal_step=0, dual_step=0)
        JSimplex.next_pricing!(state, monitor, policy)
    end
    return state.active
end

@testset "Temporary pricing returns to its prior rule after sustained progress" begin
    for T in (Float64, Rational{BigInt}), original in (:steepest_edge, :devex)
        policy = isolated_pricing_policy(T)
        state = JSimplex.PricingState(T)
        state.active = original
        monitor = JSimplex.StagnationMonitor{T}(2)
        pricing_window!(state, monitor, policy)
        @test pricing_window!(state, monitor, policy) == :dantzig
        # The weighted framework is maintained while selection uses Dantzig.
        @test state.framework_valid
        @test pricing_window!(state, monitor, policy; objective=T(3)/4) == :dantzig
        @test JSimplex.next_pricing!(state, monitor, policy) == :dantzig
        @test pricing_window!(state, monitor, policy; objective=T(1)/2) == original
        @test pricing_window!(state, monitor, policy; objective=T(1)/2) == original
    end
end

@testset "Unproductive pricing trials are bounded and cannot immediately repeat" begin
    policy = isolated_pricing_policy()
    state = JSimplex.PricingState(Float64)
    monitor = JSimplex.StagnationMonitor{Float64}(2)
    pricing_window!(state, monitor, policy)
    @test pricing_window!(state, monitor, policy) == :dantzig
    for _ in 1:3
        @test pricing_window!(state, monitor, policy) == :dantzig
    end
    @test pricing_window!(state, monitor, policy) == :steepest_edge
    @test pricing_window!(state, monitor, policy) == :steepest_edge
    @test pricing_window!(state, monitor, policy) == :dantzig
end

@testset "Disabled adaptive pricing observes without starting a trial" begin
    policy = isolated_pricing_policy(;enabled=false)
    state = JSimplex.PricingState(Float64)
    monitor = JSimplex.StagnationMonitor{Float64}(2)
    for _ in 1:8
        @test pricing_window!(state, monitor, policy) == :steepest_edge
    end
    @test monitor.state == :stalled
    state.weight_quality = :unreliable
    @test JSimplex.next_pricing!(state, monitor, policy) == :devex
    @test state.needs_reset
end

@testset "Temporary Dantzig maintains dual weights for the current basis" begin
    problem = LinearProblem(sparse([2.0 0.0; 0.0 3.0]), zeros(2); row_lower=ones(2))
    policy = isolated_pricing_policy()
    options = SolverOptions(algorithm=:dual, pricing=:auto, verbose=false)
    ws = JSimplex.initialize_workspace(problem, options;
        progress=JSimplex.SimplexProgressContext(problem; numerical_policy=policy))
    @test JSimplex._prepare_auto_pricing!(ws,:dual)
    monitor = JSimplex.StagnationMonitor{Float64}(2)
    ws.scratch.stagnation = JSimplex.WorkspaceStagnation(monitor,UInt(0),UInt(0),0,1.0,1.0)
    for _ in 1:4
        JSimplex.observe_progress!(monitor; objective=0.0, primal_violation=1.0,
            dual_violation=0.0, primal_step=0.0, dual_step=0.0)
        JSimplex._observe_auto_pricing!(ws,:dual)
    end
    @test JSimplex._effective_pricing(ws,:dual) == :dantzig
    @test isnothing(JSimplex.dual_iteration!(ws,()->false))
    @test ws.iterations == 1
    @test JSimplex._effective_pricing(ws,:dual) == :dantzig
    for row in 1:2
        rhs = zeros(2); rhs[row] = 1.0
        actual = zeros(2)
        JSimplex.transpose_solve!(actual,ws.factorization,rhs)
        @test ws.pricing_weights[ws.basis.basic_indices[row]] ≈ dot(actual,actual)
    end
    # A phase reset must preserve those current weights while ending the trial.
    JSimplex._reset_auto_pricing!(ws)
    @test JSimplex._prepare_auto_pricing!(ws,:dual)
    @test JSimplex._effective_pricing(ws,:dual) == :steepest_edge
    for row in 1:2
        rhs = zeros(2); rhs[row] = 1.0
        actual = zeros(2)
        JSimplex.transpose_solve!(actual,ws.factorization,rhs)
        @test ws.pricing_weights[ws.basis.basic_indices[row]] ≈ dot(actual,actual)
    end
end

@testset "Trial budgets survive monitor changes and policy changes" begin
    for interruption in (:monitor,:disabled,:numerical)
        policy = isolated_pricing_policy()
        state = JSimplex.PricingState(Float64)
        monitor = JSimplex.StagnationMonitor{Float64}(2)
        pricing_window!(state,monitor,policy)
        pricing_window!(state,monitor,policy)
        deadline = state.trial_until
        if interruption == :monitor
            for _ in 1:4
                monitor = JSimplex.StagnationMonitor{Float64}(2)
                pricing_window!(state,monitor,policy)
                @test state.trial_until == deadline
            end
            @test state.active == :steepest_edge
            @test state.last_transition == :trial_limit
        elseif interruption == :disabled
            @test JSimplex.next_pricing!(state,monitor,isolated_pricing_policy(enabled=false)) == :steepest_edge
            @test !state.temporary
            @test state.last_transition == :disabled
        else
            state.weight_quality = :unreliable
            @test JSimplex.next_pricing!(state,monitor,policy) == :devex
            @test !state.temporary
            @test state.needs_reset
        end
    end
end

function force_pricing_trial!(ws,algorithm)
    JSimplex._prepare_auto_pricing!(ws,algorithm)
    state = ws.scratch.pricing
    state.return_mode = state.active
    state.active = :dantzig
    state.temporary = true
    state.trial_until = 8
    return state
end

function check_basis_weights(ws,algorithm)
    m,n = size(ws.problem.A)
    checked = 0
    if algorithm == :dual
        for row in 1:m
            rhs = zeros(m); rhs[row] = 1.0
            actual = zeros(m)
            JSimplex.transpose_solve!(actual,ws.factorization,rhs)
            @test ws.pricing_weights[ws.basis.basic_indices[row]] ≈ dot(actual,actual)
            checked += 1
        end
    else
        for j in eachindex(ws.pricing_weights)
            ws.basis.states[j] == JSimplex.BASIC && continue
            ws.scratch.steepest_valid[j] || continue
            rhs = j <= n ? Vector(ws.problem.A[:,j]) : -Float64.(1:m .== j-n)
            actual = zeros(m)
            JSimplex.forward_solve!(actual,ws.factorization,rhs)
            @test ws.pricing_weights[j] ≈ sqrt(1+dot(actual,actual))
            checked += 1
        end
    end
    @test checked > 0
end

@testset "Real trial pivots preserve weights through refactorization and recovery" begin
    for algorithm in (:primal,:dual), pricing in (:auto,:steepest_edge,:devex),
        update in (:pfi,:forrest_tomlin)
        p = algorithm == :primal ?
            LinearProblem(sparse([0.5 1.0; 0.0 3.0]),[-3.0,-1.0];row_upper=ones(2)) :
            LinearProblem(sparse([2.0 0.0; 0.0 3.0]),zeros(2);row_lower=ones(2))
        policy = isolated_pricing_policy()
        o = SolverOptions(;algorithm,pricing,basis_update=update,verbose=false)
        ws = JSimplex.initialize_workspace(p,o;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        algorithm == :primal && JSimplex._primal_entering(ws,o.dual_tolerance)
        state = force_pricing_trial!(ws,algorithm)
        candidate = JSimplex._candidate_workspace(ws)
        @test candidate.scratch.pricing !== state
        @test candidate.scratch.pricing.return_mode == state.return_mode
        @test candidate.scratch.pricing.temporary
        result = algorithm == :primal ? JSimplex._primal_iteration!(ws,()->false,o.dual_tolerance) :
            JSimplex.dual_iteration!(ws,()->false)
        @test isnothing(result)
        @test JSimplex._effective_pricing(ws,algorithm) == :dantzig
        if pricing != :devex
            check_basis_weights(ws,algorithm)
            weights = copy(ws.pricing_weights)
            JSimplex.recompute!(ws;refactorize=true)
            @test ws.pricing_weights == weights
            check_basis_weights(ws,algorithm)
        else
            # Devex is a reference approximation, not a DSE inverse-row norm.
            @test all(isfinite,ws.pricing_weights)
            @test all(>=(1.0),ws.pricing_weights)
        end
        checkpoint = JSimplex.checkpoint_basis(ws)
        @test JSimplex.restore_checkpoint!(ws,checkpoint,()->false)
        @test JSimplex._effective_pricing(ws,algorithm) == :dantzig
        pricing != :devex && algorithm == :dual && check_basis_weights(ws,algorithm)
        JSimplex._reset_auto_pricing!(ws)
        @test JSimplex._effective_pricing(ws,algorithm) == (pricing == :auto ? :steepest_edge : pricing)
        @test isnothing(ws.scratch.stagnation)
        @test !ws.scratch.pricing.temporary
        @test ws.scratch.pricing.observations == 0
    end
end

@testset "Numerical recovery ends owned trials and survives phase resets" begin
    for pricing in (:auto,:steepest_edge)
        p = LinearProblem(sparse([2.0;;]),[0.0];row_lower=[1.0])
        policy = isolated_pricing_policy()
        ws = JSimplex.initialize_workspace(p,SolverOptions(;algorithm=:dual,pricing,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        force_pricing_trial!(ws,:dual)
        ws.pricing_weights[ws.basis.basic_indices[1]] = NaN
        @test isnothing(JSimplex.dual_iteration!(ws,()->false))
        @test JSimplex._effective_pricing(ws,:dual) == :devex
        @test !ws.scratch.pricing.temporary
        JSimplex._reset_auto_pricing!(ws)
        @test JSimplex._effective_pricing(ws,:dual) == :devex
    end
end

@testset "Cancelled candidates cannot publish pricing lifecycle events" begin
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[1.0])
    for event in (:pricing_steepest_edge,:pricing_progress_return,:pricing_trial_expired,:pricing_phase_reset)
        d = JSimplex.SimplexDiagnostics()
        policy = isolated_pricing_policy()
        ws = JSimplex.initialize_workspace(p,SolverOptions(pricing=:auto,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy))
        force_pricing_trial!(ws,:primal)
        cancelled = Ref(false)
        result = JSimplex._transactional_simplex_step!(ws,()->cancelled[]) do trial,stop
            JSimplex._reset_auto_pricing!(trial)
            JSimplex._simplex_event!(trial,event)
            cancelled[] = true
            nothing
        end
        @test result.status == TIME_LIMIT
        @test ws.scratch.pricing.temporary
        @test JSimplex.event_count(d,event) == 0
    end
end

@testset "Auxiliary handoff publishes a fresh phase only on acceptance" begin
    for interruption in (:none,:deadline,:observer)
        p = LinearProblem(sparse([2.0;;]),[-1.0];row_upper=[2.0])
        policy = isolated_pricing_policy()
        reached = Ref(false)
        d = JSimplex.SimplexDiagnostics(observer=(reason,trial)->begin
            if reason == :refactor_other
                reached[] = true
                interruption == :observer && error("handoff observer interruption")
            end
        end)
        ws = JSimplex.initialize_workspace(p,SolverOptions(algorithm=:dual,pricing=:steepest_edge,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy))
        force_pricing_trial!(ws,:dual)
        m = JSimplex.StagnationMonitor{Float64}(2)
        pricing_window!(JSimplex.PricingState(Float64),m,policy)
        history = JSimplex.WorkspaceStagnation(m,UInt(0),UInt(0),0,1.0,1.0)
        ws.scratch.stagnation = history
        result = try
            JSimplex.make_dual_feasible!(ws,()->interruption == :deadline && reached[])
        catch exception
            exception
        end
        @test reached[]
        if interruption == :none
            @test isnothing(result)
            @test !ws.scratch.pricing.temporary
            @test JSimplex._effective_pricing(ws,:dual) == :steepest_edge
            @test isnothing(ws.scratch.stagnation)
            check_basis_weights(ws,:dual)
        else
            @test interruption == :deadline ? result.status == TIME_LIMIT : result isa JSimplex.DiagnosticObserverFailure && result.cause isa ErrorException
            @test ws.scratch.stagnation === history
            @test history.monitor.window_count == 2
            @test ws.scratch.pricing.temporary
            @test ws.basis.basic_indices == [2]
        end
    end
end

@testset "Disabled pricing policy takes effect before the next selection" begin
    for algorithm in (:primal,:dual), pricing in (:auto,:steepest_edge,:devex)
        p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[1.0])
        ws = JSimplex.initialize_workspace(p,SolverOptions(;algorithm,pricing,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=isolated_pricing_policy()))
        state = force_pricing_trial!(ws,algorithm)
        expected = state.return_mode
        ws.progress = JSimplex.SimplexProgressContext(p;numerical_policy=isolated_pricing_policy(enabled=false))
        @test JSimplex._prepare_auto_pricing!(ws,algorithm)
        @test JSimplex._effective_pricing(ws,algorithm) == expected
        @test !ws.scratch.pricing.temporary
    end
end

@testset "A disabled-policy algorithm change does not introduce a pricing heuristic" begin
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[1.0])
    ws = JSimplex.initialize_workspace(p,SolverOptions(pricing=:auto,verbose=false))
    @test JSimplex._prepare_auto_pricing!(ws,:primal)
    @test JSimplex._prepare_auto_pricing!(ws,:dual)
    @test JSimplex._effective_pricing(ws,:dual) == :steepest_edge
end

@testset "Both primal phase-I paths retain numerical Devex without the temporary trial" begin
    for phase_one in (false,true)
        p = LinearProblem(sparse([2.0;;]),[1.0];row_lower=[1.0])
        seen = Ref(false)
        d = JSimplex.SimplexDiagnostics(observer=(event,ws)->begin
            if event == :phase_one
                JSimplex._prepare_auto_pricing!(ws,:primal)
                JSimplex._reject_auto_weight!(ws)
                force_pricing_trial!(ws,:primal)
            elseif event == :phase_primal
                seen[] = true
                @test !isnothing(ws.scratch.pricing)
                if !isnothing(ws.scratch.pricing)
                    @test ws.scratch.pricing.active == :devex
                    @test !ws.scratch.pricing.temporary
                    @test isnothing(ws.scratch.pricing.last_monitor)
                end
            end
        end)
        policy = JSimplex.NumericalPolicy(Float64;adaptive_stalling=true,adaptive_pricing=true,
            phase_one,refactor_timing=false)
        result = JSimplex._solve_diagnosed(p,d;
            options=SolverOptions(algorithm=:primal,pricing=:auto,presolve=false,scaling=:off,verbose=false),
            numerical_policy=policy)
        @test result.status == OPTIMAL
        @test result.primal ≈ [0.5]
        @test seen[]
    end
end

@testset "Primal phase construction preserves the safe rule but owns fresh history" begin
    for modern in (false,true)
        p = LinearProblem(sparse([2.0;;]),[1.0];row_lower=[1.0])
        o = SolverOptions(algorithm=:primal,pricing=:auto,verbose=false)
        policy = isolated_pricing_policy()
        ws = JSimplex.initialize_workspace(p,o;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        JSimplex._prepare_auto_pricing!(ws,:primal)
        JSimplex._reject_auto_weight!(ws)
        force_pricing_trial!(ws,:primal)
        phase = modern ? first(JSimplex._phase_one_workspace(ws,policy,()->false)) :
            first(JSimplex._primal_phase_one(p,o,ws.progress,()->false;initial=ws))
        @test JSimplex._prepare_auto_pricing!(phase,:primal)
        @test JSimplex._effective_pricing(phase,:primal) == :devex
        @test !phase.scratch.pricing.temporary
        @test isnothing(phase.scratch.pricing.last_monitor)
        @test isnothing(phase.scratch.stagnation)
        @test ws.scratch.pricing.temporary
        @test all(isone,phase.pricing_weights)
    end
end

@testset "Explicit and automatic weighted rules share productive trial returns" begin
    for algorithm in (:primal,:dual), pricing in (:auto,:steepest_edge,:devex)
        p=LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[1.0])
        d=JSimplex.SimplexDiagnostics()
        policy=isolated_pricing_policy()
        ws=JSimplex.initialize_workspace(p,SolverOptions(;algorithm,pricing,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy))
        JSimplex._prepare_auto_pricing!(ws,algorithm)
        monitor=JSimplex.StagnationMonitor{Float64}(2)
        ws.scratch.stagnation=JSimplex.WorkspaceStagnation(monitor,UInt(0),UInt(0),0,1.0,1.0)
        for objective in (1.0,1.0,0.75,0.5)
            for _ in 1:2
                JSimplex.observe_progress!(monitor;objective,primal_violation=1.0,
                    dual_violation=0.0,primal_step=0.0,dual_step=0.0)
                JSimplex._observe_auto_pricing!(ws,algorithm)
            end
        end
        @test JSimplex._effective_pricing(ws,algorithm) == (pricing == :auto ? :steepest_edge : pricing)
        @test JSimplex.event_count(d,:pricing_dantzig) == 1
        @test JSimplex.event_count(d,:pricing_progress_return) == 1
        @test JSimplex.event_count(d,:pricing_trial_expired) == 0
    end
end

@testset "Devex trials use the same reference updates as fixed Devex" begin
    for algorithm in (:primal,:dual), update in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        p=algorithm == :primal ?
            LinearProblem(sparse([0.5 1.0;0.0 3.0]),[-3.0,-1.0];row_upper=ones(2)) :
            LinearProblem(sparse([0.5 0.0;0.0 3.0]),zeros(2);row_lower=ones(2))
        o=SolverOptions(;algorithm,pricing=:devex,basis_update=update,verbose=false)
        trial=JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;
            numerical_policy=isolated_pricing_policy()))
        reference=JSimplex.initialize_workspace(p,o)
        force_pricing_trial!(trial,algorithm)
        for ws in (trial,reference)
            result=algorithm == :primal ? JSimplex._primal_iteration!(ws,()->false,o.dual_tolerance) :
                JSimplex.dual_iteration!(ws,()->false)
            @test isnothing(result)
        end
        @test trial.basis.basic_indices == reference.basis.basic_indices
        @test trial.devex_reference == reference.devex_reference
        @test trial.pricing_weights == reference.pricing_weights
        @test any(!isone,trial.pricing_weights)
        @test JSimplex._effective_pricing(trial,algorithm) == :dantzig
    end
end
