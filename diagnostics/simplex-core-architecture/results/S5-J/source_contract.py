"""Exclusive S5-J source/evidence reconciliation. No Julia or old auditor execution."""
from pathlib import Path
import hashlib,json,re,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';J=D/'results/S5-J'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def block(text,name):
 start=text.index('@testset "'+name+'"');m=re.search(r'\n[ \t]*@testset ',text[start+1:]);return text[start:] if m is None else text[start:start+1+m.start()]
names={
 'Interrupted auxiliary handoff preserves the live basis and factor':('test/simplex_handoff_atomicity_tests.jl',78),
 'Auxiliary handoff publishes a fresh phase only on acceptance':('test/adaptive_pricing_lifecycle_tests.jl',19),
 'Completed auxiliary work survives a callback exception':('test/simplex_driver_tests.jl',3),
 'Modern auxiliary dual owns its bound and cost model':('test/simplex_phase_one_auxiliary_tests.jl',12),
 'Modern auxiliary dual preserves recession and feasibility proofs':('test/simplex_phase_one_auxiliary_tests.jl',16),
 'Bound flips and auxiliary dual feasibility':('test/dual_simplex_tests.jl',106),
 'Auxiliary workspaces own their factorization backend':('test/dual_simplex_tests.jl',1),
 'Diagnostic observer failures do not become numerical statuses':('test/simplex_diagnostics_tests.jl',2)}
sourcefiles=['src/dual_simplex.jl','src/simplex_pivot.jl','src/simplex.jl','src/simplex_diagnostics.jl','src/simplex_recovery.jl','src/simplex_pricing.jl','src/sparse_pricing.jl','src/hypersparse_pipeline.jl','src/simplex_perturbation.jl']
paths={R/p for p in sourcefiles}|{R/p for p,n in names.values()}|{Path(__file__).resolve(),J/'host-before.json'}
rows=[];comparisons=[];sourcecomparisons=[]
for run in ('38142752357','38149970679'):
 meta=D/f'results/S6-A/ci-inventory-1-{run}-metadata.json';metadata=json.loads(meta.read_text());log=R/f'.superpowers/simplex-core-architecture/S6-A/ci-inventory-1/{run}-failed.log';paths.update((meta,log));lines=log.read_text().splitlines()
 for name,(file,n) in names.items():
  hits=[(i+1,line) for i,line in enumerate(lines) if name in line and '|' in line];assert len(hits)==1,(run,name)
  line,raw=hits[0];clean=re.sub(r'(?:\x1b|\^\[)\[[0-9;]*m','',raw);fields=clean.split('|',1)[1].split();assert fields[:2]==[str(n),str(n)],(name,fields)
  rows.append({'run':run,'head':metadata['headSha'],'run_conclusion':metadata['conclusion'],'name':name,'file':file,'line':line,'passed':n,'total':n,'raw':raw,'normalized':clean})
  old=subprocess.check_output(['git','show',metadata['headSha']+':'+file]).decode();a=block(old,name);b=block((R/file).read_text(),name)
  comparisons.append({'run':run,'name':name,'file':file,'historical_sha256':hashlib.sha256(a.encode()).hexdigest(),'current_sha256':hashlib.sha256(b.encode()).hexdigest(),'block_equal':a==b,'whole_file_equal':old==(R/file).read_text()})
 for file in sourcefiles:
  a=subprocess.check_output(['git','show',metadata['headSha']+':'+file]);b=(R/file).read_bytes();sourcecomparisons.append({'run':run,'file':file,'historical_sha256':hashlib.sha256(a).hexdigest(),'current_sha256':sha(R/file),'equal':a==b})
s=(R/'src/dual_simplex.jl').read_text();start=s.index('function _make_dual_feasible!');end=s.index('\nfunction _solve_continuous_dual(',start);handoff=s[start:end]
pivot=(R/'src/simplex_pivot.jl').read_text();pricing=(R/'src/simplex_pricing.jl').read_text();diagnostics=(R/'src/simplex_diagnostics.jl').read_text();recompute=(R/'src/simplex.jl').read_text();adaptive=block((R/'test/adaptive_pricing_lifecycle_tests.jl').read_text(),'Auxiliary handoff publishes a fresh phase only on acceptance');atomic=(R/'test/simplex_handoff_atomicity_tests.jl').read_text()
checks={
 '16_actual_historical_rows':len(rows)==16,
 '237_pass_each_failed_run':all(sum(x['passed'] for x in rows if x['run']==r)==237 for r in ('38142752357','38149970679')),
 '16_exact_test_blocks':all(x['block_equal'] for x in comparisons),
 'restore_precedes_auxiliary':handoff.index('_restore_active_perturbations!(workspace)')<handoff.index('recompute!(workspace)')<handoff.index('_auxiliary_workspace(workspace)'),
 'auxiliary_work_finally': 'finally\n        workspace.iterations = auxiliary.iterations\n        workspace.refactorizations = auxiliary.refactorizations' in handoff,
 'no_auxiliary_certificate_transfer':'auxiliary box optimum is inconclusive' in handoff and '_recession_direction_status(workspace, auxiliary)' in handoff,
 'trial_explicit_factor_copy':'trial.factorization = copy_basis_factorization(workspace.factorization)' in handoff,
 'trial_explicit_policy_deepcopy':'trial.scratch.refactorization = deepcopy(workspace.scratch.refactorization)' in handoff,
 'trial_uses_original_problem':'SimplexWorkspace(ws.problem,ws.options,progress' in pivot,
 'basis_remap_pretrial':handoff.index('basis.states[index] = FREE_NONBASIC')<handoff.index('trial = _candidate_workspace'),
 'last_stop_before_publication':handoff.index('time limit reached before auxiliary handoff')<handoff.index('_copy_pivot_state!(workspace, trial)'),
 'consumed_refactors_before_publication':handoff.index('workspace.refactorizations = max(workspace.refactorizations, trial.refactorizations)')<handoff.index('_copy_pivot_state!(workspace, trial)'),
 'factor_published_before_pending':handoff.index('workspace.factorization = trial.factorization')<handoff.index('for reason in trial.progress.diagnostics.observer.pending'),
 'stage_buffers_phase_reset':':pricing_phase_reset)' in pivot and 'push!(observer.pending,reason)' in pivot,
 'stage_forwards_other_events':'_diagnostic_event!(observer.live.progress.diagnostics,reason,candidate)' in pivot,
 'shared_diagnostic_counters':'SimplexDiagnostics(base.counts,base.events,base.next_event,observer' in pivot,
 'observer_count_precedes_wrapped_failure':diagnostics.index('record_event!(d, reason)',diagnostics.index('function _diagnostic_event!(d::SimplexDiagnostics,'))<diagnostics.index('throw(DiagnosticObserverFailure(exception))'),
 'phase_reset_conditional_pricing_state':'isnothing(state) && return nothing' in pricing and '_simplex_event!(ws,:pricing_phase_reset)' in pricing,
 'existing_observer_is_prepublication':'if reason == :refactor_other' in adaptive and ':pricing_phase_reset' not in adaptive,
 'existing_atomic_no_observer':'observer=' not in atomic and 'for phase_one in (false, true), interruption in (:logger, :callback, :deadline)' in atomic,
 'trial_refactor_event_before_reconstruction':recompute.index('_simplex_event!(workspace, diagnostic_reason)')<recompute.index('rhs = workspace.scratch.row_rhs',recompute.index('function recompute!')),
}
excerpts={
 'handoff':('src/dual_simplex.jl',handoff),
 'auxiliary':('src/dual_simplex.jl',s[s.index('function _auxiliary_workspace'):s.index('function _classify_recession!')]),
 'candidate_publication_helpers':('src/simplex_pivot.jl',pivot[:pivot.index('function _prepare_primal_candidate!')]),
 'phase_reset':('src/simplex_pricing.jl',pricing[pricing.index('function _reset_auto_pricing!'):pricing.index('"""Carry a safe rule')]),
 'diagnostic_wrapper':('src/simplex_diagnostics.jl',diagnostics[diagnostics.index('struct DiagnosticObserverFailure'):]),
 'existing_adaptive_test':('test/adaptive_pricing_lifecycle_tests.jl',adaptive)}
(J/'excerpts').mkdir()
excerptrows=[]
for name,(file,text) in excerpts.items():
 p=J/'excerpts'/(name+'.txt');p.write_text(text);paths.add(p);full=(R/file).read_text();excerptrows.append({'name':name,'file':file,'start_line':full[:full.index(text)].count('\n')+1,'sha256':sha(p)})
for name in ('S5-INVENTORY-NOTES.md','S5-RESTORATION.md','S5-RESTORATION-REVIEW.md','S5-COPIES.md','S5-COPIES-REVIEW.md','S4-POSTSOLVE-DUAL-WORK-CONTRACT.md','S4-POSTSOLVE-DUAL-WORK-CONTRACT-REVIEW.md','S5-PRECISION-JOURNAL-INTERRUPTION-TEST-INTEGRATION.md','S5-PRECISION-JOURNAL-INTERRUPTION-TEST-INTEGRATION-REVIEW.md'):paths.add(D/name)
I=J.parent/'S5-I';paths.update([I/'closure.json',I/'master-review.md',I/'green-review.md',I/'master-1/pins.json',I/'master-1-audit.json',I/'master-1-independent.json'])
paths.add(R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-handoff-ownership.md')
prior=json.loads((I/'master-1/pins.json').read_text())['inventory'];paths.update(Path(p) for p in prior if p.endswith('.so') or '/bin/julia' in p)
paths.update(map(Path,json.loads((J/'host-before.json').read_text())['user_hashes']))
x={'checks':checks,'all_passed':all(checks.values()),'time_ns':time.time_ns(),'rows':rows,'test_block_comparisons':comparisons,'source_comparisons':sourcecomparisons,'excerpts':excerptrows,'sha256':{str(p):sha(p) for p in sorted(paths)},'scope':'Source/evidence only; existing interrupted private trial is covered, post-publication pending observer throw remains unqualified by inspected evidence. No new numerical call.'}
with (J/'evidence.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'all_passed':x['all_passed'],'pins':len(paths),'source_equal':sum(y['equal'] for y in sourcecomparisons),'source_total':len(sourcecomparisons)}));raise SystemExit(0 if x['all_passed'] else 1)
