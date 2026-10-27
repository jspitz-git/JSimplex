from pathlib import Path
import sys,json,shutil,statistics
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-stagnation-unit-seed/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2];sys.path.insert(0,str(D));import common_reviewed as c
prep=c.read('preparation-review-2.json');c.need(prep['accepted'] and not prep['findings'],'finalization preparation accepted')
for p,h in prep['bindings'].items():c.need(c.sha(p)==h,'prep binding '+p)
co=c.read('production-commit.json');target=co['commit'];pub=c.read('publication.json');c.need(pub['accepted'] and pub['commit']==target,'published exact master')
c.need(c.git(['rev-parse','HEAD'])==c.git(['rev-parse','master'])==c.git(['rev-parse','origin/master'])==c.git(['ls-remote','origin','refs/heads/master']).split()[0]==target,'master refs')
g=c.read('GREEN-2-run/audit.json');m=c.read('MASTER-run/audit.json');red=c.read('RED-run/audit.json');measure=c.read('comparison-2/audit.json')
for arm in ['GREEN-2','MASTER']:
 a=c.read(arm+'-run/audit.json');r=c.read(arm+'-run/result-review.json');c.need(a['accepted'] and not a['expected_failures'] and r['accepted'] and not r['findings'],'accepted '+arm)
c.need(g['passed']==m['passed'],'same tested totals')
for tree in ['src','test']:c.need({str(p.relative_to(M)):c.sha(p) for p in (M/tree).rglob('*') if p.is_file()}=={str(p.relative_to(D/'GREEN-2')):c.sha(p) for p in (D/'GREEN-2'/tree).rglob('*') if p.is_file()},'actual tested tree')
extra=set()
for path in D.rglob('output/process.json'):
 p=json.loads(path.read_text());extra.update(p[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
c.put('final-host.json',c.host(extra))
I=D/'before-diagnostic';I.mkdir();ri=c.git(['rev-parse','--path-format=absolute','--git-path','index'],R);shutil.copyfile(ri,I/'diagnostic.index');c.put('diagnostic-index-before.json',{ri:dict(before=str(I/'diagnostic.index'),sha256=c.sha(I/'diagnostic.index'))})
(D/'.gitignore').write_text('/baseline/\n/RED/\n/GREEN/\n/GREEN-2/\n/before-master/\n/before-diagnostic/\n**/__pycache__/\n/publication-after.json\n')
B=D/'continuation-before';B.mkdir();cont=[R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'];mapping={}
for p in cont:
 c.need(c.sha(p)==c.read('protected-before.json')['files'][str(p)],'protected continuation before')
 q=B/('STATUS.md' if p.name=='STATUS.md' else 'roadmap.md');shutil.copyfile(p,q);mapping[str(p)]=dict(before=str(q),sha256=c.sha(q))
hist=c.read('integration-historical-path-map.json');c.put('historical-path-map.json',dict(master_before=c.TARGET,master_source_before=hist['source_before'],master_index_before=hist['master_index_before'],continuation_before=mapping,all_older_maps_preserved=True))
rows=c.read('comparison-2/summary.json')['cases'];table=[]
for arm,scope,typ,label in [('A','values','BigFloat','Whole stagnation metrics'),('A','observe','BigFloat','Whole primal observation'),('A','observe_dual','BigFloat','Whole dual observation'),('B','unit','BigFloat','Whole BigFloat unit gate'),('B','unit','Rational{BigInt}','Whole RationalBigInt unit gate'),('B','init','BigFloat','Whole initialization B'),('C','init','BigFloat','Whole initialization C'),('BC','init','BigFloat','Whole composed initialization')]:
 rr=[r for r in rows if r['variant']==arm and r['scope']==scope and r['type']==typ];c.need(rr,'table cells '+label)
 ratio=statistics.median(r['paired_ratio'] for r in rr)
 def relative(field):return statistics.median(r['candidate'][field]/r['original'][field] if r['original'][field] else 1.0 for r in rr)
 table.append(f'| {label} | {ratio:.4f} | {relative("bytes"):.4f} | {relative("events"):.4f} |')
report=f'''# Integrated stagnation and steepest initialization scalar savings

Production `{target}` normally pushed and remote-verified. Exactly four paths: two source files, an ordinary regression module and runtests inclusion. A adds only a concrete BigFloat metric specialization, reuses an already fresh private primal zero for comparisons and qualified free-price conditional magnitude. B adds BigFloat/RationalBigInt unit-basis predicates; BigFloat negative rounding retained by conditional magnitude followed by integer-one comparison. C adds only a BigFloat initializer, lazily checking shared row-weight cacheability once at its first original site after the first weight assignment. Initial returned zeros and row weights remain fresh per call; within-call original row sharing retained. Generic methods unchanged. No new scan, solve, copy, conversion or persistent numerical cache; O(1) private references/flags and cold method metadata. Objective/metric arithmetic order, all finite/context/history/callback/rebase checks, tolerances, precision/rounding, owners and exceptions retained. Independent production review found no unnecessary added work or retained numerical memory.

| Complete call | Median of cell paired time ratios | Median byte ratio | Median event ratio |
|---|---:|---:|---:|
'''+ '\n'.join(table)+f'''

Accepted comparison: {measure['assertions']} ordinary checks,3415cells/61470windows,{measure['elapsed_seconds']:.3f}s inclusive launch. BF64/128/256 x five rounding modes; sparse/dense monitor N32/128,m8/32, gate/init N8/32,m8/32. Native Float32/64 and RationalBigInt/Int64 controls. Three warm and nine alternating pairs; measured compile/recompilezero. All23GCwindows and slower/outlier cells retained. Fixture/seed/reset/cold/warm/validation/contextGC costs retained separately; import/init bounded inclusive only. BC composition measured directly. All intended event reductions retained; one A primal-observation pair has7856extra bytes despite96fewer events, allocator cause unknown. Unchanged native/exact controls also show byte variation. No universal/end-to-end speedup or native-live/free/retention proof. Unit/initializer component fixtures replace basis with structural unit columns after setup but perform no basis solves; not public-trajectory qualification. Thirteen runtime binaries are prospective readtime alias/target/hash pins, not full transitive loader/cache/import-init coverage.

Original GREEN rejected before tests: concrete method declared before SimplexWorkspace existed; separately reviewed byte-exact method relocation to simplex.jl after type definition, original stalling file restored, no candidate arithmetic/test changes. Original3.253s run and insufficient prelaunch reviews frozen.

Initial comparison104540PASS/19ERROR/exit1 rejected and frozen: diagnostic reset copied full seeds into intentionally shortened malformed arrays before the function under test. Separate reviewed keyword disables reset only for those already prepared malformed-array checks; all expected errors, candidate code and normal measured resets unchanged. Corrected comparison105921PASS, no failures/errors. No old attempt/auditor rerun.

RED{red['passed']}PASS+5expected whole-call cost failures witnessed before production source stage. GREEN{g['passed']}PASS/{g['elapsed_shared_seconds']:.3f}s and actualMASTER{m['passed']}PASS/{m['elapsed_shared_seconds']:.3f}s, each45wholefiles. Five new fixed three-pair gates require fewer events in every pair and lower median bytes; no time assertion or GC filtering. Every previous test/threshold unchanged, including historical RationalBigInt3percent gate; no old exception reused. Ordinary Test only, no custom recorder/manual Test stack. Exact source inverse, reviewed private-index commit, ff-only local integration and fresh actual-master acceptance precede normal nonforce push.

User files/env/unrelated indexes preserved. Current source/index/continuation old hashes map only to baseline/before-master/continuation-before exact bytes; all older maps/raw/rejections frozen. Full historical groups AND sessions checked using boot/start_ticks/command, exact unrelated WSL identity allowance retained, no PID-alone identity. CI off, automation paused, HH reuse disabled; broader/fullsuite/x64/native-retention/end-to-end OPEN. No automatic new experiment.
'''
(D/'FINAL-REPORT.md').write_text(report)
prefix=f'''# Current continuation — stagnation/unit-basis/row-weight scalar savings integrated, 2026-10-27

Master/origin/master `{target}` normally pushed/remote-verified, exact4paths (2src+ordinarytest+runtests). A concrete BFstagnation metric privatezero/freepricemagnitude; B BF/RationalBigInt unitgate preserving BFnegative rounding; C BFsharedrowweight cacheability once at first original site. Generic methods/checks/owners/callback/rebase/exceptions/tolerances/precision/rounding retained. No newscan/solve/copy/conversion/persistentnumericcache; independent review no unnecessary new production work/memory.

Accepted105921checks/3415cells/61470windows/74.538s; all measuredcompile/recompilezero,23GCwindows/alloutliers retained. Whole BFobservationmedian~.966-.968; BCinitializer~.866. Single A observation byte-increase pair/allocator causeunknown retained; no universal/endtoendspeedup. Initial104540PASS+19diagnostic reseterrors rejected/frozen; separately reviewed harness-only reset fix, no candidate tuning. RED{red['passed']}+5expectedcostfailures beforestage; GREEN/actualMASTER each{m['passed']}PASS/45wholefiles. Existingtests/thresholds unchanged/no newexception. Exactcommitreview/ff-only/actualmasterreview/normalpush verified; finalPASSclosure/exactdiagnosticpublication required. Evidence diagnostics/generic-stagnation-unit-seed/2026-10-27/FINAL-REPORT.md. Source/index/continuation oldbindings mapONLY baseline/before-master/continuation-before exactbytes/alloldermaps preserved. Userfiles/env/unrelatedindexes preserved; fullgroups ANDsessions/boot/start_ticks/command/noJulia with exact unrelatedWSLidentity-onlyallowance. CIoff/automationpaused/HHdisabled/broader/fullsuite/x64/native-retention OPEN. All case artifacts FROZENNEVERRERUN/rewrite; no automatic newexperiment.

## Previous continuation — preserved verbatim below

'''
for p in cont:p.write_bytes(prefix.encode()+Path(mapping[str(p)]['before']).read_bytes())
(D/'progress-final.md').write_text(f'All3+BCaccepted; comparison105921PASS; RED{red["passed"]}+5; GREEN/MASTER{m["passed"]}PASS45files; exactreviewed4pathcommit/ff-only/normalpushremoteverified. Broader/fullsuite/x64OPEN.\n')
if Path(__file__).resolve()!=(D/'finalize-reviewed.py').resolve():shutil.copyfile(__file__,D/'finalize-reviewed.py')
print('Final continuation/report prepared; master',target)
