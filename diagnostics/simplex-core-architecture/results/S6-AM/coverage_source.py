"""New source-only S6-AM coverage map; exclusive output, not a numerical runner."""
from pathlib import Path
import re,json,hashlib,subprocess,tomllib,shutil
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=r/'diagnostics/simplex-core-architecture';o=d/'results/S6-AM';o.mkdir()
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def block(file,title):
 text=(r/file).read_text();start=text.index('@testset "'+title+'"');nextset=text.find('\n@testset ',start+1);end=len(text) if nextset<0 else nextset+1
 value=text[start:end];return {'file':file,'title':title,'line':text[:start].count('\n')+1,'source':value,'sha256':hashlib.sha256(value.encode()).hexdigest(),'lexical_test_statements':len(re.findall(r'@test(?:_throws)?\b',value))}
specs=[
 ('bound_cancel','test/primal_perturbation_integration_tests.jl','Primal bound cleanup honors cancellation and auxiliary isolation','native arithmetic/adaptive setup policy','active bound journal; stop after phase_cleanup, hence already retired','callback event predicate','TIME_LIMIT, original bounds, journal absent, work equals budget; no explicit payload or kernel oracle'),
 ('bound_iter','test/primal_perturbation_integration_tests.jl','Primal perturbation shares the completed-step budget and exact branch','native arithmetic/adaptive setup policy','active bound journal remains on ITERATION_LIMIT; separate rational branch unperturbed','iteration limit, not deadline','ITERATION_LIMIT, iteration=budget=2, perturbation1/cleanup0, bounds active; no payload or kernel assertion'),
 ('driver_zero','test/simplex_driver_tests.jl','Driver honors zero remaining iterations and an expired clock','checked/adaptive','no journal created by fixture','time_limit=0 or iteration_limit=0','status and zero iterations only; no journal/payload/kernel invariant'),
 ('driver_cancel','test/simplex_driver_tests.jl','Auxiliary phases respect cancellation and preserve user errors','checked/adaptive','no owned active-bound journal in caller fixture; auxiliary phase entered','callback return/throw after phase_auxiliary','phase entered, TIME_LIMIT or same ZeroPivotException, work synchronized; no journal/payload assertion'),
 ('driver_shared_work','test/simplex_driver_tests.jl','A shared budget cannot be replenished by a fresh workspace','checked/adaptive','no journal in either starting fixture','iteration budget across workspaces','first OPTIMAL, consumed1; second ITERATION_LIMIT, total2; no finite-time expiry assertion'),
 ('driver_inner_clock','test/simplex_driver_tests.jl','Replacement workspaces pass the shared deadline to inner solves','checked/adaptive','no journal in either starting fixture','observer reads _basis_solve_stop; existing budget assigned120','two algorithms; OPTIMAL, nonempty clocks, inherited start/limit, options identity; no actual expiry or active journal'),
 ('native_private','test/native_cleanup_recovery_tests.jl','Native cleanup keeps rejected and interrupted corrections private','native arithmetic/legacy','no perturbation journal; direct private recompute helper','callback true/throw at third callback, or bad factor/dual','false or same SingularException, selected state unchanged, iterations0; NOT a real clock test or public run_from_basis entry'),
 ('native_success','test/primal_perturbation_integration_tests.jl','Native cleanup retires an owned bound journal after heuristics are disabled','adaptive setup replaced with native default','owned active bounds then successful retirement','false callback; real finite30s option','six original predicates; AL actual run captures7/7 including helper, under deadline; not interruption coverage'),
 ('bound_recovery','test/primal_perturbation_tests.jl','Basis recovery preserves active bound ownership and cooldown','native arithmetic/adaptive perturbation policy','same bound journal and buffer aliases retained','false callback to restore_checkpoint!','identity/active values/cooldown/level; checkpoint restoration, not public entry cancellation'),
 ('cost_cancel','test/simplex_perturbation_integration_tests.jl','Original-cost cleanup shares the completed-step and time budgets','checked/adaptive helper (verify source)','cost journal, not expanded bound journal','iteration limit then callback after phase_cleanup','ITERATION_LIMIT2 or TIME_LIMIT3, retired cost journal/zero costs; not native active-bound entry')]
rows=[]
for key,file,title,policy,journal,trigger,scope in specs:
 x=block(file,title);x.update(id=key,policy=policy,journal=journal,trigger=trigger,asserted_scope=scope);rows.append(x)
# Bind reuse by both executed-file list and source hash, never by pin presence alone.
b=r/'.superpowers/simplex-core-architecture/S5-C/focused-1';pins=json.loads((b/'pins.json').read_text());executed=tomllib.loads((b/'reference.toml').read_text())['files'];sp=json.loads((b/'process.json').read_text())
for x in rows:
 path=r/x['file'];x['S5C_source_matches']=h(path)==pins['inventory'][str(path)]['sha256'];x['S5C_executed_file']=path.name in executed;x['evidence']='S5-C focused1463 aggregate, exact executed source; no per-case new run' if x['S5C_source_matches'] and x['S5C_executed_file'] else 'source-only in AM; S5-C pin alone is not executed coverage'
rows_by={x['id']:x for x in rows};sources={p:(r/p).read_text() for p in sorted({x['file'] for x in rows})}
# Review exact helper profile, including the cost-only comparator.
cost=sources['test/simplex_perturbation_integration_tests.jl'];cidx=cost.index('function perturbation_chain_workspace');cend=cost.index('\nend',cidx)+4;costhelper=cost[cidx:cend]
rows_by['cost_cancel']['policy']='checked/adaptive' if 'numerical_profile=:checked' in costhelper else 'native arithmetic/adaptive'
al=json.loads((d/'results/S6-AL/provenance-1-audit.json').read_text());ak=json.loads((d/'results/S6-AK/analysis.json').read_text())
target=rows_by['native_success']['source'];stored=(d/'results/S6-AL/original-target.jl.txt').read_text();helper=(d/'results/S6-AL/shifted_primal_workspace.jl.txt').read_text();native=sources['test/primal_perturbation_integration_tests.jl'];monitor=(d/'results/S6-AL/primal_stalled_monitor.jl.txt').read_text()
prod=(r/'src/simplex_driver.jl').read_text();dual=(r/'src/dual_simplex.jl').read_text();private=(r/'src/native_cleanup_recovery.jl').read_text();oldmatches={ref:subprocess.check_output(['git','show',ref+':test/primal_perturbation_integration_tests.jl'],cwd=r)==(r/'test/primal_perturbation_integration_tests.jl').read_bytes() for ref in ['4914cbb','b720674']}
users=json.loads((d/'results/S6-AL/preflight.json').read_text())['user_hashes'];tracked=subprocess.check_output(['git','ls-files','src','test','.github'],cwd=r,text=True).splitlines()
checks={
 'refs_at_expected':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()=='3d57291e5e62c3bf7a4a316fe3841315e9437feb' and subprocess.check_output(['git','rev-parse','master'],cwd=r,text=True).strip()=='354bb1f9ebd84075c8b0de5145b0f69d2b282745',
 'source_test_CI_master':not subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=r),
 'target_helper_matches_AL':target==stored and helper in native and monitor in sources['test/primal_perturbation_tests.jl'],
 'native_test_both_historical':all(oldmatches.values()),
 'AL_accepted_but_not_historical':al['all_passed'] and len(al['checks'])==31 and al['intervals']['driver']['after_elapsed_ns']==16137016355,
 'AK_inference_preserved':'No captured run.status/message' in ak['scope'] and ak['start_ns_alone_is_not_elapsed'],
 'S5C_normal_exit':sp['returncode']==0 and sp['reason']=='exit0',
 'S5C_aggregate1463':bool(re.search(r'\|\s+1463\s+1463\s',(b/'run.log').read_text())),
 'all_mapped_S5C_source_hashes':all(x['S5C_source_matches'] for x in rows),
 'S5C_excludes_driver_private':not rows_by['driver_zero']['S5C_executed_file'] and not rows_by['native_private']['S5C_executed_file'],
 'checked_helper_explicit':'numerical_profile=:checked' in sources['test/simplex_driver_tests.jl'].split('using SparseArrays')[0],
 'bound_stop_after_cleanup':'stop=()->JSimplex.event_count(ws.progress.diagnostics,:phase_cleanup)>0' in rows_by['bound_cancel']['source'],
 'bound_retained_at_iteration_limit':'ws.scratch.perturbations.bounds.active' in rows_by['bound_iter']['source'] and 'run.status==ITERATION_LIMIT' in rows_by['bound_iter']['source'],
 'private_deadline_is_callback':'calls[] == 3' in rows_by['native_private']['source'] and 'interruption == :deadline && return true' in rows_by['native_private']['source'],
 'native_success_no_interrupt':'()->false' in target and 'TIME_LIMIT' not in target,
 'first_forced_guard_before_verify':prod.index('guarded() && return DualTermination(TIME_LIMIT')<prod.index('verified = try'),
 'deadline_shortcircuits_callback':'_budget_expired(budget) || stop()' in prod,
 'callback_exception_identity_rethrown':'exception === guarded.exception' in prod and 'stop.exception = exception' in dual,
 'finally_sync_restore_options':'finally\n        _sync_run_budget!(budget,ws)\n        ws.options = original_options' in prod,
 'nonoptimal_payload_absent':'primal = status == OPTIMAL ?' in dual and 'basis = status == OPTIMAL ?' in dual,
 'users_preserved':all(h(Path(k))==v for k,v in users.items())}
evidence=[d/'results/S6-AL/provenance-1-audit.json',d/'results/S6-AL/provenance-1-report.toml',d/'results/S6-AL/original-target.jl.txt',d/'results/S6-AK/analysis.json',d/'results/S6-AJ/coverage.json',b/'pins.json',b/'process.json',b/'reference.toml',b/'run.log']
# AJ's actual final filename is discovered read-only if the conventional one differs.
if not evidence[4].exists():evidence.pop(4)
inputs={str(r/f):h(r/f) for f in tracked};inputs.update({str(p):h(p) for p in evidence});inputs.update(users)
result={'checks':checks,'all_passed':all(checks.values()),'records':rows,'historical_matches':oldmatches,'tracked_count':len(tracked),'S5C_executed_files':executed,'input_hash_count':len(inputs),'classification_scope':'Manual source classification of ten named testsets; lexical assertion statements are not runtime counts and loop cases are not added to historical failures. No claim of universal absence in all tests or of matched timing counterfactuals.','decision':'Qualify two new native active-bound-journal public entry interruptions (callback true and identity-preserved callback exception), with no successful-control rerun. This is a coverage gap, not a historical timeout repair.'}
with (o/'coverage.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
with (o/'input-hashes.json').open('x') as f:json.dump(inputs,f,indent=2);f.write('\n')
shutil.copyfile('/tmp/s6-am-host.json',o/'host.json');shutil.copyfile(__file__,o/'coverage_source.py')
print(json.dumps({'checks':checks,'all_passed':result['all_passed'],'records':len(rows),'input_hashes':len(inputs),'cost_policy':rows_by['cost_cancel']['policy']},indent=2));assert result['all_passed']
