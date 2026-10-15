"""Fresh independent, read-only evidence checks; no historical module imports or Julia."""
from pathlib import Path
import hashlib,json,tomllib,subprocess,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
Q=R/'diagnostics/simplex-core-architecture/results/NATIVE-PIVOT-QUALIFICATION'
D=Q.parent/'NATIVE-PIVOT-RED'; RUN=Q/'runs/red'; OUT=RUN/'output'
def read(p): return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
def path(n): return Path(n) if Path(n).is_absolute() else R/n
def bound(z): return all(sha(path(n))==v for n,v in z['sha256'].items())
def save(p,z):
 with p.open('x') as f: json.dump(z,f,indent=2);f.write('\n')
def inventory(z):
 names=set(z['files'])
 for n in z['trees']:
  p=Path(n);assert p.is_dir() and not p.is_symlink()
  for f in p.rglob('*'):
   assert not (f.is_symlink() and (f.is_dir() or not f.exists()))
   if f.is_file(): names.add(str(f))
 return names==set(z['inventory']) and all(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in z['inventory'].items())
a=read(RUN/'audit.json');s=read(RUN/'sealed.json');ad=read(RUN/'admission.json');lp=read(RUN/'launch-pins.json');iv=read(RUN/'invocation.json');p=read(OUT/'process.json');cur=read(OUT/'current.json');cfg=read(RUN/'config.json');res=read(RUN/'reservation.json');post=read(RUN/'posthost.json');pre=read(RUN/'prehost.json');hs=read(RUN/'host.json');raw=tomllib.loads((OUT/'raw.toml').read_text());pc=read(D/'postcheck.json')
checks={}
checks['audit_bindings']=a['phase']=='red' and a['all_passed'] is True and a['error']=='' and bound(a)
checks['sealed_951_inventory']=len(s['files'])==len(s['inventory'])==951 and inventory(s)
checks['admission_exact_952']=ad['accepted'] is True and ad['findings']==[] and ad['scope']=='exact-stage admission' and ad['phase']=='red' and ad['pins_sha256']==sha(RUN/'sealed.json') and set(ad['sha256'])==set(s['files'])|{str(RUN/'sealed.json')} and bound(ad)
checks['launch_954_inventory']=len(lp['inventory'])==954 and set(lp['files'])==set(s['files'])|{str(RUN/'sealed.json'),str(RUN/'admission.json'),str(RUN/'prehost.json')} and lp['trees']==s['trees'] and inventory(lp) and read(OUT/'pins.json')==lp and all(lp['inventory'][n]==v for n,v in s['inventory'].items())
prep=read(Q/'preparation-pins-reviewed.json');prev=read(Q/'review-final.json');rt=read(Q/'runtime-pins.json')
checks['preparation_872_and_873_review']=len(prep['sha256'])==872 and bound(prep) and prev['accepted'] is True and prev['findings']==[] and prev['scope']=='offline preparation' and prev['pins_sha256']==sha(Q/'preparation-pins-reviewed.json') and set(prev['sha256'])==set(prep['sha256'])|{str(Q/'preparation-pins-reviewed.json')} and bound(prev)
checks['runtime_679']=len(rt['sha256'])==679 and bound(rt)
overlay=read(Q.parent/'NATIVE-PIVOT-PREPARATION/overlay-manifest.json')['reference'];stage=Path(cfg['stage'])
checks['reference73_exact']=len(overlay)==73 and not stage.is_symlink() and {str(f.relative_to(stage)) for f in stage.rglob('*') if f.is_file()}=={e['destination'] for e in overlay} and all(not (stage/e['destination']).is_symlink() and (stage/e['destination']).stat().st_nlink==1 and sha(stage/e['destination'])==e['sha256']==sha(e['source']) for e in overlay)
command=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(Q/'test-driver-reviewed.jl'),str(OUT),'red',str(stage)]
checks['exact_command_config']=s['phase']==cfg['phase']=='red' and s['config']==cfg and cfg['seconds']==30 and cfg['expected_exit']==1 and cfg['arm']=='reference' and p['cwd']==str(R) and cfg['command']==p['command']==cur['command']==iv['command']==command
checks['guard_command']=iv['guard_command']==['/usr/bin/python3','-B',str(Q/'guard.py'),'run',str(RUN/'launch-pins.json'),str(OUT),'--seconds','22','--deadline',str(iv['monotonic_start']+22),'--expected-exit','1','--',*command]
checks['reservation_links']=res==dict(one_attempt=True,phase='red',command=command,pins_sha256=sha(RUN/'launch-pins.json'),review_sha256=sha(RUN/'admission.json'),max_seconds=30) and iv['reservation_sha256']==sha(RUN/'reservation.json') and iv['review_sha256']==sha(RUN/'admission.json') and iv['pins_sha256']==p['pins_sha256']==cur['pins_sha256']==sha(RUN/'launch-pins.json')
checks['raw_complete_threads_paths']=raw['phase']=='red' and raw['complete'] is True and raw['fatal']=='' and raw['threads']==raw['blas_threads']==1 and raw['loaded']==dict(read(Q/'loaded-paths.json'),JSimplex=str(stage/'src/JSimplex.jl'))
t=raw['tests'];g=t['children'][0]
checks['exact_four_failures']=t['name']=='root' and all(t[k]==0 for k in ['pass','fail','error','broken']) and t['failures']==[] and len(t['children'])==1 and g['name']=='Missing native pivot policy contract' and g['fail']==4 and all(g[k]==0 for k in ['pass','error','broken']) and g['children']==[] and len(g['failures'])==4 and all(k in f for k,f in zip(['native_pivot_policy','_NativePivotPolicy','pivot_policy','_native_lu'],g['failures']))
checks['selected_work_zero']=raw['counts']=={} and raw['events']==raw['equations']==[] and a['result']['selected_body_native_entries']==0 and a['result']['expected_failure'] is True
sup=iv['supervisor']
checks['exit_and_deadline']=p['reason']=='exit1' and p['returncode']==1 and p['pins_unchanged'] is True and sup['returncode']==0 and sup['accepted'] is True and all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup and 0<iv['elapsed_seconds']<=30 and 0<sup['elapsed_seconds']<=iv['elapsed_seconds'] and 0<p['elapsed_including_launch']<=22
samples=[json.loads(x) for x in (OUT/'resources.jsonl').read_text().splitlines()]
checks['resource_samples']=len(samples)==5 and samples==a['result']['resources'] and min(z['available_kib'] for z in samples)==22180688 and all(z['available_kib']>=6*1024**2 and z['swap_used_kib']==0 for z in samples+[p['terminal_memory']]) and p['child_maxrss_kib']==a['result']['resident_highwater_kib']==427876
checks['identity_chain']=cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'] and all(p[role]['pid']==p[role]['pgid']==p[role]['sid']==pid and p[role]['start_ticks']==tick and p[role]['boot_id']==s['boot_id'] for role,pid,tick in [('runner',229464,13681290),('child',229465,13681339)])
checks['recorded_host_closure']=all(not h['matches'] and all(h[k]==s[k] for k in ['head','master','boot_id']) for h in [hs,pre,post]) and len(post['groups'])==210 and set(s['groups'])<=set(pre['groups'])<=set(post['groups']) and all(p[role][key] in post['groups'] for role in ['runner','child'] for key in ['pgid','sid'])
checks['raw_output_logs_exact']={f.name for f in OUT.iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log','raw.toml'} and all(f.is_file() for f in OUT.iterdir()) and (OUT/'run.log').read_bytes()==b'' and json.loads((RUN/'launcher.log').read_text())==p
checks['only_red']={f.name for f in (Q/'runs').iterdir()}=={'red'} and {f.name for f in stage.parent.iterdir()}=={'red'}
checks['author_postcheck14_bound9']=pc['all_passed'] is True and len(pc['checks'])==14 and all(pc['checks'].values()) and len(pc['sha256'])==9 and bound(pc)
# Independent fresh /proc scan, without importing any earlier host checker.
groups=set(post['groups']);matches=[];unreadable=[];races=[]
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for proc in Path('/proc').glob('[0-9]*'):
 try:
  fields=(proc/'stat').read_text().rsplit(')',1)[1].split();comm=(proc/'comm').read_text().strip();exe=''
  try: exe=str((proc/'exe').resolve(strict=True))
  except PermissionError: unreadable.append(int(proc.name))
  except FileNotFoundError: pass
  if int(fields[2]) in groups or int(fields[3]) in groups or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):
   matches.append(dict(pid=int(proc.name),pgid=int(fields[2]),sid=int(fields[3]),start_ticks=int(fields[19]),comm=comm,exe=exe))
 except (FileNotFoundError,ProcessLookupError): races.append(int(proc.name))
def git(*args): return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
host=dict(time=time.time(),boot_id=boot,groups=sorted(groups),matches=matches,unreadable_exe_pids=unreadable,process_exit_races=races,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),scope='Fresh all process stat/comm and readable executable scan; all210 identifiers checked as both PGID and SID. Inaccessible system executable links remain a visibility limit.')
checks['fresh_host210']=not matches and len(groups)==210 and all(host[k]==s[k] for k in ['head','master','boot_id'])
checks['actual_tracked_unchanged']=git('diff','--name-only')=='' and git('diff','--cached','--name-only')==''
save(D/'reviewer-result-host.json',host)
# Supplementary bindings deliberately kept outside the exact-schema stage review.
paths=[Path(__file__),D/'reviewer-result-host.json',D/'REPORT.md',D/'postcheck.py',D/'postcheck.json',D/'postcheck-host.json',D/'entry.json',RUN/'audit.json',R/'docs/superpowers/plans/2026-10-15-native-pivot-policy.md']
result=dict(all_passed=all(checks.values()),checks=checks,sha256={str(f):sha(f) for f in paths},counts=dict(sealed=951,admission=952,launch=954,runtime=679,preparation=872,offline_review=873,reference=73,audit=len(a['sha256']),resources=5,groups=210),scope='Fresh independent RED saved-result verification only; no old checker/auditor or Julia executed')
save(D/'reviewer-result-check.json',result)
print(json.dumps(dict(all_passed=result['all_passed'],checks=len(checks),failed=[k for k,v in checks.items() if not v],counts=result['counts'])))
assert result['all_passed']
