
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
    O_COUNTS[1] += 1
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
        O_COUNTS[2] += 1
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
    observations = (outcome_type=string(typeof(outcome)),
        cause_type=outcome isa JSimplex.DiagnosticObserverFailure ? string(typeof(outcome.cause)) : "none",
        latch_count=probe.latches,hit_count=probe.hits,callback_count=probe.callbacks,
        entry_iterations=entry.iterations,final_iterations=ws.iterations,
        entry_refactors=entry.refactors,final_refactors=ws.refactorizations,
        throw_iterations=probe.throw_iterations,throw_refactors=probe.throw_refactors,
        throw_phase_events=probe.throw_phase_events,throw_callbacks=probe.throw_callbacks,
        final_phase_events=JSimplex.event_count(d,:pricing_phase_reset),last_event=string(last_event))
    O_COUNTS[3] += 1
    O_RECORD[] = (checks=checks,observations=observations)
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
