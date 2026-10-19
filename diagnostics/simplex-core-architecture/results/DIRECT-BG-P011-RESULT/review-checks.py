"""Independent saved-evidence review. No imports/calls of old audit/control/checkers or Julia."""
from pathlib import Path
import hashlib,json,tomllib,math,re,subprocess,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-P011-HARNESS'
E=D.with_name('DIRECT-BG-P011-RESULT'); RUN=D/'runs/p011-300'; O=D/'outers/p011-300'
checks={}; details={}; started=time.time()
def need(v,label):
 checks[label]=bool(v)
 if not v: raise ValueError(label)
def rd(p):return json.loads(Path(p).read_text())
def h(p):
 digest=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
 return digest.hexdigest()
def bindings(obj,key='sha256'):
 return all(h(Path(p) if Path(p).is_absolute() else R/p)==v for p,v in obj[key].items())
def tree(root):
 root=Path(root);paths=list(root.rglob('*'))
 need(not root.is_symlink() and all(not p.is_symlink() for p in paths),'no_symlink_'+root.name)
 return {str(p) for p in paths if p.is_file()}
def finite(v):return type(v) in (float,int) and math.isfinite(v) and 0<=v<=300
def metric(m):
 return set(m)=={'seconds','bytes','events','compile_seconds','recompile_seconds','gc_seconds'} and all(type(m[k]) is int and 0<=m[k]<2**63 for k in ('bytes','events')) and all(finite(m[k]) for k in ('seconds','compile_seconds','recompile_seconds','gc_seconds'))
s=rd(RUN/'sealed.json');pins=rd(RUN/'launch-pins.json');adm=rd(RUN/'admission.json');audit=rd(RUN/'audit.json');author=rd(E/'author-checks.json');cfg=rd(RUN/'config.json')
runfiles=tree(RUN);need(str(RUN/'result-review.json') not in runfiles,'new_review_only')
need(set(author['sha256'])==runfiles and bindings(author),'author_exact_run_hashes')
need(set(audit['sha256'])==runfiles-{str(RUN/'audit.json'),str(RUN/'outer-closure.json')} and bindings(audit),'audit_exact_saved_hashes')
need(author['all_passed'] is True and len(author['checks'])==11 and all(v is True for v in author['checks'].values()),'author_11_checks')
need(audit['all_passed'] is True and audit['pure_timeout'] is False and audit['error']=='','audit_success')
need(adm['accepted'] is True and adm['findings']==[] and adm['scope']=='P011 diagnostic exact-run admission' and adm['phase']=='p011-300','exact_admission')
need(adm['pins_sha256']==h(RUN/'sealed.json') and set(adm['sha256'])==set(s['files'])|{str(RUN/'sealed.json')} and bindings(adm,'evidence_sha256'),'admission_evidence_membership')
need(rd(RUN/'admission-checks.json')['all_passed'] is True,'admission_check_record')
need(cfg==s['config'] and cfg['phase']==s['phase']=='p011-300' and cfg['seconds']==300 and len(cfg['command'])==11 and cfg['command'][-2:]==[cfg['payload'],cfg['stage']],'configuration_and_two_arguments')
prep=rd(D/'preparation-pins.json');pr=rd(D/'review.json');baseline=rd(D/'baseline.json');runtime=rd(D/'runtime-inputs-complete.json')['inventory'];stage=rd(D/'stages.json')['red']
need(set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']) and len(prep['sha256'])==87 and bindings(prep),'preparation_87')
need(pr['accepted'] is True and pr['findings']==[] and pr['launch_admitted'] is False and bindings(pr) and bindings(pr,'evidence_sha256'),'preparation_review')
prepared=set(prep['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(pr['evidence_sha256'])
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
expected=prepared|set(runtime)|{str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in baseline[label]}|{str(Path(cfg['stage'])/n) for n in stage['sha256']}|{str(RUN/'host.json'),str(RUN/'config.json'),str(O/'outer-ready.json')}
need(set(s['files'])==expected and len(s['files'])==1805 and len(set(s['files']))==1805,'reconstructed_seal_membership')
need(set(s['inventory'])==expected and s['inputs']==[],'sealed_inventory_membership')
need(set(pins['files'])==set(pins['inventory'])==expected|{str(RUN/n) for n in ['sealed.json','admission.json','prehost.json']}|{str(O/n) for n in ['release.json','outer-invocation.json']},'launch_membership')
need(pins['trees']==s['trees']==[cfg['stage'],str(R/'diagnostics/direct-bg-blocked-update/reproduce'),str(D.with_name('DIRECT-BG-P011-DIAGNOSTIC'))],'sealed_trees')
tree_counts={}
for root in s['trees']:
 members=tree(root);tree_counts[root]=len(members)
 need(members=={p for p in expected if p.startswith(root+'/')},'tree_membership_'+Path(root).name)
actual={}; bytecount=0
for path,item in pins['inventory'].items():
 p=Path(path);actual[path]={'resolved':str(p.resolve(strict=True)),'sha256':h(p)};bytecount+=p.stat().st_size
need(actual==pins['inventory'],'fresh_all_1810_launch_hashes_and_resolutions')
need(all(actual[p]==v for p,v in s['inventory'].items()),'fresh_all_1805_seal_hashes')
need(all(actual[p]['sha256']==v for p,v in adm['sha256'].items()),'fresh_all_1806_admission_hashes')
need(all(actual[p]==v for p,v in runtime.items()) and len(runtime)==609,'fresh_runtime609')
need(h(D.with_name('DIRECT-BG-P011-DIAGNOSTIC')/'driver.jl')=='29c8d67755e4f86a7375f89536d24a0cb119a06a583650bc3f31bc9eccc956bf','frozen_driver')
for label,root in [('diagnostic',R),('production',W)]:
 names=subprocess.check_output(['git','ls-files','src','test','.github','Project.toml'],cwd=root,text=True).splitlines()
 need(set(names)==set(baseline[label]) and all(actual[str(root/n)]['sha256']==v for n,v in baseline[label].items()),'baseline_'+label)
need(rd(RUN/'output/pins.json')==pins,'guard_pin_copy')
need({str(Path(cfg['stage'])/n) for n in stage['sha256']}==tree(cfg['stage']) and all(actual[str(Path(cfg['stage'])/n)]['sha256']==v for n,v in stage['sha256'].items()),'stage75')
payload={p.name:tomllib.loads(p.read_text()) for p in (RUN/'payload').iterdir()}
preps=['load.toml','setup.toml','snapshot-before.toml','snapshot-after.toml']
need(set(payload)==set(preps)|{'raw.toml'}|{f'record-{i}.toml' for i in range(1,13)},'exact17_payload')
need({p.name for p in (RUN/'output').iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log'},'exact5_guard_output')
raw=payload['raw.toml'];need(set(raw)=={'schema','complete','fatal','qualification','records','loaded','input_unchanged','replacement_unchanged'} and type(raw['schema']) is int and raw['schema']==1 and raw['complete'] is True and raw['fatal']=='' and raw['qualification']=='diagnostic_only' and raw['input_unchanged'] is True and raw['replacement_unchanged'] is True,'raw_schema_and_correctness')
need(raw['loaded']==dict(rd(D/'loaded-paths.json'),JSimplex=str(Path(cfg['stage'])/'src/JSimplex.jl')) and all(p in actual for p in raw['loaded'].values()),'loaded_exact_paths_pinned')
need(len(raw['records'])==12 and raw['records']==audit['result']['records'],'raw_audit_rows')
schedule=[('first',0,'original'),('first',0,'concrete'),('warm',0,'concrete'),('warm',0,'original')]
for pair in range(1,5):schedule += [('sample',pair,arm) for arm in (('original','concrete') if pair%2 else ('concrete','original'))]
for index,row in enumerate(raw['records'],1):
 need(set(row)=={'index','phase','pair','arm','inner_bytes','inner_events','assignment_ok','decision_ok','bytes_wrapper','events_wrapper','consumed_result'} and type(row['index']) is int and row['index']==index and type(row['pair']) is int and (row['phase'],row['pair'],row['arm'])==schedule[index-1] and row==payload[f'record-{index}.toml'],'row_schedule_match_'+str(index))
 need(row['assignment_ok'] is True and row['decision_ok'] is True and all(type(row[k]) is int and 0<=row[k]<2**63 for k in ['inner_bytes','inner_events']) and all(metric(row[k]) for k in ['bytes_wrapper','events_wrapper','consumed_result']),'row_values_'+str(index))
 need((row['consumed_result']['bytes'],row['consumed_result']['events'])==(400,3),'consumed400_3_'+str(index))
prep_records={k:payload[k] for k in preps}
need(all(metric(v) for v in prep_records.values()) and prep_records==audit['result']['preparation']==author['preparation'],'all4_preparation_records')
summary={};times={}
for arm,expected_cost in [('original',(608,4,1232,9)),('concrete',(400,3,800,6))]:
 rows=[r for r in raw['records'] if r['phase']=='sample' and r['arm']==arm]
 need(len(rows)==4 and all((r['inner_bytes'],r['inner_events'])==expected_cost[:2] and all((r[k]['bytes'],r[k]['events'])==expected_cost[2:] for k in ['bytes_wrapper','events_wrapper']) for r in rows),'samples_cost_'+arm)
 need(all(r[k][v]==0 for r in rows for k in ['bytes_wrapper','events_wrapper','consumed_result'] for v in ['compile_seconds','recompile_seconds','gc_seconds']),'sample_clean_'+arm)
 summary[arm]={'inner_bytes':[r['inner_bytes'] for r in rows],'inner_events':[r['inner_events'] for r in rows],'clean_wrapper_indices':[r['index'] for r in rows]}
 times[arm]={k:[min(r[k]['seconds'] for r in rows),max(r[k]['seconds'] for r in rows)] for k in ['bytes_wrapper','events_wrapper','consumed_result']}
need(summary==author['samples']==audit['result']['descriptive_sample_counters'],'sample_summaries')
need(audit['result']['qualification']=='diagnostic_only' and audit['result']['causal_attribution']=='unresolved' and audit['result']['p011_accepted'] is False and audit['result']['red_accepted'] is False and audit['result']['source_schedule_invocations']==60,'no_qualification_or_cause')
p=rd(RUN/'output/process.json');cur=rd(RUN/'output/current.json');inv=rd(RUN/'invocation.json');sup=inv['supervisor'];res=rd(RUN/'reservation.json')
need(p['reason']=='exit0' and type(p['returncode']) is int and p['returncode']==0 and sup['accepted'] is True and type(sup['returncode']) is int and sup['returncode']==0 and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and all(k not in p for k in ['error','remaining_group','remaining_session']) and 'cleanup_error' not in sup,'clean_exit0')
need(p['pins_unchanged'] is True and p['command']==cur['command']==inv['command']==cfg['command'] and p['cwd']==cur['cwd']==str(R) and cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'],'process_command_identity')
need(cur['reason']=='launch_error' and cur['returncode'] is None,'current_is_initial_sentinel_not_terminal')
need(p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==h(RUN/'launch-pins.json'),'process_pin_binding')
need(res==dict(one_attempt=True,phase='p011-300',command=cfg['command'],pins_sha256=h(RUN/'launch-pins.json'),review_sha256=h(RUN/'admission.json'),max_seconds=300) and inv['reservation_sha256']==h(RUN/'reservation.json') and inv['review_sha256']==h(RUN/'admission.json'),'one_attempt_linkage')
need(inv['guard_command']==['/usr/bin/python3','-B',str(D/'guard.py'),'run',str(RUN/'launch-pins.json'),cfg['output'],'--seconds','292','--deadline',str(inv['monotonic_start']+292),'--expected-exit','0','--',*cfg['command']],'guard_command')
need(all(finite(v) for v in [p['elapsed_including_launch'],inv['elapsed_seconds'],sup['elapsed_seconds']]) and p['elapsed_including_launch']<=292 and inv['elapsed_seconds']==audit['process_elapsed_seconds']==author['supervised_elapsed_seconds'] and p['elapsed_including_launch']==author['guard_elapsed_seconds'],'elapsed_limits')
resources=[json.loads(x) for x in (RUN/'output/resources.jsonl').read_text().splitlines()]
need(len(resources)==author['resource_samples']==6 and all(set(v)=={'available_kib','swap_used_kib','elapsed','child_memory'} and finite(v['elapsed']) and v['elapsed']<=p['elapsed_including_launch'] for v in resources) and [v['elapsed'] for v in resources]==sorted(v['elapsed'] for v in resources),'resource_schedule')
need(all(type(v[k]) is int for v in resources+[p['terminal_memory']] for k in ['available_kib','swap_used_kib']) and all(v['available_kib']>=6*1024**2 and 0<=v['swap_used_kib']<=1024**2 for v in resources+[p['terminal_memory']]),'resource_limits')
need(all(re.fullmatch(r'(VmPeak|VmHWM|VmRSS|VmSwap):\s+\d+ kB',line) for v in resources for line in v['child_memory']),'child_memory_text')
need(min(v['available_kib'] for v in resources)==author['min_available_kib']==22231908 and max(v['swap_used_kib'] for v in resources)==author['max_swap_kib']==0 and p['child_maxrss_kib']==author['child_maxrss_kib']==489704,'resource_summary')
need((RUN/'output/run.log').read_bytes()==b'' and json.loads((RUN/'launcher.log').read_text())==p,'logs_clean_match_process')
closure=rd(RUN/'outer-closure.json');host=closure['host'];outer=rd(O/'outer-ready.json');oi=rd(O/'outer-invocation.json');oo=rd(O/'outer-outcome.json');release=rd(O/'release.json')
need({p.name for p in O.iterdir()}=={'outer-ready.json','outer-invocation.json','outer-outcome.json','release.json'},'exact_outer_membership')
need(outer['identity']==oi['identity']==oo['identity']==s['outer_identity']==closure['outer_identity'] and outer['script_sha256']==h(D/'outer.py') and oi['launcher_sha256']==h(D/'launch.py'),'outer_identity_source')
need(release==dict(phase='p011-300',sealed_sha256=h(RUN/'sealed.json'),admission_sha256=h(RUN/'admission.json'),outer_ready_sha256=h(O/'outer-ready.json'),one_attempt=True) and oi['seal_sha256']==release['sealed_sha256'] and oi['review_sha256']==release['admission_sha256'] and oi['release_sha256']==h(O/'release.json'),'release_exact_binding')
need(oo['launched'] is True and oo['returncode']==0 and oo['error']=='' and closure['all_passed'] is True and bindings(closure),'external_closure_success')
need(set(closure['sha256'])=={str(O/n) for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']}|{str(RUN/n) for n in ['sealed.json','admission.json','posthost.json','audit.json']},'external_closure_exact_bindings')
expected_groups=set(s['groups'])|{p[role][key] for role in ['runner','child'] for key in ['pgid','sid']}|{outer['identity'][k] for k in ['pgid','sid']}
need(set(host['groups'])==expected_groups and len(host['groups'])==author['closed_groups']==277 and host['matches']==[] and host['unreadable_identity_pids']==[] and host['time']>p['ended'],'external277_closure')
for name in ['host.json','prehost.json','posthost.json']:
 v=rd(RUN/name);need(v['matches']==[] and v['unreadable_identity_pids']==[] and all(v[k]==s[k]==host[k] for k in ['head','master','boot_id']) and v['head']+'\trefs/heads/codex/simplex-core-architecture' in v['remote'] and s['master']+'\trefs/heads/master' in v['remote'],'host_'+name)
need(set(rd(RUN/'posthost.json')['groups'])|{outer['identity']['pgid']}==expected_groups,'posthost_group_coverage')
need(s['master']=='26e2291745999f485a74f643298ca997d65c7205' and s['head']=='11ebe6bdd401084205ebe628d35539ebb2d5e8ae','recorded_refs')
details.update(started=started,ended=time.time(),fresh_hashed_bytes_by_inventory_path=bytecount,launch_inventory_count=len(actual),seal_inventory_count=len(s['inventory']),admission_subject_count=len(adm['sha256']),runtime_count=len(runtime),tree_counts=tree_counts,baseline_counts={k:len(v) for k,v in baseline.items()},run_subject_count=len(runfiles),samples=summary,sample_time_ranges_seconds=times,preparation=prep_records,guard_seconds=p['elapsed_including_launch'],supervised_seconds=inv['elapsed_seconds'],external_group_session_count=len(expected_groups),external_unreadable_exe_count=len(host['unreadable_exe_pids']),current_json_note='Initial ownership publication retains launch_error/None sentinel; guard.py:238,253-254. Terminal process.json is exit0.',outer_sha256={str(q):h(q) for q in sorted(O.iterdir())},run_sha256={q:h(q) for q in sorted(runfiles)},julia_invoked=False,old_checkers_imported_or_executed=False)
with (E/'review-checks.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,details=details),f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=all(checks.values()),check_count=len(checks),fresh_hashed_bytes=bytecount,launch_files=len(actual),run_subjects=len(runfiles),tree_counts=tree_counts),indent=2))
