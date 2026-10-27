from pathlib import Path
import shutil
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');O=R/'diagnostics/generic-quality-devex/2026-10-27';D=R/'diagnostics/generic-quality-local/2026-10-27'
def adapt(name):return (O/name).read_text().replace(str(O),str(D)).replace('import common as c','import common_next as c').replace("[D/'output/process.json',*D.glob('*-run/output/process.json')]","[D/'output/process.json',D/'comparison-2/output/process.json',*D.glob('*-run/output/process.json')]")
s=adapt('finalize.py');start=s.index("prefix=f'''");end=s.index("if Path(__file__).resolve()",start)
block=r"""import statistics
summary=c.read('comparison-2/summary.json')['cases'];measure=c.read('comparison-2/audit.json');red=c.read('RED-run/audit.json')
table=[]
for arm,scope,label in [('A','quality','A: product magnitude, normal quality'),('B','quality','B: finalization, whole normal quality'),('B','finish','B: complete finalizer'),('AB','quality','A+B: whole normal quality'),('AB','quality_transposed','A+B: whole transposed quality'),('C','audit','C: complete primal audit')]:
 rows=[r for r in summary if r['type']=='BigFloat' and r['variant']==arm and r['scope']==scope]
 med=statistics.median(r['paired_ratio'] for r in rows);br=statistics.median(r['candidate']['bytes']/r['original']['bytes'] for r in rows);er=statistics.median(r['candidate']['events']/r['original']['events'] for r in rows)
 table.append(f'| {label} | {med:.4f} | {br:.4f} | {er:.4f} |')
table='\n'.join(table)
report=f'''# Integrated BigFloat invocation-local quality savings

Production `{target}` is integrated and normally pushed/remote-verified. Exact four paths: two production sources, one new ordinary regression module and runtests inclusion. All three proposals and A+B composition were independently accepted. A reuses a private product magnitude; B retains finalization passes while using conditional magnitudes and exact integer zero/one operands; C lazily creates one private unit after recompute/guards in the callback-free normalization loop. Both audit copies, recompute, finite/reliability tests and final price audit remain. B's scalar BigFloat roundoff specialization also serves generic/custom BigFloat-work paths; generic methods remain, rather than literally unchanged dispatch. No new vector/matrix pass, basis solve, copy, conversion or persistent numerical cache. Cold code/method metadata and local branches are accounted. Numerical safeguards, tolerances, ordered arithmetic, precision/rounding, input/scalar ownership and callback boundaries preserved. Independent reviews found no unnecessary production work or retained numeric memory.

| Complete call | Across-cell median paired time ratio | Median byte ratio | Median event ratio |
|---|---:|---:|---:|
{table}

Corrected comparison: {measure['assertions']} ordinary checks PASS, {measure['cells']}cells/{measure['windows']}windows, {measure['elapsed_seconds']:.3f}s including guard/launch. BF64/128/256 x five rounding modes, sparse/dense N32/96; actual audit basis4/16. Setup/snapshots/contextGC/cold/warm/resets separately recorded. All measured compilation/recompilation zero; all805GCwindows and outliers retained. Individual whole-call median time ratios can exceed1 (B normal quality max1.3171); no universal or end-to-end speedup claim. Consistent allocation savings support acceptance; isolated A positive/zero controls need not save allocation. Every non-BF event pair equals; Float32/64/RatInt64 byte pairs equal. RationalBigInt raw bytes vary16..59200B in268/288pairs, while cell median differences are-880..+1360B; exact allocator cause unproved. No native-live/free/peak-retention proof. Full detail: comparison-2/RESULT-REVIEW.md and raw results.toml.

Original first comparison remains REJECTED:63389PASS+2wrong diagnostic expectations for unchanged Rational nonfinite-labelled fixtures, exit1/no resultTOML. A separately reviewed one-expression expectation correction explicitly requires accurate for Rational and corrected for actually injected floating NaN; candidate/reference/inputs/schedule unchanged. Plain try/finally publishes existing raw data before Test errors rethrow. No actual numerical/cost failure was tuned or relabelled.

RED {red['passed']}PASS+4expected whole-call allocation failures. GREEN {green['passed']}PASS/{green['elapsed_shared_seconds']:.3f}s and actualMASTER {master['passed']}PASS/{master['elapsed_shared_seconds']:.3f}s, each35complete ordinary test files. No custom recorder/manualTeststack/errors/broken/skips. Four new fixed3pair cost gates require lower bytes AND events, no timing assertion; existing tests and thresholds byte-identical. Source inverse, reviewed actual commit, ff-only local master and actual-master acceptance precede normal push. Separate final PASS closure and exact diagnostic staging/publication required.

Two offline preparation refusals are preserved. Historical numeric group77336 was reused by unrelated /usr/libexec/wsl-pro-service from a different boot/start; common_next accepts only that exact pinned service identity while still examining all historical group/session IDs and rejecting any Julia. It later exited; no process was killed. Historical numerical identities absent, current process closure recorded with boot/start_ticks/command. No literal numeric-group absence claim while a qualified unrelated occupant exists.

Earlier7e306e24 exception-qualified failed Rational allocation gate remains historical and unchanged; this allpass run does not retroactively fix/reinterpret it or grant future exceptions. Fullsuite/x64/broaderS2/S3/S4/S5/S6/native-retention/end-to-end remain OPEN; CIoff/automationpaused/HHreuse disabled. User files/environment/unrelated indexes and all old raw/rejections preserved. Old source/index/continuation hashes map only to exact baseline/before-master/continuation-before images, never retroactive launch pins.
'''
(D/'FINAL-REPORT.md').write_text(report)
prefix=f'''# Current continuation — invocation-local BigFloat quality savings integrated, 2026-10-27

Master/origin/master {target} normally pushed/remote-verified; exact4paths, two sources+newordinarytest+runtests inclusion. A private product magnitude reuse; B same finalization passes with conditional magnitude/exact integer0/1; C one lazyprivateunit AFTER recompute/guards in callback-free normloop. Both auditcopies/recompute/finite/reliability/finalpriceaudit unchanged; all safeguards/tolerances/precision/rounding/orderedarithmetic/owners/callbackboundaries retained. B scalar roundoff also reaches generic BF-work paths, generic methods retained. No new scan/solve/copy/conversion/persistent numericcache; independent work-memory review found no unnecessary added production work/retention.

Corrected comparison63391PASS/2172cells39096windows/152.583s; all measuredcompile/recompile0, all805GCwindows/outliers retained. BF64/128/256x5modes+sparse/dense32/96/native-exactcontrols; allnonBF events equal, BigIntrawbytevariability retained withoutcauseattribution. WholequalityAB medians~.908, completefinalizer~.482, wholeaudit~.966 acrosscells; individualtimings may exceed1, no universal/endtoendspeedup. First63389PASS+2diagnosticexpectationfailures remains REJECTED and frozen; separate reviewed minimal Rational expectation correction/plainfinally publication, no candidatetuning.

RED{red['passed']}PASS+4expectedcostfailures; GREEN and actualMASTER each{master['passed']}PASS/35wholefiles with unchanged original tests/thresholds. Fixed3pair newwholecallgates lowerbytes/events, no timingassertion/customrecorder/manualTeststack. Independentcomparison/RED/source/GREEN/actualcommit/MASTER acceptance retained; separatePASSclosure/exactdiagnosticpublication required. Earlier7eexception/failedoldgate unchanged, no new exception.

Preflighttwooffline refusals preserved; numeric77336 was unrelated WSLservice differentboot/start, exactidentity-only exemption in common_next, allhistoricalgroups ANDsessions checked/noJulia. Do notidentifyprocessbyPIDalone orclaimnumericabsence whileunrelatedcollisionexists. Service laterexited, no processkilled. Userfiles/env/unrelatedindexes preserved. Oldbindings mapONLY baseline/before-master/continuation-before exactimages; alloldermaps/raw/reviews/scripts FROZENNEVERRERUN/rewrite. Evidence diagnostics/generic-quality-local/2026-10-27/FINAL-REPORT.md. CIoff/automationpaused/HHdisabled/broader/fullsuite/x64/native-retention OPEN. No automaticnewexperiment orautomationresume.

## Previous continuation — preserved verbatim below

'''
for p in cont:p.write_bytes(prefix.encode()+Path(mapping[str(p)]['before']).read_bytes())
(D/'progress-final.md').write_text(f'Task1 acceptedcomparison63391PASS, all3variants+AB. Task2 acceptedRED{red["passed"]}+4, GREEN{green["passed"]}PASS35files. Task3 actualMASTER{master["passed"]}PASS35files, reviewedcommit/ff-only/normalpushremoteverified. Originaldiagnosticfailure preserved, no productionnumericalexception. Broader/fullsuite/x64OPEN.\n')
"""
s=s[:start]+block+s[end:];(D/'finalize.py').write_text(s)
s=adapt('closure.py').replace("'result-review.json',","'comparison-2/admission.json','comparison-2/result-review.json',").replace("[D,D/'RED-run'","[D,D/'comparison-2',D/'RED-run'").replace("cmp=c.read('audit.json')","cmp=c.read('comparison-2/audit.json')")
s=s.replace("cmp['assertions']==33807","cmp['assertions']==63391").replace("red['passed']==9465","red['passed']==16579").replace("red['expected_failures']==6","red['expected_failures']==4").replace("g['passed']==m['passed']==186622","g['passed']==m['passed']==c.read('MASTER-run/contract.json')['expected_total']").replace('measured_assertions=33807','measured_assertions=63391')
anchor="checks['all_independent_reviews_bound']=True";insert="""rejected=c.read('result-review.json');c.need(rejected['accepted'] is False,'original rejection preserved')
for p,h in rejected['bindings'].items():before(p,h)
original=c.read('output/process.json');c.need(original['returncode']==1 and original['pins_unchanged'] is True,'original failed attempt preserved')
checks['all_independent_reviews_bound']=True""";assert anchor in s;s=s.replace(anchor,insert);(D/'closure.py').write_text(s)
pub=adapt('diagnostic-publish.py');start=pub.index("message='Record BigFloat");end=pub.index("\nsubprocess.run",start)
pub=pub[:start]+"message='Record invocation-local BigFloat quality savings\\n\\nPreserve corrected whole-function comparison, rejected original diagnostics, exact RED/GREEN and actual-master qualification, independent reviews and immutable historical mappings. Production '+target+' is all-pass qualified and normally published; prior exception-qualified evidence remains unchanged.'"+pub[end:]
(D/'diagnostic-publish.py').write_text(pub)
shutil.copyfile(O/'finalization_checks.py',D/'finalization_checks.py');shutil.copyfile(__file__,D/'prepare-finalization.py')
for name in ['finalize.py','closure.py','diagnostic-publish.py']:compile((D/name).read_text(),str(D/name),'exec')
print('Finalization source prepared unexecuted; accepted preparation review required before continuation edits')
