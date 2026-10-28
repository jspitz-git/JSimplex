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
pins=read('pins.json')
need(len(pins['inventory'])==1254,'pin count')
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
cases=read('expected-cases.json');grid=tomllib.loads((D/'grid.toml').read_text())['cells'];contract=read('contract.json')
need(grid==cases and len(cases)==2636 and len({v['id'] for v in cases})==2636,'grid')
need(len({v['context'] for v in cases})==19 and len(cases)*18==47448,'contexts/windows')
need(contract['cases']==2636 and contract['measured_windows']==47448 and contract['attempts']==1 and contract['shared_limit_seconds']==900 and contract['guard_limit_seconds']==892,'contract')
checks['grid']={'cells':2636,'contexts':19,'windows':47448}
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
put('independent-admission-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,verified_unrelated_collisions=collisions,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
findings=[dict(priority=1,file='fixtures.jl',line=81,title='Rational row controls call a floating-only method',detail='whole(:rows) dispatches every type to _primal_row_bounds!, which only accepts AbstractFloat. Both Rational contexts reach this in correctness and in the sealed grid. checkpair then indexes the captured error as a result, while its row ownership assertions and correctness oracle assume floating output buffers. Use the actual allocating exact-rational row function and type-specific alias/oracle checks without dropping cells.'),dict(priority=2,file='extra-tests.jl',line=38,title='Recovery precision widening is not exercised',detail='Stored512 values are placed only in eta values. _with_recovery_precision scans policy solve tolerance, A, costs and finite bounds instead. Add complete refresh and scheduled cases with a stored512 scanned input, independent state/storage expectations, and exact restoration of ambient precision and rounding.'),dict(priority=2,file='extra-tests.jl',line=11,title='Explicit empty and ownership boundary coverage is incomplete',detail='The claimed truly-empty block uses n16. Add null/empty primal structures and assert C empty/unit fresh-versus-input ownership across calls. Current same(new,whole(...)) only checks value/precision/sign. Rational exception tests should include stored negative infinity as well as positive infinity, retaining DivideError and fixed-width overflow checks.')]
bindings={str(D/n):sha(D/n) for n in ['DESIGN.md','PLAN.md','WORK-MEMORY.md','Reference.jl','A.jl','B.jl','C.jl','fixtures.jl','extra-tests.jl','driver.jl','expected-cases.json','grid.toml','changes.json','contract.json','pins.json','common.py','launch.py','guard/guard_reviewed.py','guard/supervisor_reviewed.py','guard/entry_gate.py','independent-admission-review.py','independent-admission-host.json']}
put('admission.json',dict(accepted=False,findings=findings,bindings=bindings,checks=checks,Julia_executed=False))
report='''# Independent admission: rejected before Julia\n\nThe sealed driver is not admitted. No Julia process, query, import, parser, probe or old audit was executed; no production or Git mutation was made.\n\n1. **P1 — rational row dispatch** (`fixtures.jl:81,114,134,140`): both rational controls call `_primal_row_bounds!`, whose private method accepts only `AbstractFloat`. The resulting captured `MethodError` is then treated as a successful row tuple and checked against untouched floating buffers. Preserve all cells, use the original exact allocating `_primal_row_bounds`, and branch owner/oracle checks by the actual result contract.\n2. **P2 — real recovery widening** (`extra-tests.jl:38`): mutating eta values to stored512 does not change the precision selected by `_with_recovery_precision`. Add full refresh/scheduled coverage with stored512 cost/policy/model/bound data, independent state/storage expectations, and exact ambient restoration.\n3. **P2 — declared boundary coverage** (`extra-tests.jl:11,48,60`): no truly empty primal case exists; repeated C calls are checked only for equal values, not the required fresh/input owner category; stored negative Rational infinity is absent.\n\nSource review found no numerical change requiring rejection in A/B/C themselves. A keeps the finite/precision guards before its sign check, preserves zero shortcuts and exact opposite-sign cancellation, and leaves addition, FastTwoSum, underflow and enclosure operations byte-identical. B adds only the Rational{BigInt} method; finite exact multiplication by a signed unit equals identity/negation, all CSC products/accumulations and allowance/finite/overflow handling remain, and native/fixed rational methods remain unchanged. Ordinary Rational infinity and zero operations still reach their existing exception paths. C preserves nested maximum order; installed Julia `abs(::Real)` uses eager `ifelse(signbit(x),-x,x)`, so the existing conditional magnitude preserves selected value/precision/input owner while removing an unused positive negation. A fresh local unit is read-only throughout both reductions. No persistent cache is introduced.\n\nNo unnecessary new full-vector scan, basis solve, copy, or retained numerical buffer was found. A adds up to two scalar sign tests at each reached sum cancellation check. B adds a cheap orientation branch per reached nonzero while deleting a Rational unit multiplication; no oriented vector is built. C removes L unit constructors and up to P discarded negations while retaining O(L+P) reductions. Forced refresh still includes storage and recovery-precision scans; scheduled calls retain cache, age, fixed-policy and reason-priority gates. Two extra specialized methods and C closure specialization need measurement; source counts are not measured allocation or elapsed-time savings.\n\nThe grid has 2,636 unique cells, 19 contexts, and 47,448 alternating measured windows. Three warmups, nine pairs, compile/recompile-zero checks, full GC/outlier records, separate fixture/reset/validation/result capture, and ordinary Test are present. The pinned single-process launcher retains 900 shared/892 guarded seconds, one Julia/BLAS thread, GC1,0, heap2G, AS8G, RAM6G and swap1G guards plus owned-process cleanup. Source inverses, explicit imports versus all owned short/long definitions, 1,254 pins, baseline tree, protected files/indexes and refs were independently checked. Fresh host evidence checks all 649 historical identifiers as both PGIDs and SIDs, boot/start ticks/commands, exact unrelated-process allowance and absence of Julia.\n\nThis is an offline rejection, not a failed measurement. Preserve these sealed bytes and this rejection; repair only the harness and re-admit the concrete revision before any numerical execution. Full solver, x64 and native retained-memory evidence remain outside this short comparison.\n'''
with (D/'admission.md').open('x') as out:out.write(report)
print(json.dumps(dict(accepted=False,findings=len(findings),checks=checks,host_no_Julia=True)))
