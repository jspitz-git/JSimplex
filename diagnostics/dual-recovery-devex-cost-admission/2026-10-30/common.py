"""Two sequential cost phases; definitions only, never Julia on import."""
from pathlib import Path
import hashlib,json,math,os,subprocess
D=Path(__file__).resolve().parent
W=D.parents[2]
ORIGINAL=W/'diagnostics/dual-recovery-devex-task4/2026-10-30'
OLD_RED=W/'diagnostics/dual-recovery-devex-task4-red/2026-10-30'
OLD_GREEN=W/'diagnostics/dual-recovery-devex-task4-green/2026-10-30'
FIX=W/'diagnostics/dual-recovery-devex-green-fixture-preparation/2026-10-30'
GREEN2_PREP=W/'diagnostics/dual-recovery-devex-green2-admission/2026-10-30'
GREEN2_RESULT=W/'diagnostics/dual-recovery-devex-green2-result/2026-10-30'
RUN=W/'.superpowers/dual-recovery-devex-task4/cost-1'
PHASES=('reference-cost','candidate-cost')
BASE=1033.6005972509156
TOTAL=1800
MASTER='c0fa748ffa61ccb7c1caaf248c40324f60bc737b'
JULIA='/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/bin/julia'
DEPOTS='/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/memory-probe/depot:/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/precompiled-full/depot:/home/jspitz/JSimplex.jl/.worktrees/ft-numerical-recovery/.superpowers/ft-recovery/depot:/home/jspitz/JSimplex.jl/.worktrees/simplex-legacy-stability/.superpowers/stability/depot:/home/jspitz/JSimplex.jl/.worktrees/simplex-performance/.superpowers/performance/depot:/home/jspitz/JSimplex.jl/.worktrees/simplex-modernization/.superpowers/sdd/2026-09-22-simplex-modernization/julia-depot:/home/jspitz/.julia'
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

def identity(pid):
 p=Path('/proc')/str(pid);s=(p/'stat').read_text();a=s[s.rfind(')')+2:].split()
 return dict(pid=int(pid),pgid=int(a[2]),sid=int(a[3]),start_ticks=int(a[19]),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace'))
def phase_ok(phase):require(phase in PHASES,'unknown cost phase')
def out(phase):phase_ok(phase);return RUN/phase
def side(phase):phase_ok(phase);return phase.split('-')[0]
def command(phase):
 return [JULIA,'--startup-file=no','--history-file=no','--color=no','--compiled-modules=existing','--pkgimages=existing','--threads=1','--gcthreads=1,0','--heap-size-hint=2G','--check-bounds=yes','--project='+str(ORIGINAL/'overlays'/side(phase)),str(ORIGINAL/'cost.jl'),side(phase)]
def environment(phase):
 return dict(JULIA_DEPOT_PATH=DEPOTS,JULIA_LOAD_PATH='@:@stdlib',JULIA_PKG_OFFLINE='true',JULIA_PKG_PRECOMPILE_AUTO='0',JULIA_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',JULIA_IMAGE_THREADS='1',JULIA_NUM_PRECOMPILE_TASKS='1',TASK4_OUTPUT=str(out(phase)/'result.toml'))
def driver_ready():
 c=read(D/'contract.json')
 require(sha(ORIGINAL/'cost.jl')==c['driver_sha256'] and sha(ORIGINAL/'tests/reference.jl')==c['reference_sha256'],'cost driver/reference changed')
 require(c['cost']==read(ORIGINAL/'contract.json')['cost'],'original measurement schedule changed')
 return True
def mapped_bindings(record,maps):
 return all(sha(maps.get(p,p))==h for p,h in record['bindings'].items())
def base_prior():
 red=read(OLD_RED/'red/audit.json');require(red['accepted'] is True and red['test_summary']==dict(Pass=7,Fail=1,Total=8),'RED acceptance')
 require(mapped_bindings(red,read(OLD_RED/'closure.json')['explicit_exact_copy_maps']),'RED raw bindings')
 bad=read(OLD_GREEN/'green/supervisor.json');require(bad['accepted'] is False and bad['returncode']==1 and not (OLD_GREEN/'green/audit.json').exists(),'failed GREEN preserved')
 g=read(GREEN2_RESULT/'green2/audit.json');review=read(GREEN2_RESULT/'review-final.json');maps=read(GREEN2_RESULT/'closure.json')['explicit_exact_copy_maps']
 require(g['accepted'] is True and g['test_summary']==dict(Pass=5774,Total=5774) and mapped_bindings(g,maps),'GREEN2 audit')
 require(review['accepted'] is True and review['runtime_accepted'] is True and review['production_admission'] is False and review['cost_qualified'] is False and mapped_bindings(review,maps),'GREEN2 independent result')
 durations=[];facts=[]
 for folder,rel,accepted in [(OLD_RED,'red',True),(OLD_GREEN,'green',False),(GREEN2_RESULT,'green2',True)]:
  p=folder/rel/'completion.json';a=read(p);require(a['supervisor_accepted'] is accepted,'prior outcome')
  durations.append(a['elapsed_inclusive_seconds']);facts.append(dict(phase=rel,accepted=accepted,elapsed=a['elapsed_inclusive_seconds'],completion_sha256=sha(p)))
 used=accumulate(durations)
 require(used==BASE==read(GREEN2_RESULT/'green2/completion.json')['total_inclusive_seconds'],'prior total reset')
 return used,facts
def reference_files():
 r=out('reference-cost');attempt=read(r/'attempt.json');ad=read(attempt['admission_path'])
 return sorted(set([str(p) for p in r.rglob('*') if p.is_file()]+[attempt['admission_path'],ad['review_report']]))
def validate_closed(phase):
 r=out(phase);closed=read(r/'closed.json');audit=read(r/'audit.json')
 require(closed['accepted'] is True and closed['phase']==phase and closed['host']['conflicts']==[] and not closed['host']['still_active_current_launcher'],'postexit closure')
 require(audit['accepted'] is True and audit['test_summary']==dict(Pass=272,Total=272) and all(sha(p)==h for p,h in audit['bindings'].items()),'previous cost audit')
 require(all(sha(p)==h for p,h in closed['bindings'].items()),'postexit files changed')
 actual={str(p) for p in r.rglob('*') if p.is_file() and p.name!='closed.json'}
 attempt=read(r/'attempt.json');ad=read(attempt['admission_path']);actual.update((attempt['admission_path'],ad['review_report']))
 require(set(closed['bindings'])==actual,'postexit file membership')
 require(closed['head']==read(r/'seal.json')['head'],'historical closed HEAD')
 require(set(closed['host']['checked_groups'])==expected_groups(phase,closed['host']['boot_id'],True),'full closed groups/sessions')
 import cost_checks
 import tomllib
 cost_checks.check_cost(tomllib.loads((r/'result.toml').read_text()),side(phase))
 return closed
def prior(phase):
 phase_ok(phase);used,facts=base_prior()
 if phase=='candidate-cost':
  validate_closed('reference-cost');r=out('reference-cost');a=read(r/'completion.json')
  require(a['supervisor_accepted'] is True and a['total_inclusive_seconds']==BASE+a['elapsed_inclusive_seconds'],'reference time/outcome')
  used=accumulate([BASE,a['elapsed_inclusive_seconds']])
  facts.append(dict(phase='reference-cost',accepted=True,elapsed=a['elapsed_inclusive_seconds'],audit_sha256=sha(r/'audit.json'),completion_sha256=sha(r/'completion.json'),closed_sha256=sha(r/'closed.json')))
 require(used<TOTAL,'shared1800 exhausted');return used,facts
def required_paths(phase):
 phase_ok(phase);paths=set()
 for folder in (ORIGINAL,OLD_RED,OLD_GREEN,FIX,GREEN2_PREP,GREEN2_RESULT,D):
  pub=read(folder/'publication.json');require(pub['accepted'] is True,'unpublished preparation')
  a=[W/n for n in pub['expected_names']];require(all(p.is_file() and not p.is_symlink() for p in a),'published file mode/membership');paths.update(a)
 runtime=Path(JULIA).parents[1]
 paths.update([Path(os.sys.executable).absolute(),Path(JULIA),runtime/'lib/libjulia.so.1.13.0',runtime/'lib/julia/sys.so',runtime/'lib/julia/libjulia-internal.so.1.13.0',runtime/'share/julia/base/timing.jl'])
 if phase=='candidate-cost':paths.update(Path(p) for p in reference_files())
 return sorted(str(p) for p in paths)
def check_inventory(pins,required):
 require(type(pins.get('files')) is list and len(pins['files'])==len(set(pins['files'])) and set(pins['files'])==set(required),'pin files membership')
 require(pins.get('trees')==[] and pins.get('inputs')==[] and set(pins['inventory'])==set(required),'pin inventory membership')
 for n,v in pins['inventory'].items():
  require(type(v) is dict and str(Path(n).resolve(strict=True))==v.get('resolved') and sha(n)==v.get('sha256'),'pin hash/resolved target '+n)
 return True
def admission_fields(seal,ad,current,phase):
 phase_ok(phase)
 require(ad.get('accepted') is True and ad.get('scope')=='numerical_admission' and ad.get('phase')==seal.get('phase')==phase,'fresh phase numerical admission')
 require(type(current) is str and len(current)==40 and current==seal.get('head')==ad.get('head'),'admitted HEAD')
 require(ad.get('command')==seal.get('command')==command(phase),'admitted exact command')
def validate_admission(seal,pins,path,current,phase):
 ad=read(path);admission_fields(seal,ad,current,phase);r=out(phase)
 require(ad.get('seal_sha256')==sha(r/'seal.json') and ad.get('pins_sha256')==sha(r/'pins.json')==seal.get('pins_sha256'),'admission concrete seal/pins')
 require(sha(ad['review_report'])==ad.get('review_report_sha256'),'admission report')
 require(type(ad.get('checks')) is dict and ad['checks'] and all(v is True for v in ad['checks'].values()),'admission checks')
 b=ad.get('bindings');require(type(b) is dict and set(pins['inventory'])<=set(b),'admission full pin coverage')
 require(b.get(str(r/'seal.json'))==sha(r/'seal.json') and b.get(str(r/'pins.json'))==sha(r/'pins.json'),'concrete seal/pins coverage')
 require(all(sha(n)==h for n,h in b.items()),'admission bindings')
 return ad
def owners(phase):
 records=[];r=out(phase)
 if (r/'attempt.json').exists():records.append(('launcher',read(r/'attempt.json')['runner']))
 for n in ('current.json','process.json'):
  if (r/'guard'/n).exists():
   a=read(r/'guard'/n);records.extend((k,a[k]) for k in ('runner','child') if k in a)
 return records
def expected_groups(phase,boot,include_current_launcher):
 old=read(D/'host.json')['host'];groups=set(old['checked_groups']) if boot==old['boot_id'] else set()
 for p in PHASES[:PHASES.index(phase)+1]:
  for role,a in owners(p):
   if a['boot_id']==boot and (include_current_launcher or p!=phase or role!='launcher'):groups.update((a['pgid'],a['sid']))
 return groups
def host():
 old=read(D/'host.json')['host'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();groups=set(old['checked_groups']) if boot==old['boot_id'] else set();excluded=[];me=identity(os.getpid())
 for phase in PHASES:
  for role,a in owners(phase):
   if a['boot_id']!=boot:continue
   if role=='launcher' and all(a[k]==me[k] for k in ('pid','start_ticks','boot_id')):excluded.append(a)
   else:groups.update((a['pgid'],a['sid']))
 conflicts=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   a=identity(p.name);comm=(p/'comm').read_text().strip()
   if comm.lower().startswith('julia') or a['pgid'] in groups or a['sid'] in groups:conflicts.append(a)
  except (FileNotFoundError,ProcessLookupError):pass
 require(not conflicts,'Julia/group/session present '+str(conflicts))
 m={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()};memory=dict(available_kib=m['MemAvailable'],swap_used_kib=m['SwapTotal']-m['SwapFree'])
 require(memory['available_kib']>=6*1024**2 and memory['swap_used_kib']<=1024**2,'memory pressure')
 refs={k:git('rev-parse',k) for k in ('HEAD','master','origin/master')}
 require(refs['master']==refs['origin/master']==MASTER,'master changed')
 require(not git('diff','HEAD','--name-only') and not git('diff','--cached','--name-only') and not git('diff','master','HEAD','--','src','test','Project.toml','.github'),'tracked files/source changed')
 return dict(boot_id=boot,checked_groups=sorted(groups),conflicts=[],memory=memory,refs=refs,still_active_current_launcher=excluded,scope='prior/all phase groups ANDsessions; live own launcher explicitly deferred to close.py')
def guard_command(seal,started,phase):
 remaining=TOTAL-seal['used_seconds'];r=out(phase)
 return [seal['guard_python'],'-B',str(D/'guard/guard_reviewed.py'),'run',str(r/'pins.json'),str(r/'guard'),'--expected-exit','0','--seconds',str(remaining-12),'--deadline',str(started+remaining-12),'--',*command(phase)]
def ensure_unused(phase):
 r=out(phase);require(not any((r/n).exists() for n in ('attempt.json','guard','result.toml','completion.json','audit.json','closed.json')),'phase attempt/output consumed')
