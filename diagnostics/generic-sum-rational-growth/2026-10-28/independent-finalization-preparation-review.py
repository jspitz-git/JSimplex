from pathlib import Path
import json,hashlib,datetime
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28')
def need(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,s):
 with Path(p).open('x') as f:f.write(s)
def put(p,v):save(p,json.dumps(v,indent=2,sort_keys=True)+'\n')
script=D/'independent-finalization-preparation-review.py';save(script,Path(__file__).read_text())
initial=read(D/'finalization-preparation-initial-review.json');need(initial['accepted'] is False and len(initial['findings'])==3,'preserved initial rejection')
for p,h in initial['bindings'].items():need(sha(p)==h,'initial frozen binding '+p)
fix=read(D/'final-controls-review-fix.json');need(fix['Julia_executed'] is False and fix['controls_executed'] is False,'unexecuted correction scope')
for name,h in {**fix['original'],**fix['canonical']}.items():need(sha(D/name)==h,'exact original/corrected source '+name)
for record in ['result-review.json','production-review.json','publication-preparation-reviewed.json','RED-run/result-review.json']:
 r=read(D/record);need(r['accepted'] is True and r['findings']==[],'existing accepted review '+record)
 for p,h in r['bindings'].items():need(sha(p)==h,'existing review binding '+p)
f=(D/'finalize-reviewed.py').read_text();cl=(D/'closure-reviewed.py').read_text();pub=(D/'diagnostic-publish.py').read_text();helpers=(D/'publication_checks.py').read_text();protection=(D/'finalization_checks.py').read_text()
need("for n in ['finalization-preparation-review.json','publication-preparation-reviewed.json','production-review.json','commit-review.json','MASTER-run/result-review.json','GREEN-run/result-review.json']:" in f,'full finalizer preparation/result preflight')
need(f.index('verify_historical_maps(D,M,main_index')<f.index('for bound_path,bound_hash')<f.index("c.put('final-host.json',h)"),'validated exact beforeimages and review bindings before mutations')
for text in ["if c.sha(bound_path)==bound_hash:continue","c.need(bound_path in exact_before,'unresolved prefinal review binding '+bound_path)","old['sha256']==bound_hash and c.sha(old['before'])==bound_hash"]:need(text in f,'strict finalizer binding '+text)
need("if Path(__file__).resolve()!=(D/'finalize-reviewed.py').resolve():shutil.copyfile(__file__,D/'finalize-reviewed.py')" in f,'canonical selfcopy guard')
need("shutil.copyfile(__file__,D/'finalize.py')" not in f,'old finalizer never overwritten')
need('Outer driver/startup work and a complete per-variant cold-specialization budget remain incompletely measured' in f,'startup cost limit')
need('compiler metadata whose full cold cost and retention were not separately measured' in f,'cold method metadata limit')
need('Per-call captured-seed closure overhead is included in the complete measured calls; native retention remains unqualified' in f,'whole-call versus native limit')
for fragment in ['about1.699x with no in-window GC','540 empty-chain','all1,080 nonempty-chain','nine Rational{{BigInt}}','2,674 preparation entries','original run remains failed','occupant identity/cause was not captured and remains unknown','PID reuse is only a hypothesis','did not relabel the original numerical run as passing or introduce a PID exception','Final acceptance additionally requires PASS closure.json','recorded separately in publication-after.json']:
 need(fragment in f,'report retained evidence/qualification '+fragment)
need("for phase,manifest in [(D,n) for n in ['pins.json','pins-reviewed.json','pins-ready.json']]+[(D/n,'pins.json') for n in ['correctness-qualification','RED-run','GREEN-run','MASTER-run']]:" in cl,'all seven historical pinsets')
for fragment in ["cmp['original_run_accepted'] is False","cmp['cases']==2636","cmp['windows']==47448","cmp['preparation']==2674","cmp['original_failed_assertions']==90","cmp['original_assertions_passed']==111259","cmp['gc_windows']==22","qualified['assertions']==28227","qualified['measured_windows']==0","red['passed']==28316","red['expected_failures']==7","red['total']==28323","g['passed']==m['passed']==c.read('MASTER-run/contract.json')['expected_total']","len(c.read('GREEN-run/contract.json')['files'])==57","c.read('GREEN-run/contract.json')['files']==c.read('MASTER-run/contract.json')['files']"]:
 need(fragment in cl,'case-specific closure guard '+fragment)
need("verify_historical_maps(D,M,mi,c.TARGET,co['names'],c.read('integration-historical-path-map.json'),hist,protected,base,c.need,digest)" in cl,'exact final source/index maps')
need("c.need(hist['master_before']==c.TARGET,'exact continuation old master ref')" in cl,'final old ref exact')
need(cl.index('verify_historical_maps(D,M,mi')<cl.index("checks['verbatim_continuation_and_maps']=True"),'no unsupported map closure claim')
need("need(set(hist['source_before'])==set(expected)" in helpers and "v['before']==str(before) and v['sha256']==baseline[name]" in helpers and "v['sha256']==protected['indexes'][main_index]==sha(before)" in helpers,'exact helper keys/paths/hashes')
need('need(set(continuations)==set(allowed)' in protection and 'endswith(Path(entry["before"]).read_bytes())' in protection,'only allowed verbatim continuation changes')
for fragment in ["for p,h in cl['bindings'].items():c.need(c.sha(p)==h", "c.need(not git(['diff','--cached','--raw','-z'])", "actual==allnames", "g(['rev-parse',':'+n])==b", "g(['rev-parse',new+':'+n])==b", "new+':refs/heads/codex/simplex-core-architecture'", "g(['ls-remote','origin','refs/heads/codex/simplex-core-architecture']).split()[0]==g(['rev-parse','origin/codex/simplex-core-architecture'])==new"]:
 need(fragment in pub,'exact diagnostic publication guard '+fragment)
need(pub.index("for n,b in expected.items():c.need(g(['rev-parse',':'+n])==b")<pub.index("'commit','-m',message"),'all staged blobs before commit')
need(pub.index("for n,b in expected.items():c.need(g(['rev-parse',new+':'+n])==b")<pub.index("'push','origin'"),'all committed blobs before push')
pins=read(D/'GREEN-run/pins.json')
new_controls=['finalize.py','closure.py','finalize-reviewed.py','closure-reviewed.py','diagnostic-publish.py','final-controls-prepare.py','final-controls-reviewed-prepare.py']
need(all(str(D/n) not in pins['inventory'] for n in new_controls),'new controls not retroactive GREEN pins')
# No host/process/Git inspection or task-code import is performed while GREEN runs.
report='''# Independent finalization preparation review

Accepted for the separate canonical controls finalize-reviewed.py, closure-reviewed.py and diagnostic-publish.py, conditional on their actual runtime prerequisites. The original unexecuted finalize.py and closure.py, all initial preparation source and the initial three-finding rejection remain preserved. No final report, continuation, closure, commit, master test or diagnostic-publication result is claimed here.

All three initial findings are resolved. The reviewed finalizer validates the integration source/index maps and original beforeimage paths/hashes, then requires the accepted finalization preparation, production/publication preparation, actual-commit, GREEN-result and actual-MASTER-result reviews. Every review binding must match current bytes or one of those validated exact original source/index beforeimages before any report or continuation mutation. Its self-copy guard names finalize-reviewed.py, so it cannot rewrite the original rejected finalizer. Actual master publication and live/tested complete source/test equality are checked before final output. Original continuation bytes are backed up and prepended verbatim, with only the two explicitly allowed paths changing.

The reviewed closure checks all seven pinsets: original, reviewed and ready comparison manifests; separate corrected correctness qualification; RED; GREEN; and actual MASTER. It validates exact path resolutions, complete tree membership, current hashes or exact historical beforeimages, original failed exit1 and rejected-supervisor evidence, both initial offline rejection records and the failed strict postexit observer. Case checks require2636 cells,47448 measurement windows,2674 preparation entries,22 GC windows, original111259 passes plus90 failures with original_run_accepted=false, corrected28227 assertions and zero measurement windows, RED28316+7=28323, and accepted all-pass GREEN/MASTER with the observed GREEN total frozen in the MASTER contract. Both runs must use the same57 ordered whole files. It now validates final master_before and the exact final/integration source/index mapping keys, paths and hashes through verify_historical_maps before claiming map closure. Final review bindings and unchanged current indexes are checked; fresh complete group/session/no-Julia checks are reserved for runtime after tests finish.

The report retains the four slower A cells (worst about1.699x with no window GC), all22 GC windows, nine unchanged RationalBigInt-control byte variations of unresolved cause, C540 empty-chain cells and1080 active-chain cells, and the distinction between cell-level paired medians and end-to-end speedup. Original numerical failure remains failed; decoder-only qualification does not repeat cost windows. The strict host-audit rejection retains unknown occupant/cause and introduces no PID exception. Source work remains O(1) added scalar state for A/B and O(chain length+packed entries) for C, with no extra scans/solves/copies/persistent numerical cache. Two specialization methods add compiler metadata; the revised wording explicitly leaves full cold cost/retention, outer-driver/startup and native retention incompletely measured, while per-call closure cost is included in measured whole calls. No native-free, universal or full-solver throughput claim is made.

Diagnostic publication requires accepted canonical closure and final review, unchanged bound artifacts, exact local/remote refs and endpoint, no unrelated staged changes, protected files/indexes and a fresh no-Julia host observation. It stages only the explicit closed diagnostic paths plus the two continuations, preserves local private stages/beforeimages, creates an exact publication plan, and checks every staged and committed blob including the plan itself before normal nonforce push and remote verification. Canonical closure.json, diagnostic-publication-plan.json and publication-after.json remain future outputs; actual report/continuation review is required before closure/publication. Existing frozen diagnostic whitespace is recorded rather than silently rewritten.

These controls were prepared after the1346-pin GREEN manifest and are bound separately here, not retroactively treated as launch pins. This review read source and immutable evidence and wrote only new exclusive reviewer artifacts. It ran no Julia, task-code imports, previous scripts, parser/probe, Git operation or host/process audit while GREEN is active. No measurement was repeated and no active-run input was changed. CI/automation/HH state and broader/full-suite/x64/native-retention scope remain unchanged/open as recorded.
'''
md=D/'FINALIZATION-PREPARATION-REVIEW.md';save(md,report)
paths=[script,md]+[D/n for n in ['finalization-preparation-initial-review.json','FINALIZATION-PREPARATION-INITIAL-REVIEW.md','finalize.py','closure.py','finalize-reviewed.py','closure-reviewed.py','diagnostic-publish.py','final-controls-prepare.py','final-controls-reviewed-prepare.py','final-controls-review-fix.json','finalization_checks.py','publication_checks.py','common.py','RESULT-REVIEW.md','result-review.json','production-review.json','publication-preparation-reviewed.json','RED-run/result-review.json','GREEN-run/admission.json','GREEN-run/contract.json','GREEN-run/pins.json','audit-qualified.json','correctness-qualification/audit.json','cost-audit-host-rejection.json']]
put(D/'finalization-preparation-review.json',dict(accepted=True,findings=[],resolved_initial_findings=3,canonical_finalizer=str(D/'finalize-reviewed.py'),canonical_closure=str(D/'closure-reviewed.py'),canonical_diagnostic_publisher=str(D/'diagnostic-publish.py'),scope='separate finalization controls preparation only; actual results/final artifacts require later independent review',Julia_executed=False,Git_operations=False,host_audit_performed=False,active_GREEN_inputs_unchanged=True,retroactive_GREEN_pins_claimed=False,future_artifacts_bound=False,bindings={str(p):sha(p) for p in sorted(set(paths))}))
print(json.dumps(dict(accepted=True,resolved_initial_findings=3,canonical_controls=3,Julia_executed=False,Git_operations=False,host_audit_performed=False,future_artifacts_bound=False)))
