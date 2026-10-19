"""Independent saved timeout record review. No Julia, no auditor rerun, no launch."""
from pathlib import Path
import json,hashlib,math,os,re,time,subprocess,tomllib,importlib.util
E=Path(__file__).resolve().parent;D=E.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS');R=D.parents[3];RUN=D/'runs/red300';O=D/'outers/red300'
HEAD='9a537a3ec590351f2a7b516a4efc53f7c790efaa';MASTER='26e2291745999f485a74f643298ca997d65c7205';checks=[]
def rd(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ck(v,n):
 checks.append(dict(name=n,passed=bool(v)))
 if not v:raise AssertionError(n)
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def bind(v,key='sha256'):
 for n,h in v[key].items():ck(sha(Path(n) if Path(n).is_absolute() else R/n)==h,'binding '+n)
def inv(pins):
 paths=set(pins['files'])
 for n in pins['trees']:
  root=Path(n);ck(root.is_dir() and not root.is_symlink(),'tree root '+n)
  for p in root.rglob('*'):
   ck(not p.is_symlink(),'tree regular '+str(p))
   if p.is_file():paths.add(str(p))
 ck(paths==set(pins['inventory']),'exact inventory tree/file membership')
 for n,v in pins['inventory'].items():ck(Path(n).is_file() and sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'],'inventory '+n)
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def main():
 s=rd(RUN/'sealed.json');lp=rd(RUN/'launch-pins.json');cfg=rd(RUN/'config.json');adm=rd(RUN/'admission.json');audit=rd(RUN/'audit.json');closure=rd(RUN/'outer-closure.json');ready=rd(O/'outer-ready.json');oi=rd(O/'outer-invocation.json');outcome=rd(O/'outer-outcome.json');release=rd(O/'release.json');proc=rd(RUN/'output/process.json');cur=rd(RUN/'output/current.json');invocation=rd(RUN/'invocation.json');sup=invocation['supervisor'];res=rd(RUN/'reservation.json')
 ck(sha(RUN/'sealed.json')=='5491b77bcb5ca7280b5ae4faea4e5dd3a421a2d77c7c501a51f0391ccc10c451' and sha(RUN/'admission.json')=='089d296f3351643294860285076c661892c003df17d54970b79908d4c63dcfe1','exact admitted seal/receipt')
 ck(adm['accepted'] is True and adm['findings']==[] and adm['scope']=='BG blocked typed exact-run admission' and adm['phase']=='red300' and adm['pins_sha256']==sha(RUN/'sealed.json'),'admission semantics')
 ck(set(adm['sha256'])==set(s['files'])|{str(RUN/'sealed.json')},'2221 exact admission membership');bind(adm);bind(adm,'evidence_sha256');inv(s);inv(lp)
 expected=set(s['files'])|{str(RUN/n) for n in ['sealed.json','admission.json','prehost.json']}|{str(O/n) for n in ['release.json','outer-invocation.json']}
 ck(set(lp['files'])==expected and lp['trees']==s['trees'] and lp['inputs']==[] and rd(RUN/'output/pins.json')==lp,'exact launch pins and guard copy')
 ck(all(lp['inventory'][n]==v for n,v in s['inventory'].items()),'seal/launch unchanged overlap')
 ck(release==dict(phase='red300',sealed_sha256=sha(RUN/'sealed.json'),admission_sha256=sha(RUN/'admission.json'),outer_ready_sha256=sha(O/'outer-ready.json'),one_attempt=True) and release['one_attempt'] is True,'strict one-attempt release')
 ck(oi==dict(identity=ready['identity'],phase='red300',seal_sha256=sha(RUN/'sealed.json'),review_sha256=sha(RUN/'admission.json'),release_sha256=sha(O/'release.json'),launcher_sha256=sha(D/'launch.py'),method='runpy.run_path launch.py as __main__ in this outer process'),'exact outer invocation')
 ck(s['config']==cfg and cfg['phase']=='red300' and cfg['seconds']==300 and cfg['expected_exit']==1,'RED config unchanged')
 ck(res==dict(one_attempt=True,phase='red300',command=cfg['command'],pins_sha256=sha(RUN/'launch-pins.json'),review_sha256=sha(RUN/'admission.json'),max_seconds=300) and res['one_attempt'] is True,'strict reservation')
 ck(invocation['reservation_sha256']==sha(RUN/'reservation.json') and invocation['review_sha256']==sha(RUN/'admission.json'),'reservation/admission invocation hashes')
 ck(proc['command']==cur['command']==invocation['command']==cfg['command'] and proc['pins_sha256']==cur['pins_sha256']==invocation['pins_sha256']==sha(RUN/'launch-pins.json') and proc['pins_unchanged'] is True,'actual command/integrity')
 gc=[invocation['python'],'-B',str(D/'guard.py'),'run',str(RUN/'launch-pins.json'),str(RUN/'output'),'--seconds','292','--deadline',str(invocation['monotonic_start']+292),'--expected-exit','1','--',*cfg['command']]
 ck(invocation['guard_command']==gc and proc['runner']['command']==' '.join(gc)+' ' and proc['child']['command']==' '.join(cfg['command'])+' ' and proc['cwd']==str(R),'exact guard command/deadline/cwd')
 ck(proc['runner']==cur['runner']==sup['guard_identity'] and proc['child']==cur['child'],'process identity linkage')
 for ident,pid in [(s['outer_identity'],209350),(proc['runner'],210015),(proc['child'],210016)]:ck(ident['pid']==ident['pgid']==ident['sid']==pid and ident['boot_id']==s['boot_id'] and ident['start_ticks']>0,'identity '+str(pid))
 ck(ready['identity']==oi['identity']==outcome['identity']==closure['outer_identity']==s['outer_identity'],'outer identity lineage')
 ck(proc['reason']=='wall_time' and proc['returncode']==-9 and type(proc['returncode']) is int and 292<proc['elapsed_including_launch']<294 and not any(k in proc for k in ['error','remaining_group','remaining_session']),'preserved wall timeout not success')
 ck(sup['soft_timeout'] is True and sup['guard_term'] is True and all(sup[k] is False for k in ['hard_timeout','child_kill','guard_kill','accepted']) and sup['returncode']==1 and 'cleanup_error' not in sup and 294<=sup['elapsed_seconds']<=invocation['elapsed_seconds']<=300,'supervisor failed within inclusive300')
 ck(outcome['launched'] is True and outcome['returncode']==2 and 'Failed attempt preserved; no automatic retry' in outcome['error'] and outcome['elapsed_with_checks_seconds']>=invocation['elapsed_seconds'],'outer failed record; includes checks outside guard')
 runfiles={str(p) for p in RUN.rglob('*') if p.is_file()};outerfiles={str(p) for p in O.iterdir() if p.is_file()}
 ck(len(runfiles)==40 and len(outerfiles)==4 and {Path(n).name for n in outerfiles}=={'outer-ready.json','release.json','outer-invocation.json','outer-outcome.json'},'exact saved run40/outer4')
 ck(set(audit['sha256'])==runfiles-{str(RUN/'audit.json'),str(RUN/'outer-closure.json')} and len(audit['sha256'])==38,'exact prior audit 38 bindings');bind(audit)
 ck(audit['all_passed'] is False and audit['pure_timeout'] is False and audit['error']=="RuntimeError('Exact payload membership')" and audit['result']=={} and audit['phase']=='red300','preserved fail-closed audit')
 cp={str(O/n) for n in ['outer-ready.json','release.json','outer-invocation.json','outer-outcome.json']}|{str(RUN/n) for n in ['sealed.json','admission.json','posthost.json','audit.json']}
 ck(set(closure['sha256'])==cp and closure['all_passed'] is True,'exact external closure8 bindings');bind(closure)
 ck({p.name for p in (RUN/'output').iterdir()}=={'pins.json','current.json','process.json','resources.jsonl','run.log'},'exact guard output5')
 ck(all(not p.is_symlink() for p in RUN.rglob('*')) and all(not p.is_symlink() for p in O.iterdir()),'regular result members')
 full=set(s['groups'])|{209350,210015,210016};ck(len(s['groups'])==286 and len(full)==289,'full289 group/session union')
 for n in ['host.json','prehost.json','posthost.json']:
  h=rd(RUN/n);ck(h['matches']==[] and h['unreadable_identity_pids']==[] and all(h[k]==s[k] for k in ['head','master','boot_id']),'saved clean identity '+n)
 ck(set(rd(RUN/'posthost.json')['groups'])==full-{209350} and set(closure['host']['groups'])==full and closure['host']['matches']==[] and closure['host']['unreadable_identity_pids']==[],'post and external full coverage')
 samples=[json.loads(x) for x in (RUN/'output/resources.jsonl').read_text().splitlines()];ck(len(samples)>1,'resource samples retained');prev=-1
 for z in samples:
  ck(set(z)<={'available_kib','swap_used_kib','elapsed','child_memory'} and {'available_kib','swap_used_kib','elapsed'}<=set(z),'resource schema')
  ck(type(z['elapsed']) in (int,float) and math.isfinite(z['elapsed']) and prev<=z['elapsed']<=proc['elapsed_including_launch'],'monotone finite resource times');prev=z['elapsed']
  if 'child_memory' in z:ck(type(z['child_memory']) is list and all(type(x) is str for x in z['child_memory']),'resource memory text')
 for z in samples+[proc['terminal_memory']]:ck(all(type(z[k]) is int and z[k]>=0 for k in ['available_kib','swap_used_kib']) and z['available_kib']>=6*1024**2 and z['swap_used_kib']<=1024**2,'resource pressure threshold')
 ck(type(proc['child_maxrss_kib']) is int and proc['child_maxrss_kib']>0,'RSS positive integer')
 spec=importlib.util.spec_from_file_location('pure_saved_oracle',D/'oracle.py');oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
 files={p.name for p in (RUN/'payload').iterdir()};expectedfiles={f'unit-{i}.toml' for i in range(1,11)}|{f'cost-{i}.toml' for i in range(1,11)}|{'load.toml','panel-load.toml','tests-load.toml'}
 ck(files==expectedfiles and len(files)==23 and len(oracle.PAYLOAD)==60 and not oracle.PAYLOAD<=files,'exact23 incomplete payload,37 missing')
 data={p.name:tomllib.loads(p.read_text()) for p in (RUN/'payload').iterdir()};schedule=rd(D/'schedule.json');summaries=[];prefix=[0]*4
 for i in range(1,11):
  u=data[f'unit-{i}.toml'];a=oracle.unit(u,i,schedule,'red');ck(True,'strict source-bound unit validator '+str(i));prefix=[x+y for x,y in zip(prefix,a)];e=u['records']['events'];sites=u['records']['sites'];p=e.get('pivot',0);z=e.get('pure_row',0)
  if i==1:
   ck(a==[11768,0,0,0] and all(sites[k]==1 for k in ['P011']+[f'P{j:03}' for j in range(95,103)]),'typed panel all11768 pass')
  else:
   finished=3 if i==2 else 2*schedule['fixtures'][(i-3)//2]['updates'];expected={f'N{k:03}':p for k in range(1,4)}|{'N004':z}|{f'N{k:03}':finished for k in range(5,13)}
   if i==2:
    expected.update({f'L{k:03}':1 for k in range(1,41)})
    for lo,hi,n in [(1,22,2),(31,32,2),(33,35,3)]:
     for k in range(lo,hi+1):expected[f'L{k:03}']=n
    expected['L025']=e.get('catch_overflow',0);expected['L030']=e.get('catch_nonfinite',0)
   else:
    f=schedule['fixtures'][(i-3)//2];updates=f['updates'];expected.update({f'N{k:03}':updates for k in range(15,26)});expected.update(N013=1,N014=1,N021=2*updates,N024=updates if f['pivot_agreement'] else 0,N026=1)
   ck(sites=={k:v for k,v in expected.items() if v},'independent event-derived site multiplicities '+str(i))
  summaries.append(dict(index=i,name=u['name'],totals=a,events=e,apis=u['records']['apis'],failures=u['records']['failures']))
 costs={n:oracle.metrics(v) for n,v in data.items() if not n.startswith('unit-')};ck(len(costs)==13,'13 existing metric records exact six fields/types/ranges')
 ck(prefix[1:]==[2,0,0] and [s['name'] for s in summaries if s['totals'][1]]==['dense96/native','dense96/markowitz'],'exact two observed expected N026 failures')
 log=(RUN/'output/run.log').read_text();ck(not re.search(r'warning|world.?age|method.*overwrit|LoadError|ERROR:|OutOfMemoryError|Test Error|FATAL|GROUP/COUNT MISMATCH',log,re.I),'no warning/error contamination before removing expected failures')
 expectedlog='BEGIN BG blocked U driver red300\n'
 for i in range(1,11):
  u=data[f'unit-{i}.toml'];expectedlog+=f"UNIT BEGIN {i} {u['name']}\n"+''.join('TEST FAILURE: N026 '+f['detail']+'\n' for f in u['records']['failures'])+f"UNIT END {i} {u['name']}\n"
 expectedlog+='UNIT BEGIN 11 sparse256/native\n\n[210016] signal 15: Terminated\nin expression starting at '+str(D/'driver.jl')+':104\n'
 ck(log==expectedlog,'exact prefix log and expected terminal SIGTERM')
 ck(json.loads((RUN/'launcher.log').read_text())==proc,'launcher log equals saved guard process record')
 refs=dict(head=git('rev-parse','HEAD'),master=git('rev-parse','master'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'))
 ck(refs['head']==s['head']==HEAD and refs['master']==s['master']==MASTER and set(refs['remote'].splitlines())=={HEAD+'\trefs/heads/codex/simplex-core-architecture',MASTER+'\trefs/heads/master'},'fresh actual local/remote refs')
 ck(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'no tracked changes')
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();ck(boot==s['boot_id'],'same actual boot');matches=[];unread=[];unreadid=[];processes=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();argv0=(p/'cmdline').read_bytes().split(b'\0',1)[0].decode(errors='replace');exe=''
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unread.append(int(p.name))
   except FileNotFoundError:pass
   z=dict(pid=int(p.name),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),state=a[0],comm=comm,argv0=argv0,exe=exe);processes.append(z)
   if z['pgid'] in full or z['sid'] in full or any(Path(v).name.lower().startswith('julia') for v in [comm,argv0,exe]):matches.append(z)
  except (FileNotFoundError,ProcessLookupError):pass
  except PermissionError:unreadid.append(int(p.name))
 mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};fresh=dict(time=time.time(),groups=sorted(full),matches=matches,unreadable_exe_pids=unread,unreadable_identity_pids=unreadid,processes=processes,boot_id=boot,refs=refs,memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']),scope='Full289 historical/outer/guard/child PGIDs AND SIDs; comm/argv0/readable exe Julia detection, inaccessible exe links explicit visibility limit')
 save(E/'result-full289.json',fresh);ck(matches==[] and unreadid==[],'fresh full289 closure/no visible Julia');ck(fresh['memory']['available_kib']>=6*1024**2 and fresh['memory']['swap_used_kib']<=1024**2,'fresh resources safe')
 ck(not (RUN/'result-review.json').exists(),'no successful RED result receipt/GREEN remains blocked')
 return dict(qualification_accepted=False,pure_timeout=False,run_files=40,outer_files=4,payload_files=23,missing_payload=sorted(oracle.PAYLOAD-files),complete_units=10,prefix_totals=prefix,units=summaries,costs=costs,guard_elapsed=proc['elapsed_including_launch'],supervisor_elapsed=sup['elapsed_seconds'],outer_elapsed=outcome['elapsed_with_checks_seconds'],resource_samples=len(samples),resource_min_available_kib=min(x['available_kib'] for x in samples),resource_max_swap_kib=max(x['swap_used_kib'] for x in samples),child_maxrss_kib=proc['child_maxrss_kib'],fresh_host_sha256=sha(E/'result-full289.json'),reviewed_files_sha256={n:sha(n) for n in sorted(runfiles|outerfiles)})
result={}
try:result=main();result['all_passed']=True
except Exception as e:result.update(all_passed=False,error=repr(e))
result.update(checks=checks,total=len(checks),passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),script_sha256=sha(__file__),julia_executed=False,auditor_rerun=False)
save(E/'result-review-check.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','units','costs','reviewed_files_sha256']},indent=2));raise SystemExit(0 if result['all_passed'] else 1)
