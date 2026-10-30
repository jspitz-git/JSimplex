from pathlib import Path
import hashlib,json,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/dual-recovery-devex-task3/2026-10-30';P=W/'diagnostics/dual-recovery-devex-task2/2026-10-30'
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *a:subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
source=json.loads((D/'source-check.json').read_text());pins=json.loads((D/'source-pins.json').read_text());build=json.loads((D/'build.json').read_text());checks={}
checks['preserved_source_record_18_checks']=len(source['checks'])==18 and all(source['checks'].values()) and source['accepted']
checks['preserved_source_record_94_bindings']=len(source['bindings'])==94 and all(Path(p).is_file() and sha(Path(p))==h for p,h in source['bindings'].items())
checks['all_81_initial_source_pins_match']=len(pins['bindings'])==81 and all(sha(Path(p))==h for p,h in pins['bindings'].items())
checks['head_matches_accepted_task2']=git('rev-parse','HEAD')=='1509f43f9a288bfa5b3ae004e0e9f07b560b5469'
checks['master_and_remote_tracking_match']=all(git('rev-parse',r)=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b' for r in ('master','origin/master'))
checks['actual_production_and_test_tracked_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
checks['all_71_production_files_match_master']=len(list((W/'src').rglob('*.jl')))==71 and all(p.read_bytes()==subprocess.check_output(['git','-C',str(W),'show','master:'+str(p.relative_to(W))]) for p in (W/'src').rglob('*.jl'))
s=(D/'simplex_recovery.jl').read_text();inverse=s
for old,new in reversed(build['recovery_changes']):
 assert inverse.count(new)==1, ('nonunique inverse',new)
 inverse=inverse.replace(new,old)
checks['all_12_recovery_changes_inverse_to_task2']=len(build['recovery_changes'])==12 and inverse==(P/'simplex_recovery.jl').read_text()
checks['numerics_byte_identical_task2']=(D/'simplex_numerics.jl').read_bytes()==(P/'simplex_numerics.jl').read_bytes()
pivot=(D/'simplex_pivot.jl').read_text();old,new=build['pivot_change']
checks['sole_pivot_opt_in_inverse_to_actual_source']=pivot.count(new)==1 and pivot.replace(new,old)==(W/'src/simplex_pivot.jl').read_text()
checks['task2_review_accepted']=json.loads((P/'review-final.json').read_text())['accepted']
checks['test_first_snapshot_preserved']=sha(D/'recovery_devex_fallback_tests.before-static-refinement.jl')==build['tests_first_sha256']
constructor=s.split('function _recovery_trial_with_pricing',1)[1].split('\nend\n',1)[0]
checks['constructor_one_recompute_factor_charge']=constructor.count('recompute!(trial;caller_guard=stop)')==constructor.count('build_factor(B,ws.options)')==constructor.count('ws.refactorizations += 1')==1
fallback=constructor.split('if !weights.ok',1)[1].split('return _RecoveryTrialResult(trial,true',1)[0]
checks['one_post_classification_stop']=fallback.count('stop()')==1
checks['fallback_core_checks_precede_preparation']=fallback.index('stop()')<fallback.index('_finite_workspace(trial)')<fallback.index('_recomputed_basis_reliable(trial)')<fallback.index('_prepare_recovery_devex!(trial)')
checks['fallback_post_stop_scope_recheck_missing']='_recovery_weight_scope' not in fallback
checks['actual_route_through_restore']=all(t in s for t in ('_repair_basis!(ws,policy,guard,original;algorithm)','_recovery_trial_with_pricing(ws,candidate,guard;algorithm)','restore_checkpoint!(ws,checkpoint,guard;algorithm)','_recovery_trial_with_pricing(ws,c,guard;algorithm)'))
pub=s.split('function _publish_recovery!(ws,trial,reason,stop;',1)[1].split('\nend\n',1)[0]
order=[':pricing_reset,trial','reason,trial',':checkpoint,trial','stop() && return false','_copy_pivot_state!','ws.factorization = trial.factorization','_store_basis_checkpoint!',':pricing_weight_rejected',':pricing_devex']
checks['unchanged_observer_then_adoption_then_new_record_order']=all(pub.index(a)<pub.index(b) for a,b in zip(order,order[1:]))
checks['no_new_publisher_callbacks']=pub.count('_recovery_observer!')==3 and pub.count('_record_recovery!')==5 and '_simplex_event!' not in pub
checks['strict_legacy_weight_wrapper']='_rebuild_recovery_weights_result!(trial,stop).ok' in s
checks['tests_private_factor_not_production_override']='mutable struct RecoveryFactor{T,F}' in (D/'recovery_devex_fallback_tests.jl').read_text() and 'build_factor' not in s.split('function repair_basis!',1)[1]
checks['feasibility_and_precision_do_not_opt_in']='repair_basis!(workspace,policy,guard)' in (W/'src/simplex_driver.jl').read_text() and '_rebuild_recovery_weights!(trial,guard)' in (W/'src/simplex_precision_recovery.jl').read_text()
bindings=dict(source['bindings']);bindings[str(D/'source-check.json')]=sha(D/'source-check.json');bindings[str(Path(__file__))]=sha(Path(__file__))
result={'scope':'New independent byte/source checks only; no Julia and no existing script rerun','checks':checks,'bindings':bindings,'all_source_checks_passed':all(checks.values())}
Path('/tmp/devex-task3-independent-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'checks':checks,'bindings':len(bindings),'all_source_checks_passed':all(checks.values())},indent=2))
