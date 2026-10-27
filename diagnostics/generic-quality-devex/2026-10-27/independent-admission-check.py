from pathlib import Path
import hashlib,json,re,subprocess,os,datetime
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-devex/2026-10-27')
M=Path('/home/jspitz/JSimplex.jl')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise RuntimeError(m)
def read(n):return json.loads((D/n).read_text())
def create(n,data):
 with (D/n).open('x') as f:
  if isinstance(data,str):f.write(data)
  else:json.dump(data,f,indent=2,sort_keys=True);f.write('\n')
changes=read('changes.json');ref=(D/'reference.jl').read_text();cand=(D/'candidate.jl').read_text()
blocks=re.findall(r'^(?:@inline )?function .*?^end\n',ref,re.M|re.S)
need(len(blocks)==9,'reference function count')
for block in blocks:
 need(sum(block in p.read_text() for p in (M/'src').glob('*.jl'))==1,'reference differs from authoritative production '+block.splitlines()[0])
for key in ('A1','A2','C'):
 c=changes[key];need(c['old'] in (M/'src'/c['file']).read_text(),'change old mismatch '+key)
want=ref.replace('module SavingsReference','module SavingsCandidate',1)
for key in ('A1','A2','C'):
 c=changes[key];need(want.count(c['old'])==1,'private replacement count '+key);want=want.replace(c['old'],c['new'],1)
b=changes['B'];need(b['new'].endswith(b['old']),'quality insertion marker');extra=b['new'][:-len(b['old'])]
want=want.replace('function _wide_solve_quality!',extra+'function _wide_solve_quality!',1)
need(want==cand,'candidate has undeclared differences')
header=ref[:ref.index('function _dual_direction')]
for local in ('_quality_components!','_accumulate_quality_term!','_wide_solve_quality!','solve_quality!','_primal_devex_candidate_weight','_primal_update_devex!'):
 need(re.search(r'(?<![A-Za-z0-9_])'+re.escape(local)+r'(?![A-Za-z0-9_!])',header) is None,'changed helper imported '+local)
for key in ('A1','A2'):need(changes[key]['new']==changes[key]['old'].replace('abs(','_primal_direction_magnitude('),'A alteration')
c=read('contract.json');need(c['cases']==1160 and c['measured_windows']==20880 and c['shared_limit_seconds']==600 and c['guard_limit_seconds']==592 and c['attempts']==1,'contract')
need(not (D/'reservation.json').exists() and not (D/'output').exists(),'launch already attempted')
env=read('environment.json')['inherited'];need(env=={},'expected clean inherited environment')
for k in ['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']:
 need(not os.environ.get(k),'environment override '+k)
pins=read('pins.json');inventory=pins['inventory']
for name,expected in inventory.items():need(str(Path(name).resolve(strict=True))==expected['resolved'] and sha(name)==expected['sha256'],'pin drift '+name)
for tree in pins['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={name for name in inventory if Path(name).is_relative_to(tree)},'tree membership '+tree)
base=read('baseline-tree.json')
for name,v in base.items():need(sha(D/'baseline'/name)==v,'baseline tree '+name)
for root in ('src','test'):
 for p in (M/root).rglob('*'):
  if p.is_file():need(sha(p)==base[str(p.relative_to(M))],'authoritative baseline drift '+str(p))
os.environ['GIT_OPTIONAL_LOCKS']='0'
def git(*args):return subprocess.check_output(['/usr/bin/git','-C',str(M),*args],text=True).strip()
need(git('rev-parse','HEAD')==git('rev-parse','master')==git('rev-parse','origin/master')=='7e306e24f064a8aa214bc88379e059def77661ab','master refs')
need(not git('diff','--name-only','HEAD','--','src','test','Project.toml'),'production drift')
protected=read('protected-before.json')
for n,v in {**protected['files'],**protected['indexes']}.items():need(sha(n)==v,'protected changed '+n)
seed=read('host-seed.json');groups=set(seed['groups']);need(len(groups)==577,'historical group coverage');procs=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();a=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x];comm=(p/'comm').read_text().strip();pgid,sid=int(st[2]),int(st[3])
  need(pgid not in groups and sid not in groups,'historical process group/session active')
  need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+a[:1]),'Julia active')
  procs.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(st[19]),command=a))
 except (FileNotFoundError,ProcessLookupError):pass
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot drift')
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'memory guard')
host=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=procs,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'])
# Review artifacts are new files and outside all pinned trees.
create('independent-admission-check.py',Path(__file__).read_text())
create('independent-admission-host.json',host)
report='''Verdict: ACCEPTED for the one guarded 600-second comparison. This is admission to measurement, not production acceptance. No unresolved critical, important, or minor findings.

Source evidence: nine reference function blocks match authoritative master source exactly; declared A1/A2/C replacements and the B method insertion reconstruct candidate.jl byte for byte after the private module rename. Changed helper names resolve locally, while unchanged dependencies resolve to the authoritative JSimplex package. The driver asserts the loaded package path. All inventory files were independently streamed through SHA-256, all three tree memberships checked, all baseline source/test files matched, protected file/index hashes checked, and HEAD/master/origin/master confirmed at 7e306e24f064a8aa214bc88379e059def77661ab. No Julia was launched by this review.

Numerical review: A changes only the existing abs evaluation sites. Julia Base abs(Real) eagerly evaluates -x but returns x for nonnegative sign, so conditional magnitude preserves selected value/precision/owner including signed zero while omitting unused negation. B retains both x reads, conversion/product/subtraction/addition and term order; it retains nonzero-a/nonzero-x and magnitude<floatmin underflow conditions. The lazily constructed call-local limit is private and comparison-only in a fixed-precision ordinary-array loop. Generic matrix/custom-vector fallback remains local and unchanged. C always computes the same fresh current-precision product. A finite current-precision product cannot exceed floatmax at that precision; NaN, negative infinity and signed zero retain the old min-selected product. Each positive infinity obtains a fresh cap. The direct tests compare value, precision, sign and input immutability across all modes and enforce fresh product/cap owners.

Concrete diagnostic: 15 BF precision/rounding contexts times 72 cells plus 48 hardware and 32 rational controls give 1160 cells and 20880 measured windows. Typed whole-call wrappers and scalar sinks are inside each timing window; fixture construction, correctness/snapshots, resets, cold/warm calls and GC preparation are outside measured windows and recorded separately. Three warm pairs precede nine alternating measured pairs; compile/recompile time must be zero. All raw windows and GC costs are retained. Ordinary Test checks results, scratch/pipeline state, input containers/elements and exception classes/messages before timing. CSC inputs are flattened to stored buffers, avoiding implicit-zero identity false failures. Empty direction/row/quality, all-BASIC Devex, short dimensions, alias, nonfinite, mixed512, plain wrapper and vector-view fallback controls are present. Underflow expected-finite is computed in the same wide precision and active rounding mode: upward/away rounding may return the minimum nonzero product, so false unsafe detection is not demanded.

Work and memory: no unnecessary production work or retained-memory increase found. A preserves O(m+nnz(basis)) residual traversal and removes only unused unary negations for nonnegative operands; no new scans, copies, conversions, solves or scratch. B preserves all outer alias/finiteness/stored-precision scans and wide scratch; sparse cost remains O(m+nnz), dense O(m*n). It adds a local readiness branch/tuple propagation, replaces K eligible floatmin constructions by at most one per call, and adds no persistent roots. Whether tuple propagation allocates or branches cost time is deliberately determined by the complete-function experiment, including negative controls; savings are not yet claimed. C replaces one unconditional floatmax construction/min per eligible Devex candidate by predicates and a fresh cap only for positive overflow; state traversal and any weight BTRAN/price remain unchanged. Update-chain length introduces no new factor; no extra basis solves. Existing owned scratch and mutability safeguards remain. Diagnostic preparation/snapshot allocations do not establish production savings.

Guard: fresh independent host evidence records 577 historical process groups/sessions, boot, start ticks and full commands, no live Julia, sufficient RAM and swap. The launch rechecks bindings/refs/environment/protected files and host state, requires an exclusive attempt/output directory, and uses the existing reviewed guard/supervisor with owned process identities, parent-death entry gate, Julia/BLAS one thread, GC1,0, heap2GiB hint, AS8GiB, RAM6GiB/swap1GiB pressure checks and inclusive shared600 deadline with 592-second guard allowance. Review does not rerun historical scripts.

Declined to judge: full-suite/end-to-end solver performance and numerical trajectories (this is a focused whole-function diagnostic); x64 behavior (aarch64 runtime only); native allocator/free counts (Julia allocation events/bytes only); MPFR sticky flags or concurrent/hostile external precision/method mutation (explicitly outside WORK-MEMORY.md scope); recovery/refactorization/update-chain stress and final production integration/tests (subsequent tasks); changing previous rejected allocation gates/release decisions (expressly prohibited by plan). No result or speedup is inferred before execution; a failed/capped attempt must remain evidence and cannot be rerun for a selected pass.
'''
create('ADMISSION-REVIEW.md',report)
bindings={str(p):sha(p) for p in D.iterdir() if p.is_file() and p.name not in ('admission.json',)}
# Also bind actual source methods/helper and guard files directly; pins binds remaining inventory.
for p in [*(D/'guard').glob('*.py'),M/'src/dual_simplex.jl',M/'src/primal_simplex.jl',M/'src/simplex_numerics.jl']:
 bindings[str(p)]=sha(p)
create('admission.json',dict(accepted=True,findings=[],bindings=bindings))
print(json.dumps(dict(accepted=True,reference_blocks=len(blocks),inventory=len(inventory),groups=len(groups),review=str(D/'ADMISSION-REVIEW.md'),admission=str(D/'admission.json'))))
