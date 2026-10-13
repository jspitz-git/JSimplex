"""Exclusive S5-P textual source/evidence collection; no Julia or old script execution."""
from pathlib import Path
import hashlib,json,re,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';P=D/'results/S5-P';O=P.parent/'S5-O'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def text(p):return (R/p).read_text()
files=['src/simplex_start.jl','src/simplex.jl','src/simplex_recovery.jl','src/simplex_driver.jl','src/dual_simplex.jl','src/simplex_numerics.jl','src/options.jl','src/simplex_pricing.jl','src/simplex_diagnostics.jl','src/simplex_refactorization.jl','src/hypersparse_pipeline.jl','src/simplex_perturbation.jl']
# Discovery is textual; two isdefined references are classified separately from calls.
hits=[];paths={Path(__file__).resolve(),P/'host-before.json',P/'host-check-1-failure.json',R/'AGENTS.md'}
for tree in ['src','test','dev']:
 for p in sorted((R/tree).rglob('*.jl')):
  lines=p.read_text().splitlines()
  for i,line in enumerate(lines):
   if 'initialize_from_basis' in line:
    hits.append(dict(file=str(p.relative_to(R)),line=i+1,text=line,context='\n'.join(lines[max(0,i-2):i+5]),kind='definition' if line.startswith('function initialize_from_basis') else 'isdefined' if 'isdefined' in line else 'call'))
    paths.add(p)
rows=[];comparisons=[];sourcecomparisons=[]
names={
'Crash produces an owned feasible structural diagonal basis':('test/simplex_start_tests.jl',360,'direct'),
'Crash chooses legal objective-aware nonbasic states':('test/simplex_start_tests.jl',7,'direct'),
'Crash guards dependent columns and zero columns':('test/simplex_start_tests.jl',5,'direct'),
'Crash consumes the existing clock and completed-step budget':('test/simplex_start_tests.jl',12,'adjacent crash/solver; not initializer stop'),
'Imported start rejects singular bases and illegal nonbasic bounds':('test/simplex_start_guard_tests.jl',3,'direct'),
'Crash preserves stored BigFloat precision below ambient precision':('test/simplex_start_guard_tests.jl',4,'direct'),
'Crash respects fixed, upper-only and free variables with rows':('test/simplex_start_state_tests.jl',6,'direct'),
'Crash handles the empty model':('test/simplex_start_state_tests.jl',3,'direct')}
for run in ['38142752357','38149970679']:
 meta=D/f'results/S6-A/ci-inventory-1-{run}-metadata.json';md=json.loads(meta.read_text());log=R/f'.superpowers/simplex-core-architecture/S6-A/ci-inventory-1/{run}-failed.log';paths.update((meta,log));lines=log.read_text().splitlines()
 for name,(file,count,scope) in names.items():
  found=[(i+1,l) for i,l in enumerate(lines) if name in l and '|' in l];assert len(found)==1
  no,raw=found[0];clean=re.sub(r'(?:\x1b|\^\[)\[[0-9;]*m','',raw);assert clean.split('|',1)[1].split()[:2]==[str(count)]*2
  rows.append(dict(run=run,head=md['headSha'],conclusion=md['conclusion'],name=name,file=file,passed=count,total=count,line=no,raw=raw,normalized=clean,scope=scope))
  old=subprocess.check_output(['git','show',md['headSha']+':'+file]);current=(R/file).read_bytes()
  # Whole-file equality is stronger than extracting possibly nested testsets.
  comparisons.append(dict(run=run,file=file,name=name,whole_file_equal=old==current,historical_sha256=hashlib.sha256(old).hexdigest(),current_sha256=sha(R/file)))
  paths.add(R/file)
 for file in files:
  old=subprocess.check_output(['git','show',md['headSha']+':'+file]);sourcecomparisons.append(dict(run=run,file=file,equal=old==(R/file).read_bytes(),historical_sha256=hashlib.sha256(old).hexdigest(),current_sha256=sha(R/file)))
s=text('src/simplex_start.jl');a=s[s.index('function initialize_from_basis'):s.index('\n_crash_numerical_exception')];j=text('src/simplex.jl');r=text('src/simplex_recovery.jl');n=text('src/simplex_numerics.jl');d=text('src/simplex_driver.jl');du=text('src/dual_simplex.jl')
checks={
 'only_production_definition':sum(x['file'].startswith('src/') for x in hits)==1,
 'all_16_CI_rows':len(rows)==16,
 '400_each_failed_run':all(sum(x['passed'] for x in rows if x['run']==q)==400 for q in ['38142752357','38149970679']),
 'all_16_whole_test_files_equal':all(x['whole_file_equal'] for x in comparisons),
 'default_before_policy_before_basis':a.index('initialize_workspace(problem,options;progress)')<a.index('_install_driver_policy!(ws,policy)')<a.index('ws.basis = Basis('),
 'copied_basis_validated_before_bounds':a.index('_validate_basis(ws)')<a.index('for j in eachindex(ws.basis.states)'),
 'bound_validation_before_invalidate_recompute':a.index('_nonbasic_value(ws,j)')<a.index('_invalidate_basis_checkpoints!(ws)')<a.index('recompute!(ws;refactorize=true,caller_guard=guard)'),
 'finite_shortcircuit_quality_before_reset':'_finite_workspace(ws) && _recomputed_basis_reliable(ws)' in a and a.index('_recomputed_basis_reliable(ws)')<a.index('reset_devex!(ws)'),
 'no_explicit_top_stop_or_deadline':'guard()' not in a and '_start_time_expired' not in a,
 'basis_two_copy_expressions':'new(Int.(basic_indices), collect(states))' in j,
 'problem_shared_default':'problem, typed_options, progress, costs, lower, upper, basis' in j,
 'bounds_owned_vcat':'lower = vcat(problem.column_lower, problem.row_lower)' in j and 'upper = vcat(problem.column_upper, problem.row_upper)' in j,
 'default_reconstruction_before_initial_event':'recompute!(workspace)\n    _simplex_event!(workspace, :refactor_initial)' in j,
 'policy_preserves_clock_offsets_shared_diagnostics':'p.iteration_offset,p.refactorization_offset,p.diagnostics,policy)' in d,
 'native_profile_default':'numerical_profile::Symbol=:native' in n and 'solve_refinement::Bool=(numerical_profile == :checked)' in n and 'recovery::Bool=(numerical_profile == :checked)' in n,
 'solve_before_optional_refinement':r.index('_pipeline_basis_solve!(destination,ws,rhs;',r.index('function _checked_basis_solve!'))<r.index('_maybe_refine_basis_solve!(destination,ws,rhs,stop;transposed) || throw'),
 'native_refinement_bypasses_stop':'policy.solve_refinement || return true' in r,
 'checkpoint_two_stops':'stop() && return false\n    _recomputed_basis_reliable(ws)' in r and '_recovery_observer!(ws.progress.diagnostics,:checkpoint,ws)\n    stop() && return false' in r,
 'final_quality_two_shortcircuited_entries':'solve_quality!(scratch,B,ws.primal[ws.basis.basic_indices],rhs,policy).reliable || return false' in r,
 'BigFloat_stored_precision_scan':'maximum(precision,problem.A.nzval;init=2)' in s and 'maximum(precision,problem.objective;init=2)' in s and 'return setprecision(f,BigFloat,bits)' in s,
 'callback_cause_rethrown':'stop.exception = exception\n        rethrow()' in du,
 'checkpoint_owns_five_vectors':'BasisCheckpoint(Basis(ws.basis.basic_indices,ws.basis.states),\n        copy(ws.costs),copy(ws.lower),copy(ws.upper)' in r,
}
paths.update(R/f for f in files)
excerpts={'initializer':('src/simplex_start.jl',s[:s.index('\n_crash_numerical_exception')]),'initialization':('src/simplex.jl',j[j.index('function _initialize_workspace_state'):j.index('function primal_infeasibility_summary')]),'recompute':('src/simplex.jl',j[j.index('function recompute!'):j.index('function _initialize_workspace_state')]),'quality':('src/simplex_recovery.jl',r[r.index('function _basis_primal_rhs'):r.index('function _publish_recovery!')]),'checkpoint':('src/simplex_recovery.jl',r[r.index('function _remember_verified_basis!'):r.index('function _sync_recovery_rejections!')]),'checked_solve':('src/simplex_recovery.jl',r[r.index('struct _BasisSolveClock'):r.index('# Precision-specialized repair')])}
(P/'excerpts').mkdir();er=[]
for name,(file,value) in excerpts.items():
 p=P/'excerpts'/(name+'.txt');p.write_text(value);paths.add(p);er.append(dict(file=file,start_line=text(file)[:text(file).index(value)].count('\n')+1,path=str(p),sha256=sha(p)))
for name in ['S5-INVENTORY-NOTES.md','S5-RESTORATION.md','S5-DUAL-AUXILIARY-PENDING-OBSERVER-TEST-INTEGRATION.md','S5-DUAL-AUXILIARY-PENDING-OBSERVER-TEST-INTEGRATION-REVIEW.md']:paths.add(D/name)
for p in O.iterdir():
 if p.is_file() and p.suffix in ['.json','.md']:paths.add(p)
for run in ['green-1','master-1']:
 for p in (O/run).rglob('*'):
  if p.is_file():paths.add(p)
paths.add(R/'docs/superpowers/plans/2026-10-13-basis-initialization-handoff-contract.md')
for p in json.loads((O/'master-1/pins.json').read_text())['inventory']:
 if p.endswith('.so') or '/bin/julia' in p:paths.add(Path(p))
paths.update(map(Path,json.loads((P/'host-before.json').read_text())['user_hashes']))
out=dict(checks=checks,all_passed=all(checks.values()),caller_hits=hits,rows=rows,test_comparisons=comparisons,source_comparisons=sourcecomparisons,excerpts=er,sha256={str(p):sha(p) for p in sorted(paths)},time_ns=time.time_ns(),scope='Text/source evidence only, no Julia parsing or execution. At most one unqualified explicit-stop/checked-checkpoint composition; no defect or runtime admission.')
with (P/'evidence.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'pins':len(paths),'hits':len(hits),'source_equal':sum(x['equal'] for x in sourcecomparisons),'source_total':len(sourcecomparisons)}));assert out['all_passed']
