# Basis update and postsolve cleanup investigation

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

The user explicitly requested coverage of every manager. FT and SS now use the same composed-permutation representation, retaining their addition operations; BG retains subtraction. SS histories that never permute rows skip the gather/scatter. All 32,421 focused factor checks passed. See the all-manager history logs for identity and coupled-column results. Before this extension, coupled histories at320 updates required BTRAN3.671ms (FT) and3.390ms (SS); the composed path removes that repeated permutation traffic. PFI has no such permutations and remains unchanged at this stage. Real-model history replay is still required to assess its coefficient-dependent cost.

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

Original-cost cleanup does not enable this repair. Restoring original costs can still expose an improving or unbounded direction, both covered by regression tests. Adaptive perturbation switches and active journals are excluded. A read-only review caught and verified fixes for mixed-policy gating and cancellation before the higher-precision fallback. Real runtime PFI validation is still pending.

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
