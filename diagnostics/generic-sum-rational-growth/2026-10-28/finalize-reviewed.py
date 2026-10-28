from pathlib import Path
import sys,json,shutil,statistics as stats
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');sys.path.insert(0,str(D));import common as c
M=c.M;R=c.R
# Validate the accepted preparation and every review binding before any mutation.
from publication_checks import verify_historical_maps
integration_map=c.read('integration-historical-path-map.json');protected=c.read('protected-before.json');baseline=c.read('baseline-tree.json');production=c.read('production-commit.json')
main_index=c.git(['rev-parse','--path-format=absolute','--git-path','index'])
prospective=dict(master_source_before=integration_map['source_before'],master_index_before=integration_map['master_index_before'])
verify_historical_maps(D,M,main_index,c.TARGET,production['names'],integration_map,prospective,protected,baseline,c.need,c.sha)
exact_before={**integration_map['source_before'],**integration_map['master_index_before']}
for n in ['finalization-preparation-review.json','publication-preparation-reviewed.json','production-review.json','commit-review.json','MASTER-run/result-review.json','GREEN-run/result-review.json']:
 r=c.read(n);c.need(r['accepted'] is True and r['findings']==[],'review '+n)
 for bound_path,bound_hash in r['bindings'].items():
  if c.sha(bound_path)==bound_hash:continue
  c.need(bound_path in exact_before,'unresolved prefinal review binding '+bound_path)
  old=exact_before[bound_path];c.need(old['sha256']==bound_hash and c.sha(old['before'])==bound_hash,'exact prefinal before binding '+bound_path)
co=c.read('production-commit.json');target=co['commit'];pub=c.read('publication.json');c.need(pub['accepted'] and pub['commit']==target,'master published')
c.need(c.git(['rev-parse','HEAD'])==c.git(['rev-parse','origin/master'])==c.git(['ls-remote','origin','refs/heads/master']).split()[0]==target,'master refs')
g=c.read('GREEN-run/audit.json');m=c.read('MASTER-run/audit.json');red=c.read('RED-run/audit.json');cmp=c.read('audit-qualified.json');c.need(g['passed']==m['passed'] and g['expected_failures']==m['expected_failures']==0,'same all-pass GREEN/MASTER')
for tree in ['src','test']:c.need({str(p.relative_to(M)):c.sha(p) for p in (M/tree).rglob('*') if p.is_file()}=={str(p.relative_to(D/'GREEN')):c.sha(p) for p in (D/'GREEN'/tree).rglob('*') if p.is_file()},'actual tested whole tree')
extra=set()
for path in D.rglob('output/process.json'):
 p=json.loads(path.read_text());extra.update(p[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
h=c.host(extra);c.put('final-host.json',h)
I=D/'before-diagnostic';I.mkdir();ri=c.git(['rev-parse','--path-format=absolute','--git-path','index'],R);shutil.copyfile(ri,I/'diagnostic.index');c.put('diagnostic-index-before.json',{ri:dict(before=str(I/'diagnostic.index'),sha256=c.sha(I/'diagnostic.index'))})
(D/'.gitignore').write_text('/baseline/\n/RED/\n/GREEN/\n/before-master/\n/before-diagnostic/\n**/__pycache__/\n/publication-after.json\n')
B=D/'continuation-before';B.mkdir();cont=[R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'];mapping={}
for p in cont:
 c.need(c.sha(p)==c.read('protected-before.json')['files'][str(p)],'continuation original bytes');f=B/('STATUS.md' if p.name=='STATUS.md' else 'roadmap.md');shutil.copyfile(p,f);mapping[str(p)]=dict(before=str(f),sha256=c.sha(f))
hist=c.read('integration-historical-path-map.json');c.put('historical-path-map.json',dict(master_before=c.TARGET,master_source_before=hist['source_before'],master_index_before=hist['master_index_before'],continuation_before=mapping,all_older_maps_preserved=True))
rows=c.read('summary-qualified.json');table=[]
for typ,arm,scope,label in [('BigFloat','A','rows','BigFloat complete row intervals'),('BigFloat','A','feasible','BigFloat original-model primal feasibility'),('Rational{BigInt}','B','cert','Rational{BigInt} whole infeasibility certificate'),('BigFloat','C','growth','BigFloat PFI growth measurement'),('BigFloat','C','refresh','BigFloat full forced metric refresh'),('BigFloat','C','scheduled','BigFloat full scheduled refactor reason')]:
 rr=[v for v in rows if v['type']==typ and v['variant']==arm and v['scope']==scope]
 c.need(rr,'reported cells '+label)
 table.append('| '+label+' | '+str(len(rr))+' | '+' | '.join(f'{stats.median(v[k]["paired_median"] for v in rr):.6f}' for k in ['seconds','bytes','events'])+' |')
report=f'''# Multiprecision interval sums, exact certification and PFI growth

Production `{target}` has sole parent `{c.TARGET}` and is normally pushed and remotely verified. Exactly four paths change: src/dual_simplex.jl, src/factorization.jl, the new ordinary test/generic_sum_rational_growth_tests.jl and its runtests inclusion.

A adds a same-sign exclusion to the existing nonzero BigFloat exact-cancellation guard, removing an unused unary negation when cancellation is impossible. Zero shortcuts, finite and precision guard order, opposite-sign equality, actual addition, FastTwoSum, underflow checks, widened interval endpoints and scalar/array owner patterns remain. Complete row intervals and original-model feasibility are measured, including their original scans and allocations.

B specializes only Rational{{BigInt}} infeasibility certification. A positive unit orientation uses rho read-only, a negative orientation uses ordinary unary negation, followed by the same remaining coefficient multiplication and CSC accumulation. Slack sign selection, all zero comparisons, allowance arithmetic, bound rejection and OverflowError-only catch remain. No oriented-rho vector, extra pass or writable shared scalar is introduced. Fixed-width rational and floating certificate methods remain unchanged. Both signs of stored infinity, explicit zero DivideError, unbounded selected-bound rejection and fixed-width overflow controls are retained.

C specializes only BigFloat PFI growth measurement. One fresh invocation-private read-only unit replaces per-update units, and the existing conditional magnitude omits discarded positive-value negations. Explicit-init nested maxima retain their left-fold order, output values/precision/owner categories, empty/subunit fresh outputs, ties and NaN/Inf behavior. Complete forced refresh and scheduled reason retain storage counting, recovery-precision scans, state caching, age gates and numerical-trigger priority. This is periodic adaptive work, not every legacy iteration; fixed rational policy skips this growth computation.

| Complete call | Cells | Median paired time ratio | Median bytes ratio | Median allocation events ratio |
|---|---:|---:|---:|---:|
'''+ '\n'.join(table)+f'''

Ratios below one favor the candidate. Each fixed cell has three warm pairs and nine alternating measured pairs. These are single-process fixture-cell medians, not independent-run confidence intervals. All 22 in-window GC occurrences, slower samples and dispersion are preserved. A has four slower cell medians; the worst sparse feasibility cell is about1.699x with no in-window GC and wide paired dispersion. C has 540 empty-chain whole-call cells with identical allocation counters and no timing gain claim; all1,080 nonempty-chain whole-call cells have lower paired medians for time, bytes and events. Unchanged-type control events match, but nine Rational{{BigInt}} A/C controls have variable byte medians (up to7152 versus5872); the cause is unassigned, not evidence of changed production arithmetic. No end-to-end solver, universal, native-free or retained-native-memory improvement is proved.

The complete saved comparison has2,636cells and47,448 measured windows, all with zero compilation/recompilation, plus2,674 preparation entries. BigFloat64/128/256 under five rounding modes, stored512 controls, Float32/64 and RationalBigInt/Int64 controls, sparse/dense row/certificate cases and real PFI replace_column! chains0/8/32 are included. Fixture/backend/update-chain construction, reset, first per-cell calls, warm calls, validation, result capture and explicit GC costs remain recorded separately. The per-cell records named cold already follow correctness and are not isolated per-variant process cold starts. Recorded compilation is attributed to correctness and validation preparation. Outer driver/startup work and a complete per-variant cold-specialization budget remain incompletely measured; no candidate-specific cold-start saving is claimed. Inclusive{cmp['elapsed_shared_seconds']:.3f}s is not kernel time. Each new per-call unit/closure/sign-selection cost is inside its whole-call window.

Both original offline admission rejections and all initial files/pins remain preserved. They caught a Rational control using a floating-only reusable row method, missing genuine recovery-precision/empty/owner/infinity controls, and an incorrect negative-infinity one-sided expectation. Separate harness-only fixes preserved all candidates and every planned cell/window before the first Julia launch.

The original comparison finished111,259 passing assertions plus90 incorrect diagnostic exact-decoder expectations, exit1 and a rejected supervisor; that original run remains failed. Installed Rational{{BigInt}}(BigFloat) uses ambient-precision ldexp while decoding the stored512 result. All90 logged values independently match1+2^-53, or1+2^-53+2^(1-p) under upward/away rounding, instead of the unchanged exact target1+2^-53+2^-400. A separate correctness-only qualification set precision only around the decoder, characterized the old rounded result, retained the exact target and verified ambient restoration. It passed28,227/28,227 ordinary assertions across19contexts in{c.read('correctness-qualification/audit.json')['elapsed_shared_seconds']:.3f}s and performed zero measurement windows. The production arithmetic, inputs and cost schedule never changed and were not remeasured.

New postexit cost-data auditors were reviewed separately and are not retroactive launch pins. Initial prospective auditor variable-shadow and missing qualifier-group checks were rejected and corrected in separate preserved scripts. A first executed complete auditor stopped before publishing any accepted output at the strict historical group/session check. Its occupant identity/cause was not captured and remains unknown; PID reuse is only a hypothesis. A fresh read-only check found all historical groups absent. A separately accepted copy added only its own observer identity record and retained the same strict full group/session and raw-data checks. That copy passed and qualified the saved cost data only; it did not relabel the original numerical run as passing or introduce a PID exception.

Original production RED:28,316PASS plus exactly7 expected allocation failures, total28,323, elapsed{red['elapsed_shared_seconds']:.3f}s. Seven fixed three-pair whole-call gates require fewer events in every pair and fewer median bytes. They impose no timing assertion or old threshold/test changes. GREEN and actual MASTER each pass{m['passed']}/{m['passed']} assertions in the same57 ordered whole files (previous51, new regression, five refactorization policy/safety/timing/factor/failure files), with inclusive elapsed{g['elapsed_shared_seconds']:.3f}/{m['elapsed_shared_seconds']:.3f}s. Ordinary Test is used without a custom recorder or manual testset-stack management. No historical release exception is reused.

Independent numerical, ownership, computational-work and retained-memory review found no unnecessary new production work or numerical storage. A trades two cheap sign checks for eliminated MPFR negations; B removes exact GMP unit multiplications without an extra vector/pass; C removes repeated units and discarded magnitudes while preserving O(chain length+packed entries) scans. All existing basis solves, copies, conversions, model/precision scans and safeguard checks remain. Two cold specialization methods add compiler metadata whose full cold cost and retention were not separately measured. Per-call captured-seed closure overhead is included in the complete measured calls; native retention remains unqualified. No new persistent numerical cache or growing ledger is introduced. Source constructor counts are not measured allocation/free/native-memory balances.

The whole tested source/test tree and protected user/environment/index state are preserved through private-index commit, independently reviewed actual commit, local ff-only integration, actual-master tests and normal publication. Old source/index/continuation bindings resolve only to exact baseline, before-master and continuation-before bytes; all older maps and rejected evidence remain intact. Fresh{len(h['groups'])} historical groups ANDsessions/boot/start_ticks/command/noJulia are checked with only the fixed exact unrelated WSL identity allowance. CI remains off, automation paused and HH reuse disabled; broader/full-suite/x64/native-retention work remains open. Final acceptance additionally requires PASS closure.json and the exact diagnostic-publication-plan.json; remote diagnostic publication is recorded separately in publication-after.json. No automatic next experiment or cleanup.
'''
(D/'FINAL-REPORT.md').write_text(report)
prefix=f'''# Current continuation — interval sum, exact certificate and PFI growth savings integrated, 2026-10-28

Master/origin/master `{target}` normally pushed and remotely verified. A BigFloat same-sign cancellation guard skips only unused negation; B Rational{{BigInt}} certificate uses read-only rho/unary sign instead of unit multiplication; C BigFloat PFI growth uses one private unit and conditional magnitudes. Exact4paths; actual arithmetic/CSC accumulation order, enclosures, tolerances, exceptions, owner categories and refactorization gates retained. No newscan/solve/copy/conversion/persistent numeric cache; independent review found no unnecessary production work or retained numerical memory.

Saved2636cells/47448compilezero windows/22GC,2674prep. Original111259PASS+90 exact-decoder oracleFAIL stays failed; separate storedprecision decoder qualification28227PASS/19contexts/0windows, no costrepeat. All90 values independently explained by ambient ldexp rounding; exacttarget unchanged. Earlieroffline rejections/auditor drafts and one transient strict-host rejection preserved; occupant/causeUNKNOWN, no PIDexception. Newqualifiedpostexit observer passed identical strict gates. A whole row/feasibility time~.78, B exactcertificate~.83, C periodicfullrefresh/scheduled~.81; allslower/GC/controlbyte variations preserved. Empty C allocations unchanged; no whole-solver/universal/native-free claim.

OriginalRED28316PASS+7expected costFAIL; GREEN/actualMASTER each{m['passed']}PASS in the same57wholefiles. Existingtests/thresholds unchanged/no oldexceptionreused. Exactinverse/privateindex/actualcommitreview/ff-only/freshMASTER/independentreviews/normalpush verified. Evidence diagnostics/generic-sum-rational-growth/2026-10-28/FINAL-REPORT.md. FinalPASSclosure and exactdiagnosticpublication outcomes are recorded by canonical output files. Prior bindings mapONLY baseline/before-master/continuation-before; all older maps/raw/rejections FROZEN NEVER RERUN/rewrite. Userfiles/env preserved, fullgroupsANDsessions/boot/start_ticks/command/noJulia; CIoff/automationpaused/HHdisabled/broaderfullsuite/x64/native-retentionOPEN. No automatic next experiment/cleanup.

## Previous continuation — preserved verbatim below

'''
for p in cont:p.write_bytes(prefix.encode()+Path(mapping[str(p)]['before']).read_bytes())
(D/'progress-final.md').write_text(f'All3accepted; original111259+90 diagnosticFAIL preserved; saved2636cells47448windowscostqualified withoutrepeat; correctness28227PASS; RED28316+7expected; GREEN/MASTER{m["passed"]}PASS57files; exact4pathcommit/ff-only/normalpushremoteverified. Broader/fullsuiteOPEN.\n')

if Path(__file__).resolve()!=(D/'finalize-reviewed.py').resolve():shutil.copyfile(__file__,D/'finalize-reviewed.py')
print('finalreport/exactcontinuation prepared',target)
