"""Exclusive S5-X literal checks and read-time pins; not a Julia parser."""
from pathlib import Path
import hashlib,json,re,time
R=Path.cwd();H=Path(__file__).resolve().parent;W=H.parent/'S5-W';D=H.parent.parent
s=(H/'candidate.jl').read_text();b=(W/'original-testset.txt').read_text();cb=s.split('    d = JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin\n')[1].split('    end)\n')[0]
original=b.splitlines(keepends=True);out=[original[0]]
for line in original[1:10]:
 token=line.strip();matches=[x for x in s.splitlines() if x.strip()==token]
 assert len(matches)==1,(token,len(matches))
 out.append(line[:len(line)-len(line.lstrip())]+matches[0].strip()+'\n')
out.extend(original[10:]);inverse=''.join(out)
checkbody=s.split('    checks = (\n')[1].split('    observations = Dict(')[0]
names=re.findall(r'^        (\w+) = ',checkbody,re.M)
fields=re.findall(r'^    (\w+)::',s.split('mutable struct S5XProbe\n')[1].split('\nend')[0],re.M)
obs=s.split('    observations = Dict(')[1].split('    output = Dict(')[0]
checks={
 'exact_original_inverse':inverse==b,
 'original6_unchanged':b in (R/'test/simplex_start_state_tests.jl').read_text() and b.count('@test ')==6,
 'one_initial_one_crash':s.count('JSimplex.initialize_workspace(')==1 and s.count('JSimplex._crash_workspace(')==1,
 'one_context':s.count('LinearProblem(')==1 and s.count('NumericalPolicy(Float64;crash=true)')==1 and s.count('SolverOptions(verbose=false)')==1,
 'probe11':len(fields)==11,
 '50_named_predicates':len(names)==len(set(names))==50,
 '12_observations':len(re.findall(r'"\w+"=>',obs))==12,
 '7copies26entries':s.count('copy(')==7 and all(x in s for x in ['copy(initial.basis.basic_indices)','copy(initial.basis.states)','copy(initial.primal)','copy(initial.reduced_costs)','copy(initial.costs)','copy(initial.lower)','copy(initial.upper)']),
 'setup_before_arm':s.index('probe = S5XProbe')<s.index('d = JSimplex.SimplexDiagnostics')<s.index('initial = JSimplex.initialize_workspace')<s.index('probe.armed = true'),
 'unarmed_early_return':cb.lstrip().startswith('probe.armed || return nothing'),
 'original_latch_stop':s.count('reason == :refactor_other && (done[]=true)')==1 and s.count('()->done[]')==1,
 'first_trial_capture':'if probe.refactor_hits == 1\n                probe.trial = ws\n                probe.refactor_work = (ws.iterations,ws.refactorizations)' in cb,
 'first_fallback_capture_throw':'if probe.fallback_hits == 1\n                probe.fallback = ws\n                probe.fallback_record = s5x_record(ws,probe.callback_count)' in cb and 'throw(probe.sentinel)' in cb,
 'callback_no_array_work':not any(x in cb for x in ['copy(', 'all(', 'for ', 'solve', 'refactor!', 'push!', 'Matrix(', '@assert']),
 'record_lookup_only':'JSimplex.event_count(d,:crash_fallback)' in s and 'recent_events(' not in s,
 'state_and_missing_duplicate_gates':all(x in checkbody for x in ['probe.refactor_hits == 1','probe.fallback_hits == 1','probe.trial !== initial','probe.fallback === initial','trial_present && all(i->trial_owners[i] !== entry_owners[i],1:11)','all(i->after_owners[i] === entry_owners[i],1:17)']),
 'work_merge_and_after':all(x in checkbody for x in ['max(entry_work[1],probe.refactor_work[1])','max(entry_work[2]+1,probe.refactor_work[2])','after_record == probe.fallback_record','probe.callbacks_after_fallback == 0']),
 'original_cause_no_return':all(x in s for x in ['failure = SingularException(42)','caught.cause === failure','no_return = !returned','wrapped_type = caught isa JSimplex.DiagnosticObserverFailure']),
 'native_and_clock_no_override':all(x in checkbody for x in ['!policy.solve_refinement','!policy.recovery','!d.kernel_timing','initial.options.time_limit == Inf','progress.start_ns === entry_clock[1]']) and 'policy.numerical_profile' not in s,
 'raw_before_aggregate':s.index('TOML.print(io,output)')<s.index('@assert all(values(checks))'),
 'no_extra_numerics_or_loops':not any(x in s for x in ['solve(', 'recompute!(', 'refactor!(', 'copy_basis_factorization(', 'setprecision(', 'BLAS.', 'for manager', 'for T ']),
 'entry17_pass':len(json.loads((H/'entry.json').read_text())['checks'])==17 and json.loads((H/'entry.json').read_text())['all_passed'] is True,
}
paths={Path(k) for k in json.loads((W/'evidence.json').read_text())['sha256']}
paths|={p for p in W.iterdir() if p.is_file()}
paths|={Path(__file__),H/'candidate.jl',H/'entry.py',H/'entry.json',H/'host.json',D/'S5-CRASH-FALLBACK-OBSERVER-ORACLE.md',D/'S5-CRASH-FALLBACK-OBSERVER-ORACLE-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-preparation.md'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for data in iter(lambda:f.read(1048576),b''):h.update(data)
 return h.hexdigest()
def dump(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
with (H/'construction-inverse.txt').open('x') as f:f.write(inverse)
paths.add(H/'construction-inverse.txt')
e=dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in sorted(paths)},predicate_names=names,probe_fields=fields,scope='OFFLINE literal checks only; every runtime expectation UNQUALIFIED',time_ns=time.time_ns())
dump(H/'evidence.json',e);print(json.dumps(dict(checks=checks,pins=len(paths),candidate_sha256=sha(H/'candidate.jl'))));assert e['all_passed']
