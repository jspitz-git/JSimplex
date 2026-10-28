from pathlib import Path
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');O=D.parents[1]/'generic-sum-rational-growth/2026-10-28'
old=(O/'finalize-reviewed.py').read_text();prefix=old[:old.index('rows=c.read(')]
prefix=prefix.replace(str(O),str(D)).replace("cmp=c.read('audit-qualified.json')","cmp=c.read('audit.json')").replace("c.put('final-host.json',h)","c.put('finalization-host.json',h)")
rest='''rows=c.read('summary.json');accepted=c.read('result-review.json')['accepted_variants'];table=[]
for typ,arm,scope,label in [('BigFloat','A','residual','BigFloat complete BTRAN row residual'),('BigFloat','B','update','BigFloat complete PFI column replacement'),('BigFloat','C','crash','BigFloat complete crash row selection'),('Rational{BigInt}','C','crash','RationalBigInt complete crash row selection')]:
 rr=[v for v in rows if v['type']==typ and v['variant']==arm and v['scope']==scope]
 c.need(rr,'reported cells '+label)
 table.append('| '+label+' | '+str(len(rr))+' | '+' | '.join(f'{stats.median(v[k]["paired_median"] for v in rr):.6f}' for k in ['seconds','bytes','events'])+' |')
report=f\'''# Residual seed, pivot magnitude and crash ranking savings

Accepted production variants: {', '.join(accepted)}. Production `{target}` has sole parent `{c.TARGET}` and is normally pushed and remotely verified. Exact production/test paths: {', '.join(co['names'])}.

A retains the original invocation-private accumulator zero as a read-only expected zero inside the BigFloat dual-row residual check. Every original residual negation, product, addition, scale, tolerance, finite/index/dimension check and division remains. No new scalar constructor, persistent cache or pass is added. Empty and zero results remain fresh per call.
B returns a finite strictly positive BigFloat pivot read-only for comparison; zero/negative/nonfinite values retain the original stored-precision context and absolute value. Complete PFI column replacement includes tolerance conversion, validation, inverse/divisions, nonzero count, new/recycled packing and update publication. Every shared helper consumer is comparison-only; BigFloat Markowitz retains its separate existing method. No arithmetic magnitude enters the published coefficients from this helper. Direct helper edge tests and later fresh affected whole-file regressions qualify its broader consumers; the private cost comparison measures PFI only.
C retains the original per-row absolute magnitude as the left operand in bounded crash ranking comparisons, only for ordinary Vector BigFloat/RationalBigInt. It retains the maximum scan, original threshold/violation check, right-side absolute computations, strict ties, cap and insertion order. Native/fixed-rational/custom-array routes remain original. This is optional initialization, not ordinary-iteration savings. No new vector/cache or scan.

The descriptions above document measured private candidates; only the listed accepted variants are present in production. Rejected variants, if any, remain diagnostic evidence and are not promoted.

| Complete call | Cells | Median paired time ratio | Median bytes ratio | Median events ratio |
|---|---:|---:|---:|---:|
\'''+ '\\n'.join(table)+f\'''

Ratios below one favor the candidate. All {cmp['cases']} cells and {cmp['windows']} windows use three warm pairs and nine alternating measured pairs; all measured compilation/recompilation is zero. All {cmp['gc_windows']} in-window GC occurrences, slower cells, negative controls and dispersion remain in raw results/summary/result review. A single process of fixture-cell medians is not an independent-run confidence interval or end-to-end solver speedup. See RESULT-REVIEW.md for per-shape/size/density acceptance and exceptions, including unaffected controls. No native allocation/free balance or retained-native-memory gain is proved.

The comparison passed {cmp['assertions']}/{cmp['assertions']} ordinary assertions in inclusive {cmp['elapsed_shared_seconds']:.3f}s. Backend/fixture construction, reset, first per-cell calls, warm calls, validation, explicit GC and result consumption are separately retained in {cmp['preparation']} preparation entries. First calls follow correctness and are not isolated cold-process starts. A complete per-variant startup/compiler metadata/retention budget is not measured. Per-call branch/local/closure overhead is included in whole-call windows; initializer setup and numerical kernels are distinguished.

The initial offline admission was rejected for dense directions incorrectly labeled sparse and missing declared boundary controls. Original files/manifests and rejected review remain unchanged. Separately sealed fixes create n/4 sparse versus n dense entries and alternate signs by surviving entry for sparse mixed cases; explicit assertions check these shapes. Empty residual, signed exact pivot thresholds, crash threshold, dimension/index errors, stored512/ambient64/128/256, all five rounding modes, signedzero/nonfinite and ownership/fresh-output controls are ordinary tests. Ties/zero/no-violation/custom arrays are correctness-only, not additional measured shapes. Candidate source and grid stayed fixed through the prelaunch harness fixes; no original rejection becomes a retroactive pass.

Original production RED has {red['passed']} passing checks plus exactly {red['expected_failures']} expected whole-call allocation failures, total {red['total']}. GREEN and actual MASTER each freshly pass {m['passed']}/{m['passed']} in the same {len(c.read('MASTER-run/contract.json')['files'])} ordered whole files, inclusive {g['elapsed_shared_seconds']:.3f}/{m['elapsed_shared_seconds']:.3f}s. Ordinary Test is used without a custom recorder/manual testset stack. Every original test/threshold, numerical safeguard, tolerance, precision and pivot policy is retained; no historical release exception is reused. No full-suite/x64 claim.

Independent numerical/ownership/computational work and memory review accepts only the production variants named above. Existing full scans, solves, copies, conversions and invariant checks remain; eliminated work is temporary scalar construction/context overhead, not relocated to a new buffer or index. Local pointer/branches and cold specialization metadata are explicit costs. No new persistent numerical cache/growing ledger is introduced; retained native memory remains unqualified.

Whole tested source/test trees, user files/environment/index state, exact private-index commit, independent actual commit review, ff-only integration, fresh actual-master tests and normal remote publication are verified. Exact older source/index/continuation bindings resolve only to baseline/before-master/continuation-before bytes; all older maps and failed records remain preserved. Fresh {len(h['groups'])} historical groups AND sessions, boot/start_ticks/command/noJulia and the sole fixed exact unrelated WSL identity allowance are checked. CIoff, automationpaused, HHreuse disabled; broader plan/fullsuite/x64/native-retention OPEN. Final acceptance additionally requires separate PASS closure.json and exact diagnostic-publication-plan; publication-after.json records remote diagnostic publication. No automatic next experiment or cleanup.
\'''
(D/'FINAL-REPORT.md').write_text(report)
head=f\'''# Current continuation — residual pivot crash candidates closed, 2026-10-28

Master/origin/master `{target}` normally pushed/remotely verified, accepted variants {','.join(accepted)} only. Exact paths/source inverse, original numerical safeguards/order/tolerances/precision/owners/pivot rules retained. No new full scan/solve/copy/conversion/persistent numeric cache. See diagnostics/generic-residual-pivot-crash/2026-10-28/FINAL-REPORT.md and independent result/production reviews for measured complete-function savings and all controls/limits; no universal/end-to-end/native-free claim.

Single comparison {cmp['assertions']}PASS/{cmp['cases']}cells/{cmp['windows']}compilezero windows/{cmp['gc_windows']}GC preserved, preparation {cmp['preparation']}. Initial offline rejection and every initial/ready artifact frozen; final sparse/sign and boundary harness fixes happened before launch, candidates/grid unchanged. OriginalRED {red['passed']}PASS+{red['expected_failures']}expectedcostFAIL; GREEN/actualMASTER {m['passed']}PASS each/{len(c.read('MASTER-run/contract.json')['files'])}samewholefiles. Independent reviews accepted; private-index commit/actualcommitreview/ff-only/freshMASTER/normalpush verified. Final PASS closure/exactdiagnosticpublication in canonical output records. All older bindings map ONLY exact baseline/before-master/continuation-before bytes; all older maps/artifacts preserved/frozen NEVER RERUN/rewrite. Userfiles/env/index protected, fullgroupsANDsessions/boot/start_ticks/command/noJulia. CIoff automationpaused HHdisabled; broader/fullsuite/x64/native-retentionOPEN. No automatic next experiment/cleanup.

## Previous continuation — preserved verbatim below

\'''
for p in cont:p.write_bytes(head.encode()+Path(mapping[str(p)]['before']).read_bytes())
(D/'progress-final.md').write_text(f'Accepted production variants {accepted}; comparison{cmp["assertions"]}PASS, RED{red["passed"]}+{red["expected_failures"]}expected, GREEN/MASTER{m["passed"]}PASS; normal masterpush remoteverified; broader OPEN.\\n')
print('final report and exact continuation prepared',target)
'''
# Final control hash is bound separately before it is executed.
text=prefix+rest
compile(text,str(D/'finalize.py'),'exec');(D/'finalize.py').write_text(text)
s=(O/'closure-reviewed.py').read_text().replace(str(O),str(D))
s=s.replace("reviews=['admission-ready.json','correctness-qualification/admission.json','correctness-qualification/result-review.json','cost-qualification-review.json','cost-audit-recovery-review.json','result-review.json'","reviews=['admission-final.json','result-review.json'")
a=s.index("c.need(c.read('admission.json')");b=s.index("checks['all_independent_reviews_bound']",a)
s=s[:a]+"c.need(c.read('admission.json')['accepted'] is False,'original rejected offline admission preserved')\n"+s[b:]
s=s.replace("['pins.json','pins-reviewed.json','pins-ready.json']","['pins.json','pins-ready.json','pins-final.json']").replace("['correctness-qualification','RED-run','GREEN-run','MASTER-run']","['RED-run','GREEN-run','MASTER-run']")
a=s.index("red=c.read('RED-run/audit.json')");b=s.index("check('unchanged_old_test'",a)
s=s[:a]+'''red=c.read('RED-run/audit.json');g=c.read('GREEN-run/audit.json');m=c.read('MASTER-run/audit.json');cmp=c.read('audit.json')
check('accepted_numerics',cmp['accepted'] is True and cmp['cases']==c.read('contract-final.json')['cases'] and cmp['windows']==c.read('contract-final.json')['measured_windows'] and cmp['preparation']==cmp['cases']+38 and cmp['compiled_zero'] is True and red['accepted'] is True and red['expected_failures']==c.read('test-gates.json')['expected_RED_failures'] and g['accepted'] is True and m['accepted'] is True and g['passed']==m['passed']==c.read('MASTER-run/contract.json')['expected_total'] and g['expected_failures']==m['expected_failures']==0)
check('same_wholefiles',c.read('GREEN-run/contract.json')['files']==c.read('MASTER-run/contract.json')['files'])
'''+s[b:]
s=s.replace('measured_assertions_passed=111259,original_measurement_failures=90,qualified_assertions=28227','measured_assertions_passed=cmp[\'assertions\'],cases=cmp[\'cases\'],windows=cmp[\'windows\']')
compile(s,str(D/'closure.py'),'exec');(D/'closure.py').write_text(s)
s=(O/'diagnostic-publish.py').read_text().replace(str(O),str(D)).replace("message='Record sum certificate and PFI growth scalar savings\\n\\nPreserve failed original diagnostics, separately qualified complete cost data and correctness, exact RED/GREEN and actual-master tests, independent reviews and immutable historical mappings.","message='Record residual pivot and crash scalar comparison\\n\\nPreserve original rejected offline preparation, complete paired cost/correctness data, exact RED/GREEN and actual-master tests, independent reviews and immutable historical mappings.")
compile(s,str(D/'diagnostic-publish.py'),'exec');(D/'diagnostic-publish.py').write_text(s)
(D/'final-controls-prepare.py').write_bytes(Path(__file__).read_bytes());print('finalization controls prepared UNEXECUTED, require independent review')
