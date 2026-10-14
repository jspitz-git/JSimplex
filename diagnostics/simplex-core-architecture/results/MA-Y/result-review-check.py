"""Independent MA-Y result review. Reads evidence; never loads Julia or old entry points.
Only writes this checker's new exclusive JSON output. No aggregate reducer.
"""
from pathlib import Path
import ast,hashlib,json,math,statistics,subprocess,tomllib
R=Path.cwd();X=R/'diagnostics/simplex-core-architecture/results/MA-X';Y=X.with_name('MA-Y')
checks={};details={}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
def check(k,v):
 checks[k]=bool(v)
 if not v:raise ValueError(k)
def finite(x):return type(x) in (int,float) and math.isfinite(x) and x>=0
pins=rd(X/'pins.json');host=rd(Y/'host.json');post=rd(Y/'posthost.json');summary=rd(Y/'result-summary.json');context=rd(X/'launch-context.json');schedule=rd(X/'schedule.json');fixtures=tomllib.loads((X.with_name('MA-R')/'fixtures.toml').read_text())
check('pins4375_hashes_realpaths',len(pins['inventory'])==4375 and all(sha(p)==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in pins['inventory'].items()))
check('full73tree_membership',len(pins['trees'])==73 and set(pins['inventory'])==set(pins['files'])|{str(p) for tree in pins['trees'] for p in Path(tree).rglob('*') if p.is_file()})
check('required_membership',set(rd(X/'required-paths.json'))==set(pins['inventory']) and len(pins['files'])==len(set(pins['files']))==4375)
check('source514_protected6',len(host['master_identity'])==514 and len(host['protected'])==6 and all(sha(R/p)==v for p,v in host['master_identity'].items()) and all(sha(p)==v for p,v in host['protected'].items()))
for area,names in [(X,['admission-review.json','numerical-review.json']),(Y,['entry.json','seal-check.json','postcheck.json'])]:
 for name in names:
  o=rd(area/name)
  check('bound_'+name,all(sha(p)==v for p,v in o['sha256'].items()))
  check('passed_'+name,o.get('all_passed',o.get('accepted')) is True)
check('seal46checks40bindings',len(rd(X/'numerical-review.json')['computed_checks'])==46 and len(rd(X/'numerical-review.json')['sha256'])==40)
check('postcheck_separate_integrity16',len(rd(Y/'postcheck.json')['checks'])==16 and rd(Y/'postcheck.json')['qualification_accepted'] is False)
check('source_bound_schedule',schedule['costs']==fixtures['cost_cases'] and len(schedule['costs'])==52)
# Reuse ONLY pure raw-schema validators after inspecting their AST. No module top-level or main executes.
tree=ast.parse((X/'audit.py').read_text());names={'require','finite','spec','expected_correctness','validate_raw'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
check('pure_validator_selection',len(nodes)==5)
ns={'D':X,'Path':Path,'tomllib':tomllib,'math':math}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(X/'audit.py')+'[pure-validation-only]','exec'),ns)
all_windows=[];resources=[];failed=[];ranges=[];elapsed=[];raws=[];groups=set(host['groups']);previous_end=0;total=0
for i in (1,2,3):
 out=X/f'run-{i}';raw=tomllib.loads((out/'raw.toml').read_text());raws.append(raw);audit=rd(X/f'audit-{i}.json');inv=rd(X/f'invocation-{i}.json');proc=rd(out/'process.json');res=rd(X/f'reservation-{i}.json');pre=rd(X/f'prelaunch-{i}.json');after=rd(X/f'posthost-{i}.json');current=rd(out/'current.json');sequence=rd(X/'sequence-reservation.json')
 v=ns['validate_raw'](raw,i);check(f'raw_schema_{i}',bool(v) and all(x is True for x in v.values()))
 check(f'audit_raw_bindings_{i}',audit['error'] is None and all(sha(p)==v for p,v in audit['sha256'].items()))
 check(f'raw_loaded_paths_pins_{i}',all(str(Path(p).resolve()) in {v['resolved'] for v in pins['inventory'].values()} for p in raw['loaded_paths'].values()) and rd(out/'pins.json')==pins)
 cmd=rd(X/'commands.json')[str(i)]
 check(f'commands_identity_{i}',proc['command']==res['command']==current['command']==cmd and inv['command'][-len(cmd):]==cmd and proc['cwd']==str(R) and proc['runner']==inv['supervisor']['guard_identity'] and all(proc[k]==current[k] for k in ('runner','child')))
 check(f'reservation_links_{i}',inv['reservation_sha256']==sha(X/f'reservation-{i}.json') and res['pins_sha256']==proc['pins_sha256']==sha(X/'pins.json') and res['review_sha256']==sha(X/'numerical-review.json') and res['context_sha256']==sha(X/'launch-context.json') and res['host_sha256']==sha(X/f'prelaunch-{i}.json') and res['sequence_sha256']==sha(X/'sequence-reservation.json'))
 check(f'serial_process_supervision_{i}',proc['returncode']==inv['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged'] is True and inv['supervisor']['accepted'] is True and inv['supervisor']['returncode']==0 and all(inv['supervisor'][k] is False for k in ('soft_timeout','hard_timeout','child_kill','guard_term','guard_kill')) and 'cleanup_error' not in inv['supervisor'] and proc['started']>=previous_end and pre['time']<=proc['started']<=proc['ended']<=after['time'])
 previous_end=proc['ended'];total+=inv['elapsed_seconds'];elapsed.append(inv['elapsed_seconds'])
 check(f'inclusive_caps_{i}',0<=proc['elapsed_including_launch']<=84 and proc['elapsed_including_launch']<=inv['elapsed_seconds']<=90 and inv['cumulative_seconds']==total<=270 and inv['supervisor']['elapsed_seconds']<=inv['elapsed_seconds'])
 check(f'prehost_full_membership_{i}',set(pre['groups'])==groups and pre['matches']==[] and pre['boot_id']==context['boot_id'] and pre['refs']==context['refs'])
 for who in ('runner','child'):
  ident=proc[who];check(f'{who}_identity_{i}',ident['boot_id']==context['boot_id'] and type(ident['start_ticks'])==int and ident['start_ticks']>0 and ident['pid']==ident['pgid']==ident['sid']>0 and bool(ident['command']));groups.update([ident['pgid'],ident['sid']])
 check(f'posthost_full_membership_{i}',set(after['groups'])==groups and after['matches']==[] and after['boot_id']==context['boot_id'] and after['refs']==context['refs'])
 ss=[json.loads(s) for s in (out/'resources.jsonl').read_text().splitlines()]+[proc['terminal_memory']];resources+=ss
 check(f'resource_samples_{i}',len(ss)>=2 and all(type(s['available_kib'])==type(s['swap_used_kib'])==int and s['available_kib']>=6*1024**2 and 0<=s['swap_used_kib']<=1024**2 for s in ss))
 rows=[];journal=[]
 for ci,(c,fixture) in enumerate(zip(raw['costs'],fixtures['cost_cases']),1):
  check(f'case_{i}_{ci}',c['id']==fixture['id'] and c['eligible'] is fixture['eligible'] and finite(c['bundle_snapshot_setup_seconds']))
  for w in c['windows']:
   location=f"cost/{c['id']}/{w['pair']}/{1 if w['side']=='reference' else 2}"
   journal.extend([dict(kind='whole-metrics',location=location,window={k:v for k,v in w.items() if k not in ('output','preserved')}),dict(kind='whole-complete',location=location,window=w)])
  measured={side:{w['pair']:w for w in c['windows'] if w['phase']=='measured' and w['side']==side} for side in ('reference','candidate')}
  check(f'matched_seven_{i}_{ci}',set(measured['reference'])==set(measured['candidate'])==set(range(4,11)))
  m=statistics.median
  rr=[measured['candidate'][j]['seconds']/measured['reference'][j]['seconds'] for j in range(4,11)]
  row={'id':c['id'],'ratio':m(rr)}
  for side in ('reference','candidate'):
   vals=list(measured[side].values());row[side+'_seconds_per_call']=m(w['seconds']/4 for w in vals)
   for key in ('bytes','events'):row[side+'_'+key]=m(w[key] for w in vals)
  if fixture['eligible']:ok=row['ratio']<1 and all(row['candidate_'+k]<row['reference_'+k] for k in ('bytes','events'))
  else:ok=row['candidate_seconds_per_call']-row['reference_seconds_per_call']<=max(0.10*row['reference_seconds_per_call'],0.4e-6) and all(row['candidate_'+k]<=row['reference_'+k] for k in ('bytes','events'))
  row['pass']=ok;rows.append(row)
  if not ok:failed.append(dict(process=i,**row))
  all_windows+=c['windows']
 check(f'independent_strict_reducers_{i}',rows==audit['process_costs']==summary['processes'][i-1]['cost_rows'])
 check(f'journal2080_exact_{i}',len(journal)==2080 and journal==tomllib.loads((out/'partial-windows.toml').read_text())['records'])
 check(f'audit_decision_{i}',len(audit['checks'])==(27 if i==1 else 25) and {k for k,v in audit['checks'].items() if v is not True}==(set() if i<3 else {'per_process_costs'}) and audit['all_passed'] is (i<3))
 target=[r['ratio'] for r in rows if r['id'].startswith('target/')];check(f'36target_gates_{i}',len(target)==36 and all(r['pass'] for r in rows if r['id'].startswith('target/')));ranges.append([min(target),max(target)])
 check(f'summary_process_{i}',summary['processes'][i-1]['invocation']==inv and summary['processes'][i-1]['process']==proc and summary['processes'][i-1]['counts']==raw['counts'] and summary['processes'][i-1]['red']==raw['red'] and summary['processes'][i-1]['setup_seconds']==[dict(id=c['id'],seconds=c['bundle_snapshot_setup_seconds']) for c in raw['costs']])
check('counts_smoke16_qualification4329',raws[0]['counts']=={'smoke':{'pass':16,'fail':0,'error':0,'broken':0},'qualification':{'pass':4329,'fail':0,'error':0,'broken':0}})
check('correctness_direct488',sum(c['calls_per_side'] for c in raws[0]['correctness'])*3+2==488)
measured=[w for w in all_windows if w['phase']=='measured']
check('all_window_call_counts',len(all_windows)==summary['windows']==3120 and len(measured)==summary['measured_windows']==2184 and len(all_windows)-len(measured)==summary['warm_windows']==936 and sum(w['calls'] for w in all_windows)==summary['cost_calls']==12480)
check('zero_compile_gc28_retained',all(w['compile_seconds']==w['recompile_seconds']==0 for w in measured) and sum(w['gc_seconds']>0 for w in measured)==summary['measured_gc_windows']==28)
check('exact_two_failed_controls',failed==summary['failed_cases'] and [(r['process'],r['id']) for r in failed]==[(3,'fallback/BigFloat/transpose'),(3,'fallback/Rational{BigInt}/forward')])
check('single_rejected_no_aggregate',summary['accepted'] is False and summary['attempt_consumed'] is True and summary['aggregate'] is None and not (X/'aggregate.json').exists() and rd(Y/'launch-exit.json')['returncode']==1 and rd(Y/'launch-exit.json')['invocations']==1 and rd(Y/'launch-exit.json')['no_retry'] is True and 'failed qualification; stop, no retry' in (Y/'launch.log').read_text())
check('resource_summary',min(s['available_kib'] for s in resources)==summary['resource_min_available_kib']==22305908 and max(s['swap_used_kib'] for s in resources)==summary['resource_max_swap_kib']==0 and total==summary['total_supervised_seconds'])
check('full176groups',len(host['groups'])==170 and len(groups)==176 and groups==set(post['groups']) and post['matches']==[] and context['groups']==host['groups'])
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  f=(p/'stat').read_text().rsplit(')',1)[1].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'exe').resolve().name.startswith('julia'):matches.append(int(p.name))
 except (FileNotFoundError,ProcessLookupError):pass
check('fresh176groups_ORsessions_noJulia',boot==context['boot_id'] and not matches)
refs={k:subprocess.check_output(['git',*a],text=True).strip() for k,a in {'head':['rev-parse','HEAD'],'master':['rev-parse','master'],'branch':['branch','--show-current'],'remote':['ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture']}.items()}
check('fresh_refs',refs==context['refs']==post['refs'])
check('tracked_and_stage_clean',not subprocess.check_output(['git','diff','--name-only','HEAD'],text=True).strip() and not subprocess.check_output(['git','diff','--cached','--name-only'],text=True).strip())
cm=rd(Y/'continuation-map.json')['old_bindings'];check('six_continuation_beforecopies',len(cm)==6 and all(sha(v['preserved'])==v['sha256'] and rd(v['source'])['sha256'][v['path']]==v['sha256'] for v in cm))
check('source_setup_budget',schedule['correctness_setup_factorizations']==len(raws[0]['correctness'])+2==162 and schedule['cost_setups']==3*len(fixtures['cost_cases'])==156 and schedule['setup_factorizations']==318 and schedule['pfi_copies']==2 and schedule['total_entries']==12968)
details.update(failed_controls=failed,target_ratio_ranges=ranges,supervised_seconds=elapsed,total_seconds=total,full_groups=sorted(groups),fresh_matches=matches,load_seconds=[r['load_seconds'] for r in raws],candidate_definition_seconds=[r['candidate_definition_seconds'] for r in raws],cost_inclusive_seconds=[r['cost_inclusive_seconds'] for r in raws],setup_sums=[sum(c['bundle_snapshot_setup_seconds'] for c in r['costs']) for r in raws])
with (Y/'result-review-check.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),qualification_accepted=False,checks=checks,details=details,checker_sha256=sha(__file__)),f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=all(checks.values()),check_count=len(checks),failed_controls=failed,target_ratio_ranges=ranges)))
