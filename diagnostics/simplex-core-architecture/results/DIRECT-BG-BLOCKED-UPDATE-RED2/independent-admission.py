"""Independent read-only exact-stage admission; writes only fresh reviewer evidence/receipt.
Never imports launch/seal/outer/audit main, runs Julia, reserves, or releases.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS'
D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2');Q=H/'outers/red300';RUN=H/'runs/red300'
MASTER='26e2291745999f485a74f643298ca997d65c7205';HEAD='b6c37d08e94fc3e6c6b28a967a8f995549929e94';BOOT='1ecae454-f1f5-4e2e-a95c-7b5474243126'
W=Path('/home/jspitz/.codex/worktrees/native-pivot-production-integration/JSimplex.jl')
checks=[];hashes={}
def check(v,label):
 checks.append(dict(check=label,passed=bool(v)))
 if not v:raise AssertionError(label)
def rd(p):return json.loads(Path(p).read_text())
def digest(p):
 d=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):d.update(b)
 return d.hexdigest()
def bound(j,key='sha256'):
 for n,h in j[key].items():
  p=Path(n);p=p if p.is_absolute() else R/p
  actual=hashes.get(str(p)) or digest(p)
  check(actual==h,'bound '+str(p))
def git(*a,root=R):return subprocess.check_output(['git',*a],cwd=root,text=True).strip()
def save(p,j):
 with Path(p).open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def identity(pid):
 p=Path('/proc')/str(pid);a=(p/'stat').read_text().rsplit(')',1)[1].split()
 return dict(pid=pid,pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
def host(groups):
 matches=[];unreadable=[];unreadable_identity=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   i=identity(int(p.name));comm=(p/'comm').read_text().strip();argv0=(p/'cmdline').read_bytes().split(b'\0',1)[0].decode(errors='replace');exe=''
   try:exe=str((p/'exe').resolve(strict=True))
   except PermissionError:unreadable.append(int(p.name))
   except FileNotFoundError:pass
   if i['pgid'] in groups or i['sid'] in groups or any(Path(v).name.lower().startswith('julia') for v in [comm,argv0,exe]):matches.append(dict(i,comm=comm,argv0=argv0,exe=exe))
  except (FileNotFoundError,ProcessLookupError):pass
  except PermissionError:unreadable_identity.append(int(p.name))
 mem={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()}
 return dict(time=time.time(),matches=matches,groups=sorted(groups),unreadable_exe_pids=unreadable,unreadable_identity_pids=unreadable_identity,memory=dict(available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),head=git('rev-parse','HEAD'),master=git('rev-parse','master'),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
start=time.time();s=rd(RUN/'sealed.json');cfg=rd(RUN/'config.json');ready=rd(Q/'outer-ready.json');prep=rd(H/'preparation-pins.json');review=rd(H/'review.json');stage=rd(H/'stages.json')['red'];repair=rd(H.with_name('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR')/'stage.json')
check(s['phase']=='red300' and s['head']==HEAD and s['master']==MASTER and s['boot_id']==BOOT,'sealed phase/ref/boot')
check(s['config']==cfg and cfg['phase']=='red300' and cfg['mode']=='red' and cfg['seconds']==300 and cfg['expected_exit']==1,'exact configured RED300')
check(len(s['files'])==len(set(s['files']))==len(s['inventory'])==1996 and set(s['files'])==set(s['inventory']),'1996 exact file/inventory membership')
prepared=set(prep['sha256'])|{str(H/'preparation-pins.json'),str(H/'review.json')}|set(review['evidence_sha256'])
expected=prepared|set(rd(H/'runtime-inputs-complete.json')['inventory'])|{str(root/n) for label,root in [('diagnostic',R),('production',W)] for n in rd(H/'baseline.json')[label]}|{str(Path(stage['path'])/n) for n in stage['sha256']}|{str(RUN/'host.json'),str(RUN/'config.json'),str(Q/'outer-ready.json')}
check(s['files']==sorted(expected),'independently reconstructed exact seal membership')
check(s['trees']==[stage['path'],str(R/'diagnostics/direct-bg-blocked-update/reproduce')] and s['inputs']==[],'exact tree/input set')
physical=set(s['files'])
for root in s['trees']:
 p=Path(root);check(p.is_dir() and not p.is_symlink(),'tree root '+root)
 for f in p.rglob('*'):
  check(not(f.is_symlink() and (f.is_dir() or not f.exists())),'tree link '+str(f))
  if f.is_file():physical.add(str(f))
check(physical==set(s['inventory']),'complete physical tree membership')
bytes_read=0
for n,v in s['inventory'].items():
 p=Path(n);check(str(p.resolve(strict=True))==v['resolved'],'resolved '+n)
 hashes[n]=digest(p);bytes_read+=p.stat().st_size;check(hashes[n]==v['sha256'],'physical sha256 '+n)
check(len(prep['sha256'])==347 and set(prep['sha256'])==set(rd(H/'required-paths.json')['paths']),'preparation exact 347 membership');bound(prep)
check(review['accepted'] is True and review['findings']==[] and review['scope']=='BG blocked U RED2 preparation' and review['launch_admitted'] is False,'independent preparation acceptance only')
check(review['pins_sha256']==digest(H/'preparation-pins.json') and set(review['sha256'])==set(prep['sha256'])|{str(H/'preparation-pins.json')} and len(review['sha256'])==348 and review['independent_checks']==2293,'348 preparation review bindings and prior checks');bound(review);bound(review,'evidence_sha256');bound(rd(H/'publication.json'))
for n,v in rd(H/'copied-files.json').items():check(hashes[str(H/n)]==digest(v['source'])==v['sha256'],'unchanged frozen control '+n)
for n,v in rd(H/'runtime-inputs-complete.json')['inventory'].items():check(s['inventory'][n]==v,'runtime binding '+n)
check(len(stage['sha256'])==75 and stage['path']==repair['stage'] and stage['sha256']==repair['stage_files'] and repair['master']==MASTER,'accepted 75-file repaired stage')
sp=Path(stage['path']);check({str(p.relative_to(sp)) for p in sp.rglob('*') if p.is_file()}==set(stage['sha256']) and not any(p.is_symlink() for p in sp.rglob('*')),'stage exact physical membership without symlinks')
for n,h in stage['sha256'].items():check(hashes[str(sp/n)]==h,'stage file '+n)
for n,v in repair['master_files'].items():
 b=subprocess.check_output(['git','show',MASTER+':'+n],cwd=R);a=(sp/n).read_bytes()
 if n=='src/JSimplex.jl':
  insertion=repair['root_insertion'].encode();check(a.count(insertion)==1,'one ordinary root adapter insertion');a=a.replace(insertion,b'',1)
 check(a==b and hashlib.sha256(b).hexdigest()==v['sha256'],'committed master bytes '+n)
check(len(repair['master_files'])==71,'71 master entries');bound(repair)
for n in ['review.json','publication.json']:
 j=rd(H.with_name('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR')/n);bound(j)
 if n=='review.json':check(j['accepted'] is True and j['findings']==[],'accepted source-only stage repair')
for label,root in [('diagnostic',R),('production',W)]:
 baseline=rd(H/'baseline.json')[label]
 check(set(git('ls-files','src','test','.github','Project.toml',root=root).splitlines())==set(baseline),'source membership '+label)
 for n,h in baseline.items():check(hashes[str(root/n)]==h,'source baseline '+label+'/'+n)
check(git('rev-parse','HEAD',root=W)==MASTER,'production HEAD master')
check(not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only'),'clean tracked tree/index')
check(git('branch','--show-current')=='codex/simplex-core-architecture','diagnostic branch')
e=rd(H/'environment.json');check({k:os.environ.get(k) for k in e}==e,'pinned non-login loading environment')
sys.path.insert(0,str(H));import control as c
check(c.config('red300')==cfg,'definitions-only independently checked config agreement')
for bad in ['green300','red600','red292','RED300','']:
 try:c.config(bad)
 except RuntimeError:pass
 else:raise AssertionError('unexpected allowed phase '+bad)
 check(True,'rejected phase '+repr(bad))
check(cfg['stage']==stage['path'] and cfg['run']==str(RUN) and cfg['output']==str(RUN/'output'),'new absolute run/stage/output routing')
check(c.guard_command(cfg,RUN/'launch-pins.json',123)[-len(cfg['command']):]==cfg['command'] and '--seconds' in c.guard_command(cfg,RUN/'launch-pins.json',123) and c.guard_command(cfg,RUN/'launch-pins.json',123)[6:10]==['--seconds','292','--deadline','415'],'292 inner / 300 inclusive command')
check(ready['waiting_only'] is True and ready['phase']=='red300' and ready['script_sha256']==hashes[str(H/'outer.py')] and ready['expected_launcher']==str(H/'launch.py'),'waiting outer script/launcher linkage')
i=identity(175431);check(i==ready['identity']==s['outer_identity'] and i['pgid']==i['sid']==175431 and i['start_ticks']==13333087 and i['boot_id']==BOOT,'live exact outer identity')
check(time.time()-ready['ready_time']<1200,'outer within admission wait window')
check({p.name for p in RUN.iterdir()}=={'sealed.json','config.json','host.json'} and {p.name for p in Q.iterdir()}=={'outer-ready.json'},'no output/reservation/release/invocation/admission')
schedule=rd(H/'schedule.json');wanted=[f'{n}/{b}' for n in ['dense96','dense256','dense96-long32'] for b in ['native','markowitz']]
check(schedule['expected_red_units']==wanted and len(schedule['units'])==28 and len(schedule['fixtures'])==13,'six N026 expected units / 28 units / 13 fixtures')
check(schedule['units']==['panel','lifecycle']+[f['name']+'/'+b for f in schedule['fixtures'] for b in ['native','markowitz']],'ordered unit schedule')
check(4*sum(f['updates'] for f in schedule['fixtures'])==512,'512 replacements across reference/candidate and both backends')
for n,fragments in {'guard.py':['resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))',"JULIA_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'",'6 * 1024**2','sample[\'swap_used_kib\'] > 1024**2'],'driver.jl':['total[2]==(RED ? 6 : 0)','r["site"]=="N026"','raw["units_completed"]==28'],'launch.py':["res=run/'reservation.json';save(res",'started=time.monotonic()','supervisor.run(cmd,log,cfg[\'output\'],started,cfg[\'seconds\'])'],'audit.py':['not warning_log(log)','Exact exit','Inclusive limit/cleanup']}.items():
 for fragment in fragments:check(fragment in (H/n).read_text(),'reviewed resource/outcome safeguard '+n+' '+fragment)
check('--heap-size-hint=2G' in cfg['command'] and '--threads=1' in cfg['command'] and '--gcthreads=1,0' in cfg['command'] and '--compiled-modules=existing' in cfg['command'],'pinned Julia resource/load flags')
groups=set(s['groups']);check(len(groups)==271 and groups==set(rd(H/'host-entry.json')['groups']),'all 271 prior groups AND sessions')
h=host(groups);check(h['matches']==[] and h['unreadable_identity_pids']==[],'fresh no prior PGID/SID or visible Julia')
check(h['head']==HEAD and h['master']==MASTER and h['boot_id']==BOOT and HEAD+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and MASTER+'\trefs/heads/master' in h['remote'],'fresh local/remote refs and boot')
check(h['memory']['available_kib']>=6*1024**2 and h['memory']['swap_used_kib']<=1024**2,'fresh RAM >=6GiB and swap <=1GiB')
check(identity(175431)==i and not (Q/'release.json').exists() and not (RUN/'output').exists(),'final still waiting no release/output')
seal_sha=digest(RUN/'sealed.json');hashes[str(RUN/'sealed.json')]=seal_sha
check(len(hashes)==1997,'exact admission 1997 hashes including seal')
evidence=dict(accepted=True,findings=[],scope='Independent RED2 exact-stage read-only checks',time=time.time(),checks=checks,check_count=len(checks),sealed_files=1996,admission_bindings=1997,logical_bytes_hashed=bytes_read,host=h,outer_identity=i,seconds_spent=time.time()-start,numerical_execution=False,release_performed=False,unnecessary_new_production_work=False,unnecessary_new_production_memory=False)
save(D/'independent-admission-evidence.json',evidence)
report='''# Independent RED2 exact-stage admission review

Accepted for one explicitly authorized red300 release only. Findings: none. Numerical, runtime and performance acceptance remain false.

The independent checker reconstructs the exact sealed membership, hashes all 1,996 files physically and checks every resolved path, then binds sealed.json as the 1,997th receipt input. Preparation is strictly accepted under its distinct scope, with 347 pins and 348 review bindings; accepted reviewer evidence and publication remain bound. All 75 repaired-stage files match; 71 master entries match Git objects directly after removal of only the documented two adapter includes. Source, runtime, wrapper, loading environment and copied driver/oracle/guard/supervisor bytes remain pinned.

Fresh local/remote HEAD and master, boot identity, all 271 historical PGIDs AND SIDs, live waiting-only outer PID/PGID/SID 175431 and start_ticks 13333087 were checked. No visible Julia, output, reservation, release or invocation exists. Inaccessible executable symlinks are reported explicitly in evidence, so no universal executable-identity proof is asserted. The controller rechecks freshness before launching.

The exact configuration preserves 300 seconds inclusive, 292 seconds inner plus cleanup, one Julia/BLAS thread, gcthreads=1,0, heap hint 2GiB, VM8GiB, RAM>=6GiB and swap<=1GiB. The 28 ordered units, 13 fixtures and 512 replacements are unchanged. Only six N026 failures in dense96, dense256 and dense96-long32, each native/Markowitz, may qualify; every other failure, warning, missing result or load error rejects. GREEN and longer phases are rejected. Reservation is exclusive and there is no automatic retry.

No unnecessary NEW production work, allocations or retained memory was found. Exact master/source/candidate/control bindings support zero new production vector/matrix scans, basis solves, conversions, copies or invariant checks at setup, refactorization, iteration, candidate, recovery or certification frequency. Cold integrity hashing scales with input bytes and occurs at the required integrity boundaries; the runtime inventory IO inside guard duration remains charged. Existing exact-rational O(n^3) relations, BigInt growth, original-B conversions, tracing/checkpoints, Julia initialization and 1536 FTRAN/512 BTRAN stream calls remain material. Candidate scratch and other ownership costs remain as documented in MEMORY-WORK.md. No sparse/dense timings or allocation improvements are claimed and no completion within 300 seconds is promised.

Declined to judge: Julia parsing/loading/ABI and numerical outcomes (this review runs no Julia); actual process cleanup and final resource adherence (future saved evidence required); performance and other precision/full-solver qualification (outside this exact Float64/Int diagnostic admission). These are explicit future acceptance boundaries, not waived requirements.

This review used the requesting-code-review reviewer role. Only this new checker, evidence, report and admission receipt were written. Frozen source/evidence, Git index and refs were untouched. The receipt grants exact-stage admission; it does not itself release the outer.
'''
with (D/'admission-review.md').open('x') as f:f.write(report)
save(RUN/'admission.json',dict(accepted=True,findings=[],scope='BG blocked U RED2 exact-stage admission',phase='red300',pins_sha256=seal_sha,sha256=hashes,evidence_sha256={str(D/n):digest(D/n) for n in ['independent-admission.py','independent-admission-evidence.json','admission-review.md']}))
print(json.dumps(dict(accepted=True,checks=len(checks),sealed_files=1996,admission_bindings=1997,logical_bytes_hashed=bytes_read,admission_sha256=digest(RUN/'admission.json'),memory=h['memory'],seconds_spent=time.time()-start)))
