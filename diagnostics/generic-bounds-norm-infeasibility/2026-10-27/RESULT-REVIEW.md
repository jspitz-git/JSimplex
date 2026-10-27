# Independent per-variant result decision

Accept A, B and C for production integration preparation, subject to prospective permanent correctness/allocation gates, original RED, implementation review and planned GREEN/MASTER checks. This is not completed integration, release approval or an end-to-end solver speedup claim.

Evidence status is explicit: original comparison-2 remains FAILED (51,891 passes, 18 faulty cap-oracle failures, exit1 and rejected supervisor). The independent source correction and separate correctness-only qualification passed 15,881 assertions, including the 18 expected NaNs and 72 caps. The new post-exit auditor qualifies existing cost data only. I independently rechecked its bindings, guard/gate/permit/source/resource state, all 1,632 ordered cells and 29,376 windows, recomputed every published per-cell cost summary and retained all 25 GC windows. Compilation and recompilation were zero in every measured window. No Julia, remeasurement or old auditor was executed.

Ratios below are medians across cells of each cell's nine paired ratios, not confidence intervals or pooled workload speedups. All cold, three warm, fixture/reset/snapshot/correctness and explicit-GC costs remain separately retained in 1,670 preparation entries. Sparse/dense dimensions 16/64, BigFloat64/128/256 and five rounding modes plus native/exact controls are included. These short kernels on one host/run cannot establish broad timing or retained-memory claims.

| Variant/path | Time ratio | Byte ratio | Event ratio | Decision |
|---|---:|---:|---:|---|
| A BigFloat snap | 0.74599 | 0.70336 | 0.71571 | accept |
| A BigFloat step | 0.74180 | 0.69520 | 0.70881 | accept |
| A BigFloat whole ratio | 0.95183 | 0.93836 | 0.93932 | accept |
| A Rational BigInt snap | 0.91534 | 0.91412 | 0.89644 | accept |
| A Rational BigInt step | 0.88869 | 0.89898 | 0.87087 | accept |
| A Rational BigInt ratio | 0.98089 | 0.97909 | 0.97379 | accept, timing modest |
| B BigFloat direct norm | 0.98900 | 0.98535 | 0.98849 | allocation benefit; timing unproved |
| B BigFloat initialization | 0.96542 | 0.93678 | 0.94927 | accept |
| B BigFloat checked FTRAN maintenance | 0.99656 | 0.99411 | 0.99568 | accept allocation benefit; timing unproved |
| C BigFloat full certificate | 0.97298 | 0.97700 | 0.97094 | accept; outcome-dependent timing |

A has lower median bytes/events in every impacted cell and no slower BigFloat cell median among 540 cells. BigFloat snap/step save 100 or 420 measured allocation events; whole ratio saves 60 or 252. Rational BigInt controls show reductions too, but only four cells per A path. One Rational ratio cell ties in time. Sharing the private read-only zero preserves Boolean results and avoids repeated constructors; lazy readiness adds a per-row branch and must remain counted.

B saves exactly five measured events and 176/208/240 bytes per direct norm or checked FTRAN call at the tested precisions. Initialization saves 85 or 325 events (existing column norms plus row norm). The unchanged checked basis solve dominates maintenance, so the tiny aggregate time change is not a demonstrated FTRAN speedup. Direct norm has 29/180 slower cell medians and 27 ties (range 0.77752–1.03896); checked FTRAN has 24/180 slower and 30 ties (range 0.96455–1.19899). These are retained, not filtered. Initialization medians are lower across 180 cells, but remain single-run evidence. Positive overflow still constructs the fresh cap; source removal counts are not claimed as universal allocation counts.

C has lower bytes/events in all 360 cells, saving 4–772 events depending on branch/orientation. It has 42 slower time medians and 12 ties, with cell median range 0.85487–1.01299. Below=true finite and one-sided controls have respective time/byte ratios 0.93940/0.95468 and 0.91736/0.93083; below=false finite and one-sided ratios are 0.98437/0.98813 and 0.95951/0.96220. Zero-tolerance paths have time ratios about 0.99848 and 1.00000, byte ratios about 0.99913: no meaningful timing benefit claimed. Both orientations and the invalid/straddling certificate controls remain covered; interval widening and all numerical safeguards are unchanged.

Native/exact unaffected routes retain baseline methods and measured event counts. Their time medians vary with coarse timer resolution/noise, and Rational byte counters show small variation despite unchanged methods: examples include Rational Int64 ratio byte ratios up to 1.00885 and norm up to 1.01276, and Rational BigInt certificate up to 1.00034. Those observations remain in independent-cost-analysis.json; they do not justify claiming every control improves or is byte-identical. No causal speed claim is based on unchanged allocations alone.

Computational work/memory review: no unnecessary new full-vector/matrix scan, basis solve, copy, conversion, repeated invariant check or retained data cache found. A remains O(rows), B retains two norm scans and the existing solve, C remains O(nnz+variables). New readiness branches and specialized-method compilation/code metadata are real costs; cold/warm and preparation measurements remain separated. Numeric safeguards take precedence and none were relaxed. Reduced measured Julia allocation events/bytes do not prove native limb freeing, reduced peak RSS or long-lived retained-memory improvements.

Prospective fixed three-pair permanent gates should require lower allocation events and lower median bytes, with no timing gate: A snap/step/whole ratio for BigFloat and Rational BigInt; B initialization and genuine checked-FTRAN maintenance for BigFloat (direct norm optional); C finite and one-sided full certificates for BigFloat below=true. Retain broader correctness/unchanged-route controls without demanding cost reductions from paths that do not change. These gates must witness original RED before candidate staging; their future outcome is not asserted here.
