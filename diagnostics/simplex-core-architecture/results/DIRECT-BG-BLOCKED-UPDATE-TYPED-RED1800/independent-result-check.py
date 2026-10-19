"""Independent saved-data review; standard library only; no imported project code or subprocess."""
from pathlib import Path
import json, hashlib, tomllib, math, re, time
E=Path(__file__).resolve().parent; D=E.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-RED1800-HARNESS'); R=D.parents[3]
RUN=D/'runs/red1800'; O=D/'outers/red1800'; OUT=RUN/'output'; P=RUN/'payload'
checks=[]; hashes={}
def ck(v,label):
 if not v: raise AssertionError(label)
 checks.append(label)
def rd(p):return json.loads(Path(p).read_text())
def digest(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def sha(p):
 p=str(p)
 if p not in hashes:hashes[p]=digest(p)
 return hashes[p]
def binds(j,key='sha256'):
 for n,h in j[key].items():ck(sha(Path(n) if Path(n).is_absolute() else R/n)==h,'binding '+n)
def inventory(j,label):
 paths=set(j['files'])
 for root in j['trees']:
  root=Path(root);ck(root.is_dir() and not root.is_symlink(),label+' tree '+str(root))
  for p in root.rglob('*'):
   ck(not(p.is_symlink() and (p.is_dir() or not p.exists())),label+' safe tree entry '+str(p))
   if p.is_file():paths.add(str(p))
 ck(paths==set(j['inventory']),label+' exact membership')
 for n,v in j['inventory'].items():ck(v=={'resolved':str(Path(n).resolve(strict=True)),'sha256':sha(n)},label+' resolved/hash '+n)
s=rd(RUN/'sealed.json'); a=rd(RUN/'admission.json'); lp=rd(RUN/'launch-pins.json');cfg=rd(RUN/'config.json'); post=rd(E/'postcheck.json')
ck(len(s['files'])==len(s['inventory'])==2352 and len(a['sha256'])==2353 and len(lp['files'])==len(lp['inventory'])==2357,'manifest sizes')
prep=rd(D/'preparation-pins.json'); prev=rd(D/'timeout-bindings.json'); pr=rd(D/'review.json');rt=rd(D/'runtime-inputs-complete.json');bl=rd(D/'baseline.json');st=rd(D/'stages.json')
ck(set(prep['sha256'])==set(rd(D/'required-paths.json')['paths']),'preparation membership');binds(prep);binds(pr);binds(pr,'evidence_sha256');binds(prev)
prepared=set(prep['sha256'])|{str(D/'preparation-pins.json'),str(D/'review.json')}|set(pr['evidence_sha256'])
expected=prepared|set(rt['inventory'])|set(prev['sha256'])|{str(RUN/'host.json'),str(RUN/'config.json'),str(O/'outer-ready.json')}
for label,root in [('diagnostic',R),('production',Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl'))]:
 for n,h in bl[label].items():ck(sha(root/n)==h,'baseline '+label+' '+n);expected.add(str(root/n))
for mode,v in st.items():
 root=Path(v['path']);actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 ck(actual==set(v['sha256']) and not any(p.is_symlink() for p in root.rglob('*')),'stage membership '+mode)
 for n,h in v['sha256'].items():ck(sha(root/n)==h,'stage '+n);expected.add(str(root/n))
ck(s['files']==sorted(expected),'reconstructed complete seal membership');inventory(s,'seal');inventory(lp,'launch')
ck(s['trees']==[cfg['stage'],str(R/'diagnostics/direct-bg-blocked-update/reproduce'),str(D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE')),str(D.with_name('DIRECT-BG-P011-TYPED-REPAIR'))] and s['inputs']==lp['inputs']==[],'sealed trees and no inputs')
ck(set(a['sha256'])==set(s['files'])|{str(RUN/'sealed.json')} and a['pins_sha256']==sha(RUN/'sealed.json'),'exact admission membership');binds(a);binds(a,'evidence_sha256')
ck(a['accepted'] is True and a['findings']==[] and a['scope']=='BG blocked typed RED repeat exact-run admission' and a['phase']=='red1800','admission disposition')
ck(set(lp['files'])==set(s['files'])|{str(RUN/n) for n in ['sealed.json','admission.json','prehost.json']}|{str(O/n) for n in ['release.json','outer-invocation.json']} and lp['trees']==s['trees'],'exact launch membership')
ck(all(lp['inventory'][n]==v for n,v in s['inventory'].items()) and rd(OUT/'pins.json')==lp,'seal launch and guard agreement')
ck(len(rd(D/'copied-files.json'))==22,'22 copies')
for n,v in rd(D/'copied-files.json').items():ck(sha(D/n)==sha(v['source'])==v['sha256'],'copy '+n)
for n,v in rd(D/'control-transform.json').items():
 text=(D/n).read_text();ck(sha(D/n)==v['prepared_sha256'] and sha(v['source'])==v['source_sha256'],'transform hashes '+n)
 if v.get('append'):ck(text.endswith(v['append']),'append '+n);text=text[:-len(v['append'])]
 for e in reversed(v['edits']):ck(text.count(e['new'])==e['count'],'inverse occurrence '+n);text=text.replace(e['new'],e['old'])
 ck(text==Path(v['source']).read_text(),'exact transform inverse '+n)
ck(len(prev['sha256'])==81,'prior81');pv=rd(prev['review']);pa=rd(prev['audit']);binds(pv);binds(pv,'evidence_sha256')
ck(pv['accepted'] is True and pv['qualification_accepted'] is False and pa['all_passed'] is False and pa['pure_timeout'] is False and not (Path(prev['run'])/'result-review.json').exists(),'prior rejected qualification frozen')
ck(rd(E/'independent-admission-check-v2.json')['count']==3467 and rd(E/'independent-admission-check-v2.json')['all_passed'] is True,'3467 admission checks retained')
ck(rd(E/'independent-admission-check-failure.json')['checker_returncode']==1 and rd(E/'independent-admission-check-failure.json')['outer_environment_differences']=={},'initial reviewer failure retained')
cmd=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--history-file=no','--project='+cfg['stage'],str(D/'driver.jl'),str(P),cfg['stage'],'red300']
ck(cfg==dict(phase='red1800',mode='red',seconds=1800,expected_exit=1,stage=st['red']['path'],run=str(RUN),output=str(OUT),payload=str(P),command=cmd)==s['config'],'exact config command and semantic phase')
p=rd(OUT/'process.json');cur=rd(OUT/'current.json');inv=rd(RUN/'invocation.json');sup=inv['supervisor'];outer=rd(O/'outer-outcome.json');ready=rd(O/'outer-ready.json')
ck(p['command']==cur['command']==inv['command']==cmd and p['cwd']==str(R),'process commands/cwd')
ck(p['pins_sha256']==cur['pins_sha256']==inv['pins_sha256']==sha(RUN/'launch-pins.json') and p['pins_unchanged'] is True,'pins receipt linkage')
ck(inv['guard_command']==[inv['python'],'-B',str(D/'guard.py'),'run',str(RUN/'launch-pins.json'),str(OUT),'--seconds','1792','--deadline',str(inv['monotonic_start']+1792),'--expected-exit','1','--',*cmd],'guard command and deadline')
ck(rd(RUN/'reservation.json')==dict(one_attempt=True,phase='red1800',command=cmd,pins_sha256=sha(RUN/'launch-pins.json'),review_sha256=sha(RUN/'admission.json'),max_seconds=1800),'one reservation exact')
ck(inv['reservation_sha256']==sha(RUN/'reservation.json') and inv['review_sha256']==sha(RUN/'admission.json'),'invocation reservation/review linkage')
ck(rd(O/'release.json')==dict(phase='red1800',sealed_sha256=sha(RUN/'sealed.json'),admission_sha256=sha(RUN/'admission.json'),outer_ready_sha256=sha(O/'outer-ready.json'),one_attempt=True),'one release exact')
ck(rd(O/'outer-invocation.json')==dict(identity=ready['identity'],phase='red1800',seal_sha256=sha(RUN/'sealed.json'),review_sha256=sha(RUN/'admission.json'),release_sha256=sha(O/'release.json'),launcher_sha256=sha(D/'launch.py'),method='runpy.run_path launch.py as __main__ in this outer process'),'outer invocation exact')
ck(ready['waiting_only'] is True and ready['phase']=='red1800' and ready['script_sha256']==sha(D/'outer.py') and ready['expected_launcher']==str(D/'launch.py'),'waiting outer source')
ck(ready['identity']==s['outer_identity']==outer['identity'] and cur['runner']==p['runner']==sup['guard_identity'] and cur['child']==p['child'],'identity links')
for ident,pid,ticks in [(s['outer_identity'],214974,14546623),(p['runner'],215655,14580804),(p['child'],215656,14580862)]:ck(ident['pid']==ident['pgid']==ident['sid']==pid and ident['start_ticks']==ticks and ident['boot_id']==s['boot_id'] and bool(ident['command']),'identity '+str(pid))
ck(s['head']=='cc9d35dc3e2c526bcae8b752ca2ea43dad9a5212' and s['master']=='26e2291745999f485a74f643298ca997d65c7205','pinned refs')
ck(p['returncode']==-11 and p['reason']=='exit-11' and sup['returncode']==1 and sup['accepted'] is False and outer['returncode']==2 and outer['launched'] is True,'failed exits')
ck(all(sup[k] is False for k in ['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill']) and 'cleanup_error' not in sup and not {'error','remaining_group','remaining_session'}&set(p),'no timeout termination or process leftovers')
ck(0<p['elapsed_including_launch']<=1792 and 0<sup['elapsed_seconds']<=inv['elapsed_seconds']<=1800 and outer['elapsed_with_checks_seconds']>inv['elapsed_seconds'],'elapsed bounds')
cl=rd(RUN/'outer-closure.json');binds(cl);h=cl['host'];groups=set(rd(D/'historical-groups.json')['groups'])|{214974,215655,215656}
ck(len(groups)==292 and set(h['groups'])==groups and cl['all_passed'] is True and cl['outer_identity']==s['outer_identity'],'all292 closure groups')
ck(set(cl['sha256'])=={str(O/n) for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']}|{str(RUN/n) for n in ['sealed.json','admission.json','posthost.json','audit.json']},'closure exact bindings')
for host in [h,*[rd(RUN/n) for n in ['host.json','prehost.json','posthost.json']]]:
 ck(host['matches']==[] and host['unreadable_identity_pids']==[] and all(host[k]==s[k] for k in ['head','master','boot_id']) and s['head']+'\trefs/heads/codex/simplex-core-architecture' in host['remote'] and s['master']+'\trefs/heads/master' in host['remote'],'saved host identities refs and closure')
audit=rd(RUN/'audit.json');binds(audit)
ck(audit['all_passed'] is False and audit['pure_timeout'] is False and audit['error']=="RuntimeError('Exact payload membership')",'failed admitted audit intact')
ck({x.name for x in OUT.iterdir()}=={'current.json','pins.json','process.json','resources.jsonl','run.log'},'guard output exact')
ck({x.name for x in P.iterdir()}=={f'{k}-{i}.toml' for k in ['unit','cost'] for i in range(1,13)}|{'load.toml','panel-load.toml','tests-load.toml'},'exact27 payload')
ck(all(x.is_file() and not x.is_symlink() for x in list(P.iterdir())+list(OUT.iterdir())) and not (RUN/'result-review.json').exists(),'raw files and no acceptance')
schedule=rd(D/'schedule.json');sites=rd(D/'assertion-sites.json');ck(len(schedule['units'])==28 and len(schedule['expected_red_units'])==6 and len(sites)==168,'full target unchanged')
for site,v in sites.items():ck((D/v['file']).read_text().splitlines()[v['line']-1].strip()==v['source'],'source assertion '+site)
def tree(t):
 ck(set(t)=={'name','pass','fail','error','broken','children'},'tree schema')
 v=[t[k] for k in ['pass','fail','error','broken']];ck(all(type(z) is int and z>=0 for z in v),'tree count types')
 for child in t['children']:v=[a+b for a,b in zip(v,tree(child))]
 return v
tot=[0]*4;unit_rows=[];failures=[]
for i in range(1,13):
 u=tomllib.loads((P/f'unit-{i}.toml').read_text());r=u['records'];e=r['events'];o=u['observations'];name=schedule['units'][i-1]
 ck(set(u)=={'index','name','complete','fatal','tests','records','observations'} and u['index']==i and u['name']==name and u['complete'] is True and u['fatal']=='','unit identity '+name)
 ck(set(r)=={'sites','events','apis','failures','failure_count','active'} and r['active']=='' and all(type(z) is int and z>0 for k in ['sites','events','apis'] for z in r[k].values()),'counter schemas '+name)
 if i==1:
  ex={f'P{n:03}':1 for n in range(1,103)}
  for n,count in [(1,5),(13,2),(15,4),(27,3),(66,2)]:ex[f'P{n:03}']=count
  for lo,hi,count in [(16,18,10),(19,20,5760),(21,26,10),(34,45,4),(62,64,3),(85,91,3)]:
   for n in range(lo,hi+1):ex[f'P{n:03}']=count
  ck(e==r['apis']=={} and o==[] and [tree(c) for c in u['tests']['children']]==[[31,0,0,0],[11619,0,0,0],[74,0,0,0],[44,0,0,0]],'panel exact groups')
 else:
  finished=3 if i==2 else 2*schedule['fixtures'][(i-3)//2]['updates'];piv=e.get('pivot',0);pure=e.get('pure_row',0)
  ck(e.get('finish',0)==e.get('event_finish',0)==e.get('event_begin',0)==finished and piv==e.get('event_panel_pivot',0)+e.get('event_scalar_pivot',0),'trace completion/pivots '+name)
  ck(e.get('event_panel_begin',0)==e.get('event_panel_commit',0)+e.get('event_panel_reject',0)-e.get('declined_before_gather',0) and e.get('event_eligibility',0)==e.get('event_panel_begin',0)+e.get('declined_before_gather',0),'panel event accounting '+name)
  ck(0<=e.get('declined_before_gather',0)<=e.get('event_panel_reject',0)<=finished and 8*e.get('event_panel_commit',0)<=e.get('event_panel_pivot',0)<=8*e.get('event_panel_begin',0) and e.get('event_scalar_suffix',0)<=finished and e.get('event_pure',0)<=pure and (e.get('event_pure',0)==0)==(pure==0),'trace work bounds '+name)
  allowed={'pivot','pure_row','finish','declined_before_gather'}|{'event_'+s for s in ['begin','finish','panel_begin','panel_pivot','scalar_pivot','pure','panel_reject','panel_commit','eligibility','scalar_suffix']}|({'catch_overflow','catch_nonfinite'} if i==2 else set());ck(set(e)<=allowed,'event names '+name)
  ex={**{f'N{n:03}':piv for n in range(1,4)},'N004':pure,**{f'N{n:03}':finished for n in range(5,13)}}
  if i==2:
   ex.update({f'L{n:03}':1 for n in range(1,41)})
   for lo,hi,count in [(1,22,2),(31,32,2),(33,35,3)]:
    for n in range(lo,hi+1):ex[f'L{n:03}']=count
   ex['L025']=e.get('catch_overflow',0);ex['L030']=e.get('catch_nonfinite',0)
   ck(ex['L025'] in (0,1) and ex['L030'] in (0,1,2) and o==[],'lifecycle catch/observations')
   api={'factory_candidate':2,'factory_micro':12,'FTRAN':13,'BTRAN':2,'replace':8,'copy':6,'refactor':8,'eliminate':8,'eliminate_fault':4}
  else:
   f=schedule['fixtures'][(i-3)//2];updates=f['updates'];ex.update({f'N{n:03}':updates for n in range(15,26)});ex.update(N013=1,N014=1,N021=2*updates,N024=updates if f['pivot_agreement'] else 0,N026=1)
   api={'factory_reference':1,'factory_candidate':1,'FTRAN':6*updates,'BTRAN':2*updates,'replace_reference':updates,'replace_candidate':updates}
   ck(len(o)==updates and all(e.get('event_'+k,0)==0 for k in ['panel_begin','panel_commit','eligibility','panel_reject']) and pure+e.get('event_scalar_pivot',0)+e.get('event_panel_pivot',0)<=2*updates*(f['n']-1+8),'RED route and work '+name)
   ck(all(set(v)=={'panels','rejections','growth','minpivot'} and type(v['panels']) is int and type(v['rejections']) is int and v['panels']==v['rejections']==0 and all(type(v[k]) is float and math.isfinite(v[k]) and v[k]>0 for k in ['growth','minpivot']) for v in o),'saved observation bounds '+name)
  ck(r['apis']==api,'exact API budget '+name)
 ck(r['sites']=={k:v for k,v in ex.items() if v},'independent source counts '+name)
 vals=tree(u['tests']);expected_fail=int(name in schedule['expected_red_units']);ck(u['tests']['name']==name and sum(vals)==sum(ex.values()) and vals[1:]==[expected_fail,0,0],'test reconciliation '+name)
 ck(type(r['failure_count']) is int and r['failure_count']==len(r['failures'])==expected_fail and all(set(v)=={'kind','site','detail'} and v['kind']=='fail' and v['site']=='N026' and 'minimum_panels' in v['detail'] for v in r['failures']),'failure names '+name)
 tot=[x+y for x,y in zip(tot,vals)];unit_rows.append(dict(index=i,name=name,totals=vals));failures.extend(dict(unit=name,**v) for v in r['failures'])
ck(tot==[55695,2,0,0] and unit_rows==post['completed_units'] and failures==post['failures'],'all prefix totals')
costs={}
for path in P.iterdir():
 if path.name.startswith('unit-'):continue
 v=tomllib.loads(path.read_text());ck(set(v)=={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'} and all(type(v[k]) is int and 0<=v[k]<=2**63-1 for k in ['bytes','events']) and all(type(v[k]) in (int,float) and math.isfinite(v[k]) and 0<=v[k]<=1800 for k in ['seconds','gc_seconds','compile_seconds','recompile_seconds']),'cost '+path.name);costs[path.name]=v
ck(costs==post['preparation'] and len(costs)==15,'all saved costs independently parsed')
log=(OUT/'run.log').read_text();begins=re.findall(r'^UNIT BEGIN (\d+) (.+)$',log,re.M);ends=re.findall(r'^UNIT END (\d+) (.+)$',log,re.M)
ck(begins==[(str(i),schedule['units'][i-1]) for i in range(1,14)] and ends==begins[:12],'exact log prefix')
ck(log.index('OutOfMemoryError()')<log.index('atexit hook threw an error: OutOfMemoryError()')<log.index('signal 11') and 'run_finalizer' in log and 'ijl_get_excstack' in log and log.count('TEST FAILURE: N026 ')==2,'OOM before finalizer segfault')
for f in failures:ck('TEST FAILURE: N026 '+f['detail'] in log,'logged failure '+f['unit'])
resources=[json.loads(line) for line in (OUT/'resources.jsonl').read_text().splitlines()];mem={k:[] for k in ['VmPeak','VmHWM','VmRSS','VmSwap']};last=-1
for row in resources:
 ck({'available_kib','swap_used_kib','elapsed'}<=set(row)<={'available_kib','swap_used_kib','elapsed','child_memory'} and math.isfinite(row['elapsed']) and last<=row['elapsed']<=p['elapsed_including_launch'],'resource schema/order');last=row['elapsed']
 ck(type(row['available_kib']) is int and row['available_kib']>=6*1024**2 and type(row['swap_used_kib']) is int and row['swap_used_kib']==0,'resource guard')
 for line in row.get('child_memory',[]):
  m=re.fullmatch(r'(VmPeak|VmHWM|VmRSS|VmSwap):\s+(\d+) kB',line);ck(m is not None,'memory field');mem[m[1]].append(int(m[2]))
summary=dict(samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_used_kib=max(x['swap_used_kib'] for x in resources),terminal=p['terminal_memory'],child_maxrss_kib=p['child_maxrss_kib'],sampled_max_kib={k:max(v) for k,v in mem.items()})
ck(summary==post['resource_summary'] and len(resources)==775 and max(mem['VmPeak'])==8*1024**2 and summary['min_available_kib']==14527116 and p['terminal_memory']==dict(available_kib=22493520,swap_used_kib=0),'resource summary exact')
ck('resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))' in (D/'guard.py').read_text() and 'preexec_fn=limits' in (D/'guard.py').read_text(),'address space cap installed')
binds(post);ck(post['all_passed'] is True and post['qualification_accepted'] is False and post['pure_timeout_qualification_proven'] is False and len(post['checks'])==21 and all(post['checks'].values()),'supplemental diagnostic disposition')
# Fresh local proc closure, no signalling or subprocess; inaccessible exe reported.
live=[];unreadable_exe=[];unreadable_identity=[]
for path in Path('/proc').glob('[0-9]*'):
 try:
  fields=(path/'stat').read_text().rsplit(')',1)[1].split();comm=(path/'comm').read_text().strip();argv=(path/'cmdline').read_bytes().split(b'\0',1)[0].decode(errors='replace');exe=''
  try:exe=str((path/'exe').resolve(strict=True))
  except PermissionError:unreadable_exe.append(int(path.name))
  except FileNotFoundError:pass
  if int(fields[2]) in groups or int(fields[3]) in groups or any(Path(z).name.lower().startswith('julia') for z in (comm,argv,exe)):live.append(dict(pid=int(path.name),pgid=int(fields[2]),sid=int(fields[3]),comm=comm,argv0=argv,exe=exe))
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:unreadable_identity.append(int(path.name))
ck(not live and not unreadable_identity,'fresh292 PGID AND SID no visible Julia')
raw_files=sorted(str(f) for root in [RUN,O] for f in root.rglob('*') if f.is_file());raw_hashes={n:digest(n) for n in raw_files}
ck(all(raw_hashes[n]==sha(n) for n in raw_files),'final raw rehash stable')
result=dict(all_passed=True,qualification_accepted=False,count=len(checks),checks=checks,unique_hashed_files=len(hashes),seal_subjects=2352,admission_subjects=2353,launch_subjects=2357,baseline_files=sum(map(len,bl.values())),runtime_entries=len(rt['inventory']),source_sites=len(sites),prefix_totals=tot,costs=costs,resources=summary,raw_file_count=len(raw_files),sha256=raw_hashes,checker_sha256=digest(__file__),fresh_host=dict(groups=sorted(groups),matches=live,unreadable_exe_pids=unreadable_exe,unreadable_identity_pids=unreadable_identity,time=time.time()),scope='Independent exact saved OOM diagnostic review; full RED remains rejected; no project imports, prior checker, auditor, Julia or subprocess execution')
with (E/'independent-result-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['all_passed','count','unique_hashed_files','raw_file_count','prefix_totals']}))
