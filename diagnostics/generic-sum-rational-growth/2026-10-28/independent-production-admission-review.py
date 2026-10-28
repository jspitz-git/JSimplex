from pathlib import Path
import os,sys,json,hashlib,subprocess,datetime,re
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28')
M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];P=D/'GREEN-run';S=D/'GREEN';B=D/'baseline'
BASE='ce5d4a74019e0dc2e656d08161641c498b159e7b';HEAD='c01e9376bdbcda7cb54ba55735cf053299b9af45'
os.environ['GIT_OPTIONAL_LOCKS']='0'
def need(v,s):
 if not v:raise RuntimeError(s)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def write(p,s):
 with Path(p).open('x') as f:f.write(s)
def git(a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a])
def g(a,root=M):return git(a,root).decode().strip()
def bindings(paths):return {str(p):sha(p) for p in sorted(set(map(Path,paths)))}
def review(p):
 r=read(p);need(r['accepted'] is True and r.get('findings',[])==[],'accepted review '+str(p))
 for n,h in r['bindings'].items():need(sha(n)==h,'review binding '+n)
 return r
script=D/'independent-production-admission-review.py'
write(script,Path(__file__).read_text())
need(g(['rev-parse','HEAD'])==g(['rev-parse','master'])==g(['rev-parse','origin/master'])==BASE,'baseline refs')
need(g(['rev-parse','HEAD'],R)==HEAD,'diagnostic ref')
need(not g(['diff','--name-only','HEAD','--','src','test','Project.toml']),'master production drift')
result=review(D/'result-review.json');need(result['accepted_variants']==['A','B','C'] and result['original_run_accepted'] is False,'accepted variants and original failed provenance')
red=review(D/'RED-run/result-review.json');need((red['passed'],red['expected_failures'],red['total'])==(28316,7,28323),'exact RED')
need(red['all_numerical_assertions_passed']==28227 and red['production_staging_authorized'] is True,'RED numerical/staging')
review(D/'correctness-qualification/result-review.json')
for root in [D,P]:
 protect=read(root/'protected-before.json')
 for n,h in {**protect['files'],**protect['indexes']}.items():need(sha(n)==h,'protected file/index '+n)
OVERRIDES=['JULIA_PROJECT','JULIA_LOAD_PATH','JULIA_BINDIR','JULIA_CPU_TARGET','JULIA_DEPOT_PATH','LD_PRELOAD','LD_LIBRARY_PATH','LD_AUDIT','BASH_ENV','ENV','PYTHONPATH','PYTHONHOME']
need(all(not os.environ.get(k) for k in OVERRIDES),'environment override')
env={k:os.environ[k] for k in OVERRIDES+['JULIA_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'] if k in os.environ}
need(env==read(P/'environment.json')['inherited']==read(D/'environment.json')['inherited'],'exact environment')
pins=read(P/'pins.json');need(len(pins['inventory'])==1346 and set(pins['files'])==set(pins['inventory']),'1346 exact pins')
for n,v in pins['inventory'].items():need(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],'pin '+n)
for tree in pins['trees']:
 need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in pins['inventory'] if Path(n).is_relative_to(tree)},'tree membership '+tree)
base=read(D/'baseline-tree.json');need(set(base)=={str(p.relative_to(B)) for p in B.rglob('*') if p.is_file()},'baseline complete membership')
for n,h in base.items():need(sha(B/n)==h==sha(M/n),'live original baseline '+n)
tracked=git(['ls-tree','-r','-z',BASE,'--','src','test','Project.toml'])
for entry in tracked.split(b'\0'):
 if not entry:continue
 meta,n=entry.split(b'\t',1);mode,kind,blob=meta.split();n=n.decode();data=(B/n).read_bytes()
 need(kind==b'blob' and mode==b'100644','baseline file mode '+n)
 need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob.decode(),'Git baseline blob '+n)
inv=read(D/'source-inverse.json');names=['src/dual_simplex.jl','src/factorization.jl','test/generic_sum_rational_growth_tests.jl','test/runtests.jl']
need(inv['accepted'] and inv['names']==names and inv['production_baseline']==BASE,'selected source names')
need({str(p.relative_to(S)) for p in S.rglob('*') if p.is_file()}==set(inv['whole_stage']),'whole stage membership')
for n,h in inv['whole_stage'].items():need(sha(S/n)==h,'whole stage bytes '+n)
need(set(inv['whole_stage'])==set(base)|{names[2]},'only new regression member')
changes=read(D/'changes.json');need([x['variant'] for x in changes]==['A','B','C'],'exact three replacements')
for n in names[:2]:
 s=(S/n).read_text()
 for ch in reversed(changes):
  if ch['file']==n:
   need(s.count(ch['new'])==1,'unique new production region '+ch['variant']);s=s.replace(ch['new'],ch['old'])
 need(s==(B/n).read_text(),'exact full inverse '+n)
for n in set(base)-set(names):need(sha(S/n)==base[n],'all untouched baseline files '+n)
for n in names:need(sha(S/n)==inv['candidate_sha256'][n],'candidate SHA '+n)
need((S/names[3]).read_text()==(B/names[3]).read_text()+'\ninclude("generic_sum_rational_growth_tests.jl")\n','only test runner include')
need(sha(S/names[2])==sha(D/'new-test.jl')==sha(D/'RED'/names[2]),'identical permanent test from RED')
reference=(D/'Reference.jl').read_text()
for arm in ['A','B','C']:
 expected=reference.replace('module SRGReference','module SRG'+arm,1)
 for ch in changes:
  if ch['variant']==arm:
   need(expected.count(ch['old'])==1,'private old region '+arm);expected=expected.replace(ch['old'],ch['new'])
 need(expected==(D/(arm+'.jl')).read_text(),'exact measured private variant '+arm)
test=(D/'new-test.jl').read_text()
need(reference in test and (D/'fixtures-reviewed.jl').read_text() in test and (D/'correctness-qualification/extra-corrected.jl').read_text() in test,'permanent numerical and reference provenance')
need('const SRGA=JSimplex\nconst SRGB=JSimplex\nconst SRGC=JSimplex' in test,'actual production aliases')
gates=read(D/'test-gates.json');need(gates['accepted_variants']==['A','B','C'] and gates['expected_RED_failures']==7 and gates['failure_line']==624,'seven frozen gates')
need(test.splitlines()[623].strip()=='@test all(after[k]["events"]<before[k]["events"] for k in 1:3)&&median(x["bytes"] for x in after)<median(x["bytes"] for x in before)','unchanged fixed allocation rule')
for n in names:
 before=B/n if (B/n).exists() else Path('/dev/null')
 d=subprocess.run(['/usr/bin/git','diff','--no-index','--check',str(before),str(S/n)],capture_output=True,text=True)
 need(d.returncode in [0,1] and not d.stdout and not d.stderr,'whitespace '+n)
contract=read(P/'contract.json');prior=D.parents[1]/'generic-bounds-norm-infeasibility/2026-10-27/GREEN-run/contract.json'
files=[names[2].split('/')[-1]]+read(prior)['files']+['refactorization_policy_tests.jl','refactorization_safety_tests.jl','refactorization_timing_tests.jl','refactorization_factor_tests.jl','refactorization_failure_tests.jl']
need(len(files)==len(set(files))==57 and contract['files']==files,'exact 57 whole test files')
need(contract['arm']=='GREEN' and contract['attempts']==1 and contract['source_root']==str(S),'one concrete GREEN attempt')
need(contract['expected_exit']==contract['expected_failures']==0 and contract['expected_failure_locations']==[] and contract['expected_total'] is None,'GREEN zero failures and no invented total')
need(contract['shared_limit_seconds']==3000 and contract['guard_limit_seconds']==2992,'shared budget')
expected_command=read(D/'contract-ready.json')['command'][:-2]+[str(P/'tests.jl')]
expected_command=[x.replace('--project='+str(M),'--project='+str(S)) for x in expected_command]
need(contract['command']==expected_command,'exact GREEN command')
driver=(P/'tests.jl').read_text()
need(' for file in '+json.dumps(files)+'\n' in driver and 'include(joinpath(ROOT,"test",file))' in driver,'exact ordinary complete includes')
need('const ROOT='+json.dumps(str(S)) in driver and '@assert realpath(pathof(JSimplex))==realpath(joinpath(ROOT,"src/JSimplex.jl"))' in driver,'runtime source identity')
need('@assert Base.active_project()==joinpath(ROOT,"Project.toml")' in driver and '@assert Threads.nthreads()==BLAS.get_num_threads()==1' in driver,'runtime project/thread identity')
for n in ['common.py','launch.py']:
 need((P/n).read_bytes()==(D/'RED-run'/n).read_bytes(),'same reviewed launch/common '+n)
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:
 need((P/'guard'/n).read_bytes()==(D/'RED-run/guard'/n).read_bytes(),'same reviewed guard '+n)
for n in files:need(str(S/'test'/n) in pins['inventory'],'complete test pin '+n)
for n in ['output','reservation.json','completed.json','supervisor.json','admission.json']:
 need(not (P/n).exists(),'fresh unexecuted phase '+n)
# Independent fresh whole-host check, including all historical groups AND sessions.
seed=read(P/'host-seed.json');groups=set(seed['groups']);need(len(groups)==655,'complete 655 historical groups')
for path in D.rglob('output/process.json'):
 rec=read(path)
 for k in ['runner','child']:
  for v in ['pgid','sid']:need(rec[k][v] in groups,'all completed process groups represented')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();need(boot==seed['boot_id'],'unchanged boot')
allow=D.parents[1]/'generic-quality-local/2026-10-27/host-identity-allowance.json'
need(sha(allow)=='f0b6a5093b9c1875ec8718bca8775bc44ba4d6d6ab98a1ac23adfe52d69f2a92','fixed unrelated identity allowance')
permitted=read(allow)['identities'];processes=[];allowed_seen=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  st=(p/'stat').read_text().rsplit(')',1)[1].split();command=[v.decode(errors='replace') for v in (p/'cmdline').read_bytes().split(b'\0') if v];comm=(p/'comm').read_text().strip()
  identity=dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=command,boot_id=boot)
  need(not any(Path(v).name.lower().startswith('julia') for v in [comm]+command[:1]),'live Julia')
  if identity['pgid'] in groups or identity['sid'] in groups:
   need(identity in permitted,'historical group/session occupied by non-allowed identity '+str(identity));allowed_seen.append(identity)
  processes.append(identity)
 except (FileNotFoundError,ProcessLookupError):pass
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines()}
need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'resource headroom')
host=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),boot_id=boot,groups=sorted(groups),processes=processes,allowed_seen=allowed_seen,no_Julia=True,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],observer_pid=os.getpid(),observer_parent_pid=os.getppid(),observer_command=sys.argv,refs=dict(master=BASE,diagnostic=HEAD))
put(D/'independent-production-host.json',host)
# Read-only checks above complete before any acceptance document is published.
production_text='''# Independent production review

Accepted for the concrete GREEN run, with no actionable numerical, ownership, exception, or avoidable-work/memory findings. This is a source review and run admission, not a GREEN pass or authorization to skip later commit/master-result review.

The actual stage has exactly four selected paths: src/dual_simplex.jl, src/factorization.jl, test/generic_sum_rational_growth_tests.jl, and the test/runtests.jl include. Full inverse replacements recover master ce5d4a74019e0dc2e656d08161641c498b159e7b byte for byte. All other baseline files and the entire stage membership are checked independently; original files/indexes remain unchanged. Measured private A/B/C are exact corresponding replacements in Reference. Original RED is independently accepted: 28,316 passes and exactly seven allocation failures at line624 (28,323 total); all28,227 numerical assertions passed. The identical permanent test is in GREEN.

A: the BigFloat sum guard retains zero shortcuts before sign tests, finite/precision gates before the reached cancellation comparison, and both separately owned exact-cancellation zeros. Nonzero same-sign values cannot cancel; NaN equality remains false and infinity cannot pass finite-left cancellation. Opposite-sign negation/equality, addition, FastTwoSum, underflow guard, all enclosures and mixed-precision behavior remain. The two sign-bit loads/comparison remove only a discarded same-sign negation. Row accumulation remains the same two sums per CSC nonzero and original feasibility scans are unchanged. This affects row/primal certification work, not simplex iteration count.

B: the added Rational{BigInt} method replaces signed-unit products with read-only rho or unary negation. Remaining matrix products/sums retain CSC order, including slack signs, zero checks, finite-bound rejection, tolerance allowance and the OverflowError-only catch. Rational infinities and zero-times-infinity still reach the same remaining DivideError operations. The generic fixed-width method and floating methods are unchanged. Installed GMP non-mutating operators allocate a fresh destination (base/gmp.jl:1097); shared positive rho and denominator owners are never mutated or returned through the Boolean result. One unit multiplication per reached nonzero and corresponding slack unit work disappear, with O(1) scalar state and no oriented vector or additional pass. Added specialization compilation is a cold cost, not claimed free.

C: only BigFloat PFI growth changes. A fresh invocation-local unit replaces L+1 constructors, and the qualified conditional magnitude skips unused positive negations over P packed values. Installed abs for Real eagerly computes its negative operand (base/number.jl:208); selected values and negative-operand rounding are preserved. Both explicit-init maxima follow mapfoldl_impl (base/reducedim.jl:330-336), preserving order, NaN/Inf/ties and output value/precision/input-or-fresh owner category. The unit is read-only and fresh on each call; no factor buffers or cross-call cache are added. Work remains O(L+P). Full forced refresh retains storage counting and recovery precision scans over matrix/costs/bounds. Scheduled refresh retains cached/fixed-policy gates, age1/every8/near-interval triggers and residual/growth reason priority. No trigger or tolerance changes.

The permanent ordinary tests compare actual production methods with a private original baseline, cover19 contexts including BigFloat64/128/256 and five rounding modes, exact/native controls, mixed512-bit stored values, signed zeros, NaN/Inf, empty inputs, invalid bounds, exception types, scalar/array owners and state restoration. Seven whole-call gates use three warmed alternating pairs, require lower allocation events in each and lower median bytes, and have no timing thresholds. Existing tests are unchanged. The corrected dyadic decoder runs only at the stored value's precision and separately characterizes the old ambient-rounded formula; this is test-oracle repair, not altered production precision.

No unnecessary added full scan, basis solve, array copy, conversion pass or retained numerical storage was found. The accepted independent cost review reports A row/feasibility median paired time ratios0.784/0.782 and byte ratios0.822/0.823; B complete exact certificate0.834 time/0.809 bytes; C growth/refresh/scheduling0.750/0.814/0.815 time and0.772/0.791/0.791 bytes. These summarize small warmed sparse/dense whole-call cells, not pooled speedups. All47,448 windows,22 GC windows, four slower A cells and nine unchanged-control byte differences remain. The original measurement's90 decoder failures remain failed; the separate28,227-assertion corrected qualification and qualified cost review support acceptance without repeating measurements. Cold compilation/preparation are separate. Closure allocation and native retained memory are not independently proven absent; full-solver throughput, large-scale behavior, x64, broader full suite, and end-to-end speedup remain unclaimed.

Concrete GREEN comprises the established51 whole files, this regression, and five affected refactorization policy/safety/timing/factor/failure files:57 total. One Julia/BLAS thread, GC1,0, existing compiled modules,2GiB heap hint,8GiB address-space limit,6GiB available-memory floor and1GiB swap ceiling remain. All1,346 pins and a fresh complete655-group/session host check passed. One attempt has a shared3,000-second allowance including startup/housekeeping, with a2,992-second guard deadline. No Julia, existing script, parser/probe, import of task code, measurement rerun or Git mutation was performed by this review. CI/automation/HH settings were not changed. Later GREEN result, actual commit, actual-master same-files/frozen-total run, and normal nonforce publication must each satisfy their separate controls.
'''
write(D/'PRODUCTION-REVIEW.md',production_text)
base_paths=[script,D/'independent-production-host.json',D/'PRODUCTION-REVIEW.md',D/'source-inverse.json',D/'baseline-tree.json',D/'changes.json',D/'result-review.json',D/'RESULT-REVIEW.md',D/'RED-run/result-review.json',D/'RED-run/audit.json',D/'new-test.jl',D/'test-gates.json',D/'Reference.jl',D/'A.jl',D/'B.jl',D/'C.jl',D/'fixtures-reviewed.jl',D/'correctness-qualification/extra-corrected.jl',P/'pins.json']+[S/n for n in names]
put(D/'production-review.json',dict(accepted=True,findings=[],accepted_variants=['A','B','C'],review_scope='actual staged production and permanent tests; GREEN execution admission prerequisite',Julia_executed=False,Git_mutated=False,baseline=BASE,names=names,unnecessary_work_or_memory_found=False,source_inverse_independently_verified=True,old_tests_unchanged=True,RED_passes=28316,RED_expected_failures=7,RED_total=28323,GREEN_pass_claimed=False,bindings=bindings(base_paths)))
admission_text='''# Independent GREEN admission

Accepted: exactly one concrete GREEN attempt over57 complete test files and1,346 unchanged pins. The list is the established51 files plus the identical permanent regression and five affected refactorization files. The driver asserts actual source/project identity and one Julia/BLAS thread, uses ordinary Test includes, and requires zero failures/errors/broken tests with ordinary completion. No future GREEN total is invented; its observed accepted total must be frozen for actual master.

The original RED remains accepted at28,316 passes/seven exact line624 allocation failures (28,323 total). Exact stage inverse and all unchanged baseline/source/test files passed independent byte checks. Numerical and work/memory review is recorded in production-review.json. Current launch/common/guard/entry/supervisor bytes match the independently reviewed RED controls. The common wrapper uses a fresh3,000-second shared clock and2,992-second guard deadline, exact pinned command, exclusive output reservation, process-identity startup handshake, parent-death gate and owned cleanup. Resource limits remain one Julia/BLAS thread,GC1,0,2GiB heap hint,8GiB address space, at least6GiB available RAM and at most1GiB swap. Fresh boot/start-tick/command identities cover all655 historical groups AND sessions; only the fixed exact unrelated identity allowance is accepted. No Julia is active.

This accepts launch only. GREEN result auditing and independent result review remain required; no commit, integration, master pass or push is claimed. Phase audit source is bound now, while future output/artifacts are deliberately not bound. The complete post-exit audit strengthens RED totals without weakening GREEN conditions. No thresholds, exceptions, timings or old failures are reclassified.
'''
write(P/'ADMISSION-REVIEW.md',admission_text)
controls=[D/n for n in ['prepare-phase.py','phase-audit.py','phase-audit-complete.py','stage.py','commit-integrate-publish.py','publication_checks.py','finalization_checks.py']]
admission_paths=[P/n for n in ['ADMISSION-REVIEW.md','common.py','launch.py','contract.json','tests.jl','pins.json','prepare.py','environment.json','host-seed.json','protected-before.json']]+[P/'guard'/n for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']]+[D/'production-review.json',D/'independent-production-host.json',D/'RED-run/result-review.json',D/'source-inverse.json',script]+controls
put(P/'admission.json',dict(accepted=True,findings=[],arm='GREEN',Julia_executed=False,pins=1346,whole_files=57,command=contract['command'],expected_exit=0,expected_failures=0,shared_limit_seconds=3000,guard_limit_seconds=2992,attempts=1,historical_groups_and_sessions=655,bindings=bindings(admission_paths)))
publication_text='''# Independent publication preparation review

The current controls are accepted as concrete preparation, conditional on later independently accepted GREEN, actual-commit and actual-master results. This is not a result claim or authority to bypass those prerequisites. Exact current production stage, regression, source inverse,57-file command,1,346-pin manifest, shared3,000-second budget and fresh655-group/session host review are bound.

commit-integrate-publish.py checks bound independent reviews before each action. It constructs only the four reviewed paths in a private index, verifies names/blobs/whitespace, creates a sole-parent commit and new codex branch, and preserves real indexes. Integration requires independent actual-commit review, unchanged target paths, exact local/tracking/remote base, fast-forward-only master update, exact committed/staged bytes and unchanged unrelated index entries. Actual master requires fresh admission and the same57 files with the observed GREEN total frozen. Push requires independently accepted actual-master results, complete tested/current/pinned tree equality, baseline beforeimage/index maps, exact allowed origin URL, normal nonforce push and local/tracking/remote verification.

publication_checks.py verifies complete source/test membership, path resolutions, current/tested hashes and historical source/index maps. finalization_checks.py requires exact allowed continuation keys, old beforeimage hashes, bound current bytes and verbatim preserved continuation suffixes; all other protected files remain byte-identical. Later diagnostics closure must separately review actual continuation artifacts and actual staged/committed names/blobs before publication; no future artifacts are bound here. Failed original measurement, corrected qualification, cost evidence, RED and old frozen provenance remain preserved. CI remains off, automation paused and HH reuse disabled; broader/full-suite/x64/native-retention coverage remains open.
'''
write(D/'PUBLICATION-PREPARATION-REVIEW.md',publication_text)
put(D/'publication-preparation-reviewed.json',dict(accepted=True,findings=[],Julia_executed=False,Git_mutated=False,scope='current integration/publication controls and concrete staged production; future results require separate review',required_future_reviews=['GREEN-run/result-review.json','commit-review.json','MASTER-run/admission.json','MASTER-run/result-review.json','diagnostics closure and exact staged/committed artifact review'],bindings=bindings(controls+[D/'PUBLICATION-PREPARATION-REVIEW.md',D/'production-review.json',P/'admission.json',D/'independent-production-host.json',D/'source-inverse.json',P/'pins.json',P/'contract.json',D/'protected-before.json',D/'baseline-tree.json',script]+[S/n for n in names])))
print(json.dumps(dict(accepted=True,production_review=True,GREEN_admission=True,publication_preparation=True,pins=1346,whole_files=57,historical_groups_and_sessions=655,Julia_executed=False,Git_mutated=False)))
