from pathlib import Path
import json,hashlib,tomllib,re,os,subprocess,datetime
D=Path(__file__).resolve().parent
M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
def need(x,m):
 if not x: raise RuntimeError(m)
def read(n):return json.loads((D/n).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(n,x):
 with (D/n).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
checks={}
pins=read('pins-reviewed.json')
need(len(pins['inventory'])==1274,'pin count')
for n,v in pins['inventory'].items():need(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],'pin '+n)
for root in pins['trees']:need({str(p) for p in Path(root).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(root)},'tree membership')
checks['pins']=len(pins['inventory'])
for n,v in read('baseline-tree.json').items():need(sha(D/'baseline'/n)==sha(M/n)==v,'baseline '+n)
for section in read('protected-before.json').values():
 for n,v in section.items():need(sha(n)==v,'protected '+n)
checks['baseline_and_protected']=True
s=(D/'baseline/src/dual_simplex.jl').read_text();f=(D/'baseline/src/factorization.jl').read_text();r=(D/'baseline/src/refactorization_policy.jl').read_text()
def reg(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
interval=reg(s,'function _primal_sum_bounds(left::T, right::T) where {T<:Rational}','function _original_reduced_cost_bounds')
cert=reg(s,'function _infeasibility_certified(workspace::SimplexWorkspace{T},','function _floating_infeasibility_certified')
growth=reg(f,'_factor_growth_measure(factor::PFIFactorization{T})','_backend_dimension')
refresh=reg(r,'function _refresh_refactor_metrics!','function _record_refactor_quality!')
scheduled=reg(r,'function _scheduled_refactor_reason','_refactor_event(reason')
ref=(D/'Reference.jl').read_text();start=ref.index('function _primal_sum_bounds')
need(ref[start:]==interval+cert+growth+refresh+scheduled+'\nend\n','reference exact clone')
changes=read('changes.json')
for change in changes:
 base=(M/change['file']).read_text();need(base.count(change['old'])==1,'unique source edit')
 candidate=base.replace(change['old'],change['new']);need(candidate.replace(change['new'],change['old'],1)==base,'source inverse')
 arm=change['variant'];want=ref.replace('module SRGReference','module SRG'+arm,1).replace(change['old'],change['new'],1)
 need((D/(arm+'.jl')).read_text()==want,'private candidate exact '+arm)
for arm in ['Reference','A','B','C']:
 text=(D/(arm+'.jl')).read_text();imports=set()
 for line in text.splitlines():
  if line.startswith('using JSimplex:'):imports.update(v.strip() for v in line.split(':',1)[1].split(','))
 owned=set(re.findall(r'(?m)^(?:function\s+)?([A-Za-z_][A-Za-z_0-9!]*)\(',text))
 need(not imports&owned,'import/owned name collision '+arm)
checks['source_inverse_and_imports']=True
cases=read('expected-cases.json');grid=tomllib.loads((D/'grid.toml').read_text())['cells'];contract=read('contract-reviewed.json')
need(grid==cases and len(cases)==2636 and len({v['id'] for v in cases})==2636,'grid')
need(len({v['context'] for v in cases})==19 and len(cases)*18==47448,'contexts/windows')
need(contract['cases']==2636 and contract['measured_windows']==47448 and contract['attempts']==1 and contract['shared_limit_seconds']==900 and contract['guard_limit_seconds']==892,'contract')
checks['grid']={'cells':2636,'contexts':19,'windows':47448}
oldpins=read('pins.json')
need(all(pins['inventory'].get(n)==v for n,v in oldpins['inventory'].items()),'old frozen inventory changed')
for n,v in read('admission.json')['bindings'].items():need(sha(n)==v,'initial admission binding '+n)
oldcontract=read('contract.json');expected=dict(oldcontract);expected['command']=[v.replace(str(D/'driver.jl'),str(D/'driver-reviewed.jl')) for v in oldcontract['command']]
need(contract==expected,'contract scope changed')
need((D/'driver-reviewed.jl').read_text()==(D/'driver.jl').read_text().replace('"fixtures.jl"','"fixtures-reviewed.jl"').replace('"extra-tests.jl"','"extra-tests-reviewed.jl"'),'driver mutation')
checks['initial_evidence_unchanged']=True
checks['auditor_static_review']=True
# Read-only host Git; never invokes a numerical runtime or an older audit script.
env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
def git(root,*args):return subprocess.check_output(['/usr/bin/git','-C',str(root),*args],env=env).decode().strip()
need(all(git(M,'rev-parse',v)=='ce5d4a74019e0dc2e656d08161641c498b159e7b' for v in ['HEAD','master','origin/master']),'master refs')
need(git(R,'rev-parse','HEAD')=='c01e9376bdbcda7cb54ba55735cf053299b9af45','diagnostic HEAD')
need(not git(M,'diff','--name-only','HEAD','--','src','test','Project.toml'),'production drift')
checks['refs']=True
old=read('host-seed.json');groups=set(old['groups']);need(len(groups)==649,'historical groups')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==old['boot_id'],'boot changed')
allowance=R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json'
need(sha(allowance)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','identity allowance')
permitted=json.loads(allowance.read_text())['identities'];processes=[];collisions=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();cmd=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip()
  ident=dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=cmd,boot_id=boot)
  need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+cmd[:1]),'live Julia')
  if ident['pgid'] in groups or ident['sid'] in groups:
   need(ident in permitted,'historical group/session collision');collisions.append(ident)
  processes.append(ident)
 except (FileNotFoundError,ProcessLookupError):pass
mem={v.split(':')[0]:int(v.split()[1]) for v in Path('/proc/meminfo').read_text().splitlines()}
need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'RAM/swap')
put('independent-revised-admission-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,verified_unrelated_collisions=collisions,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
findings=[dict(priority=1,file='extra-tests-reviewed.jl',line=63,title='Negative infinity with the selected bound unbounded returns false',detail='For rhosign=-1, mode=:one_sided, what=:infinite, below=true chooses unbounded upper for a negative coefficient; below=false chooses unbounded lower for a positive coefficient. Both return false at isfinite(bound) before reaching any DivideError. Explicit-zero multiplication still throws. The unconditional DivideError oracle rejects correct Reference and B behavior in both orientations.')]
names=['DESIGN.md','PLAN.md','WORK-MEMORY.md','Reference.jl','A.jl','B.jl','C.jl','fixtures-reviewed.jl','extra-tests-reviewed.jl','driver-reviewed.jl','expected-cases.json','grid.toml','changes.json','contract-reviewed.json','pins-reviewed.json','common_reviewed.py','launch-reviewed.py','audit.py','review-fix.json','review-fix-preserve-values.json','guard/guard_reviewed.py','guard/supervisor_reviewed.py','guard/entry_gate.py','independent-revised-admission-review.py','independent-revised-admission-host.json','admission.json','admission.md']
bindings={str(D/n):sha(D/n) for n in names}
put('admission-reviewed.json',dict(accepted=False,findings=findings,bindings=bindings,checks=checks,Julia_executed=False))
report="""# Revised independent admission: rejected before Julia

The original three admission findings have been addressed in the revised harness. Exact rational rows use the original allocating route, ownership checks distinguish its shared lower/upper output from floating buffers, and the enclosure oracle reads returned values. Empty zero-dimensional paths and fresh C output ownership are now explicit. Cost/policy/bound values are promoted to stored512 without changing their numerical values, exercising actual recovery-precision widening. The negative eta dyadic 1+2^-53+2^-400 is exactly representable at512; its Float64 result is nextfloat(1) for Nearest/Up/FromZero and1 for Down/ToZero. Installed Julia's Float64(BigFloat) conversion uses the active BigFloat rounding mode. Full refresh/scheduled tests check growth, metric age, storage count and ambient restoration.

One newly introduced P1 oracle error prevents admission (`extra-tests-reviewed.jl:57-63`). For stored negative infinity, the one-sided infinite-coefficient case selects an unbounded bound and immediately returns false in both orientations. It never reaches DivideError. The current unconditional error assertion is therefore wrong. Preserve this sealed revision; correct this case to assert false while retaining DivideError for explicit stored zero products and the remaining infinity cases. No candidate-code change is needed.

The prospective auditor was read but not executed. It checks exact typed grid order, all47,448 windows, nine alternating pairs, all2,674 preparation records, finite nonnegative timing/count fields, compile-zero measurements, typed paired results, ordinary Test success, exact command/process/gate/pin linkage, resource observations and fresh host closure. It retains raw GC/outliers and reports paired ratio medians/ranges/MAD without silently discarding zero-baseline cases. The audit alone does not establish whole-solver speedup or retained native-memory behavior; independent post-run interpretation is still required.

All1,274 pins verified, including the original1,254 immutable inventory. Initial admission bindings, candidate/source inverses, unchanged2,636-cell grid/19contexts/47,448windows, protected source/test/user files and indexes, refs and new fresh host evidence passed. No Julia or old audit was executed; no production or Git mutation occurred. All649 historical identifiers were checked as both PGIDs and SIDs using boot/start-ticks/commands and the exact unrelated-process allowance.

Production computational and memory assessment is unchanged: no unnecessary new scan, solve, array copy, persistent cache or retained numerical buffer was found. A adds scalar sign checks at sum cancellation gates; B replaces a Rational unit product with scalar orientation selection; C retains O(L+P) nested reductions and removes redundant units/positive negations. Actual elapsed/allocation savings remain unmeasured, and no launch is authorized by this rejected admission.
"""
with (D/'ADMISSION-REVIEWED.md').open('x') as f:f.write(report)
print(json.dumps(dict(accepted=False,findings=len(findings),checks=checks,host_no_Julia=True)))
