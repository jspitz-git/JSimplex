# Large-model presolver pass attribution

2026-10-14. Diagnostic profiling of unchanged master `6f68e24e8ddac42b948da8fcc2d636c010751194`.
Three user-named local inputs, native Float64 reader and ordinary reference overlay.
No candidate, production change, full solve, new precision or relaxed safeguard.
Evidence: `results/PRESOLVE-LARGE-PROFILE`. The prior conversion-cache rejection stays.

## Result and limits

The first complete observed dispatch sequences took **1.5623 s runtime, 11.7925 s
medium, 42.3303 s test**. Parsing was separate: 0.3704/4.3750/6.5466 s. All recorded
pass windows, including first profiles, have zero compilation and recompilation.
Thus the user's statement that presolve takes less than a minute is consistent
with these local measurements. These are sums of dispatcher windows, not full
public-call latency; trace maintenance/postsolve appends are included, observer
logging/hashing and controller overhead excluded. First calls are not assumed warm
just because their measured dispatch compilation is zero.

| Input | Original rows / columns / stored nonzeros | Final rows / columns / stored nonzeros | First sequence | Cumulative allocation traffic |
| --- | --- | --- | ---: | ---: |
| runtime | 43,021 / 47,148 / 277,210 | 28,453 / 31,615 / 211,789 | 1.5623 s | 1.718 GB |
| medium | 586,972 / 420,526 / 1,446,423 | 360,982 / 186,497 / 961,843 | 11.7925 s | 8.171 GB |
| test | 614,038 / 526,231 / 1,714,776 | 570,020 / 394,798 / 1,801,979 | 42.3303 s | 21.432 GB |

GB is decimal cumulative aggregate GC-counter allocation traffic, **not peak/live
memory**. Collection time is included in elapsed time. Instrumentation/hash scans
outside windows can perturb subsequent GC/cache behavior; no observer neutrality.

## Dominant passes

First complete sequence, sums across actual revisits. The table includes GC; the
JSON retains every GC/compile counter, call, dimensions and change flag.

| Model / pass | Calls | Time | Time share | Allocated GB | Allocation events |
| --- | ---: | ---: | ---: | ---: | ---: |
| runtime propagation | 4 | 0.7505 s | 48.04% | 0.660 | 19,049,650 |
| runtime sparse equalities | 5 | 0.4201 s | 26.89% | 0.606 | 11,847,456 |
| runtime singleton equalities | 5 | 0.1634 s | 10.46% | 0.127 | 1,861,641 |
| medium propagation | 3 | 4.4576 s | 37.80% | 2.183 | 62,053,399 |
| medium sparse equalities | 3 | 3.3854 s | 28.71% | 2.559 | 54,856,654 |
| medium singleton equalities | 3 | 2.2088 s | 18.73% | 1.667 | 34,496,309 |
| test propagation | 4 | 17.8470 s | 42.16% | 5.720 | 167,040,778 |
| test sparse equalities | 4 | 16.2530 s | 38.40% | 10.532 | 266,692,301 |
| test parallel rows | 4 | 4.4212 s | 10.44% | 2.213 | 52,165,872 |

The two main passes account for 74.93%, 66.51%, 80.55% respectively. This is pass
attribution; it does NOT identify what fraction of each pass is exact conversion,
row storage, arithmetic, mapping or GC. All nine pass totals are in analysis.json.
The dependent-row pass takes only 5–7.2 microseconds per first sequence and makes
no change. Every reached input exceeds its 256-row guard, so the rejected small-
model coefficient cache cannot help any of these observed trajectories.

Runtime has two additional complete, independently output/input-checked profiles:
whole dispatch sums 1.4158 and 1.3436 s. Sparse-equality totals 0.4596–0.5679 s and
propagation 0.4572–0.5393 s; their two-sample means/medians are 0.5138 and 0.4983 s,
37.24% and 36.11% of summed medians. Allocation events/bytes for these passes match
across repeats. Ordering those two passes more precisely is not supported.

Medium recorded a second complete 27-dispatch trace matching the first dimensions,
rounds, order and changed flags. Its sum is 16.0326 s: propagation 5.5143, sparse
aggregation 4.4934, singleton aggregation 3.3912 s. Final result hashing was then
interrupted by the 114-second guard, so repeat result/input equality and public
control are **not established**. This is descriptive saved timing, not a passed
complete result qualification. GC differs substantially (e.g. propagation
2.100 vs 3.057 s); do not infer a regression or stable throughput from this.

Test completed and hashed its first 35-dispatch profile. Its second repetition
stopped cooperatively after 22 dispatches at the 100-second soft deadline. That
partial prefix is 27.3442 s and is NOT compared to a complete-profile total or
used for a whole-profile warm ranking. The final original-input/owner and ambient
checks passed. No public control completed for medium or test.

## Diagnostic overhead and preservation

Three serial guarded processes took 23.9121, 114.5163 and 104.9573 s inclusive,
243.3857 s total (<360 cap). Runtime and test exited zero and passed their audits;
medium is preserved as timeout/exit -15, partial, never relabelled PASS. Its signal
stack is in hashvalue!/digest at driver main line107, AFTER the second profile's
last dispatch. Repeated type-name formatting while hashing large postsolve records
is avoidable diagnostic work. Streaming limits representation size, but did not
make this hash cheap. That diagnostic design consumed much more time than intended;
no production slowdown is implied. Do not reuse this digest implementation for a
future large-model benchmark. No retry or extended run was performed.

Runtime: three full profile result signatures equal one ordinary public presolve,
input values/owners unchanged. Medium: first completed profile input preservation
verified; second result hash interrupted. Test: first profile input preservation
and post-partial final input preservation verified; no public-result comparison.
Controller has an exact three-substitution inverse to production, original
nine-pass order/12-round limit and propagation trace retained. The added observer
never overwrites production methods or provides partial numerical success.

Source/test/CI/environment protected files, master and input pins remain unchanged.
No retained Julia/process group after closure. Before-run independent admission
verified 4,294 pins/908,882,196 bytes and all 18 required artifacts. Launch adds
pins/admission for 4,296 entries. No cache-confinement/full-native-memory claim.

## Concrete next optimization proposal

First try **lazy reuse of the exact +1 and -1 coefficient values inside the
Float64 `_propagate_row_bounds` pass**, at the `_exact_rational(stored)` conversion
in its active-row coefficient loop (`src/presolve_propagation.jl`).

Today each reached coefficient is converted afresh, even if the same unit value
was already converted in the same pass. Keep at most two private scalar references,
initially nothing. The FIRST reached +1 or -1 performs exactly the original
conversion and saves that result; subsequent occurrences reuse it. All nonunit
coefficients use the unchanged conversion. No eager scratch construction, global
cache, dictionary, scan, per-column metadata or replacement result vector.

Source work ledger: before, one exact conversion per reached coefficient; after,
one per nonunit coefficient plus at most one per sign actually encountered. Add
at most two stored-Float64 comparisons per coefficient and two private references
per pass; existing `coefficients`, min/max term buffers and bound caches stay.
For each sign with k occurrences, k-1 conversions can be avoided, without an extra
first-occurrence conversion. No new full-vector scan, solve, copy or matrix work.
These are SOURCE counts, not observed conversion frequencies or allocation totals.
The profile does not record the unit-coefficient hit rate, so a meaningful speedup
cannot yet be promised, nor can these two comparisons be assumed free.

Correctness obligation: retain exact arithmetic, row order, zero/unit shortcuts,
unbounded-bound handling, representability tests, tightenings and postsolve data.
No mutation of shared numerator/denominator owners; cached constants remain private
and only readonly arithmetic consumes them. Initially scope to Float64 inputs;
other precisions keep their original route until separately justified. Audit all
uses before implementation: array ownership does not prove scalar ownership.

The proposal is distinct from the rejected unbounded-value dictionary cache in
`reduce_dependent_rows`, and from failed MA equality/RHS kernels. It introduces
no MA scratch and does not reopen those experiments. Allocation nonincrease is a
**required acceptance condition**, not a measured property of an unbuilt candidate.
Verify primitive/nonunit-only controls, aliases, exact result and input ownership,
then a short before/after full-presolve comparison on these inputs, including
first-use setup, bytes AND allocation events, GC and compile information. A unit-
frequency counter may be collected outside timing in that separately designed
experiment. Reject if setup/dispatch adds allocations or nonunit controls regress.
No production candidate/admission or new numerical attempt is created by this
recommendation. Broader plan remains open; CIoff, HHdisabled, automationpaused.
