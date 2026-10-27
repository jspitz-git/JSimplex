from pathlib import Path
import sys,json,shutil,statistics as stats
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');sys.path.insert(0,str(D));import common as c
M=c.M;R=c.R
for n in ['publication-preparation-reviewed.json','production-review.json','MASTER-run/result-review.json','GREEN-run/result-review.json']:
 r=c.read(n);c.need(r['accepted'] and not r['findings'],'review '+n)
co=c.read('production-commit.json');target=co['commit'];pub=c.read('publication.json');c.need(pub['accepted'] and pub['commit']==target,'master published')
c.need(c.git(['rev-parse','HEAD'])==c.git(['rev-parse','origin/master'])==c.git(['ls-remote','origin','refs/heads/master']).split()[0]==target,'master refs')
g=c.read('GREEN-run/audit.json');m=c.read('MASTER-run/audit.json');red=c.read('RED-run/audit.json');cmp=c.read('comparison-2/audit-qualified.json');c.need(g['passed']==m['passed'] and g['expected_failures']==m['expected_failures']==0,'same all-pass GREEN/MASTER')
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
rows=c.read('comparison-2/summary-qualified.json');table=[]
for typ,arm,scope,label in [('BigFloat','A','snap','BigFloat whole bound-snap guard'),('BigFloat','A','step','BigFloat whole final-step guard'),('BigFloat','A','ratio','BigFloat whole primal ratio'),('Rational{BigInt}','A','snap','Rational{BigInt} whole bound-snap guard'),('Rational{BigInt}','A','step','Rational{BigInt} whole final-step guard'),('Rational{BigInt}','A','ratio','Rational{BigInt} whole primal ratio'),('BigFloat','B','norm','BigFloat direction norm'),('BigFloat','B','init','BigFloat whole steepest initialization'),('BigFloat','B','solve','BigFloat checked FTRAN and weight maintenance'),('BigFloat','C','cert','BigFloat whole infeasibility certificate')]:
 rr=[v for v in rows if v['type']==typ and v['variant']==arm and v['scope']==scope]
 c.need(rr,'reported measured cells '+label)
 table.append('| '+label+' | '+str(len(rr))+' | '+' | '.join(f'{stats.median(v[k]["paired_median"] for v in rr):.6f}' for k in ['seconds','bytes','events'])+' |')
report=f'''# Multiprecision bounds, direction cap and infeasibility scalars

Production `{target}` has sole parent `{c.TARGET}` and is normally pushed and remotely verified. Exactly four paths change: src/primal_simplex.jl, src/dual_simplex.jl, the new ordinary test/generic_bounds_norm_infeasibility_tests.jl, and its runtests inclusion.

A reuses one invocation-private, read-only comparison zero in BigFloat/Rational{{BigInt}} Boolean bound guards, including their unbounded-side zero values. Finite checks, early returns, subtraction/read order, max order and final comparisons remain. Lazy initialization preserves empty and first-nonfinite paths. The zero never escapes into a result, array, callback, or persistent cache. Generic and hardware/fixed-rational methods retain their original bodies.

B creates a fresh current-precision BigFloat direction cap only for a positive infinite product. The original two norm passes, squares, inverse, sqrt, frexp, product and cacheability checks remain. Installed min selects the product on finite ties and NaN. Mixed stored/current precision can produce the original NaN behavior after a negative wide floatmax becomes infinite under unary negation; the candidate deliberately preserves it. This is not a repair of that numerical behavior.

C uses exact integer zero at only three BigFloat certificate comparison sites and conditional magnitudes at the two existing penalty endpoints. Fresh coefficient and accumulator zeros, all interval widenings and product bounds, tolerances, finite/unbounded rejection and allowance arithmetic remain. Hardware and exact certificate routes remain unchanged.

| Complete call | Cells | Median paired time ratio | Median bytes ratio | Median allocation events ratio |
|---|---:|---:|---:|---:|
'''+ '\n'.join(table)+f'''

Ratios below one favor the candidate. Each cell has three warm pairs and nine alternating measured pairs. These are medians of fixture-cell paired medians in one process, not independent-run confidence intervals. All slower samples, outliers and all 25 in-window GC occurrences remain in the evidence. In particular the real checked FTRAN time benefit is inconclusive, and the certificate and norm gains are modest. No end-to-end or universal speedup is established. Allocation traffic is not live/native memory or a proof of deallocation.

The complete saved comparison has 1,632 cells and 29,376 measured windows, all with zero compilation/recompilation. Sparse/dense sizes16/64, BigFloat64/128/256 and all five rounding modes, stored512 values, native and Rational controls, both certificate orientations and finite/one-sided/zero-allowance cases are included. Fixture, views, reset, cold, warm, explicit GC and validation preparation are recorded separately.

The first launch failed during loading because an extracted owned short-form helper also appeared in a using import. It executed no tests or measurement windows. A separate loader-only fix removed that import without overwriting JSimplex methods. The next launch completed every planned window and 51,891 passing assertions but had 18 incorrect extra-test expectations, so its original exit1 and rejected supervisor remain frozen. Stored512 negative floatmax at lower ambient precision under Nearest/Up/FromZero can yield +Inf magnitude, zero inverse, and Inf*0=NaN in both sources. A separate correctness-only qualification corrected exactly those 18 oracle outcomes, added direct stage evidence, and passed 15,881/15,881 ordinary assertions. It performed no cost windows. A newly reviewed postexit auditor qualified the complete saved cost data without converting the original failed run into a pass or repeating the measurement.

Original production RED:15,911PASS plus exactly10 expected allocation failures, total15,921, elapsed{red['elapsed_shared_seconds']:.3f}s. Ten fixed three-pair whole-call gates require fewer events in each pair and fewer median bytes; they impose no time assertion or changes to existing tests/thresholds. GREEN and actual MASTER each pass {m['passed']}/{m['passed']} assertions in the same 51 ordered whole test files, with inclusive elapsed {g['elapsed_shared_seconds']:.3f}/{m['elapsed_shared_seconds']:.3f}s. Ordinary Test is used without custom recorders or manual testset-stack management. No historical release exception is reused.

Independent numerical/source/ownership/work/memory reviews and concrete RED/GREEN/actual-commit/MASTER admission and result reviews precede publication. Review found no unnecessary additional production scans, basis solves, copies, conversions or retained numerical storage. A replaces repeated zero construction by one private seed, B omits an unused cap constructor, and C removes discarded negations and comparison-only zeros. Existing asymptotic work and numerical safeguards remain. Cold method metadata and the small branches are explicitly accounted for in WORK-MEMORY.md; there is no new persistent numerical cache.

The whole tested source/test tree and protected user/environment/index state are preserved through private-index commit, local ff-only integration and actual-master qualification. Old source/index/continuation bindings resolve only to exact baseline, before-master and continuation-before bytes; all older maps and rejected evidence remain intact. Fresh {len(h['groups'])} historical groups AND sessions/boot/start_ticks/command/noJulia are checked with only the exact unrelated WSL identity allowance. CI remains off, automation paused and HH reuse disabled; broader/full-suite/x64/native-retention work remains open. A separate PASS closure and exact diagnostic staged/committed publication are still required. No automatic next experiment.
'''
(D/'FINAL-REPORT.md').write_text(report)
prefix=f'''# Current continuation — bounds, norm and infeasibility scalar savings integrated, 2026-10-27

Master/origin/master `{target}` normally pushed and remotely verified. A invocation-private comparison zeros in BigFloat/Rational{{BigInt}} Boolean bounds guards; B lazy BigFloat direction cap; C comparison-only zeros and endpoint magnitudes in BigFloat infeasibility certificate. Exact four paths; all tolerances, interval widenings, early guards, arithmetic/row order, ownership and fallback checks preserved. No added full scan/solve/copy/conversion or persistent numerical cache; independent review found no unnecessary production work or retained memory.

Saved comparison:1632cells/29376compilezero windows/25GC windows retained. Initial loader failure and subsequent 51891PASS+18 erroneous wide-floatmax oracle failures remain frozen/rejected. Separate correctness-only qualification15881PASS and qualified saved cost auditor accepted; no repeated measurement. Bound guards improve materially, norm/certificate benefits smaller, actual FTRAN time inconclusive. No universal/end-to-end/native-free claim.

Original RED15911PASS+10expected allocation failures; GREEN/actualMASTER each{m['passed']}PASS in the same51wholefiles. Existing tests/thresholds unchanged; no old exception reused. Exact inverse, independent reviews, private index, ff-only integration, fresh master tests and normal push verified. Evidence diagnostics/generic-bounds-norm-infeasibility/2026-10-27/FINAL-REPORT.md. Separate PASSclosure/exactdiagnosticpublication required. Prior bindings map ONLY baseline/before-master/continuation-before; all older maps/raw/rejections FROZEN NEVER RERUN/rewrite. User files/env preserved, fullgroupsANDsessions/boot/start_ticks/command/noJulia; CIoff/automationpaused/HHdisabled/broaderfullsuite/x64/native-retentionOPEN. No automatic next experiment.

## Previous continuation — preserved verbatim below

'''
for p in cont:p.write_bytes(prefix.encode()+Path(mapping[str(p)]['before']).read_bytes())
(D/'progress-final.md').write_text(f'All3accepted; complete saved1632cells29376windows cost data qualified without rerun; correctness15881PASS; RED15911+10expected; GREEN/MASTER{m["passed"]}PASS51files; exact4pathcommit/ff-only/normalpushremoteverified. Broader/fullsuiteOPEN.\n')

if Path(__file__).resolve()!=(D/'finalize.py').resolve():shutil.copyfile(__file__,D/'finalize.py')
print('finalreport/exactcontinuation prepared',target)
