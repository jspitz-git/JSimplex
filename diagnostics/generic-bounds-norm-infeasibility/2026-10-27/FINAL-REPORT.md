# Multiprecision bounds, direction cap and infeasibility scalars

Production `ce5d4a74019e0dc2e656d08161641c498b159e7b` has sole parent `9d29b1f0aa21932217b03ca7b35dd91281baaae6` and is normally pushed and remotely verified. Exactly four paths change: src/primal_simplex.jl, src/dual_simplex.jl, the new ordinary test/generic_bounds_norm_infeasibility_tests.jl, and its runtests inclusion.

A reuses one invocation-private, read-only comparison zero in BigFloat/Rational{BigInt} Boolean bound guards, including their unbounded-side zero values. Finite checks, early returns, subtraction/read order, max order and final comparisons remain. Lazy initialization preserves empty and first-nonfinite paths. The zero never escapes into a result, array, callback, or persistent cache. Generic and hardware/fixed-rational methods retain their original bodies.

B creates a fresh current-precision BigFloat direction cap only for a positive infinite product. The original two norm passes, squares, inverse, sqrt, frexp, product and cacheability checks remain. Installed min selects the product on finite ties and NaN. Mixed stored/current precision can produce the original NaN behavior after a negative wide floatmax becomes infinite under unary negation; the candidate deliberately preserves it. This is not a repair of that numerical behavior.

C uses exact integer zero at only three BigFloat certificate comparison sites and conditional magnitudes at the two existing penalty endpoints. Fresh coefficient and accumulator zeros, all interval widenings and product bounds, tolerances, finite/unbounded rejection and allowance arithmetic remain. Hardware and exact certificate routes remain unchanged.

| Complete call | Cells | Median paired time ratio | Median bytes ratio | Median allocation events ratio |
|---|---:|---:|---:|---:|
| BigFloat whole bound-snap guard | 180 | 0.745989 | 0.703361 | 0.715709 |
| BigFloat whole final-step guard | 180 | 0.741803 | 0.695205 | 0.708807 |
| BigFloat whole primal ratio | 180 | 0.951833 | 0.938356 | 0.939322 |
| Rational{BigInt} whole bound-snap guard | 4 | 0.915343 | 0.914125 | 0.896441 |
| Rational{BigInt} whole final-step guard | 4 | 0.888688 | 0.898981 | 0.870871 |
| Rational{BigInt} whole primal ratio | 4 | 0.980887 | 0.979092 | 0.973789 |
| BigFloat direction norm | 180 | 0.988999 | 0.985352 | 0.988492 |
| BigFloat whole steepest initialization | 180 | 0.965424 | 0.936782 | 0.949266 |
| BigFloat checked FTRAN and weight maintenance | 180 | 0.996564 | 0.994107 | 0.995678 |
| BigFloat whole infeasibility certificate | 360 | 0.972977 | 0.976998 | 0.970939 |

Ratios below one favor the candidate. Each cell has three warm pairs and nine alternating measured pairs. These are medians of fixture-cell paired medians in one process, not independent-run confidence intervals. All slower samples, outliers and all 25 in-window GC occurrences remain in the evidence. In particular the real checked FTRAN time benefit is inconclusive, and the certificate and norm gains are modest. No end-to-end or universal speedup is established. Allocation traffic is not live/native memory or a proof of deallocation.

The complete saved comparison has 1,632 cells and 29,376 measured windows, all with zero compilation/recompilation. Sparse/dense sizes16/64, BigFloat64/128/256 and all five rounding modes, stored512 values, native and Rational controls, both certificate orientations and finite/one-sided/zero-allowance cases are included. Fixture, views, reset, cold, warm, explicit GC and validation preparation are recorded separately.

The first launch failed during loading because an extracted owned short-form helper also appeared in a using import. It executed no tests or measurement windows. A separate loader-only fix removed that import without overwriting JSimplex methods. The next launch completed every planned window and 51,891 passing assertions but had 18 incorrect extra-test expectations, so its original exit1 and rejected supervisor remain frozen. Stored512 negative floatmax at lower ambient precision under Nearest/Up/FromZero can yield +Inf magnitude, zero inverse, and Inf*0=NaN in both sources. A separate correctness-only qualification corrected exactly those 18 oracle outcomes, added direct stage evidence, and passed 15,881/15,881 ordinary assertions. It performed no cost windows. A newly reviewed postexit auditor qualified the complete saved cost data without converting the original failed run into a pass or repeating the measurement.

Original production RED:15,911PASS plus exactly10 expected allocation failures, total15,921, elapsed30.470s. Ten fixed three-pair whole-call gates require fewer events in each pair and fewer median bytes; they impose no time assertion or changes to existing tests/thresholds. GREEN and actual MASTER each pass 314009/314009 assertions in the same 51 ordered whole test files, with inclusive elapsed 1757.683/1928.781s. Ordinary Test is used without custom recorders or manual testset-stack management. No historical release exception is reused.

Independent numerical/source/ownership/work/memory reviews and concrete RED/GREEN/actual-commit/MASTER admission and result reviews precede publication. Review found no unnecessary additional production scans, basis solves, copies, conversions or retained numerical storage. A replaces repeated zero construction by one private seed, B omits an unused cap constructor, and C removes discarded negations and comparison-only zeros. Existing asymptotic work and numerical safeguards remain. Cold method metadata and the small branches are explicitly accounted for in WORK-MEMORY.md; there is no new persistent numerical cache.

The whole tested source/test tree and protected user/environment/index state are preserved through private-index commit, local ff-only integration and actual-master qualification. Old source/index/continuation bindings resolve only to exact baseline, before-master and continuation-before bytes; all older maps and rejected evidence remain intact. Fresh 649 historical groups AND sessions/boot/start_ticks/command/noJulia are checked with only the exact unrelated WSL identity allowance. CI remains off, automation paused and HH reuse disabled; broader/full-suite/x64/native-retention work remains open. A separate PASS closure and exact diagnostic staged/committed publication are still required. No automatic next experiment.
