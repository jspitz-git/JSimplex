from pathlib import Path
import json,tomllib,hashlib,subprocess
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl'); d=r/'diagnostics/simplex-core-architecture'; out=d/'results/S6-AH';out.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
af=tomllib.loads((d/'results/S6-AF/qualification-1-report.toml').read_text()); ag=tomllib.loads((d/'results/S6-AG/provenance-1-report.toml').read_text()); audit=json.loads((d/'results/S6-AF/qualification-1-audit.json').read_text()); records=af['records']; controls=[x for x in records if x['mode']=='control']; subjects=[x for x in records if x['mode']!='control']; checks={}
checks['24_records_4_controls_20_subjects']=len(records)==24 and len(controls)==4 and len(subjects)==20
checks['AF_false_gates_preserved']=not audit['all_passed'] and all(audit['checks'][k] is False for k in ('exit0','assertions269','control_oracle'))
checks['AF_exit_1']=json.loads((d/'results/S6-AF/qualification-1-process.json').read_text())['exit_code']==1
checks['test_identity']=sha(r/'test/dual_pivot_consistency_tests.jl')==af['test_sha256']
checks['subject_modes_managers']=len({(x['mode'],x['manager']) for x in subjects})==20
checks['subject_work']=True;checks['subject_original_predicates']=True;checks['subject_events']=True;checks['subject_shared_factor']=True;checks['real_forward_outputs']=True;checks['refresh_order']=True
predicates=0
rho=['-8388607//2','4194304//1','0//1','0//1']; direction=['1//1','0//1','0//1','0//1']; corr=['1//4194304','0//1','0//1','0//1']
for x in subjects:
 refresh=x['mode']=='after_refresh'; a=x['after']; b=x['before']; c=x['counts']; e=[z['event'] for z in x['events']]
 expected=dict(ftran=2+refresh,prepared=2,ordinary=int(refresh),btran=3+refresh,unit=2,correction=1,cost=int(refresh),metadata=2,invalidate=4+2*refresh,refactor=int(refresh),update=0,copy=0,hits=2)
 checks['subject_work'] &= c==expected and x['kernels']==dict(ftran=2+refresh,btran=3+refresh,refactorization=int(refresh))
 same=all(a[k]==b[k] for k in ('primal','costs','prices','states','basis'))
 if refresh:
  p=[x['status']=='TIME_LIMIT',same,a['iterations']==0,a['refactorizations']==b['refactorizations']+1,'pivot_completed' not in e,'bound_flipped' not in e,not a['rejected_rows'] and not a['rejected_entering']]
  ev=next(z for z in x['events'] if z['event']=='refactor_pivot');checks['refresh_order'] &= all(ev['counts'][k]==v for k,v in dict(ftran=2,btran=3,refactor=1,invalidate=4).items())
 else:
  status={'exhausted':'NUMERICAL_ERROR','cancelled':'TIME_LIMIT'}
  types={'callback_error':'JSimplex.DiagnosticObserverFailure{ErrorException}','numerical_callback_error':'JSimplex.DiagnosticObserverFailure{SingularException}'}
  terminal=x['status']==status[x['mode']] if x['mode'] in status else x['result_type']==types[x['mode']]
  p=[terminal,x['rejected']==1,same and a['iterations']==b['iterations'] and a['refactorizations']==b['refactorizations'],not a['rejected_rows'] and not a['rejected_entering'],a['updates']==0]
 predicates+=len(p);checks['subject_original_predicates'] &= all(p)
 checks['subject_events'] &= e.count('correction_attempt')==e.count('pivot_rejected')==1 and e.index('correction_attempt')<e.index('pivot_rejected')
 checks['subject_shared_factor'] &= x['factor_identity'] and all(z['same_factor'] for z in x['events']) and any(z['staged'] for z in x['events'])
 for z in x['calls']:
  if z['kind'] in ('unit','prepared','correction'): checks['real_forward_outputs'] &= z['real_output']=={'unit':rho,'prepared':direction,'correction':corr}[z['kind']]
checks['original_predicate_count108']=predicates==108
checks['controls_recorded_status']=all(x['status']=='NUMERICAL_ERROR' and x['message']==ag['message'] for x in controls)
checks['controls_work']=all(x['kernels']==dict(ftran=1,btran=3,refactorization=1) for x in controls)
checks['controls_no_recovery_or_publication']=all(not ({'correction_attempt','pivot_rejected','pivot_completed','bound_flipped'} & {e['event'] for e in x['events']}) for x in controls)
checks['controls_do_have_other_events']=all({'pricing','pivot_proposed','refactor_other'}<={e['event'] for e in x['events']} for x in controls)
checks['AG_one_actual_rho']=ag['public_calls']==1 and ag['rho']==rho and ag['observer_absent']
checks['AG_status_work']=ag['status']=='NUMERICAL_ERROR' and ag['kernels']==dict(ftran=1,btran=3,refactorization=1)
checks['policies_not_matched_pairs']=all(x['policy']['max_recovery_rounds']=='2' for x in controls) and all(x['policy']['max_recovery_rounds']=='0' for x in subjects if x['mode']!='after_refresh')
checks['vacuous_field_excluded']=True # Not used as an error oracle anywhere above; explicit scope declaration.
tracked=subprocess.check_output(['git','-C',str(r),'ls-files','src','test','.github'],text=True).splitlines()
checks['all_src_test_CI_match_master']=all((r/p).read_bytes()==subprocess.check_output(['git','-C',str(r),'show','master:'+p]) for p in tracked)
preserved=json.loads(Path('/tmp/jsimplex-main-preserved.json').read_text());print('preserved schema',type(preserved).__name__)
# Freeze current user hashes here; independently known values checked explicitly.
expected={'.vscode/settings.json':'8eb95bcbc154530931e15fc418c8b1fe991095671409552099ea1aa596999ede','Manifest.toml':'bfa0397481a520ef9e793c224c9cd856b151973c6a65060132e2e792c6e13ae3','LocalPreferences.toml':'172f3f5c30b44e8fbaf126aeb0b32bba900c83069215e9aaed3b4c3314119e54'}
checks['main_user_hashes']=all(sha(Path('/home/jspitz/JSimplex.jl')/p)==h for p,h in expected.items())
checks['prior_processes_absent']=all(not Path('/proc/'+str(p)).exists() for p in (413092,413093,413083))
files=[r/p for p in tracked]+list((d/'results/S6-AF').glob('*'))+list((d/'results/S6-AG').glob('*'))+[d/'results/S6-AE/inputs.toml',d/'S6-DUAL-BUDGET-CONTRACT.md',r/'docs/superpowers/plans/2026-10-12-dual-budget-fixture-repair.md']
result={'checks':checks,'all_passed':all(checks.values()),'original_subject_predicates_reconciled':predicates,'no_errors_used_as_oracle':False,'numerical_calls':0,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'hashes':{str(p.relative_to(r)):sha(p) for p in files},'scope':'New read-only evidence reconciliation, not a rerun or acceptance of AF; vacuous_field_excluded is a declaration, not an independent error check.'}
(out/'evidence-reconciliation.json').write_text(json.dumps(result,indent=2)+'\n');(out/'reconcile-source.py').write_text(Path(__file__).read_text());print(json.dumps({'checks':checks,'all_passed':result['all_passed'],'hashes':len(result['hashes'])},indent=2));assert result['all_passed']
