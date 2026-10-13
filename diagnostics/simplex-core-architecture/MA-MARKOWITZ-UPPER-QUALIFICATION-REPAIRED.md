# MA-F repaired harness: correctness qualified, production benefit not accepted

The replacement attempt completed all 22 serial processes. Expected RED and
candidate correctness passed. All six target benefit gates passed, but six of
32 control gates failed; the full production-benefit decision is NOT ACCEPTED.
No candidate integration, tuning, extra warmup or numerical retry followed.

## Preserved failure and narrow correction

Original attempt-1 remains frozen with its pre-test Test.push_testset error.
The separately admitted MA-F-repair driver uses Test.@with_testset with exact
parent/depth restoration around the same include. One-block inverse is exact;
381 assertions, candidate, kernels, fixtures and all numerical thresholds remain
unchanged. Four original source predicates fail, nine corrected source checks
pass. This static RED/GREEN supplements, not replaces, the original runtime error.
Independent prelaunch review checked installed Test and scoped-values semantics,
all1817pins/1816required entries and24bindings; no unresolved findings. Cold
scoped-value context bookkeeping plus parent/depth/check is outside kernel windows.
Test.jl/scopedvalues.jl are prospective replacement pins, not attempt-1 pins.

## Executed correctness and work

- Reference RED: exactly0pass/2expected missing-helper failures/0error/0broken.
- Candidate: all381 assertions (62/31/96/42/78/72), no failures/errors/broken.
- Additional48fixture cases and432ordered row publications passed the frozen
  sequential exact oracle, prefix/reference parity and exact residual bounds.
- All20cost processes passed endpoint/ownership/source/scalar/metadata checks;
  ten alternating side pairs, three warm and seven measured,48cases each.
- All1920steady full/upper windows have zero compile and recompile time.
  Five steady windows have nonzero GC; all are retained, no GC/outlier filtering.

Qualification retains the admitted59outerconstructors/6copies/12refactors/
83fullforward calls/48prefix dense solves/87reference+92candidate standalone
upper calls plus48reference upper reductions. These are source/driver entry
counts, not complete observed internal backend/native attempt accounting.
Cost schedule is960constructors/4800fullforward/4800upper-reset calls,4800copies/
96000assignments,91200selectedproducts andsubtractions each,640scratchdiagnostics.
No publicsolver/transposes/updates or old full-suite rerun. Exact output checks
cover recorded endpoints, not every hidden intermediate repetition/trajectory.

## Measured full-forward benefit

Values below use seven paired candidate/reference steady-window ratios.
Times/bytes/events in summary.json are per call (four calls per steady window);
a paired-ratio median is not a ratio of separate side medians. Allocation events
are Julia aggregate GC counters, potentially including native-backed accounting,
not native allocation/free or live-retention measurements. Sparse/dense labels
describe input storage; star cases exercise sparse elimination upper work, while
core cases are dense-core controls.

| Target case | Median C/R | Range | MAD | Faster pairs | Bytes/call ref → candidate | Events/call ref → candidate |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| star32_sparse BigFloat256 | 0.5726 | 0.3250–0.6991 | 0.0110 | 7/7 | 16080 → 7440 | 455 → 215 |
| star32_sparse BigFloat512 | 0.6157 | 0.5553–0.6609 | 0.0379 | 7/7 | 21440 → 9920 | 570 → 270 |
| star32_sparse RationalBigInt | 0.8022 | 0.7473–0.8604 | 0.0271 | 7/7 | 34908 → 15052 | 930 → 417 |
| star32_dense BigFloat256 | 0.6051 | 0.5921–0.6543 | 0.0130 | 7/7 | 16080 → 7440 | 455 → 215 |
| star32_dense BigFloat512 | 0.6506 | 0.6061–0.8267 | 0.0382 | 7/7 | 21440 → 9920 | 570 → 270 |
| star32_dense RationalBigInt | 0.7687 | 0.2085–0.9154 | 0.1109 | 7/7 | 34876 → 15032 | 930 → 417 |

All six satisfy median<=0.95 and>=6/7faster. The complete decision also requires
EVERY hardware/dense-control full-forward median<=1.05. These six fail:

| Control | Median C/R | Range | MAD | Median microseconds/call ref → candidate |
| --- | ---: | --- | ---: | ---: |
| star8_sparse Float32 | 1.0976 | 0.8667–1.8889 | 0.1976 | 1.075 → 1.125 |
| star8_dense Float32 | 1.1667 | 0.7500–3.2000 | 0.1667 | 0.150 → 0.175 |
| star32_dense Float32 | 1.1250 | 0.8889–2.5714 | 0.2361 | 0.200 → 0.225 |
| star32_dense Float64 | 1.1667 | 1.0000–3.5714 | 0.1667 | 0.175 → 0.200 |
| core32_sparse RationalBigInt | 1.1760 | 0.7728–1.8049 | 0.3544 | 235.425 → 291.975 |
| core32_dense BigFloat128 | 1.0888 | 0.0503–16.6649 | 0.1055 | 228.100 → 247.750 |

Hardware controls have zero recorded bytes/events on both sides. Their tiny
windows and quantized timings limit causal inference; they still fail the frozen
gate. Dense-core Rational/BigFloat failures and all outliers/GC also remain.
No post-hoc exclusion, tolerance relaxation or retuning makes this a pass.
First-call/construction/scratch and standalone-upper metrics for ALL48cases are
reported separately in summary.json; cold windows include compilation and must
not be mixed into a steady speedup. Every raw sample is preserved. Processes,
loading/cache state, order and short windows remain possible confounders.

## Provenance and resource closure

New postprocess passed all11provenance checks; 177 portable files are byte-identical.
All1817pins, actualsrc/test/Project/CI, protected user files and local/remote refs
remained unchanged. All22terminal process records and stageaudits passed; exit0
alone was not acceptance. Independent immutable seal inspected eight gates;
one new exclusive reservation, no reuse of the original consumed reservation.
Fresh 90 old+new PGIDs ANDsessions absent/noJulia on boot
dade7243-9103-4398-bb45-fa28fbc0be72. Complete runner/child commands and startticks are in
each process.json, not inferred from PIDs alone.
Resource samples195, minimum available RAM21691196KiB,
maximum swap0KiB; inclusive launcher213.634215s is NOT a benchmark.
No resource rejection, extra process, longer cap or hidden warmup. Ordinary
--compiled-modules=existing loading is not cache confinement/import-work proof.

## Work/memory decision and continuation

Actual production is unchanged, so no NEW production scans/solves/copies/caches
or retained scratch were introduced by this step. The proposed candidate retains
its per-call eligibility work and private scratch creation inside full-forward
timings; allocation reduction alone does not establish general performance.
No full native-memory/free balance, universal speedup, end-to-end solver speedup
or full-suite/CI success follows. Correctness is qualified only in the admitted
cases; broader all-precision/backend/trajectory guarantees remain open.

MA-F requested verification and short measurement are complete. Production
promotion is rejected under this fixed admission, despite target-kernel savings.
Keep candidate and both attempts frozen. Further source analysis may use these
results, but any changed candidate or new measurement needs a separate concrete
reviewed admission; standing human short-run authorization persists. Do not
automatically rerun, tune, weaken gates or extend time. No integration plan
is created from a failed benefit decision. Broader MA/S2/S3/S4/S5/S6 remain open.

MA-F current STATUS/roadmap bindings in closure/publication/review map ONLY to
MA-F-repair/STATUS.md.before-MA-F-repair and roadmap.md.before-MA-F-repair.
All older mappings, initial failed attempt/reviews and MA-E artifacts unchanged.
Master6f68e24, actual source/test/environment/CI unchanged; automationpaused,
HHreuse disabled. The original MA-F plan and repaired admission remain frozen.
