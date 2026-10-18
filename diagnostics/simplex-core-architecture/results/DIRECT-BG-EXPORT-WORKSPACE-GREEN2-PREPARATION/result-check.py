"""Independent saved GREEN2 result review. No Julia or original auditor execution."""
from pathlib import Path
import hashlib,json,sys,tomllib,math,re
D=Path(__file__).resolve().parent;R=D.parents[3];O=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION');run=D/'runs/green2-300';out=run/'output'
sys.path.insert(0,str(D));import control as c
checks={};cache={}
def ck(n,v):checks[n]=bool(v)
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 p=Path(p);p=p if p.is_absolute() else R/p
 if str(p) not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  cache[str(p)]=h.hexdigest()
 return cache[str(p)]
def bound(v,key='sha256'):return all(sha(p)==h for p,h in v[key].items())
def finite(x):return type(x) in (int,float) and math.isfinite(x)
def inventory(v):
 expected=set(v['files'])
 for tree in v['trees']:expected.update(str(p) for p in Path(tree).rglob('*') if p.is_file())
 return set(v['inventory'])==expected and all(x==dict(resolved=str(Path(n).resolve(strict=True)),sha256=sha(n)) for n,x in v['inventory'].items())
s=rd(run/'sealed.json');ad=rd(run/'admission.json');lp=rd(run/'launch-pins.json');iv=rd(run/'invocation.json');sup=iv['supervisor'];proc=rd(out/'process.json');cur=rd(out/'current.json');a=rd(run/'audit.json');cfg=c.config('green2-300');raw=tomllib.loads((out/'raw.toml').read_text());e=rd(D/'expected-tests.json')['green'];files={str(p) for p in run.rglob('*') if p.is_file()}
ck('exact17runfiles',len(files)==17 and {p.name for p in run.iterdir()}=={'admission.json','audit.json','config.json','host.json','invocation.json','launch-pins.json','launcher.log','output','posthost.json','prehost.json','reservation.json','sealed.json'})
ck('exact6outputfiles',{p.name for p in out.iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'} and all(p.is_file() and not p.is_symlink() for p in out.iterdir()))
ck('sealed_config',s['phase']=='green2-300' and s['config']==cfg==rd(run/'config.json'))
ck('seal_inventory',len(s['files'])==1964 and inventory(s))
ck('launch_inventory',inventory(lp) and set(lp['files'])==set(s['files'])|{str(run/n) for n in ['sealed.json','admission.json','prehost.json']} and lp['trees']==s['trees'] and rd(out/'pins.json')==lp and all(lp['inventory'][n]==v for n,v in s['inventory'].items()))
ck('admission_receipt',ad['accepted'] is True and ad['findings']==[] and ad['phase']=='green2-300' and ad['scope']=='BG export workspace exact-stage admission' and ad['pins_sha256']==sha(run/'sealed.json') and set(ad['sha256'])==set(s['files'])|{str(run/'sealed.json')} and bound(ad) and bound(ad,'evidence_sha256'))
ck('audit_receipt',a['all_passed'] is True and a['pure_timeout'] is False and a['phase']=='green2-300' and a['error']=='' and set(a['sha256'])==files-{str(run/'audit.json')} and bound(a))
ck('postcheck_receipt',rd(D/'postcheck.json')['all_passed'] is True and len(rd(D/'postcheck.json')['checks'])==12 and all(rd(D/'postcheck.json')['checks'].values()) and bound(rd(D/'postcheck.json')))
ck('exact_commands',iv['command']==proc['command']==cur['command']==cfg['command'] and proc['cwd']==str(R))
ck('exact_guard_command',iv['guard_command']==c.guard_command(cfg,run/'launch-pins.json',iv['monotonic_start']) and Path(iv['python']).resolve()==Path(sys.executable).resolve())
ck('pin_identity',iv['pins_sha256']==proc['pins_sha256']==cur['pins_sha256']==sha(run/'launch-pins.json') and proc['pins_unchanged'] is True)
res=rd(run/'reservation.json');ck('exclusive_reservation',res==dict(one_attempt=True,phase='green2-300',command=cfg['command'],pins_sha256=sha(run/'launch-pins.json'),review_sha256=sha(run/'admission.json'),max_seconds=300) and iv['reservation_sha256']==sha(run/'reservation.json') and iv['review_sha256']==sha(run/'admission.json'))
ck('identity_linkage',cur['runner']==proc['runner']==sup['guard_identity'] and cur['child']==proc['child'])
ck('identity_boot_start_command',all(proc[role]['boot_id']==s['boot_id'] and type(proc[role]['start_ticks']) is int and proc[role]['start_ticks']>0 and proc[role]['command'] and proc[role]['pid']==proc[role]['pgid']==proc[role]['sid'] for role in ['runner','child']))
ck('successful_exits',proc['returncode']==sup['returncode']==0 and proc['reason']=='exit0' and sup['accepted'] is True)
ck('no_timeout_cleanup_error',not any(sup[k] for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup and 'error' not in proc)
ck('elapsed_bounded',all(finite(x) and 0<=x<=300 for x in [iv['elapsed_seconds'],sup['elapsed_seconds'],proc['elapsed_including_launch']]) and proc['elapsed_including_launch']<=292 and sup['elapsed_seconds']<=iv['elapsed_seconds'])
ck('raw_schema',set(raw)=={'phase','complete','fatal','loaded','threads','blas_threads','tests'} and raw['phase']=='green2-300' and raw['complete'] is True and raw['fatal']=='')
ck('runtime_source_threads',raw['loaded']==c.loaded_for(cfg) and type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1)
root=raw['tests'];schema={'name','pass','fail','error','broken','failures','children'}
ck('root_exact',set(root)==schema and root['name']=='root' and all(type(root[k]) is int and root[k]==0 for k in ['pass','fail','error','broken']) and root['failures']==[])
ck('eleven_exact_groups',len(root['children'])==11 and [[t['name'],t['pass'],t['fail'],t['error'],t['broken']] for t in root['children']]==e['groups'])
for k,t in enumerate(root['children']):ck('leaf_'+str(k+1),set(t)==schema and t['children']==[] and t['failures']==[] and all(type(t[n]) is int and t[n]>=0 for n in ['pass','fail','error','broken']) and t['fail']==t['error']==t['broken']==0)
ck('all7935passes',sum(t['pass'] for t in root['children'])==e['assertions']==7935 and a['result']['assertions']==7935 and a['result']['groups']==e['groups'])
log=(out/'run.log').read_text();launcher=(run/'launcher.log').read_text();combined=log+'\n'+launcher
ck('exact_checkpoints',log.splitlines()==['BEGIN BG export workspace driver green2-300','BEGIN workspace tests','BEGIN import tests','BEGIN lifecycle tests','END all BG export workspace tests'])
ck('no_warning_world_age_failure',re.search(r'(?i)\bwarning\b|world[ -]age',combined) is None and not any(x in combined for x in ['TEST FAILURE:','BROKEN TEST:','FATAL DRIVER:','GROUP/COUNT MISMATCH','ERROR:','LoadError','Test Failed','Test Error','OutOfMemoryError']))
ck('launcher_record_exact',json.loads(launcher)==proc)
resources=[json.loads(x) for x in (out/'resources.jsonl').read_text().splitlines()]
ck('nineteen_valid_samples',len(resources)==19 and all(finite(z['elapsed']) and 0<=z['elapsed']<=292 for z in resources) and all(b['elapsed']>=a['elapsed'] for a,b in zip(resources,resources[1:])))
ck('memory_samples_terminal',all(type(z['available_kib']) is int and type(z['swap_used_kib']) is int and z['available_kib']>=6*1024**2 and 0<=z['swap_used_kib']<=1024**2 for z in resources+[proc['terminal_memory']]))
ck('rss_record',finite(proc['child_maxrss_kib']) and proc['child_maxrss_kib']>0)
pre=rd(run/'prehost.json');hs=rd(run/'host.json');post=rd(run/'posthost.json')
ck('saved_host_scoped_closed',all(c.host_safe(h) for h in [hs,pre,post]) and all(all(h[k]==s[k] for k in ['head','master','boot_id']) for h in [hs,pre,post]))
ck('group_session_coverage',len(post['groups'])==252 and set(s['groups'])<=set(pre['groups'])<=set(post['groups']) and all(proc[role][key] in post['groups'] for role in ['runner','child'] for key in ['pgid','sid']))
c.preparation();c.predecessor('green2-300');c.validate_environment();c.validate_sources();ck('all_preparation_predecessors_source_runtime_valid',True)
i=rd(D/'inverse.json');before=Path(i['original']).read_text();after=Path(i['amended']).read_text();ck('only_harness_empty_identity',after.count(i['after'])==1 and after.replace(i['after'],i['before'])==before and sha(i['original'])==i['original_sha256'] and sha(i['amended'])==i['amended_sha256'])
for n in ['workspace','export','import','factor']:ck('unchanged_candidate_'+n,sha(Path(cfg['stage'])/f'src/_bgx_{n}.jl')==sha(c.C/f'{n}.jl'))
old=rd(O/'runs/green300/result-review.json');ck('old_GREEN_failed_preserved',old['correctness_accepted'] is False and old['cost_predecessor_accepted'] is False and old['result']['pass']==7934 and old['result']['error']==1 and rd(O/'runs/green300/audit.json')['all_passed'] is False and rd(O/'runs/green300/audit.json')['pure_timeout'] is False and bound(old) and bound(old,'evidence_sha256'))
h=c.full_host(post['groups']);h['memory']=c.guard.memory();ck('fresh252groups_closed',len(h['groups'])==252 and set(h['groups'])==set(post['groups']) and c.host_safe(h));ck('fresh_refs_boot_unchanged',all(h[k]==s[k] for k in ['head','master','boot_id']));ck('fresh_resources_safe',not c.guard.pressure(h['memory']));ck('no_tracked_changes',not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'))
summary=dict(passed=7935,failed=0,errors=0,broken=0,groups=11,inclusive_seconds=iv['elapsed_seconds'],samples=len(resources),min_available_kib=min(z['available_kib'] for z in resources),max_swap_kib=max(z['swap_used_kib'] for z in resources),child_maxrss_kib=proc['child_maxrss_kib'])
v=dict(all_passed=all(checks.values()),checks=checks,result=summary,host=h,run_sha256={p:sha(p) for p in sorted(files)},scope='Saved GREEN2 correctness only; no numerical rerun, cost acceptance or production promotion')
with (D/'result-check.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=v['all_passed'],checks=len(checks),failed=[n for n,b in checks.items() if not b],result=summary,groups=len(h['groups']),unreadable_exe=len(h['unreadable_exe_pids']),unreadable_identity=len(h['unreadable_identity_pids']))))
if not v['all_passed']:raise SystemExit(1)
