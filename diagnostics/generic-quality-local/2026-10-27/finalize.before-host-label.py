from pathlib import Path
import sys,json,hashlib,shutil,datetime
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];sys.path.insert(0,str(D));import common_next as c
prep=c.read('preparation-review.json')
c.need(prep['accepted'] is True and prep['findings']==[],'accepted finalization preparation')
for p,h in prep['bindings'].items():c.need(c.sha(p)==h,'preparation binding '+p)
co=c.read('production-commit.json');pub=c.read('publication.json');target=co['commit'];c.need(pub['accepted'] and pub['commit']==target,'actual master published allpass')
c.need(c.git(['rev-parse','HEAD'])==c.git(['rev-parse','master'])==c.git(['rev-parse','origin/master'])==c.git(['ls-remote','origin','refs/heads/master']).split()[0]==target,'master remote refs')
for arm in ['GREEN','MASTER']:
 a=c.read(arm+'-run/audit.json');r=c.read(arm+'-run/result-review.json');c.need(a['accepted'] and not a['expected_failures'] and r['accepted'] and r['findings']==[],'allpass '+arm)
green=c.read('GREEN-run/audit.json');master=c.read('MASTER-run/audit.json');c.need(green['passed']==master['passed'],'same full qualification total')
for tree in ['src','test']:
 actual={str(p.relative_to(M)):c.sha(p) for p in (M/tree).rglob('*') if p.is_file()};staged={str(p.relative_to(D/'GREEN')):c.sha(p) for p in (D/'GREEN'/tree).rglob('*') if p.is_file()};c.need(actual==staged,'exact current tested source/test')
extra=set()
for path in [D/'output/process.json',D/'comparison-2/output/process.json',*D.glob('*-run/output/process.json')]:
 p=json.loads(path.read_text());extra.update(p[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
c.put('final-host.json',c.host(extra))
I=D/'before-diagnostic';I.mkdir()
ri=c.git(['rev-parse','--path-format=absolute','--git-path','index'],R)
shutil.copyfile(ri,I/'diagnostic.index')
c.put('diagnostic-index-before.json',{ri:dict(before=str(I/'diagnostic.index'),sha256=c.sha(I/'diagnostic.index'))})
(D/'.gitignore').write_text('/baseline/\n/RED/\n/GREEN/\n/before-master/\n/before-diagnostic/\n**/__pycache__/\n/publication-after.json\n')
B=D/'continuation-before';B.mkdir()
cont=[R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'];mapping={}
for p in cont:
 q=B/('STATUS.md' if p.name=='STATUS.md' else 'roadmap.md');shutil.copyfile(p,q);mapping[str(p)]=dict(before=str(q),sha256=c.sha(q))
hist=c.read('integration-historical-path-map.json');c.put('historical-path-map.json',dict(master_before=c.TARGET,master_source_before=hist['source_before'],master_index_before=hist['master_index_before'],continuation_before=mapping,all_older_maps_preserved=True))
import statistics
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
if Path(__file__).resolve()!=(D/'finalize.py').resolve():shutil.copyfile(__file__,D/'finalize.py')
print('Finalreport/currentcontinuations prepared; master',target,'tests',master['passed'],'freshclosedgroups',len(c.read('final-host.json')['groups']))
