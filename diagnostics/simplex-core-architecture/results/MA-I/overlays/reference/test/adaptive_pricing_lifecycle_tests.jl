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

# Pending observer failures occur after auxiliary handoff publication.
# Keep the live/trial identity discriminator and consumed-work checks together.
mutable struct PendingObserverProbe{E}
    live::Any
    trial::Any
    entry_factor::Any
    sentinel::E
    armed::Bool
    callbacks::Int
    latches::Int
    hits::Int
    throw_iterations::Int
    throw_refactors::Int
    throw_phase_events::Int
    throw_callbacks::Int
    published_at_throw::Bool
end

function observe_pending!(probe,reason,state)
    probe.armed || return nothing
    probe.callbacks += 1
    if reason == :refactor_other && state !== probe.live &&
       !isnothing(state.progress.diagnostics) &&
       state.progress.diagnostics.observer isa JSimplex._StageObserver &&
       state.progress.diagnostics.observer.live === probe.live
        probe.latches += 1
        probe.latches == 1 && (probe.trial = state)
    end
    if reason == :pricing_phase_reset && state === probe.live &&
       probe.latches == 1 && !isnothing(probe.trial) &&
       state.factorization === probe.trial.factorization &&
       state.factorization !== probe.entry_factor
        probe.hits += 1
        probe.published_at_throw = true
        probe.throw_iterations = state.iterations
        probe.throw_refactors = state.refactorizations
        probe.throw_phase_events = JSimplex.event_count(state.progress.diagnostics,reason)
        probe.throw_callbacks = probe.callbacks
        throw(probe.sentinel)
    end
    return nothing
end

selected_owners(ws) = (ws.costs,ws.lower,ws.upper,ws.primal,ws.reduced_costs,
    ws.pricing_weights,ws.devex_reference,ws.basis.basic_indices,ws.basis.states)

function pending_observer_case()
    p = LinearProblem(sparse([2.0;;]),[-1.0];row_upper=[2.0])
    policy = isolated_pricing_policy()
    probe = PendingObserverProbe(nothing,nothing,nothing,
        ErrorException("S5-L pending observer sentinel"),false,0,0,0,0,0,0,0,false)
    d = JSimplex.SimplexDiagnostics(observer=(reason,state)->observe_pending!(probe,reason,state))
    ws = JSimplex.initialize_workspace(p,SolverOptions(algorithm=:dual,pricing=:steepest_edge,verbose=false);
        progress=JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy))
    force_pricing_trial!(ws,:dual)
    m = JSimplex.StagnationMonitor{Float64}(2)
    pricing_window!(JSimplex.PricingState(Float64),m,policy)
    history = JSimplex.WorkspaceStagnation(m,UInt(0),UInt(0),0,1.0,1.0)
    ws.scratch.stagnation = history
    probe.live = ws
    probe.entry_factor = ws.factorization
    entry = (owners=selected_owners(ws),costs=copy(ws.costs),lower=copy(ws.lower),upper=copy(ws.upper),
        problem=ws.problem,options=ws.options,progress=ws.progress,pricing=ws.scratch.pricing,
        refactor_policy=ws.scratch.refactorization,history=ws.scratch.stagnation,
        journal=ws.scratch.perturbations,iterations=ws.iterations,refactors=ws.refactorizations,
        phase_generation=ws.scratch.phase_generation)
    entry_model_matches = isequal(ws.costs[1],p.objective[1]) && iszero(ws.costs[2]) &&
        isequal(ws.lower[1],p.column_lower[1]) && isequal(ws.lower[2],p.row_lower[1]) &&
        isequal(ws.upper[1],p.column_upper[1]) && isequal(ws.upper[2],p.row_upper[1])
    entry_scope_matches = eltype(ws.costs) === Float64 && size(p.A) == (1,1) &&
        isnothing(entry.journal) && !policy.phase_one && !policy.recovery &&
        !policy.solve_refinement && policy.adaptive_pricing && policy.adaptive_stalling
    probe.armed = true
    outcome = try
        JSimplex.make_dual_feasible!(ws,()->false)
    catch exception
        exception
    finally
        probe.armed = false
    end
    trial = probe.trial
    have_trial = !isnothing(trial)
    live_owners = selected_owners(ws)
    owners_preserved = all(i -> live_owners[i] === entry.owners[i],1:9)
    owners_distinct = have_trial && all(i -> live_owners[i] !== selected_owners(trial)[i],1:9)
    vectors_equal = have_trial && all(i -> isequal(live_owners[i],selected_owners(trial)[i]),1:9)
    pricing_equal = have_trial && !isnothing(ws.scratch.pricing) &&
        !isnothing(trial.scratch.pricing) && all(field ->
            isequal(getfield(ws.scratch.pricing,field),getfield(trial.scratch.pricing,field)),
            fieldnames(typeof(ws.scratch.pricing)))
    last_event = isempty(d.events) ? :none :
        d.events[length(d.events)<64 ? length(d.events) : mod1(d.next_event-1,64)]
    checks = (
        entry_model_matches=entry_model_matches,
        entry_scope_matches=entry_scope_matches,
        one_trial=probe.latches==1,
        one_throw=probe.hits==1,
        wrapper=outcome isa JSimplex.DiagnosticObserverFailure,
        same_cause=outcome isa JSimplex.DiagnosticObserverFailure && outcome.cause === probe.sentinel,
        published_at_throw=probe.published_at_throw,
        factor_published=have_trial && ws.factorization === trial.factorization,
        factor_replaced=ws.factorization !== probe.entry_factor,
        problem_owner=ws.problem === entry.problem,
        options_owner=ws.options === entry.options,
        progress_owner=ws.progress === entry.progress,
        array_owners_preserved=owners_preserved,
        trial_array_owners_distinct=owners_distinct,
        published_vectors_equal=vectors_equal,
        entry_costs_preserved=isequal(ws.costs,entry.costs),
        entry_lower_preserved=isequal(ws.lower,entry.lower),
        entry_upper_preserved=isequal(ws.upper,entry.upper),
        policy_published=have_trial && ws.scratch.refactorization === trial.scratch.refactorization,
        policy_private=ws.scratch.refactorization !== entry.refactor_policy,
        pricing_owner=ws.scratch.pricing === entry.pricing,
        pricing_private=have_trial && ws.scratch.pricing !== trial.scratch.pricing,
        pricing_equal=pricing_equal,
        pricing_not_temporary=!isnothing(ws.scratch.pricing) && !ws.scratch.pricing.temporary,
        pricing_phase=!isnothing(ws.scratch.pricing) && ws.scratch.pricing.last_transition == :phase,
        live_history_cleared=isnothing(ws.scratch.stagnation),
        old_history_preserved=entry.history === history && history.monitor.window_count == 2,
        checkpoints_cleared=isempty(ws.scratch.checkpoints),
        phase_advanced=ws.scratch.phase_generation > entry.phase_generation,
        journal_absent=isnothing(ws.scratch.perturbations) && ws.scratch.perturbations === entry.journal,
        iterations_monotone=ws.iterations >= entry.iterations,
        refactors_monotone=ws.refactorizations >= entry.refactors,
        trial_iterations_published=have_trial && ws.iterations == trial.iterations,
        trial_refactors_published=have_trial && ws.refactorizations == trial.refactorizations,
        no_later_iterations=probe.hits==1 && ws.iterations == probe.throw_iterations,
        no_later_refactors=probe.hits==1 && ws.refactorizations == probe.throw_refactors,
        no_later_callbacks=probe.hits==1 && probe.callbacks == probe.throw_callbacks,
        event_recorded=probe.hits==1 && probe.throw_phase_events > 0,
        no_later_phase_event=probe.hits==1 && JSimplex.event_count(d,:pricing_phase_reset) == probe.throw_phase_events,
        last_event_selected=last_event == :pricing_phase_reset,
    )
    return checks
end

@testset "Pending auxiliary handoff observer failure preserves published state" begin
    checks = pending_observer_case()
    @test checks.entry_model_matches
    @test checks.entry_scope_matches
    @test checks.one_trial
    @test checks.one_throw
    @test checks.wrapper
    @test checks.same_cause
    @test checks.published_at_throw
    @test checks.factor_published
    @test checks.factor_replaced
    @test checks.problem_owner
    @test checks.options_owner
    @test checks.progress_owner
    @test checks.array_owners_preserved
    @test checks.trial_array_owners_distinct
    @test checks.published_vectors_equal
    @test checks.entry_costs_preserved
    @test checks.entry_lower_preserved
    @test checks.entry_upper_preserved
    @test checks.policy_published
    @test checks.policy_private
    @test checks.pricing_owner
    @test checks.pricing_private
    @test checks.pricing_equal
    @test checks.pricing_not_temporary
    @test checks.pricing_phase
    @test checks.live_history_cleared
    @test checks.old_history_preserved
    @test checks.checkpoints_cleared
    @test checks.phase_advanced
    @test checks.journal_absent
    @test checks.iterations_monotone
    @test checks.refactors_monotone
    @test checks.trial_iterations_published
    @test checks.trial_refactors_published
    @test checks.no_later_iterations
    @test checks.no_later_refactors
    @test checks.no_later_callbacks
    @test checks.event_recorded
    @test checks.no_later_phase_event
    @test checks.last_event_selected
end
