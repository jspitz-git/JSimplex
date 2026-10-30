"""GREEN2 definitions only: no reservation, process launch or Julia on import."""
from pathlib import Path
import hashlib,json,math,os,subprocess
import fixture_check
D=Path(__file__).resolve().parent
W=D.parents[2]
FIX=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30'
PREPARED=FIX/'prepared'
ORIGINAL=W/'diagnostics/dual-recovery-devex-task4/2026-10-30'
OLD_RED=W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30'
OLD_GREEN=W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30'
OUT=W/'.superpowers/dual-recovery-devex-task4/green2-1'
MASTER='c0fa748ffa61ccb7c1caaf248c40324f60bc737b'
USED=527.9604928489425
TOTAL=1800
JULIA='/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/bin/julia'
def require(v,m):
 if not v:raise ValueError(m)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def fresh(p,value):
 with Path(p).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def git(*args):return subprocess.check_output(['git','-C',str(W),*args],text=True).strip()
def number(v):return type(v) in (int,float) and math.isfinite(v) and v>=0
def accumulate(values):
 require(type(values) is list and values and all(number(v) and v>0 for v in values),'invalid prior time')
 return sum(values)
def includes():return read(ORIGINAL/'contract.json')['green_includes']
def fixtures():
 return fixture_check.check(PREPARED,read(D/'fixture-manifest.json'))
def command():
 return [JULIA,'--startup-file=no','--history-file=no','--color=no','--compiled-modules=existing','--pkgimages=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--check-bounds=yes','--project='+str(PREPARED/'overlays/candidate'),str(PREPARED/'green.jl')]
def environment():
 return dict(JULIA_DEPOT_PATH=DEPOTS,JULIA_LOAD_PATH='@:@stdlib',JULIA_PKG_OFFLINE='true',JULIA_PKG_PRECOMPILE_AUTO='0',JULIA_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',JULIA_IMAGE_THREADS='1',JULIA_NUM_PRECOMPILE_TASKS='1',TASK4_OUTPUT=str(OUT/'result.toml'))
def prior():
 red=read(OLD_RED/'red/audit.json');mapping=read(OLD_RED/'closure.json')['explicit_exact_copy_maps']
 require(red['accepted'] is True and red['test_summary']==dict(Pass=7,Fail=1,Total=8),'prior RED')
 require(all(sha(mapping.get(p,p))==h for p,h in red['bindings'].items()),'prior RED raw changed')
 green=read(OLD_GREEN/'green/supervisor.json')
 require(green['accepted'] is False and green['returncode']==1 and not (OLD_GREEN/'green/audit.json').exists(),'failed GREEN incorrectly accepted')
 rd=read(OLD_RED/'red/completion.json');gd=read(OLD_GREEN/'green/completion.json')
 used=accumulate([rd['elapsed_inclusive_seconds'],gd['elapsed_inclusive_seconds']])
 require(used==gd['total_inclusive_seconds']==USED and rd['total_inclusive_seconds']==rd['elapsed_inclusive_seconds'],'prior time reset/changed')
 require(gd['supervisor_accepted'] is False and rd['supervisor_accepted'] is True,'prior completion semantics')
 facts=[dict(phase='red',accepted=True,elapsed=rd['elapsed_inclusive_seconds'],completion_sha256=sha(OLD_RED/'red/completion.json'),audit_sha256=sha(OLD_RED/'red/audit.json')),dict(phase='failed-green',accepted=False,elapsed=gd['elapsed_inclusive_seconds'],completion_sha256=sha(OLD_GREEN/'green/completion.json'),supervisor_sha256=sha(OLD_GREEN/'green/supervisor.json'))]
 return used,facts
def required_paths():
 paths=set()
 for folder in (ORIGINAL,OLD_RED,OLD_GREEN,FIX,D):
  pub=read(folder/'publication.json');require(pub['accepted'] is True,'unpublished preparation')
  paths.update(W/n for n in pub['expected_names'])
 runtime=Path(JULIA).parents[1]
 paths.update([Path(os.sys.executable).absolute(),Path(JULIA),runtime/'lib/libjulia.so.1.13.0',runtime/'lib/julia/sys.so',runtime/'lib/julia/libjulia-internal.so.1.13.0',runtime/'share/julia/base/timing.jl'])
 return sorted(str(p) for p in paths)
def expected_inputs():return sorted(str(PREPARED/p) for p in read(D/'fixture-manifest.json')['fixtures'])
def check_inventory(pins,required,inputs):
 require(type(pins.get('files')) is list and len(pins['files'])==len(set(pins['files'])) and set(pins['files'])==set(required),'pin files membership')
 require(pins.get('trees')==[] and pins.get('inputs')==inputs and set(pins['inventory'])==set(required),'pin inventory/inputs membership')
 for n,v in pins['inventory'].items():
  require(type(v) is dict and str(Path(n).resolve(strict=True))==v.get('resolved') and sha(n)==v.get('sha256'),'pin hash/target '+n)
 return True
def admission_fields(seal,ad,current):
 require(ad.get('accepted') is True and ad.get('scope')=='numerical_admission' and ad.get('phase')==seal.get('phase')=='green2','fresh GREEN2 numerical admission required')
 require(type(current) is str and len(current)==40 and current==seal.get('head')==ad.get('head'),'admitted HEAD changed')
 require(ad.get('command')==seal.get('command')==command(),'admitted command changed')
def identity(pid):
 p=Path('/proc')/str(pid);s=(p/'stat').read_text();a=s[s.rfind(')')+2:].split()
 return dict(pid=int(pid),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
def host(extra=()):
 old=read(D/'host.json')['host'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 groups=set(old['checked_groups']) if boot==old['boot_id'] else set()
 groups.update(extra);excluded=[]
 owners=[]
 if (OUT/'attempt.json').exists():owners.append(read(OUT/'attempt.json')['runner'])
 for record in ('current.json','process.json'):
  if (OUT/'guard'/record).exists():
   proc=read(OUT/'guard'/record);owners.extend(proc[k] for k in ('runner','child') if k in proc)
 me=identity(os.getpid())
 for a in owners:
  if a['boot_id']!=boot:continue
  if all(a[k]==me[k] for k in ('pid','start_ticks','boot_id')):
   excluded.append(a) # launcher must remain alive until its own audit finishes
  else:groups.update((a['pgid'],a['sid']))
 conflicts=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=identity(p.name);comm=(p/'comm').read_text().strip()
   if comm.lower().startswith('julia') or a['pgid'] in groups or a['sid'] in groups:conflicts.append(a)
  except (FileNotFoundError,ProcessLookupError):pass
 require(not conflicts,'Julia/group/session present '+str(conflicts))
 m={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()}
 memory=dict(available_kib=m['MemAvailable'],swap_used_kib=m['SwapTotal']-m['SwapFree'])
 require(memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2,'memory pressure')
 refs={k:git('rev-parse',k) for k in ('HEAD','master','origin/master')}
 require(refs['master']==refs['origin/master']==MASTER,'master changed')
 require(not git('diff','HEAD','--','src','test','Project.toml','.github') and not git('diff','master','HEAD','--','src','test','Project.toml','.github'),'production/test changed')
 return dict(boot_id=boot,checked_groups=sorted(groups),conflicts=[],memory=memory,refs=refs,still_active_current_launcher=excluded,scope='full prior groups AND sessions/new guard-child closure; own live launcher explicitly deferred to independent postexit closure')

DEPOTS='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/memory-probe/depot:/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/precompiled-full/depot:/home/jspitz/JSimplex.jl/.worktrees/ft-numerical-recovery/.superpowers/ft-recovery/depot:/home/jspitz/JSimplex.jl/.worktrees/simplex-legacy-stability/.superpowers/stability/depot:/home/jspitz/JSimplex.jl/.worktrees/simplex-performance/.superpowers/performance/depot:/home/jspitz/JSimplex.jl/.worktrees/simplex-modernization/.superpowers/sdd/2026-09-22-simplex-modernization/julia-depot:/home/jspitz/.julia'
def validate_admission(seal,pins,path,current):
 ad=read(path);admission_fields(seal,ad,current)
 require(ad.get('seal_sha256')==sha(OUT/'seal.json') and ad.get('pins_sha256')==sha(OUT/'pins.json')==seal.get('pins_sha256'),'admission seal/pins changed')
 require(sha(ad['review_report'])==ad.get('review_report_sha256'),'admission report changed')
 require(type(ad.get('checks')) is dict and ad['checks'] and all(v is True for v in ad['checks'].values()),'admission checks')
 bindings=ad.get('bindings');require(type(bindings) is dict and set(pins['inventory'])<=set(bindings),'admission runtime coverage')
 require(bindings.get(str(OUT/'seal.json'))==sha(OUT/'seal.json') and bindings.get(str(OUT/'pins.json'))==sha(OUT/'pins.json'),'admission must bind concrete seal and pins')
 require(all(sha(n)==h for n,h in bindings.items()),'admission binding changed')
 return ad
def guard_command(seal,started):
 remaining=TOTAL-seal['used_seconds']
 return [seal['guard_python'],'-B',str(D/'guard/guard_reviewed.py'),'run',str(OUT/'pins.json'),str(OUT/'guard'),'--expected-exit','0','--seconds',str(remaining-12),'--deadline',str(started+remaining-12),'--',*command()]
def ensure_unused(out):
 require(not any((Path(out)/p).exists() for p in ('attempt.json','guard','result.toml','completion.json','audit.json')),'GREEN2 attempt/output already consumed')
