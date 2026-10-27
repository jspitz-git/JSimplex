from pathlib import Path
import os,json,hashlib,subprocess,shutil,datetime
M=Path('/home/jspitz/JSimplex.jl');R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');O=R/'diagnostics/generic-residual-magnitudes/2026-10-26';D=R/'diagnostics/generic-quality-devex/2026-10-27';BASE='7e306e24f064a8aa214bc88379e059def77661ab'
os.environ['GIT_OPTIONAL_LOCKS']='0'
def git(*a,root=M):return subprocess.check_output(['git','-C',str(root),*a],text=True).strip()
def need(x,s):
 if not x:raise RuntimeError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
need(git('rev-parse','HEAD')==git('rev-parse','master')==git('rev-parse','origin/master')==BASE,'refs')
need(not git('diff','--name-only','HEAD','--','src','test','Project.toml'),'source drift')
seed=json.loads((O/'exception-closure-host.json').read_text());groups=set(seed['groups']);procs=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();a=[s.decode(errors='replace') for s in (p/'cmdline').read_bytes().split(b'\0') if s];comm=(p/'comm').read_text().strip();pg,si=int(st[2]),int(st[3]);need(pg not in groups and si not in groups,'old groups/session');need(not any(Path(s).name.lower().startswith('julia') for s in [comm]+a[:1]),'Julia active');procs.append(dict(pid=int(p.name),pgid=pg,sid=si,start_ticks=int(st[19]),command=a))
 except (FileNotFoundError,ProcessLookupError):pass
mem={s.split(':')[0]:int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'RAMswap')
D.mkdir(parents=True)
def put(n,x):(D/n).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
h=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),groups=sorted(groups),processes=procs,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],no_Julia=True,diagnostic_head=git('rev-parse','HEAD',root=R),master=BASE)
put('host-before.json',h);put('host-seed.json',h)
for n in ['src','test']:shutil.copytree(M/n,D/'baseline'/n)
for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']:shutil.copyfile(M/n,D/'baseline'/n)
put('baseline-tree.json',{str(p.relative_to(D/'baseline')):sha(p) for p in (D/'baseline').rglob('*') if p.is_file()})
old=json.loads((O/'protected-before.json').read_text());put('protected-before.json',{k:{p:sha(p) for p in v} for k,v in old.items()})
keys=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME'];need(all(not os.environ.get(k) for k in keys),'environment overrides');put('environment.json',dict(inherited={k:os.environ[k] for k in keys+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}))
(D/'common.py').write_text((O/'common.py').read_text().replace("TARGET='9bdcd64f3ecb8d1b929906c6d5b24e0e9127cfed'","TARGET='"+BASE+"'"))
(D/'PLAN.md').write_text('''# Whole-function BigFloat residual, quality and Devex savings

Human specification: briefly measure all three proposals for complete-function correctness, time, allocation bytes/events; autonomously integrate accepted variants with all numerical checks and independent review.

A: Existing BF-only dual direction and tableau-row residual checks use the already qualified conditional magnitude at original abs sites. No order/scan/rounding/tolerance/precision/pipeline/alias/exception change. All negative cases remain controls.
B: Add a narrow BF quality-components method for Vector{BigFloat} work/scale, ordinary Matrix{BigFloat} or SparseMatrixCSC{BigFloat}, Vector{BigFloat} x/rhs and ordinary term vector. Original generic/virtual matrix/native/exact/custom array route unchanged. Local private floatmin created lazily only at first eligible underflow comparison, reused ONLY within the fixed-precision callback-free scalar loop. Conditional magnitude at original sites. Preserve both source x reads, product/conversion/subtraction/scale/order/underflow predicates, no zero-predicate shortcut or removed check. No shared output/cache. Measure complete solve_quality!, including wide scratch and original alias/input/precision checks.
C: Existing BF Devex candidate helper computes original fresh product and builds floatmax only for positive infinity. Finite current-precision product cannot exceed current floatmax, NaN/negative infinity remain original min-selected product. Overflow must create a fresh scalar cap EACH TIME; no shared mutable clamp. Preserve all weight max/clamp and candidate/pivot/price/solve behavior.

Task1: exact private namespaces (no production overwrite), ordinary Test correctness before timing, sparse/dense N32/128, BF64/128/256 x five rounding modes, positive/negative/mixed/zero and BF mixed512 stored values, nonfinite/extremes/empty/dim/alias/custom-array fallback controls. Devex shared and actual BTRAN+price paths (4-row basis), quality transposed/nontransposed. Native FP32/64/exact controls where supported. Three warm pairs + nine alternating measured pairs; typed whole-call sink; fixture/reset/cold/warm and GC preparation separately recorded, no filtering, compile/recompile zero required. One guarded short comparison600s. Independent admission and result review; choose each variant independently on correctness and complete-function cost.
Task2: permanent ordinary regression test, focused RED cost expectations supported by Task1; baseline RED before production candidate; stage exact accepted source only; GREEN new tests + unchanged31-file regression closure and core numerics/primal/dual affected tests. No custom recorder/manual Test stack. Preserve older rejected master and allocation exception; do not weaken old thresholds or reinterpret prior failure. If same older allocation gate fails, diagnose without rerun-to-pass and require new explicit release decision unless independently resolved.
Task3: independent production+actualcommit review including work/memory, exact private-index commit, ff-only local master, fresh host/admission, ordinary actual master tests1800s, independent outcome, normal nonforce push to origin/master under current autonomous authorization. Preserve real userfiles/env/indexes and exact beforeimages. No unrelated source changes/CI/HH/automation changes. Diagnostic publication separately on codex/simplex-core-architecture with exact staged names and failfast checks. Current plan broader/fullsuite/x64 remain open.

Global: all completed historical scripts/raw/pins frozen never rerun/rewrite. Reuse existing R isolation for diagnostics and private exact staged source copies; M remains untouched until reviewed integration. Full historical577groups AND sessions/boot+startticks+command/noJulia fresh before any launch. Julia/BLAS1, GC1,0, heap2GiB hint, AS8GiB, RAMavailable6GiB/swap<=1GiB; compiled-modulesexisting. No long LP/fullsuite run; established short ordinary affected regression closure rather than unauthorized hours-long fullsuite. Tests1800s; no numerical retry to select a passing sample; timeout-only longer allowance remains human standing policy. Keep all GC/outliers, no universal/end-to-end/nativefree claim.
''')
(D/'progress.md').write_text('# SDD ledger — plan: '+str(D/'PLAN.md')+'\nRuling: reuse existing isolated R and private stage clones; current human authorizes short experiments, accepted production integration/master verification/push. Preserve evidence instead of deleting skill scratch. Established affected-regression closure used; broad fullsuite remains OPEN to respect no hours-long runs.\nPre-flight: A and C share existing magnitude helper; B owns local comparison-only limit and ordinary typed-array seam. Generic source imports must bind locally changed helpers.\nTask1: preparing, no Julia yet.\n')
shutil.copyfile(__file__,D/'bootstrap.py');print(D,'groups',len(groups),'availableKiB',mem['MemAvailable'])
