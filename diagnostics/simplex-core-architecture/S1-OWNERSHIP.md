# S1 mutation ownership and validation dependencies

Inventory against production `fe839aa`, unchanged in implementation checkout at
this milestone. This is a static audit, not proof of a shipped optimization.
Symbols below are searchable source anchors; lengths are `m` rows, `n` structural
columns, `v = m+n` working variables and `k` factor updates.

## Ownership and aliases

`SimplexWorkspace` is mutable. Its vectors, `Basis`'s mutable arrays, the matrix
inside `LinearProblem`, factorization, scratch, pricing state and policy context
are reachable through diagnostics and internal APIs. Identity/length equality
alone does not establish unchanged contents. Public `Basis` construction copies
inputs; the `Val(:owned)` constructor transfers freshly allocated arrays.
Workspace costs/bounds are initially independent arrays, but later perturbation
journals and phase adoption deliberately replace their owners.

`_new_candidate_workspace` owns cached value vectors and scratch but initially
**shares the live factorization and problem**. `_copy_pivot_state!` copies all
working value arrays, basis arrays, pricing state/pool, sparse/hypersparse caches,
selected scratch and scalar counters. A token attached only to workspace identity
would be wrong after this copy. Candidate scratch is reused between attempts.

`_replace_pivot_column!` marks pending mutation *before* calling a backend because
triangular updates may mutate and then throw. `_discard_candidate!` can rebuild
the live factor from the old basis. `_transactional_simplex_step!` publishes
arrays and factor before emitting buffered completion events. `_StageObserver`
also forwards some events immediately, so a staged candidate is not a guarantee
that no user code ran. Keep failure work counts even when a candidate is discarded.

No new global generation scheme is selected. Existing counters have narrower
meanings: pricing basis/cost versions, hypersparse membership generations,
checkpoint phase generation and precision-transfer provenance are not generic
finite-state certificates.

## Mutation inventory

| State | Producers / mutations | Frequency and ownership implications |
| --- | --- | --- |
| Basis indices and states | `simplex.jl`: `_initialize_workspace_state`; `dual_simplex.jl`: `_apply_bound_flips!`, `_dual_iteration_unchecked!`, `_flip_bounds!`, `_auxiliary_workspace`, auxiliary handoff; `primal_simplex.jl`: pivot/flip branches, legacy phase-I construction and basis mapping; `primal_updates.jl`: `_apply_primal_flip!`, `apply_primal_pivot!` | Setup, every accepted step/flip, recovery and phase boundaries. Basic indices and statuses both matter; a flip changes status without changing factors. |
| Basis/factor pair | `simplex.jl`: `recompute!(refactorize=true)`; `simplex_pivot.jl`: `_replace_pivot_column!`, `_discard_candidate!`, transactional publication; `simplex_recovery.jl`: `_recovery_trial`, `_repair_basis!`, `_publish_recovery!`; `simplex_phase_one.jl`: `_phase_refactor!`, artificial removal, `_adopt_phase_basis!`; `solver.jl`: `_project_postsolve_basis!`, `cleanup_original` | Replacement/refactorization may invalidate before throwing. Direct projection replacements/refactors bypass pivot event counts. Solves mutate backend scratch even if mathematical factors are unchanged. Backend storage lifecycle belongs to S4. |
| Primal values | `simplex.jl`: `recompute!` writes nonbasic and solved basic values; dual updates/flips; primal flip/pivot/point reconstruction; `simplex_pivot.jl`: `_prepare_primal_candidate!`, `_copy_pivot_state!`; `legacy_primal_point.jl`: `_restore_legacy_primal_point!` (candidate, midpoint, rollback), `_try_native_primal_point_correction!`; phase artificial normalization; projection/cleanup/precision transfer | Each iteration/candidate and recovery. Successful reconstruction is not necessarily a bound-feasible or equation-feasible point. Restoration can mutate, check, then roll back in `finally`. A previous finite result cannot cover a new point merely because the basis matches. |
| Reduced costs | `simplex.jl`: `_recompute_reduced_costs!`; `dual_simplex.jl`: `update_duals!`, `_try_refine_dual_prices!`, small-pivot cost stabilization, backward-step correction; `legacy_dual_prices.jl`: native correction publication; `primal_updates.jl`: `_apply_reduced_costs!`, `apply_primal_pivot!`; perturbation and copies/adoption | Per step plus setup/recovery. Price refinement can preserve basis but replace prices. Basic entries are explicitly zeroed by several producers. |
| Objective costs | `simplex.jl`: initialization and `_restore_original_costs!`; dual feasibility/ratio/pivot stabilization and `update_duals!`; auxiliary workspaces; `simplex_perturbation.jl`: perturb, restore and retire journal; phase-I objective construction/adoption; precision transfer | Changes may occur within a normal dual step, not only at phase boundaries. `update_duals!` can shift costs to zero an infeasible reduced cost. A costs-once-per-phase cache is unsafe. |
| Lower/upper bounds | Initialization; dual auxiliary bounds; primal artificial-column tightening; `simplex_phase_one.jl`: phase setup/removal/adoption; `simplex_perturbation.jl`: owned bound expansion/restoration; recovery and precision copies; projection chooses nonbasic states from bounds | Active workspace bounds and original problem bounds are different certificate dependencies. Infinite bounds are valid; `_finite_workspace` intentionally does not scan them. |
| Pricing weights/reference/mode | `reset_devex!`; dual `update_dse!`, `update_devex!`, invalid-DSE fallback; primal lazy `_primal_steepest_weight!`, `_primal_update_steepest!`, Devex update; `simplex_pricing.jl`: prepare, validate, reject, reset, phase inheritance; recovery weight rebuild; precision transfer | Per candidate/iteration plus entry. Selection itself can build weights and perform solves. Dantzig omits the positive-weight condition; effective mode can change without replacing the vector. Primal and dual weight geometry differs. |
| Numeric scratch/support | RHS/unit/direction creation, FTRAN/BTRAN, row pricing, residual refinement, `_copy_pivot_state!`; `hypersparse_pipeline.jl`: `_pipeline_changed!`, `_reset_pipeline_support!`, `_rebuild_pipeline_support!`, `_copy_hypersparse_cache!`; `sparse_pricing.jl`: cache copy/invalidation | Borrowed arrays are valid only until their next producer. Exact cancellation/signed zero changes support. Membership rollover explicitly clears marks; no numerical-result reuse follows from that generation. |
| Whole state/model/precision | Phase adoption replaces costs/bounds/basis/primal/prices/weights/factor/scratch; recovery copies private trial; `simplex_precision.jl`: `_transfer_precision`, journal remapping; `simplex_precision_recovery.jl`: private higher-precision attempts; solver postsolve/scaling | Setup/phase/recovery. Dimension, ordering, matrix value changes, policy/tolerance and stored BigFloat precision invalidate applicable certificates. Matching dimensions or object IDs alone are insufficient. |

Additional ingress: external observers, arbitrary stop closures, custom loggers,
and aliases retained by those callbacks can write any reachable mutable array
or replace a workspace field. Bounds/matrix/weights can be modified indirectly,
not only by assignments containing the variable name `workspace`.

## Validation dependency table

| Check and consumers | Exact relevant inputs | Producers / invalidation | Work and reuse boundary |
| --- | --- | --- | --- |
| `_finite_workspace` in dual/primal entry, weight update, post-step, recovery and final internal solution | All entries of primal, reduced_costs, costs; all positive finite pricing_weights unless `_weight_pricing(ws,:dual) == :dantzig`; effective pricing state/options/fallback flags | Every producer of those arrays or mode; arbitrary callback/alias exposure; field replacement, resize or failed mutation | Up to 4v scalar visits, no solves/copies. Hardware Float32/64 loops visit every element of a reached vector; generic `all` may short-circuit. Does **not** validate basis, factors, bounds, model, scratch, feasibility or residuals. |
| `_validate_basis` before basis assembly/recompute | Matrix dimensions, basic_indices, states, scratch.basic_mask capacity | Pivot/status changes, phase/projection/copy/alias access | O(m+v), writes mask. Recompute with refactor checks twice but a logger runs between them; unconditional reuse is not justified. |
| `all(isfinite,rho/tableau_row/direction)` in pivot construction | Actual borrowed solve/price outputs | Solve, pricing, refinement, scratch aliases | O(m) / O(v); finite workspace does not include these buffers. Preserve checks. |
| `_dual_row_residual_ratio` | Current basis matrix entries/order, rho, selected unit row, numerical precision/roundoff model | Basis/model/rho/selected-row changes; corrected BTRAN | Checks B' rho = e_r. O(nnz(B)+m) work. Distinct from direction residual. |
| `_dual_direction_residual_ok!` | Basis entries/order, entering-column RHS, solved direction, selected pivot/row as used by function | New entering candidate, FTRAN/refinement, basis/model changes | Checks B d = a_j. Scratch writes invalidate support as required. A row residual cannot certify it. |
| `validate_pivot!` / solve quality | Both independent row and column estimates, RHS and basis, policy, pivot indices, native arithmetic precision | Any preceding estimate/candidate/basis mutation or retry | Two independent equations plus contractions. No replacement by a cached finite bit. |
| `_recomputed_basis_reliable` in recovery | Current B, actual basic primal, nonbasic values/status/bounds for RHS, rho and c_B, numerical policy | Recompute, point/cost/bound changes, checkpoint/model/phase mismatch | Basis assembly, copies/gathers and residuals. Cold/recovery work; matching a saved basis alone is insufficient. |
| Primal/dual infeasibility summaries | Primal vs active bounds; reduced costs vs basis states/fixed bounds and tolerances | Values, costs/prices, bounds, states, options | O(v). Finite values need not be feasible. |
| `_legacy_primal_reconstruction_feasible`, point certificate | Finite point, active bounds, A and row activity values, original bounds unless an owned perturbation journal applies, tolerance | Every reconstruction/candidate/midpoint/correction/rollback/bound or matrix change | Native equation residual may traverse nnz(A); current point certificate already shares row-bound work inside one call. |
| `_original_primal_feasible` and `_original_optimality_certified` | Original model/mapping, original bounds/objective, primal witness, dual witness/reduced-cost enclosures, tolerances | Postsolve/unscaling, working-to-original mapping, cleanup, perturbed costs/bounds, corrected witness | Final original-model obligation. Working-model certificates are not interchangeable. |
| Exact support validity | Owned values array, membership/index arrays, matrix row access if used | Every dense writer, array replacement/copy, matrix mutation or cache reset | Existing invalidation plus O(length) rebuild when invalid. No pruning; a finite-state cache would not certify support. |

## Four dual checks: why the number alone is misleading

On the ordinary successful HH/steepest-edge prefix path, source call sites
correspond to outer `_dual_optimize!`, `dual_iteration!` entry,
`update_dual_pricing_weights!`, and `_dual_after_iteration!`. The earlier aggregate
census reports calls, not per-call-site counts; confirm this attribution with a
focused diagnostic before claiming an exact saved scan count.

1. Outer entry runs after stop and pricing preparation. Before the inner entry
   check, the inner function calls stop and pricing preparation again. Those can
   invoke caller code, reset weights or change mode. Feasibility repair in the
   outer loop can also mutate values/prices and log/refactor.
2. Before weight validation, bound flips and dual/primal updates have modified
   checked data; DSE itself can overflow. Its solve/refinement gateway can emit
   events. This is fresh data, not the outer entry state.
3. After weight validation, factor replacement, basis/status changes, snapping the
   leaving primal to its bound, completion observers and optional recomputation
   intervene before `_dual_after_iteration!` checks. It cannot reuse the earlier
   whole-state Boolean unconditionally.
4. Before the next outer entry there are stagnation/pricing/perturbation hooks,
   a stop callback and preparation again. Do not carry a Boolean across steps.

`update_dual_pricing_weights!` already has an early successful return immediately
after its finite check with no intervening changes. This is proven local reuse
already in baseline, not a new optimization. Its recovery path must check again:
Devex fallback and the current Devex update can each create invalid state;
`test/dual_weight_validation_tests.jl` specifically covers both failures.

## Callback, exception and phase rules for a future contract

- `_diagnostic_event!`, `_recovery_observer!`, non-buffered `_StageObserver`, any
  arbitrary stop callback, and logger invocation end a reusable validation scope.
  Keeping an observer's alias permits later in-place mutation. Read-only observer
  *intent* does not make its type a read-only contract.
- Preserve callback exception identity/provenance; do not reclassify a caller's
  SingularException as numerical recovery. Failed writes must invalidate before
  mutation, not only on successful return.
- No token moves from live to candidate, checkpoint to recovery trial, or phase to
  phase by copying its integer generation. Re-establish locally after publication.
- Existing checkpoint phase generation increments with UInt arithmetic; it is not
  selected for the new contract. If a later stage chooses counters, define wrap
  reset and test it before deployment. The initial S1 proposal uses no counters.
- Aliased BigFloat values and precision-transfer paths need their own semantics;
  do not infer them from Float64 bitwise equality or silently promote arithmetic.

## Selected next experiment and cost review

A **lexically scoped** entry validation on a demonstrably read-only internal
clock deadline is a possible narrow experiment. Public arbitrary callbacks retain
full checking. First introduce/characterize an internal deadline object holding
only start time and limit, and prove that the prospective reuse interval contains
no observer/logger, auto-pricing transition or dual-feasibility repair. The current
closures have no such explicit type contract. See the [S1-A subplan](../../docs/superpowers/plans/2026-10-11-simplex-state-entry.md).

This inventory does not prove any *remaining* general `_finite_workspace` call
unnecessary. It does find a possible avoidable repeated scan in the restricted
owned-deadline path, conditional on that proof and testing. An O(v) content hash
or copies to detect alias mutation would replace rather than eliminate the scan;
a persistent per-array global generation framework adds mutation bookkeeping and
retention without solving untracked aliases. Neither is justified here.

No production change was made, so this milestone adds zero solver scans, solves,
allocations or retained memory. Guard hashing is setup/postprocessing, streams
files in 1 MiB chunks and retains O(number of pinned files) metadata. It is outside
numerical timings. Long-run logs must be streamed; broad source/snapshot pinning
has real I/O cost and must not be placed inside measured solver regions.
