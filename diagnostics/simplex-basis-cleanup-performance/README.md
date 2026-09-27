# Basis update and postsolve cleanup investigation

This branch reduces dense basis-history overhead, keeps feasible postsolve bases, and fixes several native-precision retry defects. **Runtime primal Bartels–Golub remains unresolved:** the final attempt stagnates until its time limit. No tolerance relaxation or adaptive-policy redesign is introduced.

| Measurement | Result | Scope |
| --- | --- | --- |
| Runtime dual PFI | OPTIMAL in271.74s, original primal certificate passed | Completed run before the last two narrowly scoped features |
| PFI post-reduced work | About12s, including1195 postsolve primal pivots | Cleanup no longer dominates this run |
| Runtime dual BG | 1.73x faster at iteration21,617 with matching objective/infeasibility records | Both profiles stop at360s; no completion claim |
| Medium captured history | Warm triangular solves approximately3.5ms →1.1ms | Same320 early exchanges, before/after active upper cache; cold rebuilding also measured |
| Final runtime primal BG | TIME_LIMIT360s,42,461 iterations, stagnant phase I | Earlier marginal exit avoided; overall primal stability/performance still unsatisfactory |

Production tip: `01c6dd7`. See [review and verification](review.md) and detailed evidence below. Each verified feature has a separate commit in `fix/simplex-basis-cleanup-performance`.

Baseline: `1ffdbc2f6abf951c31c4ae5676a47dcc92924600`.

The user supplied `runtime-dual-user.log` from another machine. Its exact source revision and environment are unknown. Configuration: legacy dual simplex, steepest-edge pricing, native Bartels–Golub updates, refactorization interval 80, iteration limit 1,000,000, unlimited time, integrality relaxed.

Reduced solve: iteration 56004 at 2063.2132997 s, objective 51425691.762097925, zero reported primal infeasibility. Original cleanup starts at iteration 56008. Projection temporarily reaches zero primal infeasibility and the target objective, then the previous infeasible basis reappears. Final: OPTIMAL, iteration 119197, 9114.1910496 s. About 7051 seconds (77% of solve time) follow the reduced solve. The log alone does not identify why projection was rejected.

User log SHA-256: `6709b0ad00b027e636c5027d685ffa1abfe5e2c2cccfde55504c0a9aee0e923b`.

## Composed dense row histories

At 28,000 rows, replacing distinct identity columns generates actual pure-rotation histories. Before: FTRAN 171.8/415.2/890.4 microseconds and BTRAN 324.1/913.7/3133.9 microseconds for 20/80/320 updates. After composing permutations: FTRAN 142.7/134.6/150.7 microseconds and BTRAN 118.1/119.8/119.3 microseconds. These isolated identity-basis timings demonstrate removal of redundant permutation traversal, not whole-solver speedup. Arithmetic operations remain in their original order.

Validation: 22,888 checks passed across the new differential suite, factorization, triangular reuse/reset, hypersparse history and pivot atomicity tests. The new suite compares floating results with explicit old-history replay using `isequal`, checks exact arithmetic and residuals against actual updated matrices, aliases, independent copies, and changing dimensions.

Baseline runtime dual, interval80: TIME_LIMIT at360.002s,21,619 iterations,271 refactorizations, peak RSS2.12GiB. FTRAN30.44s, BTRAN33.41s, refactorization6.60s, pricing7.79s. Replacement appears in14,250 of26,502 profiler samples, motivating a separate pure-swap batching change. Compilation/startup outside solver time makes outer time413.02s.

## Batched BG factor updates

Pure adjacent row swaps now visit each affected packed column once and rotate its row indices/values as a group. The existing spike scratch marks unique affected columns; short runs do not scan the full matrix. Nonzero elimination arithmetic and pivot comparisons retain their scalar path. On the identity-history benchmark, per-update time fell from 640.7–748.0 to 399.8–484.0 microseconds.

The combined regression suite passed 30,797 checks, including 1,200 assertions comparing every updated packed upper factor and pivot-history record with the scalar implementation from baseline `1ffdbc2`.

## Other basis managers

The user explicitly requested coverage of every manager. FT and SS now use the same composed-permutation representation, retaining their addition operations; BG retains subtraction. SS histories that never permute rows skip the gather/scatter. All 32,421 focused factor checks passed. See the all-manager history logs for identity and coupled-column results. Before this extension, coupled histories at320 updates required BTRAN3.671ms (FT) and3.390ms (SS); the composed path removes that repeated permutation traffic. PFI has no such permutations and remains unchanged at this stage. Real-model early-history replay is reported below; later-fill behavior remains unmeasured.

## Additional user reports

The user confirmed that `runtime-primal-bg-user.log` used Bartels–Golub, while `runtime-dual-pfi-user.log` used PFI. Both otherwise used the configuration above. Source files were found under `/home/jspitz/logs/`.

PFI first reports dual feasibility loss at iteration 52,497 after 302.233 seconds. Its maximum dual violation is 1.0002033976466948e-7, just above the configured 1e-7 tolerance; primal infeasibility is still 1,224.439. The original-model retry also fails, ending at iteration 63,801 after 339.343 seconds. This failure precedes postsolve cleanup.

The primal BG log contains repeated consecutive-iteration refactorizations and a singular factorization at iteration 2,991. The available file ends during the original-model retry at iteration 3,151; the user reports that the run ultimately failed numerically, but that final status is absent from this snapshot.

`runtime-dual-pfi-user.log` SHA-256: `34e3a5c5c0f67a80a0e9185b05d8d5a70742beddd5246d94da2e0d66a4d063f7`.

`runtime-primal-bg-user.log` SHA-256: `a3ce10a1d323c46675c3c81349b330867eec2a21a580493e50bc17a172f9079b`.

## Feasible postsolve cleanup

A small regression reproduces rejection of a feasible basis solely because one objective-neutral coordinate differs from the supplied target. Legacy projection now accepts an independently feasible original-model basis and runs primal optimization with original costs; adaptive projection retains its coordinate rule. Terminal original-model primal and optimality certificates remain required.

The isolated runtime cleanup experiment uses JSimplex presolve/postsolve with a reduced solution and basis supplied by local HiGHS 1.15.0. HiGHS reported dropping one coefficient of magnitude 1.78e-16. The projected original point was independently certified by JSimplex, so this experiment measures cleanup behavior, not end-to-end solver performance. The same serialized original-model target/basis was used for both runs.

Before: ITERATION_LIMIT after 5,000 cleanup pivots, 67 refactorizations, 68.97 seconds. Dual initialization abandoned primal feasibility. After: OPTIMAL after 1,185 pivots, 19 refactorizations, 33.51 seconds including compilation; objective 51,425,691.7621028, original primal certificate passed. See `cleanup-before.toml` and `cleanup-after.toml`. External model snapshots remain local and are not committed.

Independent read-only review covered factor histories and cleanup. It found a caller-logger exception provenance issue in the new cleanup message; a regression reproduced both swallowed numerical exceptions and the guard fixed them. The reviewer confirmed the fix. The numerical failures reported in the newer PFI/primal logs remain separate investigations.

Cleanup validation: 11,972/11,972 checks passed across workspace, presolve, solver, retry, primal/dual, phase-I budgets, precision recovery, BigFloat, numeric-type and benchmark regressions. This functional suite used Julia `-O1` to reduce LLVM compilation time; performance experiments use default optimization.

## Local primal BG reproduction

With the six-minute budget, the source at cleanup commit `2b17ff2` reached TIME_LIMIT after 363.25 solver seconds: 6,322 completed iterations and 170 refactorizations. The reduced phase failed near iteration 1,129 and the original-model retry remained in phase I. Peak RSS was about 1.88 GiB.

Kernel diagnostics attributed 322.32 seconds to pricing, 286.25 to FTRAN, 6.36 to BTRAN and only 1.37 to factorization. These timings overlap: pricing invokes FTRAN for steepest-edge weights. Residual-triggered retries invalidate every cached weight even though refactorization retains the same basis. There were 89 residual-triggered refactorizations and 366 rejected candidates. This supports investigating both the unsafe pivots that precede the failures and the unnecessary global weight rebuild after a retry. It does not justify weakening residual checks.

The supplied Windows primal log has 438 adjacent progress records separated by exactly one iteration, totaling 1,316.70 seconds. Their median is 2.995 seconds per iteration, versus 0.00915 seconds per iteration in the 80-iteration intervals. These are descriptive log statistics, not matched machine benchmarks.

## Native repair of marginal working prices

A small LP reproduced the reported boundary failure in both hardware floating types, all four basis managers and both bound orientations. The new helper makes a bounded, representable adjustment to nonbasic costs of an already perturbed legacy working objective after fresh factorization. It never changes original coefficients or tolerances. Each offending price must be within twice the dual tolerance; each individual repair is capped at four tolerances, with a feasible margin. This is not a cumulative perturbation bound.

Original-cost cleanup does not enable this repair. Restoring original costs can still expose an improving or unbounded direction, both covered by regression tests. Adaptive perturbation switches and active journals are excluded. A read-only review caught and verified fixes for mixed-policy gating and cancellation before the higher-precision fallback. The completed local runtime PFI validation is reported below; the exact other-machine failure is not claimed as reproduced.

Native-price validation: 2,290/2,290 checks passed, including old dual-simplex behavior, hardware-type exclusions, correction cycles, adaptive perturbation isolation and postsolve original-cost certificates. The behavioral reproducer failed in all 16 configurations before implementation; mixed-policy and cancellation review regressions failed before their guards were added.

## Primal retry pricing

A controlled stale-factor regression keeps the true basis unchanged and forces a single numerical retry. With16 and256 improving columns, the previous retry performed20 and260 FTRAN calls. Preserving unrelated steepest-edge estimates reduces both cases to5 calls while retaining the corrected primal solution and exactly one refactorization. The selected entering weight is refreshed; adaptive retry invalidation and numerical pivot checks retain their previous behavior.

A separate1200-iteration runtime diagnostic prefix found accepted relative pivots of4.36e-9,2.49e-9 and7.10e-10 at iterations1076–1078. Rebuilding those preceding bases reproduces their directions. By iteration1079, even a fresh factorization has an unacceptable transpose residual. This points to basis conditioning rather than merely inaccurate accumulated updates. The phase-I objective is still about605,732, so this is not an already feasible phase-I problem continuing unnecessarily. These observations are diagnostic evidence, not yet a stabilization fix.

Retry-pricing validation:582/582 broader primal, numerical guard, candidate retry and cleanup checks passed with `-O1`. The final focused suite passed18/18, including a non-unit basis with deliberately inaccurate positive pricing estimates and original-model feasibility/optimality checks.

The matching1200-iteration diagnostic prefix decreased from22.17s to6.88s after retaining unrelated weights; pricing fell from15.32s to0.208s. Trajectories diverge after the first retry, so these are bounded-prefix measurements, not time-to-optimum results. The expanded trace caught the damaging pivot at iteration1079:1.3094e-12 against a direction norm1.4084e9 (relative9.30e-22). Subsequent directions grow to about3e21. The original absolute zero cutoff alone admits this pivot.

## Correlated roundoff in primal pivot histories

At the damaging runtime pivot, the stored FTRAN and BTRAN pivots agree to about1e-27, despite a tiny true coefficient. A new factorization gives9.4562e-13 from FTRAN and4.5397e-13 from BTRAN. The stored row residual test alone therefore cannot detect this history error.

The legacy Float32/Float64 path now refreshes a nonempty history once when the pivot is below `eps(T)*norm(direction,Inf)`, preserving the independently feasible primal point and retrying through existing checks. It does not introduce a new hard pivot cutoff: a genuinely small pivot may proceed after fresh solves. Adaptive policies and other scalar types retain their previous paths.

The small injected-history reproducer previously accepted a false pivot and reported internal OPTIMAL at x=0 for an LP whose optimum is x=1. This demonstrates a wrong internal termination, not an incorrectly certified result from the public solver. The regression failed24 assertions before the fix. The fix and genuine-small-pivot controls pass56/56 checks across four managers and both hardware types. Independent read-only review found no blocker; repeated refactorizations on strongly scaled problems remain a performance risk to measure.

Roundoff-refresh validation:328/328 focused guard, retry, native correction, point-preservation and Harris checks passed. A3000-iteration runtime prefix takes16.68s with46 refactorizations and avoids the original1079 false pivot. However, the reduced phase still fails at1118 and retries the original model; this is a verified local correction, not a complete runtime primal stabilization result.

## Bounded preference for stable primal candidates

The legacy hardware-float path now defers up to eight candidates whose selected pivot is at most `sqrt(eps(T))*norm(direction,Inf)`, looking for a stable pivot or bound flip. If none is found within that bound, it retries under the ordinary numerical checks. Weak but genuine required pivots remain available. All candidate searches retain cancellation and rejection cleanup.

Read-only review exposed two issues in the initial design: unbounded work when all improving candidates are weak, and lost refresh bookkeeping on recursive pricing exhaustion. Both were reproduced (three failing assertions) and fixed. The final focused suite passes519/519. The earlier behavioral test had48 expected failures and16 test-harness errors from accessing a missing terminal result; that assertion was corrected to a safe predicate.

The unbounded diagnostic prototype was interrupted after3360 recorded iterations (about120 solver seconds); its log remains local. With the eight-candidate cap, a5000-iteration prefix finishes in35.89s. The reduced model still encounters a singular basis at iteration2999 and retries the original model. This is not a claim that runtime primal now completes successfully; the remaining tiny-pivot acceptance needs investigation.

## Relative agreement at tiny pivots

The fresh basis at iteration2999 returns FTRAN1.4806350483260688e-12 and BTRAN8.514047651924245e-13. The old absolute agreement floor1e-12 accepts this42.5% discrepancy. Agreement now uses only the symmetric relative scale `sqrt(eps(T))*max(abs(forward),abs(transpose))`; absolute pivot eligibility remains a separate check. Sixteen native-type/manager/sign regressions failed before the change; exact and one-ULP agreement controls pass. The combined guard suite passes583/583, with no read-only review blocker.

The subsequent full runtime primal BG attempt requested360s but terminated NUMERICAL_ERROR at236.44s,13,715 iterations and1,389 refactorizations. The original singular pivot is avoided, but the reduced phase later loses feasibility at4151 and the original-model retry also loses feasibility. This is an unresolved primal limitation, not a successful completion. Pricing totals34.66s, FTRAN31.08s, BTRAN15.17s and refactorization5.66s; these overlapping kernels must not be summed. Peak RSS is about1.88GiB;27.5GB of cumulative allocations is not simultaneous memory use. Different trajectories prevent interpreting the iteration count as matched progress toward the optimum.

## Completed runtime dual PFI run

With the requested legacy/steepest-edge/native configuration and interval80, runtime finished OPTIMAL in271.74s,54,018 iterations and291 refactorizations. The original-model primal certificate passed; objective51,425,691.76210421. The requested time budget was900s. Peak RSS was1.92GiB;13.60GB cumulative allocations are not simultaneous memory use.

The last reduced progress record is at52819/259.724s, followed by four pivots after restoring original costs. Postsolve projects361 basis columns, then primal cleanup needs1195 pivots. Final time271.741s is about12.02s after that last reduced record (including the four cost-restoration pivots and postsolve overhead). The post-projection cleanup itself spans about10.45s. This full-model result confirms that cleanup no longer dominates this run. The other machine's exact environment remains unknown; a local completed run does not by itself prove cross-machine reproducibility of the marginal-price failure.

## Matched runtime dual Bartels–Golub profile

Using the same six-minute profiling script as the baseline, the updated solver reaches30,243 iterations versus21,619 before (about40% more). Both runs end TIME_LIMIT; neither number is a completed solve time. All271 common progress records have identical objective and primal infeasibility strings. At the last common record, iteration21,617 takes208.063s versus359.968s before:1.73x faster at matched numerical progress.

The updated run reaches a later, more expensive part of the trajectory; its cumulative kernel times and2.94GiB process peak RSS should not be compared as if both runs performed the same work. See `runtime-bg-matched-progress.json`, both full logs, and the before/after profiles.


## Medium history and interval diagnostics

The captured basis at iteration2000 has360,982 rows and186,497 structural columns. Replaying the next320 actual exchanges through all four managers gives zero relative FTRAN/BTRAN residuals on the tested all-ones RHS. At320 updates, warmed PFI solves take approximately0.64/0.69ms, FT3.49/3.50ms, SS3.66/3.67ms and BG3.73/3.80ms. Even fresh triangular factors take roughly3ms, indicating overhead independent of accumulated numerical eliminations. This early history mostly consists of pure permutations; it does not represent later fill or prove that arbitrary long histories are cheap.

The separate60-second interval runs are throughput diagnostics, not completion attempts. Their recorded `working_*` values are inspected after the solver returns; auxiliary cleanup may already have restored original bounds and costs. Consequently those values must not be interpreted as live auxiliary-phase progress or a feasibility certificate. The phase label is the last observed phase. `process_peak_rss` is cumulative across the sequential process, not an independent per-case peak. Single short timings include startup and GC variability. Detailed counts and kernels remain useful for comparison, with these limits.


Observed medium iterations within each60-second solver budget, before the active-upper optimization (`707fbb6`):

| Manager | Interval20 | Interval80 | Interval320 |
| --- | ---: | ---: | ---: |
| PFI | 3822 | 4294 | 4480 |
| Bartels–Golub | 1238 | 623 | 1169 |
| Forrest–Tomlin | 1194 | 1028 | 852 |
| Suhl–Suhl | 868 | 883 | 904 |

These single runs do not establish a monotonic law; in particular the BG interval80 observation is anomalously slow. They confirm remaining whole-iteration overhead beyond warmed history application. No completed medium optimum is claimed.

## Active identity upper columns

Commit `3efba07` removes repeated scans of identity upper columns from dense hardware-type solves. On the same320-exchange medium history, warmed triangular FTRAN/BTRAN decrease from approximately3.5ms to1.1ms. Cumulative first FTRANs, including cache reconstruction after each exchange, decrease from roughly1.3s to1.1–1.2s. See [the detailed comparison](active-upper-results.md). All33,117 factor checks pass; no independent review blocker remains. Whole-solver results above predate this final factor optimization.

## Missing preservation in the absolute-small-pivot retry

The final-factor5000-iteration diagnostic prefix again loses reduced-model feasibility at4151. The computed point violates a bound by1.0001618054280663e-7; the retained candidate passes working bounds, the unperturbed phase-I problem rows and row consistency. This is a phase-I certificate, not feasibility of the original runtime input (the artificial objective is still positive). Diagnostic clipping to the exact bound fails row certification, so no general clipping repair is introduced.

The absolute-small-pivot retry lacked the certified-point preservation already present in the residual retry. A small stale-factor regression reproduces this omission across all four managers and both hardware types (40 failed assertions). The fix captures the current point before refactorization and offers it to the existing independently certified restoration helper. Adaptive exclusions, fresh pivot checks and cancellation remain unchanged. This fixes a missing branch; it does not by itself resolve the preceding degenerate stagnation.

The final focused guard suite passes623/623 checks with `-O1`; independent read-only review found no blocker. Full-model follow-up is recorded below.

## Reproduction

Run from this worktree, with one Julia thread and one BLAS thread. Local runs used Julia1.13.0 on aarch64 Linux and a24GiB virtual-memory ceiling. Numerical jobs were sequential. Functional suites used `-O1`; performance scripts used default optimization. `big.mps`, `largo.mps`, `AnyMod.mps` and their canonical-path aliases were excluded.

```bash
export JULIA_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
julia --project=. diagnostics/simplex-basis-cleanup-performance/reproduce/runtime-debug.jl /home/jspitz/mps/runtime.mps dual pfi 900 /tmp/runtime-dual-pfi.toml
julia --project=. diagnostics/simplex-basis-cleanup-performance/reproduce/runtime-debug.jl /home/jspitz/mps/runtime.mps primal bartels_golub 360 /tmp/runtime-primal-bg.toml
julia --project=. diagnostics/simplex-basis-cleanup-performance/reproduce/interval-comparison.jl /home/jspitz/mps/medium.mps 60 /tmp/medium-intervals.toml
python3 diagnostics/simplex-basis-cleanup-performance/reproduce/prepare-corpus.py /tmp/jsimplex-corpus
JSIMPLEX_CORPUS_MANIFEST=/tmp/jsimplex-corpus/quick-inputs.toml JSIMPLEX_CORPUS_OUTPUT=/tmp/quick-corpus.toml julia -O1 --project=. diagnostics/simplex-basis-cleanup-performance/reproduce/quick-corpus.jl
```

The corpus manifest hashes the decompressed inputs and reuses recorded independent reference objectives from the [previous external corpus](../simplex-legacy-stability/quick-corpus.json) and the [HiGHS reference](../simplex-performance/highs-reference.json). Model files are not included. Its timings are functional-run observations, not consistently warmed performance comparisons. A diagnostic prefix can be requested with `JSIMPLEX_DEBUG_ITERATIONS=5000`; it must not be reported as a completion attempt.


## Final runtime primal follow-up

At production tip `01c6dd7`, the full360-second attempt ends TIME_LIMIT after42,461 iterations and1,925 refactorizations. The earlier reduced-model failure at4151 no longer aborts the solve, but the phase-I objective remains around1,419,148.32. From roughly4365 onward, the reported dual infeasibility is approximately8.08e21 and the run stagnates. This is not a successful primal stabilization result, and its higher iteration count must not be presented as better progress toward the optimum.

The run records38,100 point restorations certified for the working phase-I problem and92,102 rejected candidates. Later scheduled refactorizations generally occur every80 iterations, following an earlier storm of1,412 pivot-triggered refactorizations. Pricing totals44.54s, FTRAN27.80s, BTRAN14.70s and refactorization6.96s; timings overlap. Peak RSS is about1.90GiB, while104.73GB is cumulative allocation traffic, not resident memory. Original-problem OPTIMAL certification was never reached.

Further primal work must address degenerate candidate selection and ill-conditioned bases, rather than just preventing the marginal feasibility exit. This branch retains the independently verified missing-path correction but makes no claim of HiGHS/Clp parity or a completed medium solve.


## Final external validation

Production tip `01c6dd7` passes all72 external LP solves: nine hash-matched inputs, both legacy algorithms and all four basis managers. Every case returns OPTIMAL, matches its independent reference objective and passes original-input primal certification. The225 corpus assertions and71 final cleanup assertions all pass (`-O1`). Cases: NetLib afiro/adlittle/kb2/sc50a; MIPLib pk1/flugpl/stein9inf/markshare_4_0 as LP relaxations; mps fast0507.

See `final-corpus.toml` and `final-functional.log`. Functional fast0507 observations are approximately12–14s dual and15–17s primal under `-O1`; these are not a warmed default-optimization benchmark or a claim of subsecond performance. All numerical jobs have completed. The11 production feature commits and this diagnostic archive remain in the isolated worktree; master is unchanged.
