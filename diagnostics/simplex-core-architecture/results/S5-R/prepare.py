"""Exclusive S5-R text preparation. Never invokes Julia or a Julia parser."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';O=D/'results/S5-R';Q=O.parent/'S5-Q'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(name,text):
 with (O/name).open('x') as f:f.write(text)
def jout(name,value):write(name,json.dumps(value,indent=2)+'\n')
qe=json.loads((Q/'evidence.json').read_text());qc=json.loads((Q/'closure.json').read_text());qi=json.loads((Q/'independent.json').read_text());qh=json.loads((Q/'host-before.json').read_text())
for d in (qe,qc,qi):
 assert all(x is True for x in d['checks'].values()) and all(sha(p)==v for p,v in d['sha256'].items())
groups=set(qh['groups']);hits=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split()
  if int(v[2]) in groups or (p/'comm').read_text().startswith('julia'):hits.append(dict(pid=int(p.name),pgid=int(v[2]),start_ticks=v[19],command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (OSError,ValueError,IndexError):pass
assert not hits
host=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=hits,refs={x:subprocess.check_output(['git','rev-parse',x],text=True).strip() for x in ['HEAD','master']},remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True),user_hashes={p:sha(p) for p in qh['user_hashes']},time_ns=time.time_ns())
assert host['user_hashes']==qh['user_hashes'];jout('host-before.json',host)
original=(Q/'existing-setup.txt').read_text();lines=original.splitlines(True);setup=''.join(x[8:] for x in lines[:-1]);call=lines[-1][12:].rstrip('\n')
setup=setup.replace('SimplexProgressContext{T,Nothing}','SimplexProgressContext{T,typeof(d)}').replace('7,11,nothing,policy)','7,11,d,policy)')
call=call.replace(';policy,progress)', ';policy,progress,stop=guard)')
head='''# S5-R UNEXECUTED diagnostic candidate. A separate reviewed launcher is required.
using JSimplex, SparseArrays, TOML

mutable struct S5RProbe
    workspace::Any
    default_indices::Any
    default_states::Any
    imported_indices::Any
    imported_states::Any
    stage::Int
    ordered::Bool
    callbacks::Int
    initial_hits::Int
    imported_hits::Int
    checkpoint_hits::Int
    stop_calls::Int
    throws::Int
    armed::Bool
    at_throw::Any
end
S5RProbe() = S5RProbe(nothing,nothing,nothing,nothing,nothing,0,true,0,0,0,0,0,0,false,nothing)

function s5r_selected_work(ws)
    d=ws.progress.diagnostics
    return (ftran=d.kernel_calls[:ftran],btran=d.kernel_calls[:btran],
        factor=d.kernel_calls[:refactorization],iterations=ws.iterations,
        refactors=ws.refactorizations,checkpoint=d.counts[:checkpoint],
        initial=d.counts[:refactor_initial],other=d.counts[:refactor_other],
        correction=d.counts[:correction],attempt=d.counts[:correction_attempt],
        events=length(d.events),last=isempty(d.events) ? :none : d.events[end],
        phase=ws.scratch.phase_generation,history=length(ws.scratch.checkpoints))
end

function (probe::S5RProbe)(reason,state)
    probe.callbacks += 1
    if reason === :checkpoint && probe.stage == 0
        probe.ordered &= probe.callbacks == 1
        probe.stage = 1
    elseif reason === :refactor_initial && probe.stage == 1
        probe.initial_hits += 1
        probe.workspace = state
        probe.default_indices = state.basis.basic_indices
        probe.default_states = state.basis.states
        probe.ordered &= probe.callbacks == 2 && state.refactorizations == 0
        probe.stage = 2
    elseif reason === :refactor_other && probe.stage == 2 && state === probe.workspace
        probe.imported_hits += 1
        probe.imported_indices = state.basis.basic_indices
        probe.imported_states = state.basis.states
        probe.ordered &= probe.callbacks == 3 && state.refactorizations == 1
        probe.stage = 3
    elseif reason === :checkpoint && probe.stage == 3 && state === probe.workspace
        probe.checkpoint_hits += 1
        probe.ordered &= probe.callbacks == 4 && probe.stop_calls == 1
        probe.stage = 4
        probe.armed = true
    else
        probe.ordered = false
    end
    return nothing
end

function s5r_case(output)
    T=Float64; update=:pfi; backend=:native
    probe=S5RProbe()
    d=JSimplex.SimplexDiagnostics(;observer=probe,kernel_timing=true)
    sentinel=ErrorException("S5-R explicit imported-checkpoint stop")
    stop = () -> begin
        probe.stop_calls += 1
        if probe.armed
            probe.ordered &= probe.stage == 4 && probe.stop_calls == 2
            probe.throws += 1
            probe.at_throw = s5r_selected_work(probe.workspace)
            throw(sentinel)
        end
        probe.ordered &= probe.stage == 3 && probe.stop_calls == 1
        return false
    end
    guard=JSimplex._guard_stop_callback(stop)
    # BEGIN SOURCE SETUP
'''
tail='''    # END SOURCE SETUP
    entry=(indices=basis.basic_indices,states=basis.states,start=progress.start_ns,
        objective=progress.objective,scaling=progress.scaling,diagnostics=d,
        policy=policy,options=options,problem=p)
    saved_indices=copy(basis.basic_indices)
    saved_states=copy(basis.states)
    ws=nothing
    caught=nothing
    returned=false
    try
        # BEGIN SOURCE CALL
'''
after='''        # END SOURCE CALL
        returned=true
    catch exception
        caught=exception
    end
    retained=probe.workspace
    present=retained !== nothing
    after=present ? s5r_selected_work(retained) : nothing
    expected=(ftran=2,btran=2,factor=1,iterations=0,refactors=1,checkpoint=1,
        initial=1,other=1,correction=0,attempt=0,events=3,last=:refactor_other,
        phase=UInt(1),history=0)
    checks=(
        no_return=!returned && ws === nothing,
        original_exception=caught === sentinel,
        guarded_exception=guard.exception === sentinel,
        workspace_observed=present,
        exact_order=probe.ordered && probe.stage == 4,
        initial_once=probe.initial_hits == 1,
        imported_once=probe.imported_hits == 1,
        target_once=probe.checkpoint_hits == 1,
        four_callbacks=probe.callbacks == 4,
        two_stops=probe.stop_calls == 2,
        one_throw=probe.throws == 1,
        armed=probe.armed,
        caller_indices_owner=basis.basic_indices === entry.indices,
        caller_states_owner=basis.states === entry.states,
        caller_indices_values=basis.basic_indices == saved_indices,
        caller_states_values=basis.states == saved_states,
        imported_indices_owner=present && retained.basis.basic_indices === probe.imported_indices,
        imported_states_owner=present && retained.basis.states === probe.imported_states,
        indices_not_caller=present && retained.basis.basic_indices !== entry.indices,
        states_not_caller=present && retained.basis.states !== entry.states,
        indices_not_default=present && retained.basis.basic_indices !== probe.default_indices,
        states_not_default=present && retained.basis.states !== probe.default_states,
        imported_indices_values=present && retained.basis.basic_indices == saved_indices,
        imported_states_values=present && retained.basis.states == saved_states,
        problem_shared=present && retained.problem === entry.problem,
        diagnostics_shared=present && retained.progress.diagnostics === entry.diagnostics,
        objective_shared=present && retained.progress.objective === entry.objective,
        objective_constant=present && retained.progress.objective_constant === progress.objective_constant,
        scaling_shared=present && retained.progress.scaling === entry.scaling,
        original_clock=present && retained.progress.start_ns === entry.start,
        iteration_offset=present && retained.progress.iteration_offset == progress.iteration_offset == 7,
        refactor_offset=present && retained.progress.refactorization_offset == progress.refactorization_offset == 11,
        policy_shared=present && retained.progress.numerical_policy === entry.policy,
        native_recovery=policy.numerical_profile === :native && policy.recovery && !policy.solve_refinement,
        sparse_policy=policy.sparse_pricing && policy.hypersparse,
        options_preserved=present && retained.options === entry.options,
        infinite_limit=options.time_limit == Inf,
        selected_at_throw=probe.at_throw == expected,
        selected_after_unwind=after == expected,
        no_later_selected_work=after == probe.at_throw && probe.at_throw !== nothing,
    )
    observations=Dict(
        "caught_type"=>string(typeof(caught)),"sentinel_type"=>string(typeof(sentinel)),
        "guard_exception_type"=>string(typeof(guard.exception)),
        "returned"=>returned,"callbacks"=>probe.callbacks,"stop_calls"=>probe.stop_calls,
        "throws"=>probe.throws,"stage"=>probe.stage,
        "start_ns"=>string(progress.start_ns),"scalar"=>string(T),
        "update"=>string(update),"backend"=>string(backend))
    work_record(x) = isnothing(x) ? Dict("present"=>false) :
        Dict(string(k)=>(v isa Symbol ? string(v) : v) for (k,v) in pairs(x))
    raw=Dict("checks"=>Dict(string(k)=>v for (k,v) in pairs(checks)),
        "observations"=>observations,"at_throw"=>work_record(probe.at_throw),
        "after_unwind"=>work_record(after))
    open(output,"w") do io
        TOML.print(io,raw)
    end
    @assert all(values(checks)) "S5-R selected oracle failed; preserve and stop"
    return nothing
end

length(ARGS) == 1 || error("Expected one fresh raw TOML output path")
ispath(only(ARGS)) && error("Refusing to overwrite an existing result")
s5r_case(only(ARGS))
'''
candidate=head+setup+tail+'        '+call+'\n'+after
write('candidate.jl',candidate)
restored_setup=setup.replace('SimplexProgressContext{T,typeof(d)}','SimplexProgressContext{T,Nothing}').replace('7,11,d,policy)','7,11,nothing,policy)')
inverse=''.join('        '+x for x in restored_setup.splitlines(True))+'            '+call.replace(';policy,progress,stop=guard)',';policy,progress)')+'\n'
assert inverse==original
jout('provenance.json',dict(original_source='test/simplex_precision_tests.jl',original_excerpt_sha256=sha(Q/'existing-setup.txt'),candidate_sha256=sha(O/'candidate.jl'),inverse_byte_exact=True,substitutions=['dedent setup by 8 columns and selected call by 12','progress type Nothing -> typeof(d)','progress diagnostics nothing -> d','selected call add stop=guard'],candidate_lines=len(candidate.splitlines()),predicate_names=[l.strip().split('=')[0] for l in candidate.split('    checks=(\n',1)[1].split('    )\n',1)[0].splitlines()],probe_fields=15,entry_fields=9,selected_work_fields=14,input_copies=2,input_entries=6,observation_fields=12))
paths=set(qe['sha256'])|set(qi['sha256'])|{str(p) for p in Q.rglob('*') if p.is_file()}|{str(O/'prepare.py'),str(O/'candidate.jl'),str(O/'host-before.json'),str(O/'provenance.json'),str(R/'docs/superpowers/plans/2026-10-13-basis-initialization-stop-preparation.md')}
# Normalize all current-stage paths to absolute identities.
paths={str(Path(p).resolve()) for p in paths}
jout('pins.json',dict(sha256={p:sha(p) for p in sorted(paths)},scope='Fresh offline read-time hashes, not launch pins',time_ns=time.time_ns()))
print(json.dumps(dict(candidate_sha256=sha(O/'candidate.jl'),lines=len(candidate.splitlines()),pins=len(paths))))
