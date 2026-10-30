from pathlib import Path
import hashlib,json,subprocess
D=Path(__file__).resolve().parent;W=D.parents[2];P=W/'diagnostics/dual-recovery-devex-task2/2026-10-30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def req(v,m):
 if not v:raise RuntimeError(m)
b=json.loads((D/'build.json').read_text());s=(D/'simplex_recovery.jl').read_text();restored=s
for a,new in reversed(b['recovery_changes']):
 req(restored.count(new)==1,'inverse anchor');restored=restored.replace(new,a)
pivot=(D/'simplex_pivot.jl').read_text();a,new=b['pivot_change'];pins=json.loads((D/'source-pins.json').read_text())
checks={'recovery_exact_Task2_inverse':restored==(P/'simplex_recovery.jl').read_text(),'numerics_byte_identical_Task2':(D/'simplex_numerics.jl').read_bytes()==(P/'simplex_numerics.jl').read_bytes(),'pivot_exact_master_inverse':pivot.replace(new,a)==(W/'src/simplex_pivot.jl').read_text(),'single_existing_opt_in':pivot.count(new)==1,'tests_first_snapshot':sha(D/'recovery_devex_fallback_tests.before-static-refinement.jl')==b['tests_first_sha256'],'all81_readtime_pins':len(pins['bindings'])==81 and all(sha(Path(n))==h for n,h in pins['bindings'].items()),'Task2_parents_preserved':all(sha(Path(n))==h for n,h in b['parent_sources'].items())}
# Inspect only the publication delta for callback-free, post-adoption records.
pub=s.split('function _publish_recovery!(ws,trial,reason,stop;',1)[1].split('\nend\n',1)[0]
checks['same_observer_order']=pub.index(':pricing_reset,trial')<pub.index('reason,trial')<pub.index(':checkpoint,trial')<pub.index('stop() && return false')<pub.index('_copy_pivot_state!')
checks['commit_only_pricing_records']=pub.index('ws.factorization = trial.factorization')<pub.index('_store_basis_checkpoint!')<pub.index(':pricing_weight_rejected')<pub.index(':pricing_devex')
checks['two_new_records_no_observers']=pub.count('_recovery_observer!')==3 and pub.count('_record_recovery!')==5
constructor=s.split('function _recovery_trial_with_pricing',1)[1].split('\nend\n',1)[0]
checks['single_factory_boundary']=constructor.count('build_factor(B,ws.options)')==1 and constructor.count('ws.refactorizations += 1')==1
checks['single_recompute']=constructor.count('recompute!(trial;caller_guard=stop)')==1
checks['one_fallback_post_stop']=constructor.split('if !weights.ok',1)[1].split('return _RecoveryTrialResult(trial,true',1)[0].count('stop()')==1
checks['core_revalidation_before_reset']=constructor.index('stop() && return nothing',constructor.index('if !weights.ok'))<constructor.index('_finite_workspace(trial)',constructor.index('if !weights.ok'))<constructor.index('_prepare_recovery_devex!')
checks['rho_buffer_distinct_by_source']='C(zeros(T,m),zeros(T,m),zeros(T,m),zeros(T,m),zeros(Int,m)' in (W/'src/simplex_pivot.jl').read_text()
checks['repair_restore_explicit_forwarding']='restore_checkpoint!(ws,checkpoint,guard;algorithm)' in s and '_repair_basis!(ws,policy,guard,original;algorithm)' in s
checks['source_only_report']='UNEXECUTED' in (D/'REPORT.md').read_text()
checks['production_src_test_unchanged']=not subprocess.check_output(['git','-C',str(W),'diff','HEAD','--','src','test','Project.toml','.github'],text=True).strip()
bindings=dict(pins['bindings']);bindings.update({str(p):sha(p) for p in D.iterdir() if p.is_file() and p.name!='source-check.json'})
r=dict(accepted=all(checks.values()),scope='Task3 source inverse/prospective tests only; no Julia',checks=checks,bindings=bindings)
with (D/'source-check.json').open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
print(json.dumps(dict(accepted=r['accepted'],checks=checks,bindings=len(bindings))))
req(r['accepted'],'source check failed')
