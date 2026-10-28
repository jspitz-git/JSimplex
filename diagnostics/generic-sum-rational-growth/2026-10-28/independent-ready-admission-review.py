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
pins=read('pins-ready.json')
need(len(pins['inventory'])==1288,'pin count')
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
cases=read('expected-cases.json');grid=tomllib.loads((D/'grid.toml').read_text())['cells'];contract=read('contract-ready.json')
need(grid==cases and len(cases)==2636 and len({v['id'] for v in cases})==2636,'grid')
need(len({v['context'] for v in cases})==19 and len(cases)*18==47448,'contexts/windows')
need(contract['cases']==2636 and contract['measured_windows']==47448 and contract['attempts']==1 and contract['shared_limit_seconds']==900 and contract['guard_limit_seconds']==892,'contract')
checks['grid']={'cells':2636,'contexts':19,'windows':47448}
for prior in ['pins.json','pins-reviewed.json']:
 need(all(pins['inventory'].get(n)==v for n,v in read(prior)['inventory'].items()),'prior inventory changed '+prior)
for prior in ['admission.json','admission-reviewed.json']:
 for n,v in read(prior)['bindings'].items():need(sha(n)==v,'prior binding '+n)
oldcontract=read('contract-reviewed.json');expected=dict(oldcontract);expected['command']=[v.replace(str(D/'driver-reviewed.jl'),str(D/'driver-ready.jl')) for v in oldcontract['command']]
need(contract==expected,'ready contract scope changed')
for before,after in [('driver-reviewed.jl','driver-ready.jl'),('common_reviewed.py','common_ready.py'),('launch-reviewed.py','launch-ready.py'),('audit.py','audit-ready.py')]:
 text=(D/before).read_text()
 for old,new in [('extra-tests-reviewed.jl','extra-tests-ready.jl'),('common_reviewed','common_ready'),('admission-reviewed.json','admission-ready.json'),('contract-reviewed.json','contract-ready.json'),('pins-reviewed.json','pins-ready.json'),('audit.py','audit-ready.py')]:text=text.replace(old,new)
 need(text==(D/after).read_text(),'nonfilename change '+after)
old='    out=checkpair(a,b,:B);@test out[1]===:error;@test out[2]===DivideError'
new="""    out=checkpair(a,b,:B)
    if rhosign==-1&&mode===:one_sided&&what===:infinite
     @test out[1]===:value;@test out[2]===false
    else
     @test out[1]===:error;@test out[2]===DivideError
    end"""
text=(D/'extra-tests-reviewed.jl').read_text();need(text.count(old)==1 and text.replace(old,new)==(D/'extra-tests-ready.jl').read_text(),'exact oracle correction')
need(not (D/'output').exists() and not (D/'reservation.json').exists(),'attempt already reserved')
overrides=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']
need(all(not os.environ.get(k) for k in overrides),'environment overrides')
need({k:os.environ[k] for k in overrides+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}==read('environment.json')['inherited'],'environment drift')
checks.update(prior_inventories_and_bindings_unchanged=True,exact_oracle_correction=True,auditor_filename_only=True,no_attempt=True,environment=True)
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
put('independent-ready-admission-host.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,verified_unrelated_collisions=collisions,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree']))
report="""# Independent READY admission: accepted for one guarded comparison

The sole revised-review oracle error is corrected exactly: stored negative infinity with a selected unbounded bound asserts `(:value,false)` in both orientations; explicit-zero products and the remaining infinity cases still assert DivideError. Each case retains two assertions. No bound, tolerance, arithmetic precision, candidate body, grid cell or measured window was changed by this correction. READY driver/common/launcher/auditor differences are filename substitutions only.

All earlier findings are resolved. Rational row controls use the original allocating exact method and assert its lower/upper alias contract; floating rows retain provided buffers. Exact enclosures inspect actual return values. Zero-dimensional A/B/C controls exercise real paths, fresh empty/subunit C results are checked across calls, and full refresh/scheduled recovery probes use stored512 cost/policy/bound inputs with their original numerical values. The negative eta dyadic -(1+2^-53+2^-400) requires512 precision to preserve its last bit and has an independently derived Float64 oracle under all five rounding modes; storage/age/state/input and ambient restoration checks remain.

The private Reference and A/B/C bodies were checked against actual master ce5d4a74019e0dc2e656d08161641c498b159e7b with exact inverse edits and no explicit imported-owned short/long definition collisions. The candidate numerical assessment is unchanged: A preserves all cancellation/finite/precision/FastTwoSum/enclosure safeguards; B changes only Rational{BigInt} signed-unit coefficient preparation and retains CSC order, allowances, zero/bound checks and exception handling; C preserves nested maximum order, selected value/precision/ownership and read-only local unit lifetime. Fixed-rational and floating certificate controls remain unchanged.

No unnecessary new full-vector scan, basis solve, array copy, persistent cache or retained numerical buffer was found. A adds up to two scalar sign checks per reached cancellation gate, B adds scalar orientation selection per reached nonzero while removing a unit Rational multiply, and C retains O(L+P) reductions while removing L unit constructors and unused positive-value negations. Forced refresh retains storage/recovery scans; scheduled calls retain age/cache/fixed-policy/priority logic. Extra method/closure specialization and actual allocation/time effects require this comparison; source operation counts are not speedup claims.

The frozen comparison contains2,636 cells,19 contexts,47,448 measured windows, three warmups and nine alternating pairs, with ordinary Test and compile/recompile-zero checks. Fixture/reset/cold/warm/validation/result-capture/GC costs are separated, all outliers and GC windows retained. The statically reviewed auditor checks all typed raw cells/windows and2,674 preparation records, paired typed results, ordinary Test totals, exact command/process/gate/pin linkage, all RAM/swap observations and fresh closure before reporting. Its raw paired ratios/median/range/MAD preserve zero-baseline uncertainty; independent result interpretation is still required.

All1,288 pins verified, including every earlier1,274/1,254 inventory entry and both rejected admission bindings. Prior sealed evidence, source/test/user files and indexes are unchanged. Fresh host evidence confirms correct master/diagnostic refs, no Julia, sufficient RAM/swap, exact inherited environment and all649 historical PGIDs AND SIDs with boot/start-tick/command identity and only the fixed unrelated-process allowance. No prior attempt/output exists.

Admission covers exactly the pinned READY command, one attempt,900 shared/892 guarded seconds, one Julia/BLAS thread, GC1,0, heap2G, AS8G, RAM6G and swap1G limits with existing owned-process guards. No Julia/query/import/parser/probe, old audit, production mutation or Git mutation was executed during this review. Admission authorizes the comparison only; numerical success, measured savings, production integration, full solver/x64 and native retained-memory evidence are not yet established.
"""
with (D/'ADMISSION-READY.md').open('x') as f:f.write(report)
names=['DESIGN.md','PLAN.md','WORK-MEMORY.md','Reference.jl','A.jl','B.jl','C.jl','fixtures-reviewed.jl','extra-tests-ready.jl','driver-ready.jl','expected-cases.json','grid.toml','changes.json','contract-ready.json','pins-ready.json','common_ready.py','launch-ready.py','audit-ready.py','review-oracle-fix.json','guard/guard_reviewed.py','guard/supervisor_reviewed.py','guard/entry_gate.py','independent-ready-admission-review.py','independent-ready-admission-host.json','admission.json','admission-reviewed.json','ADMISSION-READY.md']
bindings={str(D/n):sha(D/n) for n in names}
put('admission-ready.json',dict(accepted=True,findings=[],bindings=bindings,checks=checks,Julia_executed=False))
print(json.dumps(dict(accepted=True,findings=0,checks=checks,host_no_Julia=True)))
