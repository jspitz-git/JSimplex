from pathlib import Path
import sys,json,ast,hashlib,tomllib,statistics,collections,subprocess
sys.dont_write_bytecode=True
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');P=D/'GREEN-run';G=D/'GREEN';Q=D/'comparison-2';K=D/'correctness-qualification'
sys.path.insert(0,str(P));import common as c
sha=c.sha
load=lambda p:json.loads(Path(p).read_text())
put=lambda p,obj:Path(p).open('x').write(json.dumps(obj,indent=2,sort_keys=True)+'\n')
write=lambda p,s:Path(p).open('x').write(s)
c.unchanged();host=c.host();pins=load(P/'pins.json');contract=load(P/'contract.json');inv=load(D/'source-inverse.json');changes=load(D/'changes.json')
assert len(pins['inventory'])==1312
names=['src/dual_simplex.jl','src/primal_simplex.jl','test/generic_bounds_norm_infeasibility_tests.jl','test/runtests.jl']
assert inv['names']==names and inv['production_baseline']==c.TARGET=='9d29b1f0aa21932217b03ca7b35dd91281baaae6'
assert set(inv['whole_stage'])=={str(p.relative_to(G)) for p in G.rglob('*') if p.is_file()}
for n,h in inv['whole_stage'].items():assert sha(G/n)==h
base=load(D/'baseline-tree.json');assert set(inv['whole_stage'])==set(base)|{names[2]}
for n,h in base.items():
 assert sha(D/'baseline'/n)==h
 if n not in names:assert sha(G/n)==h
for n in names[:2]:
 s=(D/'baseline'/n).read_text()
 for ch in changes:
  if ch['file']==n:
   assert s.count(ch['old'])==1
   assert ch['old'] in (Q/'Reference.jl').read_text() and ch['new'] in (Q/(ch['variant']+'.jl')).read_text()
   s=s.replace(ch['old'],ch['new'])
 assert s==(G/n).read_text()
assert (G/names[2]).read_bytes()==(D/'new-test.jl').read_bytes()
assert (G/names[3]).read_text()==(D/'baseline'/names[3]).read_text()+'\ninclude("generic_bounds_norm_infeasibility_tests.jl")\n'
for n in names:
 assert sha(G/n)==inv['candidate_sha256'][n]
 before=D/'baseline'/n if n in base else Path('/dev/null')
 r=subprocess.run(['/usr/bin/git','diff','--no-index','--check',str(before),str(G/n)],capture_output=True,text=True)
 assert r.returncode in [0,1] and not r.stdout and not r.stderr
for name in ['result-review.json','RED-run/result-review.json','correctness-qualification/result-review.json','comparison-2/cost-qualification-review.json']:
 r=load(D/name);assert r['accepted'] and not r.get('findings',[])
 for p,h in r['bindings'].items():assert sha(p)==h,(name,p)
red=load(D/'RED-run/audit.json');assert red['passed']==15911 and red['expected_failures']==10 and red['total']==15921
oldfiles=load(D.parents[1]/'generic-ratio-monitor/2026-10-27/GREEN-run/contract.json')['files']
assert contract['files']==['generic_bounds_norm_infeasibility_tests.jl']+oldfiles and len(set(contract['files']))==51
assert contract['arm']=='GREEN' and contract['source_root']==str(G) and contract['attempts']==1
assert contract['expected_exit']==contract['expected_failures']==0 and contract['expected_failure_locations']==[]
assert contract['shared_limit_seconds']==3000 and contract['guard_limit_seconds']==2992
assert contract['command']==[v.replace('--project='+str(c.M),'--project='+str(G)) for v in load(Q/'contract.json')['command'][:-2]]+[str(P/'tests.jl')]
assert (P/'common.py').read_bytes()==(Q/'common.py').read_bytes()
assert (P/'launch.py').read_text()==(Q/'launch.py').read_text().replace('592','2992').replace('600','3000')
for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']:assert (P/'guard'/n).read_bytes()==(Q/'guard'/n).read_bytes()
for p in [D/'stage.py',D/'commit-integrate-publish.py',D/'publication_checks.py',D/'finalization_checks.py',P/'launch.py',P/'common.py']:ast.parse(p.read_text())
assert 'shutil.copyfile(__file__' not in (D/'stage.py').read_text()
assert not (P/'output').exists() and not (P/'reservation.json').exists()
t=(G/names[2]).read_text()
for p in [Q/'Reference.jl',Q/'fixtures.jl',K/'extra-corrected.jl']:assert p.read_text() in t
assert '# RED whole-call allocation gate' in t.splitlines()[726]
assert 'new["seconds"]<' not in t and t.count('# RED whole-call allocation gate')==1
raw=tomllib.loads((Q/'output/results.toml').read_text());groups=collections.defaultdict(list);windows=gc=0
for cell in raw['cells']:
 pairs=collections.defaultdict(dict)
 for w in cell['windows']:
  windows+=1;gc+=w['gc_seconds']>0
  assert w['compile_seconds']==w['recompile_seconds']==0
  pairs[w['pair']][w['arm']]=w
 assert len(pairs)==9 and all(set(p)=={'original',cell['variant']} for p in pairs.values())
 if cell['type']=='BigFloat' or cell['type']=='Rational{BigInt}' and cell['variant']=='A':
  groups[cell['type']+'/'+cell['scope']].append({k:statistics.median(p[cell['variant']][k]/p['original'][k] for p in pairs.values()) for k in ['seconds','bytes','events']})
assert len(raw['cells'])==1632 and windows==29376 and gc==25 and len(raw['preparation'])==1670
summary={k:dict(cells=len(v),ratios={m:statistics.median(x[m] for x in v) for m in ['seconds','bytes','events']},slower_time_cells=sum(x['seconds']>1 for x in v),all_lower_bytes_events=all(x['bytes']<1 and x['events']<1 for x in v)) for k,v in groups.items()}
assert all(v['all_lower_bytes_events'] for v in summary.values())
write(D/'independent-production-review.py',Path(__file__).read_text());put(D/'independent-production-host.json',host);put(D/'independent-production-costs.json',dict(summary=summary,cells=1632,windows=windows,gc_windows=gc,preparation_entries=1670))
report='''# Independent production review

Accepted A, B and C in the exact four-file GREEN candidate for the prospective 51-file GREEN and subsequent commit review. There are no unresolved numerical, work, allocation, ownership or integration-control findings. This review does not claim GREEN, actual MASTER, publication or final closure has already passed. No Julia or Git mutation was performed by this reviewer.

The authoritative parent is actual master 9d29b1f0aa21932217b03ca7b35dd91281baaae6. Each baseline region was matched uniquely and byte-for-byte to comparison-2 Reference; each replacement matched its canonical A/B/C fragment. Reapplying the three replacements independently reproduces both complete production files. The remaining changes are the exact permanent regression file and one runtests include. Every other staged file equals the frozen baseline; all complete stage hashes, membership and whitespace checks passed. The stale diagnostic worktree src was not used as the source baseline.

A runs in tolerated-negative candidate bound snaps and final step validation during ratio pricing. Finite/early-return gates, lower-read/subtraction before upper-read/subtraction, predicted-point arithmetic, comparisons, ties, tolerances and row order remain unchanged. Bound and workspace arrays are concrete owned vectors and these arithmetic paths have no callback or precision transition. The invocation-private zero is read-only, returned only through internal max choices and never escapes the Boolean result. Empty or first-nonfinite step paths construct no zero. O(rows plus unbounded sides) zero constructions become at most one per reached guard, with one readiness check per visited step row. No extra row scan is introduced. Generic native/fixed-rational methods remain exact baseline bodies.

B runs in steepest initialization and checked-FTRAN weight maintenance. It retains both norm scans, existing column views, basis solve, scaled arithmetic, inverse/squares/sqrt/frexp order, partial writes and cacheability checks. The fresh current-precision product is bounded by the current-precision finite maximum unless positive infinite. Julia's AbstractFloat min returns the product on a finite tie, NaN and negative infinity; selecting it directly preserves these cases and owner/precision/signed-zero behavior. Positive infinity still creates a fresh cap per call. Existing mixed stored512 negative extreme inputs can produce NaN through current-precision negation overflow; that original behavior is correctly preserved. New work is O(1) infinity/sign predicates in exchange for the otherwise unused cap constructor.

C runs on full floating infeasibility certification. Exact integer-zero comparisons preserve BigFloat signs and zero behavior. Coefficient endpoints are computed at current precision by the original products/additions and widenings, even when input rho has stored512 precision. The conditional magnitude either reads a nonnegative endpoint or performs the same current-precision negation as abs; nextfloat still creates the widened magnitude. All coefficient/accumulator fresh zeros, interval arithmetic, every prevfloat/nextfloat, allowance/tolerance computation, endpoint multiplication, finite/unbounded/sign rejection and accumulation order remain unchanged. No endpoint aliases an output or gets mutated. Complexity stays O(variables+nonzeros); exact/native dispatch remains unchanged.

Work/memory finding: no unnecessary added vector/matrix scan, solve, array copy, conversion, invariant pass, persistent numerical cache, precision increase or update-chain retention was found. A's readiness branch and six new method bodies/compiled metadata are real costs, distinct from numerical buffers. No cache invalidation scheme is required. Savings are measured Julia allocation events/bytes, not proof of native limb freeing, reduced RSS or retained-memory improvement.

I independently recomputed all affected type/path cost ratios from the raw 1,632 cells and 29,376 windows. All measured compilation/recompilation is zero; all 25 GC windows and 1,670 cold/warm/fixture/reset/snapshot/validation/GC preparation entries remain. Sparse/dense 16/64 cases, BigFloat64/128/256 and five rounding modes plus native/exact controls are covered. All affected cell medians reduce bytes/events. BigFloat whole ratio time/byte/event ratios are 0.95183/0.93836/0.93932; initialization 0.96542/0.93678/0.94927; checked FTRAN 0.99656/0.99411/0.99568; certificate 0.97298/0.97700/0.97094. Direct norm has 29 slower time cells, checked FTRAN 24 and certificate 42. These short single-host results establish allocation reductions, not broad FTRAN/norm/solver timing benefits. Rational A has only four cells per path. No end-to-end or long-lived memory claim is warranted.

The original failed loader and comparison run with 18 incorrect cap expectations remain preserved. Correctness-only qualification passed 15,881 assertions with source-derived NaN expectations; no cost remeasurement substituted for the original data. The independently reviewed original-source RED has 15,911 passes and exactly ten expected allocation-gate failures, 15,921 total. Permanent ordinary tests retain numerical parity, signed zero, stored512, precision/rounding context, input owners, views, malformed dimensions, invalid witnesses, both orientations, unbounded signs and partial error states. Ten fixed three-pair whole-call gates require lower events in each pair and lower median bytes with zero measured compilation; no timing threshold or old numerical threshold was changed.

The corrected staging script's redundant self-copy issue is resolved and its beforeimage retained. Reviewed commit/integrate/push controls require exact candidate membership/hashes, private index and exact commit names/blobs/sole parent, independent actual-commit review, local fast-forward and protected unrelated indexes, fresh actual-MASTER tests matching the GREEN total, approved origin, normal nonforce push and remote verification. Historical source/index beforeimage checks bind the current four paths and exact parent. 51 whole files are the previous 50 plus this new test. Broader full suite, x64, native-retention, CI/automation/HH release coverage remain open. Future finalization/diagnostic-publication scripts are outside this initial preparation approval and require separate review.
'''
write(D/'PRODUCTION-REVIEW.md',report)
prodpaths=[D/n for n in ['PLAN.md','WORK-MEMORY.md','changes.json','new-test.jl','test-gates.json','source-inverse.json','result-review.json','RESULT-REVIEW.md','independent-production-review.py','independent-production-host.json','independent-production-costs.json','PRODUCTION-REVIEW.md','stage.py','commit-integrate-publish.py','publication_checks.py','finalization_checks.py']]+[G/n for n in names]+[Q/n for n in ['Reference.jl','A.jl','B.jl','C.jl','audit-qualified.json','summary-qualified.json','output/results.toml','output/run.log','output/process.json']]+[K/'result-review.json',D/'RED-run/result-review.json',D/'RED-run/audit.json',D/'RED-run/output/run.log',P/'contract.json',P/'pins.json']
put(D/'production-review.json',dict(accepted=True,findings=[],Julia_executed=False,Git_mutated=False,scope='exact GREEN candidate; future GREEN/MASTER/commit/publication gates required',names=names,parent=c.TARGET,variants=['A','B','C'],unnecessary_work_or_memory_found=False,bindings={str(p):sha(p) for p in prodpaths}))
controls=[D/n for n in ['stage.py','commit-integrate-publish.py','publication_checks.py','finalization_checks.py','source-inverse.json','production-review.json','PRODUCTION-REVIEW.md']]+[P/'contract.json',P/'pins.json']
put(D/'publication-preparation-reviewed.json',dict(accepted=True,findings=[],Julia_executed=False,scope='prepared exact four-path private-index commit, reviewed commit fast-forward, fresh51 MASTER, normal push controls only; no actual operation attested',bindings={str(p):sha(p) for p in controls}))
write(P/'ADMISSION-REVIEW.md','# Independent GREEN admission\n\nAccepted one prospective GREEN run over the previous 50 complete files plus the new regression (51 total), expected exit0 and no failed/error/broken/skipped tests. Fresh 1,312 pins, exact source/project/thread identity, inherited environment, protected files/indexes/refs and historical process group/session/start-tick/command/boot checks passed; no Julia is active. Existing guard/supervisor and 2,992/3,000-second absolute/shared ceiling are unchanged from reviewed RED. Exact production source and ordinary ten allocation gates are reviewed in PRODUCTION-REVIEW.md. Original-source RED independently witnessed 15,911 passes plus ten intended failures. This is admission only, not a claimed successful GREEN result. No Julia or Git mutation was performed.\n')
put(P/'independent-host.json',host)
admpaths=[P/n for n in ['pins.json','contract.json','tests.jl','common.py','launch.py','ADMISSION-REVIEW.md','independent-host.json']]+[D/'production-review.json',D/'publication-preparation-reviewed.json',D/'independent-production-review.py']+[P/'guard'/n for n in ['entry_gate.py','guard_reviewed.py','supervisor_reviewed.py']]
c.unchanged()
put(P/'admission.json',dict(accepted=True,findings=[],bindings={str(p):sha(p) for p in admpaths},expected_exit=0,expected_failures=0,files=51,pins=len(pins['inventory']),groups=len(host['groups']),Julia_executed=False,scope='one prospective exact GREEN whole-file run'))
print(json.dumps(dict(accepted=True,paths=names,pins=len(pins['inventory']),groups=len(host['groups']),files=51,Julia_executed=False)))
