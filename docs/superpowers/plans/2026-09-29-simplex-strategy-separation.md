# Separate numerical kernels from simplex strategies

The user requested both separations identified in the primal audit: keep the
weak-pivot preference out of the fixed strategy, and stop selecting numerical
implementations implicitly through `simplex_strategy`.

## Design

- Both public strategies use the existing native numerical implementation.
  Native pivot checks, compensated residual corrections, point certification,
  and original-model checks remain available independently of strategy flags.
- `adaptive_pricing` controls the bounded weak-pivot preference. A rejected
  numerical candidate still uses bounded retry/refactorization in either strategy.
- Preserve the `NumericalPolicy` field layout. An explicit internal
  `numerical_profile=:checked` selects the previous alternative numerical stages;
  individual internal flags remain overridable. Strategy selection only supplies
  defaults for heuristics. This is not a new public solver option.
- Perturbations depend on their heuristic flag and stagnation monitoring. Their
  original-model cleanup is mandatory, including resumed journals after flags
  have been disabled. Cleanup may choose a feasible primal/dual method after
  restoring model data, without changing the numerical policy of that method.
- Preserve the native phase-I-to-II recomputation and shared work/time budgets.
  No default precision escalation, merge, push, or environment-file changes.

## Verification sequence

1. Reproduce the policy coupling and weak-pivot preference with small regressions.
2. Verify native and explicit checked policies independently, including all four
   basis managers and both floating hardware types for the pivot preference.
3. Exercise native safeguards, perturbation restoration, disabled-heuristic
   resumptions, callbacks, budgets, alternate numerical stages, and postsolve.
4. Run bounded external model checks and a five-minute native runtime run.
5. Review the final diff, record outcomes and limitations, and commit locally.

Run only one numerical Julia process at a time through the existing 8 GiB virtual
memory wrapper and the available-RAM/swap guard. Keep all previous worktrees and
untracked environment files.
