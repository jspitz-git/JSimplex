"""Exclusive source-text preparation only: no Julia parser or execution."""
from pathlib import Path
import hashlib,json
R=Path.cwd();L=R/'diagnostics/simplex-core-architecture/results/S5-L';src=R/'test/adaptive_pricing_lifecycle_tests.jl';s=src.read_text()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
helpers=[];bindings=[]
for name in ('isolated_pricing_policy','pricing_window!','force_pricing_trial!'):
 start=s.index('function '+name+'(');end=s.index('\nend\n',start)+5;text=s[start:end];helpers.append(text);bindings.append({'name':name,'file':str(src.relative_to(R)),'start_line':s[:start].count('\n')+1,'source_text':text,'sha256':hashlib.sha256(text.encode()).hexdigest()})
start=s.index('@testset "Auxiliary handoff publishes a fresh phase only on acceptance"');end=s.index('\n@testset ',start+1);fixture=s[start:end]
with (L/'fixture-source.txt').open('x') as f:f.write(fixture.rstrip()+'\n')
setup1=fixture[fixture.index('        p ='):fixture.index('        reached =')]
setup2=fixture[fixture.index('        ws ='):fixture.index('        result =')]
dedent=lambda x:''.join(line[4:] if line.startswith('    ') else line for line in x.splitlines(keepends=True))
body=r'''
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
__SETUP1__    probe = PendingObserverProbe(nothing,nothing,nothing,
        ErrorException("S5-L pending observer sentinel"),false,0,0,0,0,0,0,0,false)
    d = JSimplex.SimplexDiagnostics(observer=(reason,state)->observe_pending!(probe,reason,state))
__SETUP2__    probe.live = ws
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
    observations = (outcome_type=string(typeof(outcome)),
        cause_type=outcome isa JSimplex.DiagnosticObserverFailure ? string(typeof(outcome.cause)) : "none",
        latch_count=probe.latches,hit_count=probe.hits,callback_count=probe.callbacks,
        entry_iterations=entry.iterations,final_iterations=ws.iterations,
        entry_refactors=entry.refactors,final_refactors=ws.refactorizations,
        throw_iterations=probe.throw_iterations,throw_refactors=probe.throw_refactors,
        throw_phase_events=probe.throw_phase_events,throw_callbacks=probe.throw_callbacks,
        final_phase_events=JSimplex.event_count(d,:pricing_phase_reset),last_event=string(last_event))
    return checks,observations
end

# Unexecuted at S5-L. Only a separately admitted launcher may invoke this file.
length(ARGS) == 1 || error("one fresh output file path is required")
output = only(ARGS)
ispath(output) && error("refuse to overwrite output")
checks,observations = pending_observer_case()
open(output,"w") do io
    TOML.print(io,Dict("checks"=>Dict(string(k)=>v for (k,v) in pairs(checks)),
        "observations"=>Dict(string(k)=>v for (k,v) in pairs(observations))))
end
all(values(checks)) || error("S5-L pending observer qualification failed; preserve output and stop")
'''
body=body.replace('__SETUP1__',dedent(setup1)).replace('__SETUP2__',dedent(setup2))
candidate='# S5-L OFFLINE candidate: UNEXECUTED, no launch admission.\nusing JSimplex, SparseArrays, LinearAlgebra, TOML\n\n'+'\n'.join(helpers)+body
with (L/'candidate.jl').open('x') as f:f.write(candidate)
with (L/'source-provenance.json').open('x') as f:json.dump({'source_sha256':sha(src),'helpers':bindings,'setup1_original':setup1,'setup2_original':setup2,'setup_indent_removed':4,'fixture_source_sha256':sha(L/'fixture-source.txt'),'candidate_sha256':sha(L/'candidate.jl'),'prepare_sha256':sha(Path(__file__)),'scope':'Text-only exact helper and fixture setup extraction. No parser/runtime validation.'},f,indent=2);f.write('\n')
print(json.dumps({'candidate_sha256':sha(L/'candidate.jl'),'helpers':len(helpers),'lines':len(candidate.splitlines())}))
