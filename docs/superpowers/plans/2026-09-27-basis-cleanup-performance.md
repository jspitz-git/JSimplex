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

- [ ] Establish old-history performance at 28,000 rows and 20/80/320 real identity column replacements; retain baseline runtime profile.
- [ ] Write differential tests against explicit old-history replay, including nonzero eliminations, rotations, both transposes, aliasing, copy, refactorization and scalar types. Assert pure permutations compile to zero numeric operations. Run the regression and observe the missing cache fail.
- [ ] Implement incremental logical-to-physical map and ordered eliminations; route only dense BG history traversal through it. Reset cache after successful factorization; copies own their cache.
- [ ] Run new regression plus factorization, triangular history/reset, hypersparse, atomicity and precision tests. Rerun benchmark and compare arithmetic bitwise with old replay.
- [ ] Commit verified feature and measurements.

### Task 1b: Batch pure row swaps during basis updates

Files: `src/triangular_factorization.jl`, new `test/bartels_golub_rotation_tests.jl`, `test/runtests.jl`.

Evidence: the baseline runtime profile attributes 14,250 of 26,502 samples to BG replacement, including repeated sparse row swaps. Existing compressed history only avoids storing these swaps; it still performs each swap on the upper factor.

Interface: private `_rotate_upper_rows!(upper, columns_by_row, first, last)` and `_last_pure_bartels_golub_swap(upper, first)`; existing update API unchanged.

- [ ] Test packed row rotation against literal row permutation and old adjacent swaps, including empty/singleton/dense columns and exact types; run before implementing.
- [ ] Detect consecutive strictly zero elimination entries, batch their row permutation, retain normal scalar elimination for all other cases. Preserve pivot selection and history ordering.
- [ ] Run factorization, sparse-history, ownership, precision and allocation regressions, and compare replacement time on the same history benchmark.
- [ ] Commit verified update feature.

### Task 1c: Extend the investigation to every basis manager

User scope clarification: include FT, SS and PFI because all exhibit slowdown.

Files: `src/triangular_rows.jl`, factor structs/copies/reset, `test/triangular_composed_rows_tests.jl`, shared replay helper, `reproduce/all-history-bench.jl`.

- [ ] Measure sparse identity and coupled-column histories for PFI, FT, SS and BG at20/80/320 updates.
- [ ] Run FT/SS cache and bitwise replay regressions before implementation; extend the composed cache using addition for FT/SS and subtraction for BG without coefficient sign conversion.
- [ ] Run shared factorization, allocation, precision, aliasing, sparse-history and copy regressions, then repeat all-manager measurements.
- [ ] Commit verified FT/SS feature. Capture real-model histories for PFI and all triangular managers to distinguish coefficient growth from redundant traversal.

### Task 2: Preserve useful postsolve bases

Files: `src/solver.jl`, new `test/postsolve_cleanup_performance_tests.jl`, `test/runtests.jl`, diagnostic scripts/report.

Interface: retain `_project_postsolve_basis!` and `cleanup_original` signatures, `SolveContext` budget, original-model feasibility/cost checks.

- [ ] Capture projection rejection on runtime or a small exact reproducer and document the failed condition. Add a test that exposes unnecessary fallback or dual reinitialization from an already primal-feasible original basis.
- [ ] Retain valid original-model primal bases without requiring coordinate identity; invoke primal cleanup for primal-feasible legacy bases using original costs. Keep dual path for infeasible bases and existing numerical fallback. Require original-model certification before OPTIMAL.
- [ ] Run cleanup/presolve, budget, primal/dual, precision/retry and original-result regression tests; include invalid targets, zero budgets, nonoptimal feasible targets and nonfinite inputs.
- [ ] Commit verified cleanup feature.

### Task 3: Real-model validation and review

Files: `diagnostics/simplex-basis-cleanup-performance/`.

- [ ] Run sequential matched interval20/80/320 progress comparisons on medium; run runtime dual with at least360s; report status, objective, primal feasibility, iterations, refactorizations, kernel time and peak RSS.
- [ ] Run both algorithms on external NetLib, MIPLib LP relaxations and mps examples, including fast0507 where practical; do not extrapolate incomplete runs to completion.
- [ ] Request an independent read-only whole-branch code review; address significant findings with regression tests.
- [ ] Commit final English report and leave worktree available for review.
