from pathlib import Path
import json,hashlib,subprocess,os,re,datetime,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');Q=D/'GREEN-run';M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];S=D/'GREEN';base='1a6b9d81e89b44c5c75b95b6c92e0916c2d19730'
def need(x,m):
 if not x:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def git(a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')).decode().strip()
def bindings(r):
 need(r['accepted'] is True and r.get('findings',[])==[],'review accepted')
 for p,h in r['bindings'].items():need(sha(p)==h,'review binding '+p)
for name in ['comparison-3/result-review.json','RED-ready-run/result-review.json']:bindings(read(D/name))
red=read(D/'RED-ready-run/audit.json');need(red['passed']==15415 and red['expected_failures']==5,'witnessed RED')
inv=read(D/'source-inverse.json');old=read(D/'baseline-tree.json');changes=read(D/'changes.json')
actual={str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()};need(actual==inv['whole_stage'],'whole stage')
need(old=={str(p.relative_to(D/'baseline')):sha(p) for p in (D/'baseline').rglob('*') if p.is_file()},'baseline tree')
names=sorted(n for n in set(old)|set(actual) if old.get(n)!=actual.get(n));need(names==inv['names'] and len(names)==7,'seven changes')
for n in names:
 need(actual[n]==inv['candidate_sha256'][n],'candidate binding '+n)
 if n.startswith('src/'):
  s=(S/n).read_text()
  for ch in reversed(changes):
   if 'src/'+ch['file']==n:need(s.count(ch['new'])==1,'unique inverse');s=s.replace(ch['new'],ch['old'])
  need(s==(D/'baseline'/n).read_text(),'exact independent inverse '+n)
  need(subprocess.check_output(['/usr/bin/git','-C',str(M),'show',base+':'+n])==(D/'baseline'/n).read_bytes(),'authoritative git source '+n)
need((S/'test/generic_virtual_free_pivot_tests.jl').read_bytes()==(D/'new-test-reviewed.jl').read_bytes(),'reviewed test exact')
need((S/'test/runtests.jl').read_text()==(D/'baseline/test/runtests.jl').read_text()+'\ninclude("generic_virtual_free_pivot_tests.jl")\n','only test inclusion')
for tree in ['src','test']:
 a={str(p.relative_to(M)):sha(p) for p in (M/tree).rglob('*') if p.is_file()};need(a=={n:h for n,h in old.items() if n.startswith(tree+'/')},'M original '+tree)
need(git(['rev-parse','HEAD'])==git(['rev-parse','master'])==git(['rev-parse','origin/master'])==base,'refs')
need(not git(['diff','--name-only','HEAD','--','src','test','Project.toml']),'M clean targets')
need(git(['rev-parse','HEAD'],R)==read(Q/'host-before.json')['diagnostic_head'],'R ref')
protected=read(Q/'protected-before.json')
for p,h in {**protected['files'],**protected['indexes']}.items():need(sha(p)==h,'protected '+p)
pins=read(Q/'pins.json');need(set(pins['files'])==set(pins['inventory']) and len(pins['inventory'])==1234,'pin membership')
for p,v in pins['inventory'].items():need(str(Path(p).resolve(strict=True))==v['resolved'] and sha(p)==v['sha256'],'pin '+p)
for t in pins['trees']:need({str(p) for p in Path(t).rglob('*') if p.is_file()}=={p for p in pins['inventory'] if Path(p).is_relative_to(t)},'tree '+t)
contract=read(Q/'contract.json');need(contract['arm']=='GREEN' and contract['source_root']==str(S) and contract['expected_exit']==contract['expected_failures']==0 and contract['attempts']==1 and contract['shared_limit_seconds']==2400 and contract['guard_limit_seconds']==2392,'contract')
previous=read(R/'diagnostics/generic-quality-local/2026-10-27/GREEN-run/contract.json')['files'];need(contract['files']==['generic_virtual_free_pivot_tests.jl',*previous] and len(contract['files'])==len(set(contract['files']))==36,'36 prior full files')
text=(Q/'tests.jl').read_text();need(json.loads(re.search(r'for file in (\[.*\])',text)[1])==contract['files'],'driver includes');need('include(joinpath(ROOT,"test",file))' in text and '@testset "Virtual free pivot GREEN"' in text,'ordinary test')
for n in ['common.py','launch.py','audit.py','guard/entry_gate.py','guard/guard_reviewed.py','guard/supervisor_reviewed.py']:ast.parse((Q/n).read_text())
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:need((Q/'guard'/n).read_bytes()==(D/'RED-ready-run/guard'/n).read_bytes(),'same witnessed guard')
need(not (Q/'output').exists() and not (Q/'reservation.json').exists(),'unlaunched GREEN')
vars=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME'];need(all(not os.environ.get(k) for k in vars),'environment overrides');found={k:os.environ[k] for k in vars+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ};need(found==read(Q/'environment.json')['inherited'],'inherited environment')
seed=read(Q/'host-seed.json');groups=set(seed['groups']);need(len(groups)==603,'603 historical groups')
allow=R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json';need(sha(allow)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed allowance');allowed=read(allow)['identities'];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'boot');procs=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();args=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip();ident=dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=args,boot_id=boot)
  need(not any(Path(x).name.lower().startswith('julia') for x in [comm]+args[:1]),'active Julia')
  if ident['pgid'] in groups or ident['sid'] in groups:need(ident in allowed,'historical identity')
  procs.append(ident)
 except (FileNotFoundError,ProcessLookupError):pass
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'memory')
host=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=procs,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']);put(Q/'independent-review-host.json',host)
report='''Independent production source and GREEN admission review — PASS, pre-execution only.

The independent offline checker verified all 537 staged files, exact seven changed paths, all 1234 launch pins/resolved targets/tree memberships, original production refs and protected files/indexes, and a fresh 603-group/session host observation. Exact reverse substitutions restore authoritative base 1a6b9d81 in all five source files; unchanged files retain baseline hashes. The new permanent test is byte-identical to witnessed RED's reviewed test; runtests only adds its inclusion. RED was independently accepted with 15415 passes and exactly five intended whole-call cost failures. No Julia query, import, compilation, launch or old checker was run by this reviewer.

A is restricted to ordinary BigFloat vectors and implicit price matrices. Each original coefficient, conversion, multiplication, subtraction, residual/scale update, term increment and underflow guard remains in traversal order. Private units are first created at their original nonempty loop sites; lazy floatmin stays invocation-local. All broader dimension, finite, precision, alias and quality checks remain, including complete price predicate vcat and scratch work. B changes only free-nonbasic magnitudes; generic other-type abs, negative-tolerance predicates, ties, full/pool scan order and scoring/weight callbacks remain. C adds BigFloat-only pivot methods and preserves basis assembly, both complete quality calls, recovery gates, finite/sign/nonzero/inverse/division checks, contraction and independent agreements. Integer zero/one are exact, and roundoff additions/multiplication keep original order. Magnitudes are reused only after their original gates. No mutable input scalar is modified or published; no persistent cache is introduced.

No unnecessary added production work or retained numerical memory was found. A executes per price audit or virtual solve, retaining O(nnz(A)+n+m) terms and all existing quality scans/solves/copies/conversions. Unit source constructions fall from n+3m to at most three; per-term floatmin becomes at most one lazy instance. These are source-work counts, not heap measurements. B executes per full candidate/pool visit or summary entry, preserving scans and callbacks. C executes per checked/incremental pivot, retaining O(m) contraction, existing vector scans and two full certificates. New locals/branches and cold O(1) specialized-method metadata are acknowledged. There is no new update-chain dependence or retained numeric workspace cache.

The accepted comparison provides representative sparse/dense whole-call evidence at bases 4/16, n32/128, BigFloat64/128/256 and five rounding modes, plus native/exact controls. All 1440 A cells reduce bytes/events in all nine pairs; B's 600 positive/mixed cells reduce allocations while 600 negative/bound controls retain them; all 360 nonzero C cells reduce allocations, but 14 timing medians are slower. Representative BF128 nearest n128,m16 sparse A is 681.1 to 434.7 us, 951008 to 581248 bytes and 25437 to 16582 events; dense A 2215.7 to 1354.1 us, 2640800 to 1577792 bytes and 70119 to 45016 events. Sparse C is 75.8 to 71.5 us, 93024 to 87232 bytes and 2705 to 2523 events; dense C timing is 224.3 to 222.4 us. Fixture/FTRAN/BTRAN, initialization, correctness compilation, resets and GC are separate. Measured compilation is zero and all 114 GC windows/outliers remain. No universal, end-to-end, ordinary native-dual or retained-memory speedup is inferred. Full-suite/x64 and wider trajectories remain open.

GREEN admission covers exactly 36 whole test files with ordinary Test, zero expected failures, one attempt, shared 2400-second limit (2392 guard), original resource/identity/pidfd/parent-death gates and exclusive outputs. Launch validates these bindings again and refreshes host state. Result acceptance, actual commit review, local fast-forward, actual-master qualification and publication are later gates, not established by this admission.
'''
with (D/'PRODUCTION-REVIEW.md').open('x') as f:f.write(report)
source_bind={str(S/n):h for n,h in actual.items()};source_bind.update({str(D/'baseline'/n):h for n,h in old.items()})
for n in ['changes.json','source-inverse.json','new-test-reviewed.jl','WORK-MEMORY.md','SOURCE-REVIEW.md','PRODUCTION-REVIEW.md','comparison-3/result-review.json','comparison-3/RESULT-REVIEW.md','comparison-3/audit-final.json','RED-ready-run/result-review.json','RED-ready-run/audit.json']:source_bind[str(D/n)]=sha(D/n)
put(D/'production-review.json',dict(accepted=True,findings=[],bindings=source_bind,pre_execution_only=True,unnecessary_new_work_or_retained_numeric_memory=False,exact_changed_names=names,no_Julia_executed=True))
admit={p:v['sha256'] for p,v in pins['inventory'].items()}
for p in [Q/'pins.json',Q/'independent-review-host.json',D/'production-review.json',D/'PRODUCTION-REVIEW.md',Path(__file__)]:admit[str(p)]=sha(p)
put(Q/'admission.json',dict(accepted=True,findings=[],bindings=admit,arm='GREEN',whole_files=36,pins=1234,historical_groups=603,one_attempt=True,shared_limit_seconds=2400,no_Julia_executed=True))
print(json.dumps(dict(accepted=True,stage_files=len(actual),baseline_files=len(old),pins=len(pins['inventory']),groups=len(groups),changed_names=names)))
