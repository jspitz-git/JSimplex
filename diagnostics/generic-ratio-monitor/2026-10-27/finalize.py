from pathlib import Path
import sys,json,shutil,statistics as stats
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27');sys.path.insert(0,str(D));import common_complete as c
M=c.M;R=c.R
for n in ['publication-preparation-reviewed.json','production-review.json','MASTER-run/result-review.json','GREEN-run/result-review.json']:
 r=c.read(n);c.need(r['accepted'] and not r['findings'],'review '+n)
co=c.read('production-commit.json');target=co['commit'];pub=c.read('publication.json');c.need(pub['accepted'] and pub['commit']==target,'master published')
c.need(c.git(['rev-parse','HEAD'])==c.git(['rev-parse','origin/master'])==c.git(['ls-remote','origin','refs/heads/master']).split()[0]==target,'master refs')
g=c.read('GREEN-run/audit.json');m=c.read('MASTER-run/audit.json');red=c.read('RED-run/audit.json');cmp=c.read('audit.json');c.need(g['passed']==m['passed'] and g['expected_failures']==m['expected_failures']==0,'same all-pass GREEN/MASTER')
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
rows=c.read('summary.json');table=[]
for arm,scope,phase,label in [('A','ratio','end','Whole primal ratio'),('B','progress','ordinary','Whole ordinary progress observation, B only'),('C','progress','end','Whole end-window progress observation, C only'),('BC','progress','end','Whole end-window progress observation, B+C'),('B','workspace','end','Whole workspace observation/context, B only'),('C','workspace','end','Whole workspace observation/context, C only'),('BC','workspace','end','Whole workspace observation/context, B+C')]:
 rr=[v for v in rows if v['type']=='BigFloat' and v['variant']==arm and v['scope']==scope and v['phase']==phase]
 table.append('| '+label+' | '+str(len(rr))+' | '+' | '.join(f'{stats.median(v[k]["paired_median"] for v in rr):.6f}' for k in ['seconds','bytes','events'])+' |')
report=f'''# BigFloat ratio zeros and stagnation magnitudes

Production `{target}`, sole parent `{c.TARGET}`, normally pushed and remote verified. Exactly four paths: src/primal_simplex.jl, src/simplex_stalling.jl, new ordinary test/generic_ratio_monitor_tests.jl and its runtests inclusion.

A bypasses fresh-zero max construction only when a BigFloat ratio value is strictly positive (including +Inf, whose original max owner is preserved). NaN, -Inf, both zeros and negative values retain the original freshzero/max expression. Both ratio passes, movements/divisions, tie/pivot/rejection order, snap/step feasibility checks, fallback and all tolerances remain. B uses conditional BigFloat step magnitudes after the same conversions and validation, preserving shortcircuit/divisions/history/state/context/hash/callback/event work. C specializes BigFloat normalized improvement magnitudes after the same equality gate, preserving normalized divisions/subtraction/multiplication, max order and fresh zero returns. Other types retain their original magnitude arithmetic. All stored/current precisions, five rounding modes, array/scalar owners, aliases and exception partial state are qualified.

| Complete BigFloat call | Cells | Median paired time ratio | Median bytes ratio | Median events ratio |
|---|---:|---:|---:|---:|
'''+ '\n'.join(table)+f'''

Ratios below one favor the candidate. Each cell has three warm pairs and nine alternating measured pairs; these are single-process fixture-cell medians, not independent-run confidence intervals or end-to-end solver speedups. A all180 measured BigFloat positive-step cells lower bytes/events and pairedmedian time; correctness also covers zero, negative/tolerated/unsafe and nonfinite paths, whose timing is not inferred from those positive-step fixtures. B negative-only progress paths save no events. Whole workspace observation retains the dominating full scans; its time gains are inconclusive with slower/outlier cells (including non-GC slowdowns) preserved. B workspace has some byte increases despite nonincreasing events; exact-control byte differences with unchanged events also remain unattributed, not hidden or interpreted as production work savings. BC numerical/cost composition independently accepted. Hardware/exact timing equivalence, universal speedup, native free/live retention and observer neutrality are not proved.

One short guarded measurement:52721/52721 ordinary assertions,1225cells,22050windows, measured compilation/recompilationzero; all{cmp['gc_windows']}GC windows retained. Inclusive elapsed{c.read('completed.json')['elapsed_shared_seconds']:.3f}s is not the benchmark. BF64/128/256xfive rounding modes and stored512, Float32/64/RationalBigInt/Int64 controls; sparse/dense16/64 ratio and workspace cases, positive/negative/mixed signs, first/ordinary/end-window progress. Fixture/reset/snapshot/validation/cold/warm/explicitGC preparation recorded separately. Direct independent largest-pivot and multi-window state/rounded-equal oracles supplement full source-reference parity. No custom Test recorder/manual stack and no repeated measurement.

Initial offline admission rejected missing isresidual helper, incorrect row1 tie oracle and promised edge coverage. Original rejected admission/files/pins remain frozen. Separate reviewed/final/ready/complete harness additions corrected the helper and row8 largest-pivot expectation, added empty and dyadic safe/unsafe tolerated-negative cases, stored512 steps/metrics/anchors and fresh-zero/alias coverage; a directed-rounding oracle assumption and stale monitor-state output were corrected before any Julia. Candidate bodies/grid/window arithmetic unchanged. Positive-infinity shorthand in original plan/work ledger is corrected only by WORK-MEMORY-ERRATUM.md. No failed numerical run or retroactive pass; no old experiment/auditor rerun.

Ordinary original RED:24721PASS+4expected allocation failures=24725, all numerical controls passing, elapsed{red['elapsed_shared_seconds']:.3f}s. Four fixedthreepair gates require lower allocation events each pair and lower median bytes, with no timing assertions or old test/threshold changes. GREEN and actualMASTER each{m['passed']}/{m['passed']} assertions in the exact same50orderedwholefiles, inclusive{g['elapsed_shared_seconds']:.3f}/{m['elapsed_shared_seconds']:.3f}s. All earlier tests remain byte-identical except the new runtests inclusion; no historical release exception is reused. Independent source/measurement/RED/GREEN/actualcommit/MASTER reviews, exact source inverse and strict diffcheck precede normal publication.

Computational review found no unnecessary added production work or retained numerical memory. A adds one cheap positivity predicate per reached clamp and removes O(m) unused zero constructions; negative fallback still pays that predicate. B removes up to2 discarded negations per observation, C up to2 per reached improvement. Same full scans/solves/copies/conversions/invariant checks, O(1) transient local state and cold method metadata only; no persistent numerical cache or shared mutable zero. Full WORK-MEMORY ledger and independent reviews retain scope limits.

Exact user/env/index protection and whole tested tree preserved through private-index commit, localff-only integration and separately admitted actualMASTER verification. All old source/index/continuation bindings map only to baseline/before-master/continuation-before exactbytes; older maps remain unchanged. Fresh{len(h['groups'])}historicalgroups ANDsessions/boot/startticks/command/noJulia with the fixed unrelated WSL identity-only allowance. CIoff, automationpaused, HHreuse disabled; broader/fullsuite/x64/native-retention OPEN. Separate PASSclosure and exact staged/committed diagnostic publication still required. Allcaseartifacts frozen after publication; noautomatic new experiment.
'''
(D/'FINAL-REPORT.md').write_text(report)
prefix=f'''# Current continuation — BigFloat ratio and stagnation savings integrated, 2026-10-27

Master/origin/master `{target}` normally pushed/remoteverified. Exact4paths: BigFloat positive ratio clamps avoid unusedzero, conditional stepmagnitudes and normalizedimprovement magnitudes; generic/exact routes and allguards/tolerances/order/owners/callback/context/recoveryprecision remain. No newscan/solve/copy/conversion/persistentcache; independentreview no unnecessaryproductionworkmemory. A positive includes+Inf (sameowner), otherexceptional/zero/negative fallback originalfreshzero/max; exactproseerratum separate.

One short measurement52721PASS/1225cells/22050compilezerowindows/{cmp['gc_windows']}GCwindows preserved; no remeasurement. BFwholepositivestep ratio median time~0.922/bytes~0.908, monitor standalone savesallocations; wholeworkspace timeinconclusive/allslowercases andbytevariationretained. No endtoend/universal/nativefreeclaim. Allinitialofflineharnessrejections and beforeversions preserved; finalcorrectness expectations fixed beforeJulia with candidate unchanged.

RED24721PASS+4expectedcostFAIL; GREEN/actualMASTER each{m['passed']}PASS/50samewholefiles, oldtests/thresholdsunchanged/no oldexceptionreused. Exactinverse/privateindexcommit/ff-only/freshMASTER/independentreviews/normalpush verified. Evidence diagnostics/generic-ratio-monitor/2026-10-27/FINAL-REPORT.md. FinalPASSclosure/exactdiagnosticpublication separatelyrequired. Oldbindings mapONLY baseline/before-master/continuation-before; alloldermaps/raw/rejections FROZENNEVERRERUN/rewrite. Userfiles/env preserved, freshfullgroupsANDsessions/boot/startticks/command/noJulia; CIoff/automationpaused/HHdisabled/broader/fullsuite/x64/native-retentionOPEN. Noautomaticnewexperiment.

## Previous continuation — preserved verbatim below

'''
for p in cont:p.write_bytes(prefix.encode()+Path(mapping[str(p)]['before']).read_bytes())
(D/'progress-final.md').write_text(f'All3accepted; one52721PASS1225cells22050windows comparison; RED24721+4expected; GREEN/MASTER{m["passed"]}PASS50files; exact4pathcommit/ff-only/normalpushremoteverified. Broader/fullsuiteOPEN.\n')

if Path(__file__).resolve()!=(D/'finalize.py').resolve():shutil.copyfile(__file__,D/'finalize.py')
print('finalreport/exactcontinuation prepared',target)
