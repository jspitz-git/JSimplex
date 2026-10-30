"""Task4 read-only/pure helpers. Import does not reserve, launch or load Julia."""
from pathlib import Path
import hashlib,json,math,os,subprocess
D=Path(__file__).resolve().parent
W=D.parents[2]
RUN=W/'.superpowers/dual-recovery-devex-task4/qualification-1'
PHASES=('red','green','reference-cost','candidate-cost')
MASTER='c0fa748ffa61ccb7c1caaf248c40324f60bc737b'
JULIA='/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/bin/julia'
DEPOTS='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/memory-probe/depot:/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/precompiled-full/depot:/home/jspitz/JSimplex.jl/.worktrees/ft-numerical-recovery/.superpowers/ft-recovery/depot:/home/jspitz/JSimplex.jl/.worktrees/simplex-legacy-stability/.superpowers/stability/depot:/home/jspitz/JSimplex.jl/.worktrees/simplex-performance/.superpowers/performance/depot:/home/jspitz/JSimplex.jl/.worktrees/simplex-modernization/.superpowers/sdd/2026-09-22-simplex-modernization/julia-depot:/home/jspitz/.julia'
def require(v,m):
 if not v:raise ValueError(m)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def fresh(p,obj):
 with Path(p).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
def read(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git','-C',str(W),*a],text=True).strip()
def phase_ok(p):require(p in PHASES,'unknown phase')
def identity(pid):
 p=Path('/proc')/str(pid);s=(p/'stat').read_text();a=s[s.rfind(')')+2:].split()
 return dict(pid=int(pid),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
def memory():
 r={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()}
 return dict(available_kib=r['MemAvailable'],swap_used_kib=r['SwapTotal']-r['SwapFree'])
def host(extra=()):
 historical=read(D/'host.json');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 groups=set(historical['checked_groups']) if boot==historical['boot_id'] else set();groups.update(extra)
 for p in RUN.glob('*/guard/process.json'):
  r=read(p)
  for k in ('runner','child'):
   a=r.get(k,{})
   if a.get('boot_id')==boot:groups.update((a['pgid'],a['sid']))
 conflicts=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=identity(p.name);comm=(p/'comm').read_text().strip()
   if comm.lower().startswith('julia') or a['pgid'] in groups or a['sid'] in groups:conflicts.append(a)
  except (FileNotFoundError,ProcessLookupError):pass
 require(not conflicts,'Julia/group/session present: '+str(conflicts))
 mem=memory();require(mem['available_kib']>=6*1024**2 and mem['swap_used_kib']<=1024**2,'memory pressure')
 refs={r:git('rev-parse',r) for r in ('HEAD','master','origin/master')}
 require(refs['master']==refs['origin/master']==MASTER,'master changed')
 require(not git('diff','HEAD','--','src','test','Project.toml','.github'),'actual production/test changed')
 return dict(boot_id=boot,checked_groups=sorted(groups),conflicts=conflicts,memory=mem,refs=refs)
def command(phase):
 phase_ok(phase);side='reference' if phase in ('red','reference-cost') else 'candidate'
 entry='red.jl' if phase=='red' else 'green.jl' if phase=='green' else 'cost.jl'
 args=[JULIA,'--startup-file=no','--history-file=no','--color=no','--compiled-modules=existing','--pkgimages=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--check-bounds=yes','--project='+str(D/'overlays'/side),str(D/entry)]
 if entry=='cost.jl':args.append(side)
 return args
def environment(phase):
 return dict(JULIA_DEPOT_PATH=DEPOTS,JULIA_LOAD_PATH='@:@stdlib',JULIA_PKG_OFFLINE='true',JULIA_PKG_PRECOMPILE_AUTO='0',JULIA_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',JULIA_IMAGE_THREADS='1',JULIA_NUM_PRECOMPILE_TASKS='1',TASK4_OUTPUT=str(RUN/phase/'result.toml'))
def previous(phase):
 phase_ok(phase);used=0.0;records=[]
 for p in PHASES[:PHASES.index(phase)]:
  root=RUN/p;a=read(root/'audit.json');require(a['accepted'],'previous stage not accepted')
  require(all(sha(n)==h for n,h in a['bindings'].items()),'previous result changed')
  elapsed=read(root/'completion.json')['elapsed_inclusive_seconds']
  require(type(elapsed) in (int,float) and math.isfinite(elapsed) and elapsed>0,'previous time')
  used+=elapsed;records.append(dict(phase=p,audit_sha256=sha(root/'audit.json'),elapsed=elapsed))
 require(used<1800,'shared budget exhausted')
 return used,records
