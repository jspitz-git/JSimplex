# Legacy basis updates and postsolve cleanup performance

The user reports slow legacy dual simplex and original-model cleanup, and severe slowdown with longer Bartels–Golub update chains. Work in an isolated worktree, implement sequentially and commit verified features. Preserve native problem precision and numerical safeguards; do not redesign adaptive mode.

## Design

1. Compile Bartels–Golub row permutations into one logical-to-physical map. Store nonzero eliminations in physical coordinates in their original order. Dense FTRAN applies those eliminations then one gather; BTRAN scatters once then applies transposed eliminations in reverse order. Existing update records remain the source of truth for sparse solves. The cache is private, incrementally extended, reset after successful refactorization, and independently rebuilt by copied factors. Do not reassociate arithmetic or drop coefficients.
2. Reproduce rejection of postsolve projection before modifying cleanup. A reconstructed original-model feasible basis need not match every coordinate of the supplied point: a degenerate face can have multiple equivalent points. Feasibility plus ordinary original-cost optimization must remain required. Prefer primal optimization when the reconstructed basis is primal feasible, retaining dual cleanup and restored-basis fallback where appropriate. Preserve shared time and iteration budgets and terminal validation.
3. Compare real-model profiles and intervals 20/80/320, record both iteration progress and solution quality. A fixed-time incomplete run is not a completion speedup. Run external small models and relevant numerical, ownership, and allocation regressions. Preserve the user's raw log.

## Constraints

All repository text and commits in English. One numerical job at a time, one Julia/BLAS thread, 24 GiB virtual-memory ceiling. Never solve or factorize big.mps, largo.mps, AnyMod.mps or aliases. Runtime completion attempts receive at least 360 seconds. Preserve worktrees, local logs and diagnostics. No merge or push without a new instruction.

## Scope clarification

The user explicitly requested investigation of all basis managers. Apply permutation composition to FT and SS as well, retaining their addition arithmetic and independent within-update transpose operations. Profile PFI on real histories; do not attribute its coefficient-dependent product-form cost to permutations it does not perform.
