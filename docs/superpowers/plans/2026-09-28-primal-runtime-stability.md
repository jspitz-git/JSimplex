# Primal Runtime Stability Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans sequentially, with one final independent review.

**Goal:** Prevent the reproduced legacy primal singular-basis failure and validate
runtime.mps with all four managers.

**Architecture:** Investigate recorded pivots before changing acceptance. The first
confirmed defect is correlated FTRAN/BTRAN error on a fresh native factor: an
apparently agreed pivot is actually zero. For weak hardware-float candidates,
probe pivot accuracy with one native compensated residual correction before
committing the basis exchange. Preserve existing retry/rejection machinery.

**Tech Stack:** Julia 1.13, native Float32/Float64 arithmetic, existing compensated
residual kernels and all basis managers.

**Spec:** User request and the evidence in diagnostics/primal-runtime-stability.

## Global Constraints

- Legacy primal only; adaptive behavior and tolerances unchanged.
- Higher precision only in independent diagnostic references, not the new check.
- One Julia job; 8 GiB virtual memory and available-memory/swap watchdog.
- Never solve or factorize big.mps, largo.mps or AnyMod.mps.
- English repository artifacts. Verified commits in the isolated worktree.
- Previous optimization series merged/pushed at 8c694d0; this fix stays separate.

## Review Focus

- Correlated solve errors must not create a singular basis.
- A genuinely small pivot in a scaled model must remain usable.
- Cancellation/nonfinite correction must leave the live basis unchanged.
- Generic/exact arithmetic and adaptive dispatch must retain their behavior.
- Whole LP validation must include original feasibility, not just iteration progress.

## Task 1: Guard correlated weak pivots

Files: src/legacy_primal_pivot.jl, src/primal_simplex.jl,
test/legacy_primal_correlated_pivot_tests.jl, test/runtests.jl.

Consumes existing _compensated_solve_quality!, _pivot_quality_buffers,
_ordinary_forward_solve!, and the existing legacy row-check/retry contract.
Produces an optional direction-aware row validation, keeping old callers valid.

- [x] Run the two-row correlated-error regression on baseline; verify rejection
      and unchanged basis assertions fail. Preserve the scaled genuine-pivot case.
- [x] For a weak pivot, compute a compensated residual against the actual basis,
      solve one correction in the same type, and reject when the selected pivot
      changes materially. Do not publish the correction or mutate the live basis.
- [x] Connect rejection to existing bounded candidate retry; cover cancellation,
      and unchanged non-legacy/generic paths. Nonfinite correction rejection has
      static review only; a dedicated fault-injection regression is deferred.
- [x] Run focused primal and factor tests, then replay the captured failing pivot.
- [x] Commit after independent checks show the root defect is prevented.

## Task 2: Keep safe Harris candidates during tolerated bound snaps

Files: src/primal_simplex.jl, test/primal_bound_snap_tests.jl.

The captured state exposed a second defect: summing individually tolerated
violations rejects large safe pivots. Match the existing legacy per-bound
feasibility contract without changing adaptive behavior.

- [x] Reproduce with structural basic variables just outside their bounds:
      48 failing assertions before the correction.
- [x] Use the maximum individual violation for legacy bound-snap validation.
- [x] Preserve unsafe-snap rejection, cover both directions and Float32/Float64,
      and replay the recorded runtime point with all four managers.
- [x] Commit after 1,162 focused assertions and 32 captured-state checks pass.

## Task 3: Validate independent LP trajectories

Files: diagnostics/primal-runtime-stability/reproduce and results.

- [x] Reproduce and compare runtime primal for PFI/FT/SS/BG sequentially.
- [x] If another failure appears, record a separate hypothesis and regression
      before changing behavior; do not stack speculative stabilization rules.
- [x] Run the external NetLib/MIPLib/mps corpus and existing relevant regressions.
- [x] Run resource-bounded project checks; report any compilation limitation.
- [x] Obtain independent whole-branch review and commit reproducible evidence.

## Remaining limitation

The two local defects are verified, but full runtime convergence is not achieved.
All four bounded runs stay in phase I. SS replay confirms a two-basis cycle and
a separate discrepancy between stored reduced prices and direction-implied costs.
Investigate that discrepancy in a separate sequential worktree; do not describe
this branch as a complete runtime stability fix. Native-only checks remain the
constraint, with adaptive behavior unchanged.
