# S6-AD: dual recovery cause, ownership and work contract

Source/exact-offline analysis at diagnostic51ac324/master3c0af5c. No Julia, factor,
workspace, certificate or solver call. Production and tests unchanged. New offline
script `reproduce/dual_causal_contract.py` passes27 checks and writes immutable
`results/S6-AD/exact-contract.json`. This is a conditional design proof, not numerical
qualification or an explanation of the historical x64 path. Independent review pending.

## Reconciled evidence and original coverage

Current dual test SHA matches saved S6-H. Eleven relevant source/test files match
actual master. Saved H20 control/observed pairs have equal recorded fields, row2,
entering5, accepted direction residual and disagreeing pivots. H's separate probes
are not a capture of hidden runtime candidate arithmetic. Both historical maps
contain48 failures: expected ordinary callback wrapper4, numerical callback wrapper4,
cancelled status4, rejection count16, selected state16, after-refresh status4.
The16 state mismatches differ only by retained refactors1 versus2; no arithmetic
cause follows from this. H/I/J evidence is reused without executing old drivers.

| Current test group | Assertions / cases | Preservation route |
| --- | --- | --- |
| Exact duplicate safety | 48 / eight legacy-adaptive manager cases | Keep native helper and entire public test byte-identical |
| Bounded unpublished recovery | 80 / four modes x four managers | Keep public dual_iteration!, policies, callbacks, five original assertions; future fixture must prove zero new refactors before rejection |
| Consistent small pivot | 60 / ten scalar-manager cases | Keep all direct native public coverage byte-identical |
| Cancellation after refresh | 28 / four managers | Keep public entry and seven original assertions; distinguish one retry refactor from ordinary repair and rollback |

S6-J remains REJECTED. Calling retry explicitly changes public coverage and leaves
ordinary numerical refactors possible. Neither retained original oracle nor local
GREEN292/292 qualified its zero/exact-one work assumption. No count relaxation.

## Branch, ownership and work map

Locations refer to current files pinned in exact-contract.json.

| Location | Trigger and action | State / work consequence |
| --- | --- | --- |
| dual_simplex.jl:693-716 | Public entry wraps stop, initial stop, auto-pricing/finite guards | Exact stop exception provenance preserved; numerical exceptions handled separately |
| simplex_pivot.jl:422 | Native policy has pivot_validation=recovery=false | Starts ordinary unchecked kernel; an arbitrary NUMERICAL_ERROR here does NOT automatically emit pivot_rejected |
| dual_simplex.jl:1139-1194 | Pricing, unit BTRAN, row quality; residual ratio >1 tries native correction, then refactor_residual unless already refreshed | Ordinary refactor independent of retry max_recovery_rounds; each recursive attempt repeats pricing/BTRAN |
| dual_simplex.jl:1212-1255 | Harris ratio; no candidate | Below-cutoff eligible or stable uncertain returns NUMERICAL_ERROR; otherwise one ordinary refactor before infeasibility checks when not refreshed |
| dual_simplex.jl:1259-1342 | Prepared FTRAN, direction residual, correction, optional refactor or stronger refinement | Ordinary repair can precede the disagreement boundary and ruin zero-work oracle |
| dual_simplex.jl:1346-1371 | Row/column pivot disagreement; try native tableau | Nonstaged native-tableau helper returns false without correction; enters transactional retry through public path. Staged failure throws _PivotRejection(:refresh) |
| legacy_dual_correction.jl:107-181 | Staged, empty updates, native policy, max_refinements>0; corrected row and ratio reselection | Real correction BTRAN; no eligible corrected candidate returns false. It need not publish correction event or mutate live numerical arrays |
| dual_simplex.jl:1381-1440 | Tiny pivot rebuild, stabilization, flips and factor update after agreement | Must be unreachable for proposed rejection subject; no fake decisions to bypass these safeguards |
| simplex_pivot.jl:45-124 | Candidate copies owned numerical vectors and basis state into reusable storage | Factor object is initially SHARED, not copy_basis_factorization. Refactor policy state and live counts/timers shared; caches/scratch selectively copied |
| simplex_pivot.jl:214-275 | Transaction performs, discards terminal/error, or commits | Commit copies state before completion callbacks; pending factor update marks potential shared-factor mutation |
| simplex_pivot.jl:178-210 | Discard retains max refactor count; pending update triggers callback-free old-basis refactor | Zero-count guarantee requires no factor update. Failure does not refund work |
| simplex_pivot.jl:306-412 | Bounded retry owns rejected sets and candidate refresh | Rejection event on live state; cancellation at next attempt, observer wrapper propagates; finally clears both sets. Default refresh produces refactor_pivot, independently of ordinary repairs |
| simplex.jl:412-480 | Refactor -> increment -> event -> primal/dual recompute | refactor_pivot is before recomputation. Native no-refinement checked solves still run after observer merely sets stop flag; next retry stop check discards candidate, keeps one refactor |
| simplex_diagnostics.jl:81-99; simplex_pivot.jl:20-37 | Observer exceptions wrapped, including SingularException; staged completion events buffered | User exception is not numerical backend failure. Refactor/correction events can be forwarded before publication |
| simplex_recovery.jl:471-498 | Stop or shared clock used for refinement; native checked solve uses pipeline | Deadline is caller-owned public guard and original progress clock; no observer solves/certificates allowed |

No factor copy occurs on this native transactional route. Checkpoint, feasibility
trial and other recovery copies exist elsewhere and are not qualified by this fact.
Any future wrapper must preserve concrete field compatibility and shared identity,
forward ordinary/prepared/BTRAN/invalidation/refactor semantics, expose real updates,
count BEFORE forwarding including throws and calls after injection limit, and fail
closed for unexpected copy/update routes. AB phase-only wrapper cannot be transplanted.

## Exact candidate and rejected shortcuts

Pure identity duplicate was rejected: rho=e2 makes its column1 price zero, so it
cannot reach pivot disagreement; ordinary no-candidate refactor remains reachable.
An injected coefficient below Harris cutoff is also insufficient on native public
entry: that branch returns NUMERICAL_ERROR without entering retry or firing callbacks.
One-shot injection only on public initial BTRAN is insufficient: retry then sees an
exact row, takes no-candidate ordinary refactor and repeats S6-J's work defect.

A conditional alternative keeps four rows/five structural columns, nonnegative
columns, zero costs, equality rhs=-B[:,2], basis1:4, fixed row variables at rhs:

```
delta = 2^-23; h = 2^-22
B = [1 1 0 0; 1-delta 1+delta 0 0; 0 0 1 0; 0 0 0 1]
A = [B B[:,1]]
```

Both old represented B and new B are nonsingular. New det=2^-22. Exact basis point
is -e2, duplicate direction e1, exact unit-row solution
rho=[-2^22+1/2,2^22,0,0]. Thus replacing column2 with duplicate column1 remains singular.
After each of the two expected real unit-row BTRANs (public and first staged attempt),
a proposed bounded adapter would declare rho_bad=rho-h*e1. NO adapter exists yet.
All coefficients/RHS/declared vectors and elementary CSC checks are binary64-exact;
Python rounded checks are explicitly separate from rational algebra and not Julia
code-generation/backend proof.

- B' rho_bad-e2=[-h,-h,0,0]. Legacy residual tolerances are
  max(Float64(1e-12),256eps*(scale+1)); both nonzero residuals are strictly below
  these unchanged bounds (approximately2^-21). No ordinary row repair is required
  IF the declared vector and proposed basis/states actually reach this code.
- Duplicate tableau coefficient is -h; below-bound orientation=-1 gives h greater
  than unchanged Float64(1e-7) cutoff. Other structural columns are basic, row
  variables fixed. Zero reduced cost gives Harris step0; only entering5 is eligible.
- IF the real prepared FTRAN returns e1, its exact residual is zero and pivot at row2
  is zero, so direction repair is unnecessary. Pivot disagreement is certain:
  row=-h, column=0 fail sign/separation tests before tiny-pivot/refactor branch.
- First public disagreement enters retry without native correction because helper
  requires staged workspace. Repeat declared unit-row output in first candidate.
- In staged native-tableau correction, exact RHS is [h,h,0,0], exact correction
  [h,0,0,0]. Corrected row and compensated duplicate price are exact; duplicate
  price becomes0, fixed rows stay ineligible, no candidate remains. Reselection
  returns false before direction correction, causing _PivotRejection(:refresh).
- With max_recovery_rounds0, one rejection then exhaustion or original observer
  cancellation/exception, no update/refactor. With original default refresh budget,
  next candidate refreshes once and original refactor_pivot observer requests stop.
  No additional unit-row call is expected before return; injection limit remains2.

This preserves public rejection reachability conditionally, not its historical
arithmetic stress. B changes equations and row-coordinate bounds; feasibility is
empty in both old/new nonnegative duplicate models since x2=-1 is forced, but hidden
trajectories and tolerance envelopes are not claimed equivalent. Native original
safety/small-pivot groups stay untouched. Original options/policies/tolerances stay.

## Missing runtime evidence and qualification gates

Current evidence cannot prove the new managers' raw unit/prepared/correction solves,
setup lifecycle or compensated residual enclosure, public prepared-cache ownership,
candidate field dispatch, or event/counter ordering. These are explicit prerequisites,
not inferred from dyadic mathematics or saved S6-AB/S results. No fresh old control.
Separate S6-AE plan first checks only new component endpoints on fresh B and actual
-I -> B refactor lifecycle, four managers; no workspace/public solve or adapter.
If that passes, a later separate public-boundary plan must preserve all original
callbacks and exact zero/one work assertions, with owned read-only observations.

Predicted public subject work conditional on this route: two unit BTRANs, two
prepared FTRANs, one correction BTRAN, zero update/copy/refactor. After-refresh
cancellation additionally one refactor, one ordinary primal FTRAN and one zero-cost
BTRAN (event precedes recomputation); no second unit BTRAN budget may reset. Count
whole kernels and all factor attempts/RHS classes, not only hits/events. Unexpected
extra work rejects qualification. Setup, ordinary iteration, retry correction and
post-call validation must be separate. No production speedup/cost claim.

## Work and limits

No production work, allocations or retained memory changed. Offline rational4x4
elimination and27 assertions only; reused evidence loaded, not rerun. No benchmark
is justified for this documentation/diagnostic work. CI remains disabled. Historical
CI cause/private states, x64/fullsuite/broaderS6 remain open; S2-A/S6-J remain rejected.
