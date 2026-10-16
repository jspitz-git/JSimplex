"""Fresh independent offline checks. No project imports or executable numerical paths."""
from pathlib import Path
import hashlib,json,os,subprocess,time,tomllib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/NATIVE-PIVOT-COST-PREPARATION'; RUN=D/'runs/cost'
checks=[]; findings=[]; hashes={}
def rd(p):return json.loads(Path(p).read_text())
def path(p):return Path(p) if Path(p).is_absolute() else R/p
def sha(p):
 p=path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def check(label,v):
 checks.append(dict(name=label,passed=bool(v)))
 if not v:findings.append(label)
def bind(label,m,mapping=None):
 bad=[]
 for n,h in m.items():
  p=path(n);p=(mapping or {}).get(str(p),p)
  try:
   if sha(p)!=h:bad.append(n)
  except OSError as e:bad.append(n+': '+repr(e))
 check(label,not bad);return dict(count=len(m),mismatches=bad)
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
S=rd(RUN/'sealed.json');cfg=rd(RUN/'config.json');P=rd(D/'preparation-pins.json');review=rd(D/'review-final.json');source=rd(D/'source-check.json')
check('seal exact 1001 unique files and matching inventory',len(S['files'])==len(set(S['files']))==1001 and set(S['files'])==set(S['inventory']))
sealbad=[]
for n,v in S['inventory'].items():
 try:
  actual=sha(n);hashes[n]=actual
  if actual!=v['sha256'] or str(Path(n).resolve(strict=True))!=v['resolved']:sealbad.append(n)
 except OSError as e:sealbad.append(n+': '+repr(e))
check('all 1001 sealed contents and realpaths',not sealbad)
check('exact run prelaunch membership',set(p.name for p in RUN.iterdir())=={'config.json','sealed.json','host.json','admission-checks.py'})
check('no numerical outputs reservation or launch files',all(not (RUN/n).exists() for n in ['reservation.json','output','invocation.json','launch-pins.json','launcher.log']))
details={'sealed':dict(count=len(S['files']),mismatches=sealbad)}
details['preparation']=bind('all 920 preparation bindings',P['sha256'])
check('920 exact required preparation names',len(P['sha256'])==920 and set(P['sha256'])==set(rd(D/'required-paths.json')['paths']))
check('accepted exact 921 preparation review',review['accepted'] is True and review['findings']==[] and review['scope']=='offline preparation' and review['pins_sha256']==sha(D/'preparation-pins.json') and set(review['sha256'])==set(P['sha256'])|{str(D/'preparation-pins.json')} and len(review['sha256'])==921)
details['review']=bind('921 preparation review bindings',review['sha256']);details['review_evidence']=bind('preparation supplemental evidence',review['evidence_sha256'])
check('86 accepted preparation checks',rd(D/'reviewer-checks.json')['all_passed'] is True and rd(D/'reviewer-checks.json')['checks']==86)
check('18 source checks 219 bindings',source['all_passed'] is True and source['checks']==18 and len(source['sha256'])==219)
details['source']=bind('all 219 source bindings',source['sha256'])
for name in ['closure.json','publication.json']:
 z=rd(D/name);check('accepted current '+name,z['all_passed'] is True);details[name]=bind('current '+name+' bindings',z['sha256'])
M=rd(D.parent/'NATIVE-PIVOT-PREPARATION/overlay-manifest.json');stage=Path(cfg['stage'])
check('candidate 75 reference 73',len(M['candidate'])==75 and len(M['reference'])==73)
check('exact nonsymlink candidate tree',not stage.is_symlink() and {str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}=={e['destination'] for e in M['candidate']} and not any(p.is_symlink() for p in stage.rglob('*')))
check('75 staged source and original hashes',all(sha(stage/e['destination'])==e['sha256']==sha(e['source']) for e in M['candidate']))
check('73 original reference hashes',all(sha(e['source'])==e['sha256'] for e in M['reference']))
check('sole sealed candidate tree',S['trees']==[str(stage)] and S['inputs']==[])
sm=rd(D/'source-map.json')
check('12 byte-identical copies',len(sm['byte_identical'])==12 and all((D/n).read_bytes()==Path(p).read_bytes() for n,p in sm['byte_identical'].items()))
for n,e in sm['changed'].items():
 text=(D/n).read_text();ok=True
 for edit in reversed(e['edits']):
  ok &= text.count(edit['after'])==1;text=text.replace(edit['after'],edit['before'],1)
 check('exact whole-file inverse '+n,ok and text==Path(e['source']).read_text())
G=D.parent/'NATIVE-PIVOT-GREEN2-PREPARATION/runs/green2';GR=D.parent/'NATIVE-PIVOT-GREEN2';O=D.parent/'NATIVE-PIVOT-QUALIFICATION/runs/green'
a=rd(G/'audit.json');gr=rd(G/'result-review.json');old=rd(O/'audit.json')
check('GREEN2 passed original GREEN remains false',a['all_passed'] is True and a['phase']=='green2' and old['all_passed'] is False and old['phase']=='green')
details['green2_audit']=bind('GREEN2 audit full bindings',a['sha256']);details['failed_green']=bind('failed GREEN audit full bindings',old['sha256'])
check('GREEN2 exact canonical75 review',gr['accepted'] is True and gr['findings']==[] and gr['scope']=='stage result' and gr['phase']=='green2' and gr['pins_sha256']==sha(G/'audit.json') and len(gr['sha256'])==75 and set(gr['sha256'])==set(a['sha256'])|{str(G/'audit.json')})
details['green2_review']=bind('GREEN2 review 75 bindings',gr['sha256']);details['green2_evidence']=bind('GREEN2 separate16 bindings',gr['evidence_sha256']);check('GREEN2 evidence exactly16',len(gr['evidence_sha256'])==16)
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';mapping={str(status):D/'STATUS.md.before-cost',str(road):D/'roadmap.md.before-cost'};derived=[]
for name in ['closure.json','publication.json']:
 z=rd(GR/name);check('GREEN2 accepted '+name,z['all_passed'] is True);details['green2_'+name]=bind('GREEN2 preserved '+name,z['sha256'],mapping)
 for n,h in z['sha256'].items():
  if str(path(n)) in mapping:derived.append(dict(record=str((GR/name).relative_to(R)),pointer=['sha256',n],key=n,sha256=h,preserved_path=str(mapping[str(path(n))].relative_to(R))))
check('exact four independently derived continuation mappings',len(derived)==4 and derived==rd(D/'continuation-mappings.json')['mappings'])
check('214 predecessor groups closed',not rd(GR/'closure-host.json')['matches'] and len(rd(GR/'closure-host.json')['groups'])==214 and set(rd(GR/'closure-host.json')['groups'])==set(S['groups']) and len(set(S['groups']))==214)
inputs=rd(D/'inputs.json');original=rd(D.parent/'NATIVE-ACCURACY-PREPARATION/inputs.json')
check('unchanged original B4 matrices and three RHS',inputs['fixtures']==original['fixtures'] and [f['name'] for f in inputs['fixtures']]==['sparse32','dense32','sparse96','dense96'])
check('TOML JSON same fixtures schedule',tomllib.loads((D/'inputs.toml').read_text())==inputs)
schedule=[]
for f in inputs['fixtures']:
 for r in range(1,12):
  for arm in ('C','P') if r%2 else ('P','C'):schedule.append(dict(id=len(schedule)+1,fixture=f['name'],arm=arm,round=r,warm=r<=3))
check('88 exact alternating windows 24warm 64measured',inputs['schedule']==schedule and len(schedule)==88 and sum(s['warm'] for s in schedule)==24)
check('exact component and native-source counts',rd(D/'budget.json')['cost']==dict(construction=88,refactor=176,forward=2816,transpose=1408,windows=88,fresh_native_source=176,private_lu_source=88) and 88*48==4224)
check('output payload and Info counts',sum(f['matrix']['n']*22*48*8 for f in inputs['fixtures'])==2162688 and 88*4*48*8==135168)
saved=rd(D/'saved-C.json');check('saved C source tokens unchanged',all(sha(v['path'])==v['sha256'] and tomllib.loads(Path(v['path']).read_text())['outputs']==v['outputs'] for vs in saved.values() for v in vs))
expected=['/bin/bash','/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh','--compiled-modules=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--project='+str(stage),str(D/'cost-driver.jl'),str(RUN/'output'),str(stage),str(D/'inputs.toml')]
check('exact one cost command 45 seconds',cfg==S['config'] and cfg['command']==expected and cfg['seconds']==45 and cfg['phase']=='cost' and cfg['arm']=='candidate' and cfg['expected_exit']==0 and cfg['run']==str(RUN) and cfg['output']==str(RUN/'output'))
env=rd(D/'environment.json');check('exact current loading environment',{k:os.environ.get(k) for k in env}==env)
check('expected HEAD master and clean tracked source',git('rev-parse','HEAD')==S['head']=='1dd0bc58a124e365a53c926770c13bd7c494959f' and git('rev-parse','master')==S['master']=='6f68e24e8ddac42b948da8fcc2d636c010751194' and not git('diff','--name-only') and not git('diff','--cached','--name-only'))
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();processes=[];matches=[];unreadable=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();exe=''
  try:exe=str((p/'exe').resolve(strict=True))
  except PermissionError:unreadable.append(int(p.name))
  except FileNotFoundError:pass
  item=dict(pid=int(p.name),pgid=int(s[2]),sid=int(s[3]),start_ticks=int(s[19]),comm=comm,exe=exe,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
  processes.append(item)
  if item['pgid'] in S['groups'] or item['sid'] in S['groups'] or comm.lower().startswith('julia') or Path(exe).name.lower().startswith('julia'):matches.append(item)
 except (FileNotFoundError,ProcessLookupError):pass
mem={line.split(':')[0]:int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()}
host=dict(time=time.time(),boot_id=boot,head=git('rev-parse','HEAD'),master=git('rev-parse','master'),groups=S['groups'],process_count=len(processes),processes=processes,matches=matches,unreadable_exe_pids=unreadable,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],scope='Fresh full /proc stat/comm/readable-exe scan of all214 PGIDs AND SIDs; inaccessible executable symlinks are a visibility limitation')
check('same boot fresh full214 process and Julia absence',boot==S['boot_id'] and not matches)
check('fresh availableRAM6GiB swap1GiB',host['available_kib']>=6*1024**2 and host['swap_used_kib']<=1024**2)
check('pidfd runtime support',hasattr(os,'pidfd_open') and hasattr(__import__('signal'),'pidfd_send_signal'))
save(RUN/'admission-host.json',host)
save(RUN/'admission-checks.json',dict(all_passed=not findings,checks=checks,findings=findings,details=details,scope='Fresh independent offline exact-stage checks; no prior checker or numerical path executed'))
print(json.dumps(dict(all_passed=not findings,check_count=len(checks),findings=findings,sealed=len(hashes),preparation=len(P['sha256']),stage=len(M['candidate']),process_count=len(processes),matches=matches,unreadable_exe_pids=unreadable,available_kib=host['available_kib'],swap_used_kib=host['swap_used_kib'])))
