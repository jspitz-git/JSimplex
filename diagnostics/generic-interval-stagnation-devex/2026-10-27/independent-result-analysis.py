from pathlib import Path
import sys,json,tomllib,statistics,math,collections,datetime,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-interval-stagnation-devex/2026-10-27');P=D/'comparison-2';Q=D/'correctness-qualification'
sys.path.insert(0,str(Q));import common_reviewed as c
c.unchanged()
for f in [P/'reconciliation-review.json',P/'audit-reconciled.json',Q/'result-review.json',Q/'audit.json']:
 a=json.loads(f.read_text());assert a['accepted'] is True
 for p,h in a['bindings'].items():assert c.sha(p)==h,p
rec=json.loads((P/'audit-reconciled.json').read_text());assert rec['original_run_accepted'] is False and rec['measurement_rerun'] is False and rec['cells']==1813 and rec['windows']==32634 and rec['qualification_assertions']==15213
h=c.host(json.loads((P/'audit-host.json').read_text())['groups']);assert len(h['groups'])==623
raw=tomllib.loads((P/'output/results.toml').read_text());summary=json.loads((P/'summary-reconciled.json').read_text());assert len(raw['cells'])==len(summary['cases'])==1813
groups=collections.defaultdict(list);all_rows=[];gc=0;representative=[]
for cell,reported in zip(raw['cells'],summary['cases']):
 names=['context','type','n','rows','scope','density','shape','variant'];r={k:cell[k] for k in names};arm=cell['variant'];rat=[];bs=[];es=[];orig=[];cand=[]
 for pair in range(1,10):
  rows=cell['windows'][(pair-1)*2:pair*2];by={w[1]:w for w in rows};a,b=by['original'],by[arm];assert a[0]==b[0]==pair
  rat.append(b[2]/a[2]);bs.append(a[3]-b[3]);es.append(a[4]-b[4]);orig.append(a);cand.append(b);gc+=sum(w[5]>0 for w in rows)
 med=statistics.median(rat);r.update(paired_ratio=med,ratio_MAD=statistics.median(abs(x-med) for x in rat),ratio_min=min(rat),ratio_max=max(rat))
 for rows,name in ((orig,'original'),(cand,'candidate')):r[name]={field:statistics.median(w[i+2] for w in rows) for i,field in enumerate(('seconds','bytes','events'))}
 for values,field in ((bs,'bytes'),(es,'events')):r['all_pairs_lower_'+field]=all(x>0 for x in values)
 assert r==reported,cell['id']
 item=dict(id=cell['id'],**r,median_bytes_saved=statistics.median(bs),median_events_saved=statistics.median(es),all_pairs_nonincreasing_bytes=all(x>=0 for x in bs),all_pairs_nonincreasing_events=all(x>=0 for x in es))
 all_rows.append(item)
 mode='nearest' if 'Nearest' in cell['context'] else 'other'
 key=(arm,cell['type'],cell['scope'],mode if arm=='A' and cell['type']=='BigFloat' else 'all',cell['shape'])
 groups[key].append(item)
 if cell['context']=='BF128_RoundingMode{:Nearest}()' and cell['n']==64 and cell['density']=='dense' and cell['shape']=='positive':representative.append(item)
assert gc==summary['GC_affected_windows']==rec['GC_affected_windows']==58
aggregates=[]
for key,values in groups.items():
 ag=dict(zip(('variant','type','scope','mode','shape'),key));ag.update(cells=len(values),median_cell_paired_ratio=statistics.median(v['paired_ratio'] for v in values),cell_ratio_range=[min(v['paired_ratio'] for v in values),max(v['paired_ratio'] for v in values)],median_bytes_saved_range=[min(v['median_bytes_saved'] for v in values),max(v['median_bytes_saved'] for v in values)],median_events_saved_range=[min(v['median_events_saved'] for v in values),max(v['median_events_saved'] for v in values)],every_pair_nonincreasing_bytes=all(v['all_pairs_nonincreasing_bytes'] for v in values),every_pair_nonincreasing_events=all(v['all_pairs_nonincreasing_events'] for v in values));aggregates.append(ag)
for arm,count in [('A',720),('B',540),('C',405)]:assert len([v for v in all_rows if v['type']=='BigFloat' and v['variant']==arm])==count
for arm in ('A','C'):assert all(v['all_pairs_nonincreasing_bytes'] and v['all_pairs_nonincreasing_events'] for v in all_rows if v['type']=='BigFloat' and v['variant']==arm)
assert all(v['all_pairs_lower_bytes'] and v['all_pairs_lower_events'] for v in all_rows if v['type']=='BigFloat' and v['variant']=='C')
assert all(v['all_pairs_lower_bytes'] and v['all_pairs_lower_events'] for v in all_rows if v['type']=='BigFloat' and v['variant']=='B' and v['shape']!='negative')
assert all(v['median_events_saved']==0 for v in all_rows if v['type']!='BigFloat' or (v['variant']=='B' and v['shape']=='negative'))
analysis=dict(cells=1813,windows=32634,GC_affected_windows=58,all_reconciled_rows_recomputed_equal=True,aggregates=aggregates,representative_BF128_nearest_dense_64x16_positive=representative,decisions={k:'accept for ordinary regression and production integration' for k in ('A','B','C')},measurement_rerun=False)
with (D/'independent-result-analysis.json').open('x') as f:json.dump(analysis,f,indent=2);f.write('\n')
with (D/'independent-result-host.json').open('x') as f:json.dump(h,f,indent=2);f.write('\n')
shutil.copyfile(__file__,D/'independent-result-analysis.py')
report='''# Independent measured per-variant review

Accept A, B and C for the planned ordinary RED/GREEN regression and production integration workflow. This is acceptance of the measured private variants, not a claim that production integration or full-suite verification is complete. No further measurements or source tuning were performed.

Evidence integrity: recomputing every reported cell summary directly from the preserved raw TOML exactly reproduced all 1813 summaries and 32634 windows, including paired medians/MAD/ranges, bytes and allocation events. All 58 GC-affected windows remain. The qualification passed 15213/15213 ordinary assertions in 42.425849299 seconds. The original measurement is still rejected with 55982 passes and 360 diagnosed invalid-oracle assertions; it is not retroactively a passing process. The independently reviewed reconciliation qualifies its complete cost records using the successful corrected oracle/owner qualification. Measurement was not rerun.

Fresh checks verified the reconciliation and qualification SHA bindings, all current prospective pins/protected files/indexes/refs/environment and the full 623 historical group/session identities with boot/start ticks/commands; no Julia was active. The fixed identity-only unrelated-process allowance is unchanged. All private candidate modules retain the reviewed exact source transformations. The original measurement was bounded to 71.150892954 seconds by the supervisor, with no forced numerical termination; minimum sampled available RAM was 21389864 KiB and swap used was zero.

A — accepted. In the 12 nearest-rounding positive cells per consumer, median paired candidate/reference time ratios were 0.822 rows, 0.821 feasibility, 0.841 reduced costs and 0.828 witness certification. Mixed-sign equivalents were 0.919, 0.919, 0.924 and 0.923. Positive nearest-rounding cells saved 244–39680 allocation events depending on consumer/dimension; mixed cells saved 120–17776. Negative-only nearest and all four non-nearest modes had zero event/byte savings, consistent with the guarded source paths. Every pair in all 720 BigFloat cells had nonincreasing bytes and events. This supports guarded kernel savings, not a universal timing gain: the unchanged non-nearest reduced-cost group includes a cell ratio of 1.325, and all timings/outliers remain. Existing FastTwoSum/FMA/underflow/precision/rounding/zero-unit guards and whole witness arithmetic are unchanged.

B — accepted. Across 60 positive cells per scope, median paired ratios were 0.665 new setup, 0.873 cold observer and 0.974 rebase; mixed-sign counterparts were 0.848, 0.940 and 0.987. Every positive/mixed pair reduced both managed bytes and allocation events. Positive setup/cold saved 384–1280 events and rebase 96–320; mixed saved half those counts. Negative-only cases saved zero events and had ratios 0.996/0.998/1.001. Their median byte differences range from a 320-byte increase to a 128-byte saving; unchanged native/exact controls also show small byte differences with unchanged event counts. These byte variations are reported without attributing a cause or claiming universal byte savings. Existing conversions, cost/primal/bound/context scans, monitor ownership, callback ordering and recovery-precision policy remain. Concrete specialization adds cold method metadata only.

C — accepted for consistent allocation reduction. All nine pairs in all 405 BigFloat scalar/shared/full-BTRAN cells saved 176–384 bytes and 5–9 allocation events per call. Positive/mixed pivots save 9 events; negative pivots save 5. Overall median cell paired ratios were 0.667 for the scalar helper, 0.957 for shared-row updates and 0.998 for actual BTRAN/price updates. The full-BTRAN result does not support a meaningful timing improvement; individual cell ratios range 0.901–1.125. The unit, quotient, exceptional upper cap and returned owner behavior remain unchanged numerically, including NaN/signed-zero/infinity and stored/ambient precision. Existing BTRAN, pricing and candidate traversal costs are retained.

Representative whole functions, BigFloat128 nearest rounding, dense 64 columns/16 rows, positive inputs (median managed bytes/events per call):

| Variant / whole function | Original bytes → candidate | Original events → candidate | Median paired time ratio |
| --- | ---: | ---: | ---: |
| A witness certification | 6542608 → 5272848 | 207449 → 167769 | 0.828 |
| B new monitor | 99808 → 58912 | 3986 → 2706 | 0.659 |
| B cold observer | 258976 → 218016 | 9975 → 8695 | 0.884 |
| B rebase observer | 318496 → 308224 | 11923 → 11603 | 0.961 |
| C shared-row update | 16720 → 16384 | 521 → 512 | 0.972 |
| C BTRAN/price update | 372528 → 372192 | 11643 → 11634 | 0.980 |

The last column is the median of nine paired ratios, not the ratio of marginal time medians. For example, the representative C BTRAN marginal medians are 299.8 µs original and 308.7 µs candidate despite its paired ratio being below one; this illustrates the uncertainty and is another reason not to claim a BTRAN timing gain. The full stratified data, ranges and counts are in independent-result-analysis.json.

Work/memory conclusion: no unnecessary added production scans, solves, copies, conversions, caches or retained storage were found. A removes up to two reached sum and one reached product discarded nonnegative negations within existing O(nnz) certification scans. B removes one discarded nonnegative magnitude operation per eligible scalar in existing setup/rebase traversals; no metric is reused across callback events. C removes unconditional finite-cap construction and eligible pivot negation from one leaving-weight computation per update, retaining the existing candidate scan/solve/price work. No change scales additionally with update-chain length, and no shared mutable constants or caches are introduced.

Limits: timings come from nine alternating pairs of small fixed sparse/dense fixtures, not solver trajectory experiments or independent process replications. All compilation, fixture initialization, cold/warm/reset/snapshot-validation and context-GC costs are separated in the original raw records; the qualification is correctness-only. Allocation-event counts and managed bytes are not full native-allocation or retained-memory measurements. No speedup is inferred from iteration count. Full native/import/loader closure, broader problem coverage, full-suite and cross-architecture correctness remain open. Ordinary original RED, production GREEN, whole-branch review and the authorized integration checks remain mandatory next steps.
'''
with (D/'RESULT-REVIEW.md').open('x') as f:f.write(report)
paths=[D/n for n in ['RESULT-REVIEW.md','independent-result-analysis.json','independent-result-analysis.py','independent-result-host.json','changes.json','source-clones.json','measurement-rejection.json']]+[P/n for n in ['audit-reconciled.json','audit-reconciled-reviewed.py','reconciliation-review.json','RECONCILIATION-REVIEW.md','summary-reconciled.json','pins.json','output/results.toml','output/run.log','output/process.json','output/resources.jsonl','supervisor.json','independent-failure-source-review.json','audit-host.json']]+[Q/n for n in ['audit.json','result-review.json','RESULT-REVIEW.md','pins-reviewed.json','fixtures.jl','tests.jl','output/run.log','output/process.json']]
res=dict(accepted=True,findings=[],accepted_variants=['A','B','C'],rejected_variants=[],decisions={'A':{'accepted':True,'basis':'guarded nearest-rounding managed-allocation savings with qualified numerical equivalence'},'B':{'accepted':True,'basis':'positive/mixed setup/rebase event savings with qualified conversion/precision/owner/callback equivalence; negative/control byte variation not attributed'},'C':{'accepted':True,'basis':'all-pair allocation savings in scalar/shared/actual-BTRAN paths; no meaningful actual-BTRAN timing claim'}},original_measurement_run_accepted=False,measurement_rerun=False,qualification_assertions=15213,cells=1813,windows=32634,GC_affected_windows=58,production_integration_complete=False,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),bindings={str(p):c.sha(p) for p in paths})
with (D/'result-review.json').open('x') as f:json.dump(res,f,indent=2);f.write('\n')
print('Independent per-variant acceptance A/B/C saved; all1813 summaries recomputed exact;623groups; original measurement rejection preserved; no measurements rerun.')
