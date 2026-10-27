from pathlib import Path
import sys,json,shutil,statistics
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-virtual-free-pivot/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];sys.path.insert(0,str(D));import common_ready as c
prep=c.read('preparation-review.json');c.need(prep['accepted'] and not prep['findings'],'finalization preparation accepted')
for p,h in prep['bindings'].items():c.need(c.sha(p)==h,'prep binding '+p)
co=c.read('production-commit.json');target=co['commit'];pub=c.read('publication.json');c.need(pub['accepted'] and pub['commit']==target,'published exact master')
c.need(c.git(['rev-parse','HEAD'])==c.git(['rev-parse','master'])==c.git(['rev-parse','origin/master'])==c.git(['ls-remote','origin','refs/heads/master']).split()[0]==target,'master refs')
g=c.read('GREEN-run/audit.json');m=c.read('MASTER-run/audit.json');red=c.read('RED-ready-run/audit.json');measure=c.read('comparison-3/audit-final.json')
for arm in ['GREEN','MASTER']:
 a=c.read(arm+'-run/audit.json');r=c.read(arm+'-run/result-review.json');c.need(a['accepted'] and not a['expected_failures'] and r['accepted'] and not r['findings'],'accepted '+arm)
c.need(g['passed']==m['passed'],'same tested totals')
for tree in ['src','test']:c.need({str(p.relative_to(M)):c.sha(p) for p in (M/tree).rglob('*') if p.is_file()}=={str(p.relative_to(D/'GREEN')):c.sha(p) for p in (D/'GREEN'/tree).rglob('*') if p.is_file()},'actual tested tree')
extra=set()
for path in D.rglob('output/process.json'):
 p=json.loads(path.read_text());extra.update(p[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
c.put('final-host.json',c.host(extra))
I=D/'before-diagnostic';I.mkdir();ri=c.git(['rev-parse','--path-format=absolute','--git-path','index'],R);shutil.copyfile(ri,I/'diagnostic.index');c.put('diagnostic-index-before.json',{ri:dict(before=str(I/'diagnostic.index'),sha256=c.sha(I/'diagnostic.index'))})
(D/'.gitignore').write_text('/baseline/\n/RED/\n/GREEN/\n/before-master/\n/before-diagnostic/\n**/__pycache__/\n/publication-after.json\n')
B=D/'continuation-before';B.mkdir();cont=[R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'];mapping={}
for p in cont:
 c.need(c.sha(p)==c.read('protected-before.json')['files'][str(p)],'protected continuation before')
 q=B/('STATUS.md' if p.name=='STATUS.md' else 'roadmap.md');shutil.copyfile(p,q);mapping[str(p)]=dict(before=str(q),sha256=c.sha(q))
hist=c.read('integration-historical-path-map.json');c.put('historical-path-map.json',dict(master_before=c.TARGET,master_source_before=hist['source_before'],master_index_before=hist['master_index_before'],continuation_before=mapping,all_older_maps_preserved=True))
rows=c.read('comparison-3/summary-final.json')['cases'];table=[]
for arm,scope,label in [('A','audit','Whole implicit price audit'),('A','virtual','Whole virtual quality'),('A','virtual_transposed','Whole transposed virtual quality'),('B','enter_dantzig','Whole free Dantzig pricing'),('B','enter_devex','Whole free Devex pricing'),('B','partial_hit','Whole partial-hit or small full fallback'),('B','partial_rebuild','Whole invalidated partial or small full fallback'),('B','summary','Whole dual summary'),('C','pivot','Whole checked pivot')]:
 rr=[r for r in rows if r['variant']==arm and r['scope']==scope and r['type']=='BigFloat'];ratio=statistics.median(r['paired_ratio'] for r in rr);br=statistics.median(r['candidate']['bytes']/r['original']['bytes'] for r in rr);er=statistics.median(r['candidate']['events']/r['original']['events'] for r in rr);table.append(f'| {label} | {ratio:.4f} | {br:.4f} | {er:.4f} |')
report=f'''# Integrated BigFloat virtual audit, free-variable and checked-pivot savings

Production `{target}` normally pushed and remote-verified. Exactly seven paths: five source files, one ordinary regression module and runtests inclusion. A specializes only ordinary BigFloat vectors and implicit price-audit matrices, reusing private unit coefficients and the qualified private term helper/lazy floatmin while retaining all original terms/conversions/products/residuals/term counts/underflow checks. B changes only free-nonbasic magnitude predicates in multiprecision full entering, generic pool eligibility and multiprecision dual summary; generic magnitude remains abs for other scalar types. C adds BigFloat checked pivot/agreement methods with conditional magnitudes and integer zero/one, retaining basis assembly, both full quality calls and every gate. Same arithmetic order, tolerances, precision/rounding, scalar and array owners, exceptions and callback boundaries. No new scan/solve/copy/conversion/persistent numerical cache; O(1) private locals and cold method/code metadata only. Independent review found no unnecessary added production work or retained numerical memory. C is a checked/incremental path saving, not ordinary native-dual speedup.

| Complete BigFloat call | Median of cell paired time ratios | Median byte ratio | Median event ratio |
|---|---:|---:|---:|
'''+ '\n'.join(table)+f'''

Accepted comparison: {measure['assertions']} ordinary tests PASS,3328cells/59904windows,87.684s inclusive launch. BF64/128/256 x five rounding modes, sparse/denseN32/128,bases4/16; native Float32/64,RationalBigInt/Int64 controls. Fixed3warm and9alternatingpairs. All measured compile/recompile zero;114GCwindows and all outliers retained. Fixture/FTRAN/BTRAN/snapshots/validation/cold/warm/reset/contextGC costs separately retained; module/process initialization bounded only in inclusive wall time. N32 partial cases explicitly full fallback; N128+4 exercises genuine cache hit and invalidated rebuild. Full implicit audit includes vcat and fresh scratch. All1440A BigFloatcells lowerbytes/events eachpair. Bpositive/mixed600cells lowerbytes/events; negative/bound600same, with timing noise. Cnonzero360cells lowerbytes/events,346cellmedians faster/14slower, maxratio1.1101; zero120sameallocation. C accepted for robust allocation savings with modest/nonuniform time benefit. Native/exact events unchanged; small byte/timing variations retained, allocation-cause attribution not proved. No universal/end-to-end speedup or native-live/free/retention proof.

Failed first comparison frozen:954PASS/0FAIL/3ERROR/exit1, all same SparseVector diagnostic destination unsupported by FTRAN. Separate one-expression Vector conversion preserves values and candidate. Failed second comparison frozen:120716PASS/4FAIL/0ERROR/exit1; four newly authored Float64 ideal-direction bit-equality assertions were invalid for default scaled UMFPACK. Final correction retains strict baseline/candidate bit equality and all original status/quality/owner/context checks, plus exact B*wanted==rhs and independently rational residual <=8eps(Float64)*max(1,||B||inf||x||inf,||rhs||inf);12native snapshots independently recomputed. Production tolerance/precision/backend unchanged; all other exact ideal checks retained. Both failures remain rejected. A false fix-checks exact_inverse metadata field was preserved and superseded only by independent exact-inverse evidence. The first post-exit auditor passed all data gates and wrote summary, then failed final metadata publication because loop m shadowed regex m; separate post-exit audit-final.py fixes only root_summary/newoutputpaths. Its summary is byte-identical; it is not a launch pin. No numerical rerun for that auditor fix.

RED {red['passed']}PASS+5expectedwhole-call allocation failures before production-stage edits. An unexecuted initial RED preparation lacked outer module import before aliases; separate reviewed test import correction preserved all numerical expectations. GREEN {g['passed']}PASS/{g['elapsed_shared_seconds']:.3f}s and actualMASTER {m['passed']}PASS/{m['elapsed_shared_seconds']:.3f}s, each36wholefiles. Existing tests/thresholds unchanged; fixed3pair newallocation gates, no time assertions/customTestrecorder/manualTeststack. Exactsourceinverse/actualcommitreview/ff-onlylocalmaster/freshactualmasteracceptance precede normalnonforcepush. Seven committed blobs verified.

Userfiles/env/unrelatedindexes preserved. Current source/index/continuation old hashes map ONLY baseline/before-master/continuation-before exact bytes; older maps and raw/rejections remain frozen. Full historical PGIDs ANDsessions/boot+start_ticks+command/noJulia checked; exact old unrelated WSL identity allowance retained, never PID-alone. Prior7e306e24 exception remains historical unchanged, no new exception. CIoff/automationpaused/HHreuse disabled; broaderS2/S3/S4/S5/S6/fullsuite/x64/native-retention/end-to-end OPEN. No automatic new experiment.
'''
(D/'FINAL-REPORT.md').write_text(report)
prefix=f'''# Current continuation — BigFloat virtual/free/checked-pivot savings integrated, 2026-10-27

Master/origin/master `{target}` normally pushed/remote-verified, exact7paths (5src+ordinarytest+runtests). A implicitpricequality privateunits/termmagnitude/lazyfloatmin, fullvcat/scratch/guards retained. B free-nonbasic conditionalmagnitude in fullpricing/pool/summary, othertypesgenericabs. C BFcheckedpivot/agreement conditionalmagnitudes/integer0/1/sameorderedarithmetic, bothqualities/assembly/allguards retained; no ordinarynative-dual claim. Safeguards/tolerances/precision/rounding/owners/callbacks/exceptions preserved. No newscan/solve/copy/conversion/persistentnumericcache; independentreview no unnecessarynewproductionworkmemory.

Accepted120872checks/3328cells59904windows/87.684s, measuredcompile/recompile0/all114GC/outliers retained. Awholeauditmedianratio~.722/bytes~.696, Bpositivefree~.572/mixed~.825, negative/bound~1; Csmall/nonuniformtime, nonzero360loweralloc346faster14slower. No universal/endtoendspeedup. Original954+3diagnostictypeerrors and120716+4invalidFloat64idealoracles remain rejected/frozen; separate exactdiagnosticcorrections with strictcandidateparity and rationalnativebound, no tolerance/backend/candidate tuning. OriginalauditorpublicationTypeError andfalsefixmetadata preserved; independentpostexitfinalaudit accepted, neverretroactivelaunchpin.

RED{red['passed']}+5expectedcostfailures beforestage; GREEN/actualMASTER each{m['passed']}PASS/36wholefiles, existingtests/thresholds unchanged/no newexception. OriginalunexecutedREDouterimporterror preserved; correctedordinarytest reviewed. Exactcommitreview/ff-only/actualmasterreview/normalpush verified; finalPASSclosure/exactdiagnosticpublication required. Evidence diagnostics/generic-virtual-free-pivot/2026-10-27/FINAL-REPORT.md. Userfiles/env/unrelatedindexes preserved; source/index/continuation oldbindings mapONLY baseline/before-master/continuation-before exactbytes/alloldermaps preserved. Full historicalgroups ANDsessions/boot/start_ticks/command/noJulia, exact unrelatedWSLidentity-onlyallowance; noPID-alone identity. CIoff/automationpaused/HHdisabled/broader/fullsuite/x64/native-retention OPEN. Allcaseartifacts FROZENNEVERRERUN/rewrite; no automatic newexperiment.

## Previous continuation — preserved verbatim below

'''
for p in cont:p.write_bytes(prefix.encode()+Path(mapping[str(p)]['before']).read_bytes())
(D/'progress-final.md').write_text(f'All3 accepted; comparison120872PASS; RED{red["passed"]}+5; GREEN/MASTER{m["passed"]}PASS36files; exactreviewed7pathcommit/ff-only/normalpushremoteverified. Broader/fullsuite/x64OPEN.\n')
if Path(__file__).resolve()!=(D/'finalize.py').resolve():shutil.copyfile(__file__,D/'finalize.py')
print('Final continuation/report prepared; master',target)
