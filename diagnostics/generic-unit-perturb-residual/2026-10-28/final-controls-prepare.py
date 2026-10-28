from pathlib import Path
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');O=D.parents[1]/'generic-residual-pivot-crash/2026-10-28'
s=(O/'finalize-reviewed.py').read_text();s=s[:s.index("rows=c.read(")].replace(str(O),str(D)).replace('import common as c','import common_qualified as c')
s+='''rows=c.read('summary.json');accepted=c.read('result-review.json')['accepted_variants'];table=[]
for arm,scope,mode,label in [('A','devex','unit','RationalBigInt unit Devex'),('A','steepest','unit','RationalBigInt unit cached steepest'),('A','devex','mixed','RationalBigInt mixed Devex'),('A','steepest','mixed','RationalBigInt mixed cached steepest'),('A','devex','nonunit','RationalBigInt nonunit Devex'),('A','steepest','nonunit','RationalBigInt nonunit cached steepest'),('B','dual','unit','BigFloat whole dual perturbation'),('B','primal','unit','BigFloat whole bound perturbation'),('C','residual','unit','Whole LP residuals, all contexts'),('C','outer','unit','Outer residual precision wrapper, all contexts')]:
 rr=[v for v in rows if v['variant']==arm and v['scope']==scope and v['mode']==mode and (v['context']=='Rational{BigInt}' if arm=='A' else v['context'].startswith('BF') if arm=='B' else True)]
 c.need(rr,'reported cells '+label)
 table.append('| '+label+' | '+str(len(rr))+' | '+' | '.join(f'{stats.median(v[k]["paired_median"] for v in rr):.6f}' for k in ['seconds','bytes','events'])+' |')
elapsed=c.read('completed.json')['elapsed_shared_seconds']
report=f\'''# Unit-weight pricing, perturbation scales and residual copy savings

Accepted variants: {', '.join(accepted)}. Production `{target}`, sole parent `{c.TARGET}`, is normally pushed and remotely verified. Exact changed paths: {', '.join(co['names'])}.

A specializes RationalBigInt weighted score: same fresh square first; division omitted only for finite costs and unit weight. GMP numerator/denominator ownership remains fresh, including zero and unit. All other Rational and nonunit/nonfinite routes retain arithmetic, exceptions and scalar ownership. Complete Devex and cached-steepest pricing retain eligibility, scans, counters and strict ties. Unit cell-median time ratios about0.70/0.74 and mixed0.89/0.88 favor the candidate. Nonunit cases have about4.0% Devex/1.2% cached-steepest median overhead from added predicates, unchanged events and small allocation-counter byte fluctuations. This tradeoff is explicitly accepted; no universal gain or partial-pool timing claim.

B uses a fresh local BigFloat unit in each reached dual-cost/bound scale, replacing the second identical constructor. The unit is never cached across candidates, callbacks, invocations or changes of numeric context. All abs/arithmetic order, owner/type/policy/monitor/cooldown, feasibility, representability, cap, cancellation, journal publication, invalidation and event checks remain. Complete public interventions show modest median time gains and stable allocation savings:32 or224events,896–8064bytes per measured active call. These are stagnation interventions, not each ordinary iteration. Two specialized methods add cold method/code metadata; no persistent numerical storage is added.

C removes the outer copy of an already fresh vector slice and copy(y) before vcat. All independent output containers, BigFloat scalar input copies, original RationalBigInt scalar sharing, precision/dimension/finite checks and CSC arithmetic order remain. Each evaluation removes two length-m temporary vector containers and2m element copies. All measured calls save three aggregate allocation events and160–688bytes; elapsed-time benefit is inconclusive. Calls occur at refinement initialization, accepted auxiliary candidates and certificate projection candidates reaching residual evaluation. Existing scans, conversions, arithmetic and solves are retained.

| Complete call | Cells | Median of cell paired time ratios | Bytes ratio | Events ratio |
|---|---:|---:|---:|---:|
\'''+ '\\n'.join(table)+f\'''

Ratios below one favor the candidate. One admitted process passed {cmp['assertions']}/{cmp['assertions']} ordinary assertions, {cmp['cases']}cells, {cmp['windows']} measured windows and {cmp['preparation']} preparation records. Each cell uses3warm and9alternating measured pairs. All measured compile/recompile times are zero. All {cmp['gc_windows']} GC windows, slower samples/cells, signs, densities, sizes and unchanged controls are retained. BigFloat64/128/256 uses all5rounding modes, plus native/fixed/exact controls; n16/64, m=min(8,n/2). Sparse/dense preparation and whole residual/perturbation work are measured; A pricing does not use the matrix arithmetic itself. Comparison shared elapsed is {elapsed:.6f}s from completed.json; supervisor-only elapsed is {c.read('supervisor.json')['elapsed_seconds']:.6f}s. The inherited audit field named elapsed_shared_seconds contains the latter and is not the full shared clock. No repeated numerical comparison was needed.

Fixture/backend construction, reset, first calls, warm calls, validation, GC and consumption are separately recorded. First calls follow correctness tests, not isolated cold-process starts. Nine pairs in one process do not establish independent-run confidence or solver-wide speedup. No native allocation/free ledger or retained-native-memory gain is proved; counters are aggregate allocation traffic, not live storage.

Before numerical launch, independent reviews found and corrected offline harness/ledger issues: score oracle type, dimensions, vacuous owner test, active journal window count, post-arithmetic callback exception coverage, residual call frequency, Rational scalar sharing and copied-pin filename. Every original script/manifest/rejected review is preserved; corrected versions are separate, without retroactive pins. Runtime covers actual shifts, active journal level2, stop and identical exceptions before/after arithmetic, empty/overlapping/dimension/nonfinite residuals, input owners, BigFloat stored512/direct and outer contexts. Arbitrary callback precision/policy/unrepresentability cross-products remain source-preserved or reused whole-file coverage, not a newly executed exhaustive matrix.

Original RED: {red['passed']}PASS + exactly {red['expected_failures']} expected allocation failures, total {red['total']}. Ten permanent gates use3warm/3alternating measured pairs with lower events in each pair and lower medianbytes; no timing assertion or weakened old threshold. GREEN and actual MASTER freshly pass {g['passed']}/{m['passed']} in the same {len(c.read('MASTER-run/contract.json')['files'])} ordered whole files, inclusive {g['elapsed_shared_seconds']:.3f}/{m['elapsed_shared_seconds']:.3f}s. These include every67previous file plus the new test and14affected files. Ordinary Test is used without a custom recorder/manual testset stack. No historical release exception is reused; broader/full-suite/x64 remain OPEN.

Independent numerical and work/memory review found no unnecessary new full scan, solve, conversion, copied vector, repeated invariant check or persistent numeric cache. A nonunit predicates and B cold specializations are accounted costs. Exact source inversion, complete staged/tested trees, private-index sole-parent commit, ff-only integration, actual-master verification, normal push and remote identity are checked. User files/environment/index state and all older evidence/maps remain preserved. Final fresh host covers {len(h['groups'])} groups ANDsessions with boot/start_ticks/command/noJulia; sole exact unrelated WSL identity allowance unchanged. CIoff, automationpaused, HHreuse disabled; no cleanup or automatic next experiment.

This prepublication record was prepared after production verification. At preparation, diagnostic closure/publication remained pending. Canonical closure.json, diagnostic-publication-plan.json and publication-after.json record their subsequent outcomes.
\'''
(D/'FINAL-REPORT.md').write_text(report)
head=f\'''# Current continuation — unit pricing, perturbation and residual integration completed, 2026-10-28

Master/origin/master `{target}` normally pushed/remotely verified; accepted variants {','.join(accepted)} only. Source inverse and all numerical safeguards/tolerances/precision/owners/pivot policy retained. A has disclosed nonunit predicate overhead; B modest intervention savings; C allocation savings without a timing-speedup claim. See diagnostics/generic-unit-perturb-residual/2026-10-28/FINAL-REPORT.md and independent reviews.

Comparison {cmp['assertions']}PASS/{cmp['cases']}cells/{cmp['windows']}compilezero windows/{cmp['gc_windows']}GC preserved, {cmp['preparation']}preparation records. OriginalRED {red['passed']}PASS+{red['expected_failures']}expectedcostFAIL; GREEN/actualMASTER {m['passed']}PASS each/{len(c.read('MASTER-run/contract.json')['files'])}same wholefiles. Private-index/actualcommitreview/ff-only/freshMASTER/normalpush verified. At preparation of this prepublication continuation, diagnostic closure/publication remained pending; canonical output records contain subsequent outcomes. Exact older source/index/continuation bindings map ONLY baseline/before-master/continuation-before bytes; all older maps/rejections/raw preserved FROZEN NEVER RERUN/rewrite. Userfiles/env/index protected; fullgroupsANDsessions/boot/start_ticks/command/noJulia. CIoff automationpaused HHdisabled; broader/fullsuite/x64/native-retentionOPEN. No automatic next experiment/cleanup.

## Previous continuation — preserved verbatim below

\'''
for p in cont:p.write_bytes(head.encode()+Path(mapping[str(p)]['before']).read_bytes())
(D/'progress-final.md').write_text(f'Accepted {accepted}; comparison{cmp["assertions"]}PASS, RED{red["passed"]}+{red["expected_failures"]}expected, GREEN/MASTER{m["passed"]}PASS; normal masterpush remoteverified; broader OPEN.\\n')
print('final report and exact continuation prepared',target)
'''
compile(s,str(D/'finalize.py'),'exec');(D/'finalize.py').write_text(s)
s=(O/'closure.py').read_text().replace(str(O),str(D)).replace('import common as c','import common_qualified as c').replace('admission-final.json','admission-qualified.json').replace('contract-final.json','contract-qualified.json')
s=s.replace("reviews=['admission-qualified.json'","reviews=['source-production-review.json','test-control-review.json','admission-qualified.json'")
s=s.replace("c.read('admission.json')['accepted'] is False","c.read('independent-source-admission-rejected.json')['accepted'] is False and c.read('independent-final-admission-rejected.json')['accepted'] is False")
s=s.replace("['pins.json','pins-ready.json','pins-final.json']","['pins.json','pins-reviewed.json','pins-final.json','pins-qualified.json']")
needle=" elif p.is_relative_to(M/'src')"
s=s.replace(needle," elif str(p) in {str(D/'WORK-MEMORY.md'),str(D/'PLAN.md')}:q=Path(str(p)+'.before-review')\n elif p==D/'DESIGN.md':q=D/'DESIGN.md.before-owner-clarification'\n"+needle)
compile(s,str(D/'closure.py'),'exec');(D/'closure.py').write_text(s)
s=(O/'diagnostic-publish.py').read_text().replace(str(O),str(D)).replace('import common as c','import common_qualified as c').replace('Record residual pivot and crash scalar comparison','Record unit pricing perturbation and residual savings');compile(s,str(D/'diagnostic-publish.py'),'exec');(D/'diagnostic-publish.py').write_text(s)
(D/'final-controls-prepare.py').write_bytes(Path(__file__).read_bytes());print('new final controls UNEXECUTED; independent review required before mutation')
