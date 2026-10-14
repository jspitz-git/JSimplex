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

## Prior work and corrected recommendation

The user correctly pointed out that propagation has already been investigated.
Existing diagnostics outside the core-architecture directory include rounds38
(unit products),77 (fixed-bound conversion sharing),137 (equal-denominator sums)
and many other propagation changes; MA-P separately rejected general MA use in
RHS staging. A large measured share alone does not justify repeating these paths.
The initial unit-conversion propagation suggestion is withdrawn as the next action;
its report bytes are preserved in report.before-user-correction.md. The original
postcheck report binding resolves ONLY to that preserved report. All numerical
records and analysis remain unchanged.

Recommend a distinct small change in **sparse equality aggregation: avoid converting
an absent or stored-zero old matrix entry to Rational{BigInt} when its value will
immediately be discarded by the existing nonzero-multiplier update**.

Current source at src/presolve_aggregation.jl:462 first retrieves a staged exact
value from matrix_updates, otherwise calls _exact_rational(A[other_row,other]).
Only afterward, for a nonzero multiplier, it computes the product and uses
iszero(old_value) ? -product : ... . For structural fill-in, the original lookup
returns zero; its fresh exact representation is unnecessary on this branch.

This is not a repetition of round25 (lazy dictionary defaults, which only avoided
conversion on dictionary HITS) or round96 (negate product instead of subtracting
from an ALREADY exact zero). Both historical reports explicitly leave the original
MISS conversion in place. Round103 applied a related stored-zero check to the
separate free-doubleton path; it is evidence for an existing design pattern, not
proof of benefit or correctness in sparse aggregation's staged-update dictionary.

Concrete prospective design: retain one dictionary lookup using a missing sentinel.
On a miss read the original stored coefficient exactly once. If that stored value
is zero AND the multiplier is nonzero, retain a zero marker, compute the unchanged
exact product, and feed its negation through the SAME _represent_exact and staged
commit path. Nonzero old values, all dictionary hits (including staged cancellation
to zero), and zero multipliers preserve the original route. Do not confuse a
missing dictionary key with a staged nonzero replacement of an originally zero
matrix slot. Initial qualification can be Float64 only; other precision routes
remain original until their contract is separately checked.

Work/memory ledger: one existing dictionary lookup and CSC access per missing key;
add a scalar stored-zero test, eliminate one exact zero conversion per eligible
update. No new scan, cache, vector, scratch number, solve, traversal, retained
matrix or worklist. Existing cost/bound/coefficient staging, dictionary publication,
fill caps, row order, exact representability and postsolve records remain intact.
No new eagerly initialized scratch or global roots. Scalar aliases must still be
reviewed; no BigInt operand is mutated. This targets allocation removal in a pass
that costs 28–38% on the large complete profiles and allocates 2.559/10.532GB on
medium/test, without attributing all that cost to zero conversion.

The profile identifies the pass, not its internal conversion hit rate or time
share. Therefore **speedup and allocation nonincrease are not yet measured**.
Required before/after acceptance: matching complete reduced model/postsolve and
input owners, absent and explicit signed zero, dictionary hits/nonzero overwrite,
staged cancellation, zero multipliers, nonzero controls, rejected staging, and
small/large full presolve timing including setup. Bytes AND allocation events must
not increase; no safeguard/precision/tolerance change or allocation-noise waiver.
Use cheap canonical fingerprints rather than the current per-element type-name
hashing for future large-model observations. No new candidate, admission, Julia
retry or integration is authorized by this report itself. Frozen prior rejections
stay; broader plan open, CIoff/HHdisabled/automationpaused.
