from pathlib import Path
import sys,json,shutil,statistics
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-interval-stagnation-devex/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];sys.path.insert(0,str(D));import common as c
r=c.read('preparation-review.json');c.need(r['accepted'] and not r['findings'],'reviewed finalization')
for p,h in r['bindings'].items():c.need(c.sha(p)==h,'preparation binding '+p)
co=c.read('production-commit.json');target=co['commit'];pub=c.read('publication.json');c.need(pub['accepted'] and pub['commit']==target,'exact master published')
c.need(c.git(['rev-parse','HEAD'])==c.git(['rev-parse','master'])==c.git(['rev-parse','origin/master'])==c.git(['ls-remote','origin','refs/heads/master']).split()[0]==target,'master refs')
g=c.read('GREEN-run/audit.json');m=c.read('MASTER-run/audit.json');red=c.read('RED-run/audit.json');measure=c.read('comparison-2/audit-reconciled.json');q=c.read('correctness-qualification/audit.json')
for arm in ['GREEN','MASTER']:
 a=c.read(arm+'-run/audit.json');r=c.read(arm+'-run/result-review.json');c.need(a['accepted'] and not a['expected_failures'] and r['accepted'] and not r['findings'],'accepted '+arm)
c.need(g['passed']==m['passed'],'same whole-suite total')
for tree in ['src','test']:c.need({str(p.relative_to(M)):c.sha(p) for p in (M/tree).rglob('*') if p.is_file()}=={str(p.relative_to(D/'GREEN')):c.sha(p) for p in (D/'GREEN'/tree).rglob('*') if p.is_file()},'actual tested tree')
extra=set()
for path in D.rglob('output/process.json'):
 p=json.loads(path.read_text());extra.update(p[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
h=c.host(extra);c.put('final-host.json',h)
I=D/'before-diagnostic';I.mkdir();ri=c.git(['rev-parse','--path-format=absolute','--git-path','index'],R);shutil.copyfile(ri,I/'diagnostic.index');c.put('diagnostic-index-before.json',{ri:dict(before=str(I/'diagnostic.index'),sha256=c.sha(I/'diagnostic.index'))})
(D/'.gitignore').write_text('/baseline/\n/RED/\n/GREEN/\n/before-master/\n/before-diagnostic/\n**/__pycache__/\n/publication-after.json\n')
B=D/'continuation-before';B.mkdir();cont=[R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'];mapping={}
for p in cont:
 c.need(c.sha(p)==c.read('protected-before.json')['files'][str(p)],'exact continuation before')
 f=B/('STATUS.md' if p.name=='STATUS.md' else 'roadmap.md');shutil.copyfile(p,f);mapping[str(p)]=dict(before=str(f),sha256=c.sha(f))
hist=c.read('integration-historical-path-map.json');c.put('historical-path-map.json',dict(master_before=c.TARGET,master_source_before=hist['source_before'],master_index_before=hist['master_index_before'],continuation_before=mapping,all_older_maps_preserved=True))
rows=c.read('comparison-2/summary-reconciled.json')['cases'];table=[]
for arm,scope,label in [('A','rows','Rows / nearest / positive+mixed'),('A','feasible','Original feasibility / nearest / positive+mixed'),('A','reduced','Reduced costs / nearest / positive+mixed'),('A','witness','Whole witness / nearest / positive+mixed'),('B','new','Monitor setup / positive+mixed'),('B','cold','Whole cold observer / positive+mixed'),('B','rebase','Whole dual rebase observer / positive+mixed'),('C','leaving','Leaving Devex scalar / all shapes'),('C','devex_shared','Whole shared Devex / all shapes'),('C','devex_solve','Whole BTRAN+price Devex / all shapes')]:
 rr=[v for v in rows if v['type']=='BigFloat' and v['variant']==arm and v['scope']==scope and (arm=='C' or v['shape']!='negative') and (arm!='A' or 'Nearest' in v['context'])];c.need(rr,'table group '+label)
 ratio=statistics.median(v['paired_ratio'] for v in rr)
 relative=lambda f:statistics.median(v['candidate'][f]/v['original'][f] if v['original'][f] else 1 for v in rr)
 table.append(f'| {label} | {len(rr)} | {ratio:.4f} | {relative("bytes"):.4f} | {relative("events"):.4f} |')
report=f'''# Integrated BigFloat interval, monitor setup and Devex scalar savings

Production `{target}` normally pushed and remote-verified. Exactly five paths: dual_simplex.jl, simplex.jl, primal_simplex.jl, the new ordinary regression and runtests inclusion. A changes only reached guarded BigFloat interval magnitudes; every zero/unit alias, FastTwoSum/FMA/underflow/rounding/precision/enclosure gate and fallback remains. B adds concrete BigFloat monitor setup/rebase specializations AFTER the workspace type definition, retaining generic methods and every original conversion. C adds a BigFloat leaving Devex specialization with a fresh unit first, unchanged quotient and final max, and a fresh cap only on positive overflow. Input/output scalar owners, arrays, NaNs, signed zeros, exceptions, callbacks and numerical tolerances retained. No new matrix/vector scan, basis solve, copy, conversion, invariant pass or persistent numerical cache. Local branches/scalars and cold method metadata only; independent whole-branch review found no unnecessary added production work or retained numerical memory.

| Complete BigFloat call / measured group | Cells | Median paired time ratio | Median bytes ratio | Median events ratio |
|---|---:|---:|---:|---:|
'''+ '\n'.join(table)+f'''

These are fixture-cell medians across nine alternating pairs after three warm pairs. A gains are confined to reached nearest-rounding guards; the other four modes and negative sign controls must not be presented as improvements. B positive/mixed event savings are consistent; negative/control paths with unchanged event counts have byte variation, including small increases whose allocator cause is not attributed to this code. C all405BigFloat cells/allninepairs save176..384B and5..9events percall, but actual BTRAN+price time near1.0 is not meaningful timing improvement. All58GCwindows, outliers and slower cells retained; no universal or end-to-end solver speedup, native allocation/free, live-memory retention or fullsuite/x64 proof.

One numerical measurement:1813orderedcells/32634windows, all measured compile/recompilezero, supervisor elapsed{measure['elapsed_seconds']:.3f}s. BF64/128/256xfive modes plus Float32/64 and RationalBigInt/Int64 controls, sparse/dense n16/64,m8/16, three sign shapes. Actual initial −I basis preserved for complete Devex BTRAN; shared preparation includes genuine BTRAN/price outside the shared window with costs retained separately. Row/reduced/witness functions include all output allocation and original checks. Monitor whole cold/rebase includes finite/context/scaling/history/event/callback work. Fixture, reset, snapshots/validation, cold/warm and explicit context GC costs recorded separately; import/init only bounded by wall guard. Thirteen named binary readtime pins are not full transitive loader/cache/import/native-memory closure.

Original comparison-2 remains REJECTED55982PASS/360diagnosticFAIL/0ERROR. All failures are exact-oracle/owner expectations at the recorded five fixture lines: installed RationalBigInt(AbstractFloat) uses ambient-rounded ldexp and loses stored512bits; whole monitor calls _with_recovery_precision at stored512 and restores the outside context, so expected outside precision and always-detached scales were wrong. Candidate/reference comparisons, all1813whole-call validations and32634compile checks passed. Original source/log/raw/pins/admission remain frozen. Separate ordinary correctness qualification uses Base.decompose stored dyadic bits, known exact binary values, added negative512 inputs, source-derived active512 and positive-input scale alias expectations; it passed{q['assertions']}/{q['assertions']} in{q['elapsed_seconds']:.3f}s. It changes no production arithmetic, tolerance, candidate, measured input or window. Newly reviewed POSTEXIT auditor links exact original failures and complete cost/preparation data to qualified correctness; cost data accepted separately, never retroactive original-run PASS. No cost remeasurement.

Pre-Julia rejected preparations remain preserved: missing actual B/C stored512 coverage and negative whole pivot, then host metadata lacking diagnostic_head. Separate corrected copies preserve all candidate bodies/grid/checks; author and reviewer verify corrected refs before launch. Offline nonunique overloaded selector and independent review-field name mismatch also stopped before stage/Julia and remain preserved.

Ordinary original RED{red['passed']}PASS+6expected whole-function allocation failures before production source stage; six fixed three-pair tests require lower events each pair and lower median bytes, no time threshold/GC filtering. GREEN{g['passed']}PASS/{g['elapsed_shared_seconds']:.3f}s and actualMASTER{m['passed']}PASS/{m['elapsed_shared_seconds']:.3f}s, each49wholefiles with identical total and no errors/skips/broken/custom recorder/manual Test stack. Every old test/threshold unchanged, no old exception reused. Exact inverse and strict diff-check/load-order verification precede GREEN. Actual commit review, private index, ff-only local integration and fresh actual-master acceptance precede normal nonforce push; all five blobs and remote ref verified.

User files/environment/unrelated indexes preserved. Exact old source/index/continuation bindings map only to baseline/before-master/continuation-before; all older maps/raw/rejections remain frozen. Fresh{len(h['groups'])}historical groups ANDsessions/boot/startticks/command/noJulia, exact unrelated WSL identity-only allowance retained. CIoff, automationpaused, HHreuse disabled; broader/fullsuite/x64/native-retention/end-to-end remain OPEN. No automatic new experiment.
'''
(D/'FINAL-REPORT.md').write_text(report)
prefix=f'''# Current continuation — BigFloat interval/monitor/Devex savings integrated, 2026-10-27

Master/origin/master `{target}` normally pushed/remote-verified, exact5paths(3src+ordinarytest+runtests). Aconditionalmagnitudes onlywithin originalBFintervalNearest guards; allFMA/FastTwoSum/underflow/precision/rounding/enclosures retained. BconcreteBFmonitor setup/rebase AFTERtype, originalconversions/owners/recoveryprecision/callback/context/hash/history/scans retained. CBFDevexleaving freshunitfirst/samequotient/finalmax/caponlypositiveoverflow. Generic/native/exact routes and tolerances/coefficients/arithmeticorder/exception/ownerchecks retained. No newscan/solve/copy/conversion/persistentnumericcache; independent review no unnecessaryproductionworkmemory.

One measured1813cells32634windows/58GC/allcompilezero. Original55982PASS+360diagnosticoracleFAIL remains REJECTED/frozen. Exactdyadic decoder and actualinternal512/owner expectations separatelyqualified15213PASS; newpostexitstrictauditor accepts costdataonly, NOcostremeasurement/no candidate/window tuning/retroactivepass. Abenefit onlyNearestpositive/mixed; Bsetup/coldpositive/mixedsaves, negative/controlbytevariationunattributed; Call405BFcells lower176..384B/5..9events butactualBTRANtime~1 NOTmeaningfulspeedup. No universal/endtoendclaim. Allprelaunch rejections/offlineerrors preserved.

RED{red['passed']}+6expectedcostfailures; GREEN/actualMASTER each{m['passed']}PASS/49wholefiles, alloldtests/thresholdsunchanged/no newexception. Exactsourceinverse/loadorder/strictdiffclean/privateindexcommitreview/ff-only/freshMASTER/normalpush verified; finalPASSclosure and exactdiagnosticpublication separatelyrequired. Evidence diagnostics/generic-interval-stagnation-devex/2026-10-27/FINAL-REPORT.md. Source/index/continuation oldbindings mapONLY baseline/before-master/continuation-before exactbytes/alloldermaps preserved. Userfiles/env/unrelatedindexes preserved; fullgroups ANDsessions/boot/startticks/command/noJulia with exactunrelatedWSLidentity-onlyallowance. CIoff/automationpaused/HHdisabled/broader/fullsuite/x64/native-retentionOPEN. Allcaseartifacts FROZENNEVERRERUN/rewrite; noautomaticnewexperiment.

## Previous continuation — preserved verbatim below

'''
for p in cont:p.write_bytes(prefix.encode()+Path(mapping[str(p)]['before']).read_bytes())
(D/'progress-final.md').write_text(f'All3accepted; one1813/32634measurement retained with rejected360badtestexpectations, separatelyqualified15213PASS; RED{red["passed"]}+6; GREEN/MASTER{m["passed"]}PASS49files; exact5pathcommit/ff-only/normalpushremoteverified. Broader/fullsuiteOPEN.\n')
if Path(__file__).resolve()!=(D/'finalize.py').resolve():shutil.copyfile(__file__,D/'finalize.py')
print('Final continuation/report prepared; master',target)
