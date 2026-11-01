# Task6 same-policy whole-solve comparison

Task6 is completed on the experimental branch, parent `0a06785c508f89103a09b3c4c6a238baca0db36f`, with original master `9940bdabe149e922afa60b5364227a7e7393bc75` unchanged. No engine/production/test/environment/CI code was changed in Task6. The user explicitly authorized publishing the accumulated experiment branch after completion; no production promotion or master push is included.

## Decision and practical limits

All16 fixed cases return original-certified OPTIMAL on both sides, with original-model feasibility/objective/input-preservation checks. Qualification passed236 ordinary assertions over66 complete solves; comparison passed749 over224 complete windows (64warm,160measured). All160 measured compile/recompile times are zero. The genuine separately qualified infeasible fallback stays an honest INFEASIBLE/no-payload boundary, not a speed result. Initial diagnostic admission rejection and parser RED remain preserved; no numerical attempt failed or was repeated.

Of the 13 cases with real E normal commits and no main fallback, all five observed time ratios are below1 in 0, above1 in 4, and straddle1 in 9. These are descriptive five-pair ranges, not confidence intervals or statistical significance. The inactive/presolve-only cases remain visible and receive no engine-saving interpretation. Entire solve time includes original model copy/presolve/scaling/init, E private import/index/newfactor, normal and rejected work, repair/refactor, export, any legacy cleanup/retry and final original certification. Different numerical trajectories/iteration counts must not be called kernel-only savings. No single kernel window substitutes for a verified result.

This small-case comparison does not establish a large-LP end-to-end benefit, an order-of-magnitude saving, or production readiness. Saved runtime/fast0507 basis/history inputs are not a source-bound short complete fixed-Devex/PFI solve schedule; their conditional admission was not established. They were not run or replaced by component windows. No integration proposal is accepted from this record; retain the implementation as an opt-in experiment. Any wider input/precision/backend or intended-policy/DSE comparison needs its own concrete admission.

The observed paired time medians exceed1 in all13 activated cases. For n16 sparse/dense they are1.623/1.890; for n64 sparse/dense1.235/1.607, with unchanged16/64whole iteration counts. Their byte ratios are2.486/2.308 and1.550/1.098. Adlittle with presolve uses80reference versus72E iterations yet its time median ratio is1.125: fewer iterations did not produce a total saving. None of these observations establishes a universal slowdown outside this corpus.

All160 measured GC times are zero. Many first reference windows immediately after the separately recorded postwarm GC are elevated despite compile/recompile0 (for example n16dense1.098ms versus later0.049–0.081ms). These values and every paired ratio are retained. Their cause—cache/native-release/scheduling or another effect—was not captured and is not inferred from zero GC. This first-window effect increases scatter and precludes confident small-percentage conclusions; no discard, extra warmup, calibration or rerun was used to improve ratios. There is no credible end-to-end gain on this corpus.

## Complete-window measurements

Ratios are E/reference within the same pair. Two complete warm solves per arm precede five alternating measured pairs per case; first pair reference then E, second E then reference, continuing rotation. Both observers are nothing; reference is ordinary public J.solve with no diagnostics, E is unchanged solve_experimental with its required bounded diagnostics/counters and NoEvents. Thus intrinsic E counter/record overhead is included, not subtracted. Reference event/kernel counts are qualified separately, never substituted for these uninstrumented wall times. All medians/ranges/MAD/times/bytes/allocation events/GC/iteration/refactor values are in compare-run/audit.json, and every raw sample remains in guard/run.log.

| Case | Activated | Ref / E median ms | Paired time median [range] | MAD | Bytes ratio | Events ratio | Ref / E whole iterations |
|---|---|---:|---:|---:|---:|---:|---:|
| n16_sparse | True | 0.0361 / 0.0671 | 1.6228 [1.4170,1.9620] | 0.1024 | 2.4858 | 2.1693 | 16 / 16 |
| n16_dense | True | 0.0584 / 0.1127 | 1.8904 [0.2027,2.0391] | 0.1487 | 2.3076 | 2.1905 | 16 / 16 |
| n64_sparse | True | 0.2459 / 0.2805 | 1.2351 [0.5693,1.2969] | 0.0617 | 1.5504 | 1.5465 | 64 / 64 |
| n64_dense | True | 1.1509 / 1.8655 | 1.6072 [0.5668,2.0804] | 0.2354 | 1.0982 | 1.5712 | 64 / 64 |
| mps_afiro_mps_p0 | True | 0.1177 / 0.1516 | 1.2880 [0.1330,1.8993] | 0.2130 | 1.6520 | 1.5767 | 22 / 22 |
| mps_afiro_mps_p1 | True | 0.5919 / 0.8188 | 1.0163 [0.4444,1.8085] | 0.5719 | 1.0685 | 1.0230 | 9 / 9 |
| mps_netlib_adlittle_mps_p0 | True | 0.6263 / 0.9009 | 1.3968 [0.5072,1.6251] | 0.0549 | 1.0634 | 1.2539 | 92 / 92 |
| mps_netlib_adlittle_mps_p1 | True | 2.8622 / 2.9475 | 1.1252 [0.8418,1.3900] | 0.2474 | 1.0299 | 1.0041 | 80 / 72 |
| mps_netlib_sc50a_mps_p0 | True | 0.2653 / 0.3619 | 1.3641 [0.3400,1.4395] | 0.0754 | 1.3520 | 1.3873 | 53 / 53 |
| mps_netlib_sc50a_mps_p1 | True | 1.7241 / 1.9689 | 1.1275 [0.6993,1.3066] | 0.0992 | 1.0350 | 1.0057 | 38 / 38 |
| mps_generated_degenerate-box_mps_p0 | True | 0.0155 / 0.0354 | 2.2857 [1.3863,2.9256] | 0.1438 | 2.9341 | 2.3369 | 1 / 1 |
| mps_generated_degenerate-box_mps_p1 | False | 0.0874 / 0.0929 | 1.0453 [0.4956,1.0742] | 0.0289 | 1.1317 | 1.0280 | 0 / 0 |
| mps_generated_phase-one_mps_p0 | True | 0.0239 / 0.0421 | 2.5161 [1.2050,2.8257] | 0.3096 | 2.9227 | 2.3182 | 2 / 2 |
| mps_generated_phase-one_mps_p1 | False | 0.0743 / 0.0849 | 1.1427 [0.3605,2.2283] | 0.1330 | 1.0801 | 1.0193 | 0 / 0 |
| mps_generated_scaled-diagonal_mps_p0 | True | 0.0185 / 0.0429 | 2.2054 [1.2399,3.1544] | 0.3808 | 2.9415 | 2.3182 | 2 / 2 |
| mps_generated_scaled-diagonal_mps_p1 | False | 0.0791 / 0.0892 | 1.1277 [0.6153,1.2478] | 0.1201 | 1.1429 | 1.0306 | 0 / 0 |

Warm compilation and all case preparation, external correctness/input checks, one explicit postwarm full-GC per case and formatting are outside the solve windows and recorded separately. The complete solve function itself—including record/diagnostic allocation, its setup and certification—is inside every window. Natural measured GC and outliers are retained. Two warm calls are the frozen schedule, not repeated tuning; no allocation threshold from old generic tests is applied. GC bytes/events are aggregate allocation traffic, potentially including native callbacks, not live memory/native malloc/free accounting. GC pressure and preparation/release costs must not be inferred absent from zero in-window GC.

## Actual work attribution

The following E counters include the whole imported main phase and its recovery. They exclude original init/auxiliary/cleanup bodies, which remain explicitly separately counted boundaries; original work/time is included in total windows. Candidate measured EC/KC/RC/legacy count fields match separately qualified counts in every measured sample (postcheck), while fixed primitive counters remain enabled inside all timed E phases. PC candidate/ratio/plan/flip/Devex counters and their physical arrays are read only by the independently qualified diagnostic clone at setup/exit; they are not copied/walked in timed phases. Cold captured PC values are retained in qualify-run/audit.json INSPECT records, not advertised as independently observed hidden native work.

| Case | E commits | Proposals | Rejected | FTRAN | BTRAN | BFRT F | Corrections | Refactor attempts | RHS capture | Output capture | Direction residual terms | Journal fields | Original cleanup |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| n16_sparse | 16 | 16 | 0 | 16 | 16 | 0 | 0 | 0 | 512 | 512 | 76 | 203 | 0 |
| n16_dense | 16 | 16 | 0 | 16 | 16 | 0 | 0 | 0 | 512 | 512 | 2312 | 592 | 0 |
| n64_sparse | 64 | 64 | 0 | 67 | 67 | 0 | 0 | 3 | 8576 | 8576 | 316 | 941 | 0 |
| n64_dense | 64 | 64 | 0 | 67 | 67 | 0 | 0 | 3 | 8576 | 8576 | 135200 | 8512 | 0 |
| mps_afiro_mps_p0 | 10 | 10 | 0 | 10 | 10 | 0 | 0 | 0 | 540 | 540 | 191 | 163 | 0 |
| mps_afiro_mps_p1 | 5 | 5 | 0 | 5 | 5 | 0 | 0 | 0 | 200 | 200 | 77 | 79 | 1 |
| mps_netlib_adlittle_mps_p0 | 80 | 80 | 0 | 83 | 83 | 0 | 0 | 3 | 9296 | 9296 | 7160 | 6206 | 0 |
| mps_netlib_adlittle_mps_p1 | 71 | 71 | 0 | 74 | 74 | 34 | 0 | 3 | 9646 | 9646 | 9793 | 4924 | 1 |
| mps_netlib_sc50a_mps_p0 | 26 | 26 | 0 | 27 | 27 | 0 | 0 | 1 | 2700 | 2700 | 1551 | 1198 | 0 |
| mps_netlib_sc50a_mps_p1 | 24 | 24 | 0 | 25 | 25 | 1 | 0 | 1 | 2142 | 2142 | 1948 | 1060 | 1 |
| mps_generated_degenerate-box_mps_p0 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 4 | 4 | 4 | 8 | 0 |
| mps_generated_degenerate-box_mps_p1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| mps_generated_phase-one_mps_p0 | 2 | 2 | 0 | 2 | 2 | 0 | 0 | 0 | 8 | 8 | 9 | 17 | 0 |
| mps_generated_phase-one_mps_p1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| mps_generated_scaled-diagonal_mps_p0 | 2 | 2 | 0 | 2 | 2 | 0 | 0 | 0 | 8 | 8 | 4 | 12 | 0 |
| mps_generated_scaled-diagonal_mps_p1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

Frequency/source attribution:

- Setup: existing full original copy/presolve/scaling/initial factor work; E additionally validates/copies owned numeric/basis/scaling state, builds one current-B factor and row index, and classifies invariants. phase_factor_builds/row_index_builds/entry_validated_values/invariant_rebuilds quantify named portions. Initial source owners overlap the imported graph until return. Task1's unchanged duplicate cold inverse-zeroing pass remains deferred.
- Each proposal/candidate: maintained leaving membership, full mathematical relevant-support Harris/BFRT and candidate validation, planned field/union enumeration and Devex terms. Cold PC counters expose their actual visits; no hidden dropped coefficient or tolerance change. These operations can dominate dense affected unions even though repeated global invariants were removed.
- Each solve: genuine native factor interface call, saved RHS capture and dense output/support capture, plus original complete BTRAN row residual. Kernel row_checks counts entries, not the native/original row-residual interior terms. Direction residual rows/terms and pricing entries are observed. Native private scaling/orientation/refinement/packing work is not completely instrumented; no source-derived bound is relabelled an observed count. Counters overlap by definition and must not be summed as a global native-work budget.
- Each commit/recovery: checked planned writes, journal entries/fields and classification of changed values; factor update and every retry/refactor/correction is counted. Refactor rebuilds can add actual primal/cost solves, residual checks and invariant rebuilds. The controller never credits a rejected proposal as a pivot. The qualified INFEASIBLE boundary exercises3 rejected proposals, no accepted pivot and one legacy continuation; its rejection/rebuild work is not treated as ordinary successful speed.
- Legacy and final answer: all setup/aux/primal cleanup/original retry/certification scans and solves are retained. Reference instrumentation uses existing diagnostics(kernel_timing=true) once per case; its full primal/iterations/refactors match public reference. Existing diagnostic spans are not complete backend entry counts or PREforward proof. Precision-boost/lp-refinement/repair/certification event fields are preserved, as are E original boundary notices. No whole-vector scan, native factor overlap, callback cost or full-state invariant is silently claimed zero.

## Retention and process memory

Cold diagnostic clone changes only its own nominal adapter type and two read-only snapshots, verified by exact inverse. It uses original controls and matches E results/phase counters. Actual Vector backing Memory capacities are captured with identity deduplication at setup/exit; fixed proposal/journal/invariant/support/receipt/recovery/index reserves do not shrink or grow. The payload measure covers selected vectors and excludes native/backend-private allocation, headers and other ownership overlap. Julia reachable graph bytes include model/factor references and have different scope; neither is live native heap, peak memory or proof of release. No engine graph is retained in the scalar output record. Record retained Julia size is measured after each primary E solve; solution/current input/check snapshot and current scalar records are the bounded diagnostic roots.

| Case | E setup / exit reachable graph B | Selected setup / exit vector payload B |
|---|---:|---:|
| n16_sparse | 24301 / 27021 | 12504 / 12504 |
| n16_dense | 31500 / 37708 | 16104 / 16104 |
| n64_sparse | 70741 / 87229 | 50040 / 50040 |
| n64_dense | 197748 / 326204 | 113544 / 113544 |
| mps_afiro_mps_p0 | 39081 / 42121 | 22931 / 22931 |
| mps_afiro_mps_p1 | 31565 / 32741 | 17268 / 17268 |
| mps_netlib_adlittle_mps_p0 | 89460 / 128508 | 59165 / 59165 |
| mps_netlib_adlittle_mps_p1 | 85191 / 117879 | 56438 / 56438 |
| mps_netlib_sc50a_mps_p0 | 60607 / 79351 | 39050 / 39050 |
| mps_netlib_sc50a_mps_p1 | 49585 / 66201 | 30549 / 30549 |
| mps_generated_degenerate-box_mps_p0 | 10900 / 11100 | 1572 / 1572 |
| mps_generated_phase-one_mps_p0 | 10901 / 11213 | 1572 / 1572 |
| mps_generated_scaled-diagonal_mps_p0 | 10835 / 11115 | 1540 / 1540 |

Process resource high-water includes compilation, both arms, native code/data and the diagnostic process. It is not an isolated per-arm memory comparison. Full sampled records, terminal memory and child getrusage maxRSS remain in each guard directory.

| Process | Inclusive seconds | Samples | Min available KiB | Max swap KiB | Child maxRSS KiB |
|---|---:|---:|---:|---:|---:|
| qualify | 86.648067240 | 86 | 19808524 | 0 | 2470800 |
| compare | 94.510277024 | 94 | 19773008 | 0 | 2507140 |

Both processes had separately admitted common1800s allowances including loading/warmup/output/audit/terminal checks, exact boot/start/command/group ANDsession closure, one Julia/BLAS1 and original memory guards. The initial622 qualification and642 comparison manifests pin actual source/project/runtime/input/guard paths; later audits/reviews are separate read-time bindings, not retroactive launch pins. No old numerical driver or auditor was rerun.

## Review, preservation and next decision

Initial607 admission rejected the zero-argument macro delimiter and incomplete parser ordinary-summary/case-ID gates before Julia. Actual pure offline RED exposed missing ordinary-count rejection; corrected code has27 separate synthetic parser checks. Initial607 sources/pins/review/RED remain under before-admission-review/admission-before-map; both actual numerical processes used separately accepted corrected manifests. Postcheck binds985 successful ordinary assertions and all named work/capacity/guard checks. Final whole-branch/result review must explicitly assess correctness, work and retention; no promotion is automatic.

Rulings: cold exact-inverse inspector and separately instrumented reference are qualification-only (cost if wrong: neutrality must fail admission, not be assumed); primary E intrinsic counters remain charged (cost: this is the actual current opt-in implementation, not a hypothetical stripped engine); runtime/fast0507 whole-model viability is unestablished (cost: no conclusion for those large models); no intended-policy comparison is claimed for an unimplemented E-DSE path (cost: only same-policy organizational evidence). Existing cold Task1 duplicate inverse-zeroing is deferred unchanged; no tuning/fix is smuggled into timing.

Task5 root README closure/review/publication bindings map only through continuation-map.json to README.md.before-Task6. Task5 source files remain current and byte-identical, so no source remapping is needed. All older maps/failed records/raw/reviews stay frozen. Exact local commit and the user-authorized normal push must preserve all work; master remains unchanged and CI disabled.
