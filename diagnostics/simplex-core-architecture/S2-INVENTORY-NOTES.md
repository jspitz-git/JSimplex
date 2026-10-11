# S2 static prerequisite notes (not an accepted experiment)

Source inspected: architecture branch production tree identical to master beb161b.
No new numerical run or production change. S0 calibration/reference still pending.

- Existing apply_primal_flip!, apply_primal_pivot! and update_reduced_costs! already
  implement incremental arithmetic (primal_updates.jl). Reuse these kernels.
  Pivot price validation scans the full reduced-cost row before publication;
  flip/pivot value validation scans basis values before writes. Both update the
  existing pricing-basis generation. Do not duplicate these mutations or caches.
- _audit_primal_values! copies primal and reduced costs, calls recompute!, checks
  finite/recomputed-basis reliability, then compares native-precision predictions
  and the independent price residual. Its two full-vector copies and reconstruction
  are real costs. An experimental error estimator must save more than its own
  scans and required independent audits; fixed 20-step audits alone are not it.
- _primal_iteration_core! sends incremental_primal_pivots through staged retry.
  The native path instead uses _legacy_primal_iteration! and its bounded candidate
  search, one fresh-basis retry, direction/price recovery and weak-pivot handling.
- _legacy_primal_row_validation_enabled explicitly excludes incremental_primal,
  incremental_primal_pivots, pivot validation, solve refinement, recovery and
  staged workspaces. Enabling an existing flag therefore bypasses direction-price
  consistency, transpose-row validation and correlated-small-pivot safeguards.
  This is the first guard dependency to retain explicitly in an S2 design.
- _transactional_simplex_step! reconstructs ordinary primal candidates before
  publication. Incremental flips/pivots instead audit every20 iterations; a
  corrected audit may be published for incremental pivots if primal feasible.
  Full audit/certification obligations cannot be inferred from finite values.
- _can_preserve_primal_bound_value disables native bound-value retention on the
  same incremental/staged policies. Moving between routes changes reconstruction
  behavior and arithmetic, not just operation counts.
- Relevant historical regressions: legacy_primal_correlated_pivot_tests,
  legacy_primal_direction_price_tests, legacy_primal_point*_tests,
  primal_update_tests, native_primal_completion_tests and strategy separation.
  Precision/backend coverage and original certificates remain acceptance gates.

Next S2 planning task after S0: list exact numerical guards lost by the candidate
route and map how each remains enforced before proposing an error budget or
reconstruction controller. No default or public policy flag change is justified.

## Guard and work map for the subplan

Let m be the basis dimension and n the working variable count. These are static
cost bounds, not measured exclusive costs; a residual scan can reuse buffers.

| Existing protection | Entry/dependency | Work and experimental obligation |
| --- | --- | --- |
| Direction-price agreement | legacy_primal_pivot.jl `_legacy_primal_direction_price_ok`; objective costs, current prices, selected FTRAN and basis indices | O(m) ordered native arithmetic, no copy. Keep before accepting a selected candidate; finite values alone are insufficient. |
| Transpose-row residual and pivot agreement | `_legacy_primal_pivot_row_status!`; current factors/basis and leaving unit row | One BTRAN, residual check, pricing row, finite row checks; native correction on failed residual. Reuse the accepted row for DSE/Devex and price update, not a second BTRAN. |
| Correlated small-pivot sensitivity | `_legacy_primal_direction_pivot_ok!`; actual basis, selected column and compensated residual | O(m) maximum/finite scans; for a small pivot, basis residual and one correction FTRAN. Keep independent of ordinary forward/transpose agreement. |
| Update-history tiny-pivot retry | primal_simplex.jl `unresolved_pivot`; nonempty factor updates, relative column scale, fresh-basis flag | O(m) scale scan then bounded refactor/retry. Incremental bookkeeping must not suppress the history test. |
| Weak-candidate deferral and bounded search | primal_simplex.jl `defer_weak`; legacy candidate retry route | Candidate selection/retry behavior changes when switching to `_retry_simplex_step!`; preserve protections explicitly rather than treating the checked route as equivalent. |
| Bound-value and native point retention | legacy_primal_point/joint_point and `_can_preserve_primal_bound_value` | Policies and staged ownership disable current preservation paths. A failed audit/reconstruction must use a validated fallback, never publish the predicted point because it was finite. |
| Atomic incremental mutation | primal_updates.jl `apply_primal_flip!`, `apply_primal_pivot!` | Predict-before-write m scan, then m value updates; pivot also n price validation/update and factor update. Preserve alias/shape checks, basis generation and masks; do not add another copy of these operations. |
| Independent audit | `_audit_primal_values!` | Two n-sized copies, recompute, finite/basis-quality checks, value comparison and independent price residual. Account for this in total cost and invalidate the error budget after any correction. |
| Publication and interruptions | simplex_pivot.jl `_transactional_simplex_step!` | Candidate copies plus staged completion events; audit every20 for current incremental flags. The new controller must specify failure rollback and final stop semantics instead of inheriting an unexplained interval. |
| Final original certificate | `_internal_solution`, solver postsolve/cleanup/retry | Independent original feasibility and optimality remain mandatory; any local estimate is insufficient to certify final success. |

The hardware-specific row guard is enabled only for Float32/Float64 and excludes
both incremental flags and staged workspaces. Other supported precisions retain
their existing paths until their numerical contract is explicitly implemented
and tested. This inventory does not infer cross-precision safety from a Float64
benchmark. Before implementation, the subplan must specify how an experimental
path preserves each row above without simply enabling an existing policy flag.
