# Basis and Cleanup Performance Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan sequentially.

**Goal:** Remove redundant work in legacy Bartels–Golub solves and preserve useful original-model postsolve bases.

**Architecture:** Cache composed row permutations without changing numerical operations. Repair cleanup only after reproducing its rejection or feasibility loss, and retain original-model certification.

**Tech Stack:** Julia, SparseArrays/UMFPACK, Test, Profile, external MPS fixtures.

**Spec:** `docs/superpowers/specs/2026-09-27-basis-cleanup-performance.md`

## Global Constraints

English repository content; sequential work and numerical jobs; one Julia/BLAS thread; 24 GiB limit. Do not solve/factorize big.mps, largo.mps or AnyMod.mps (including aliases). Runtime completion attempts at least 360 seconds. Native precision; no adaptive redesign. Preserve worktrees and diagnostics. Commit each verified feature.

## Review Focus

- Cache scratch aliasing with rhs, destination, and existing factor work vectors.
- Copy/refactorization ownership after partially consumed or failed updates.
- Exact arithmetic, mixed scalar inputs, and ambient BigFloat precision.
- Cleanup accepting a feasible point without a valid original-cost terminal certificate.
- Shared iteration/time limits across projection, primal cleanup and fallback.

### Task 1: Compose dense Bartels–Golub row permutations

Files: `src/triangular_factorization.jl`, new `src/bartels_golub_rows.jl`, `src/JSimplex.jl`, new `test/bartels_golub_rows_tests.jl`, `test/runtests.jl`, diagnostic reproduction scripts.

Interface: retain `forward_solve!`, `transpose_solve!`, `replace_column!`, `refactorize!`, `copy_basis_factorization`; introduce private `BartelsGolubRowCache{T}` and `_sync_bartels_golub_rows!`.

- [x] Establish old-history performance at 28,000 rows and 20/80/320 real identity column replacements; retain baseline runtime profile.
- [x] Write differential tests against explicit old-history replay, including nonzero eliminations, rotations, both transposes, aliasing, copy, refactorization and scalar types. Assert pure permutations compile to zero numeric operations. Run the regression and observe the missing cache fail.
- [x] Implement incremental logical-to-physical map and ordered eliminations; route only dense BG history traversal through it. Reset cache after successful factorization; copies own their cache.
- [x] Run new regression plus factorization, triangular history/reset, hypersparse, atomicity and precision tests. Rerun benchmark and compare arithmetic bitwise with old replay.
- [x] Commit verified feature and measurements.

### Task 1b: Batch pure row swaps during basis updates

Files: `src/triangular_factorization.jl`, new `test/bartels_golub_rotation_tests.jl`, `test/runtests.jl`.

Evidence: the baseline runtime profile attributes 14,250 of 26,502 samples to BG replacement, including repeated sparse row swaps. Existing compressed history only avoids storing these swaps; it still performs each swap on the upper factor.

Interface: private `_rotate_upper_rows!(upper, columns_by_row, first, last)` and `_last_pure_bartels_golub_swap(upper, first)`; existing update API unchanged.

- [x] Test packed row rotation against literal row permutation and old adjacent swaps, including empty/singleton/dense columns and exact types; run before implementing.
- [x] Detect consecutive strictly zero elimination entries, batch their row permutation, retain normal scalar elimination for all other cases. Preserve pivot selection and history ordering.
- [x] Run factorization, sparse-history, ownership, precision and allocation regressions, and compare replacement time on the same history benchmark.
- [x] Commit verified update feature.

### Task 1c: Extend the investigation to every basis manager

User scope clarification: include FT, SS and PFI because all exhibit slowdown.

Files: `src/triangular_rows.jl`, factor structs/copies/reset, `test/triangular_composed_rows_tests.jl`, shared replay helper, `reproduce/all-history-bench.jl`.

- [x] Measure sparse identity and coupled-column histories for PFI, FT, SS and BG at20/80/320 updates.
- [x] Run FT/SS cache and bitwise replay regressions before implementation; extend the composed cache using addition for FT/SS and subtraction for BG without coefficient sign conversion.
- [x] Run shared factorization, allocation, precision, aliasing, sparse-history and copy regressions, then repeat all-manager measurements.
- [x] Commit verified FT/SS feature.
- [ ] Capture real-model histories for PFI and all triangular managers to distinguish coefficient growth from redundant traversal.

### Task 2: Preserve useful postsolve bases

Files: `src/solver.jl`, new `test/postsolve_cleanup_performance_tests.jl`, `test/runtests.jl`, diagnostic scripts/report.

Interface: retain `_project_postsolve_basis!` and `cleanup_original` signatures, `SolveContext` budget, original-model feasibility/cost checks.

- [x] Capture projection rejection on runtime or a small exact reproducer and document the failed condition. Add a test that exposes unnecessary fallback or dual reinitialization from an already primal-feasible original basis.
- [x] Retain valid original-model primal bases without requiring coordinate identity; invoke primal cleanup for primal-feasible legacy bases using original costs. Keep dual path for infeasible bases and existing numerical fallback. Require original-model certification before OPTIMAL.
- [x] Run cleanup/presolve, budget, primal/dual, precision/retry and original-result regression tests; include invalid targets, zero budgets, nonoptimal feasible targets and nonfinite inputs.
- [x] Commit verified cleanup feature (`2b17ff2`; 11,972 regression checks passed).

### Task 3: Real-model validation and review

Files: `diagnostics/simplex-basis-cleanup-performance/`.

- [ ] Run sequential matched interval20/80/320 progress comparisons on medium; run runtime dual with at least360s; report status, objective, primal feasibility, iterations, refactorizations, kernel time and peak RSS.
- [ ] Run both algorithms on external NetLib, MIPLib LP relaxations and mps examples, including fast0507 where practical; do not extrapolate incomplete runs to completion.
- [ ] Request an independent read-only whole-branch code review; address significant findings with regression tests.
- [ ] Commit final English report and leave worktree available for review.

### Task 4: Investigate the supplied numerical failures

- [ ] Reproduce the dual PFI failure near the feasibility threshold; distinguish inaccurate prices from genuinely shifted working costs. Retain the original tolerance and original-cost optimality certificate.
- [ ] Reproduce primal Bartels–Golub refactorization storms and the singular pivot; record the triggering checks before choosing a correction.
- [ ] Add focused failing regressions for confirmed causes, verify each correction in native precision and commit it separately.
- [ ] Repeat the matching runtime configurations with at least 360 seconds per completion attempt.

- [x] Implement native, bounded repair of marginal prices in an already perturbed legacy objective; retain tolerance and original-cost checks. Behavioral RED16/16; GREEN2,290/2,290; independent review findings resolved. Real runtime PFI validation remains pending.

### Task 4b: Preserve unrelated primal pricing weights during a retry

Evidence: local runtime primal BG spends322s in pricing but only1.37s in factorization over363s. A fixed-basis retry on16/256 duplicate improving columns performs20/260 FTRAN calls because both retry branches invalidate every cached steepest-edge weight.

- [x] Reproduce linear FTRAN growth with a small fault-injection test while checking the corrected pivot and primal solution.
- [x] For legacy retries, invalidate only the selected entering weight after refactorizing the unchanged basis; preserve the adaptive path and all residual/pivot guards.
- [x] Run primal guard, pricing, retry and original-certificate regressions (582/582 plus18/18 focused); repeat runtime diagnostic prefix (22.17s to6.88s) and obtain independent read-only review.
- [x] Commit the verified retry-pricing feature.

### Task 4c: Refresh history-dependent pivots below direction roundoff

Evidence: runtime iteration1079 accepts a pivot1.3094e-12 in a direction of norm1.4084e9. Both stored solves agree; fresh FTRAN instead gives9.4562e-13, below the existing1e-12 absolute cutoff. The new basis produces directions near3e21. A small stale-history example can give matching FTRAN/BTRAN pivots and a tiny row residual despite an exactly zero true pivot.

- [x] Run a failing small behavioral regression across native Float32/Float64 and all managers; retain a genuinely small pivot control.
- [x] Before changing a legacy basis, refresh an existing history once when the selected pivot is below `eps(T)*norm(direction,Inf)`. Preserve the independently feasible primal point, retry pricing, and apply existing guards to fresh solves. Do not hard-reject genuinely scaled pivots or alter adaptive policies.
- [x] Verify numerical guard regressions and runtime prefixes, obtain read-only review, then commit the feature.

Outcome:328/328 focused checks passed; prefix3000 completes in16.68s. Original1079 pivot avoided, but reduced phase still fails at1118. Continue investigating candidate choice.

### Task 4d: Prefer a stable entering alternative before weak pivots

Evidence: refreshing the catastrophic history pivot avoids the first collapse, but the reduced runtime phase continues accepting directions with relative pivots around1e-10 and later collapses again. A two-variable LP provides a stable bound flip behind a higher-scored degenerate weak pivot.

- [x] Reproduce selection of the weak pivot despite an immediately feasible stable alternative; retain an all-weak, necessary-pivot control.
- [x] In legacy Float32/Float64, first defer at most eight candidates whose relative pivot is below `sqrt(eps(T))`. Defer weaker candidates without changing the basis, then retry with the existing guards if no stable candidate exists. Bound both passes, preserve cancellation and rejection cleanup, and leave adaptive policies unchanged.
- [x] Run native numerical-guard regressions and a runtime diagnostic prefix; independently review and commit after verification.

Verified:519/519 checks; reviewer findings reproduced and fixed. Runtime5000 prefix35.89s, but reduced phase still singular at2999. Continue examining fresh tiny-pivot agreement.

### Task 4e: Require relative agreement for tiny primal pivots

The fresh iteration2999 basis gives FTRAN1.480635e-12 versus BTRAN8.514048e-13. The current `max(zero_tolerance,sqrt(eps(T))*abs(pivot))` accepts this42% discrepancy, and the next basis is singular. The absolute zero cutoff and the relative pivot-agreement test serve different purposes.

- [x] Reproduce acceptance of a25% tiny-pivot discrepancy across managers, signs and both hardware types; require exact and one-ULP agreements to remain valid.
- [x] Remove the absolute floor from relative FTRAN/BTRAN agreement, retain all existing zero-pivot cutoffs and native correction gates.
- [x] Run focused numerical guards and the matching runtime configuration; review and commit verified correction.

Verified guard correction:583/583 checks and independent review. Full360s-budget primal run terminates NUMERICAL_ERROR at236.44s/13,715 iterations after later feasibility loss. Primal stabilization remains incomplete.

### Task 4f: Inspect marginal primal point failures

The full primal run still fails on a marginal feasibility violation. Capture computed and predicted basic values at certification failure. Test whether a small native correction can be independently certified against unchanged bounds and rows. Do not change tolerances or publish an uncertified point. Implementation depends on snapshot evidence; not yet started.

### Task 1d: Skip unchanged identity upper columns in dense hardware solves

The captured early medium history shows approximately3.5ms triangular solves versus0.6ms PFI, even with a fresh basis. The triangular upper factor starts as identity but every dense solve visits all360,982 columns. Cache ascending indices of nonidentity columns for Float32/Float64; skip only stored singleton positive-unit diagonal columns. Preserve nonidentity arithmetic order and the original fallback for other scalar types. Invalidate before mutation independently of history count and sparse-cache presence; copies start dirty. Measure cache rebuilding as well as warm solves.

- [x] Add cache lifecycle and differential arithmetic regressions, including explicit stored zeros, signed zeros, copies and failed updates.
- [x] Implement the private active-column cache and verify all factor regressions.
- [x] Replay the same medium history, including first solves after updates, review and commit.
