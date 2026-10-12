# S6-Q: nearly singular Float64 point provenance

> Use superpowers:executing-plans inline. Diagnostic only; no production/test edit.

S6-N original and S6-P balanced matrices both return Float64 objective gap-1/16
from an accepted2^-47row violation. S6-O triangular passes equality but changes
presolve topology/main route. Neither is accepted as a permanent replacement.
Do not repeat these four-type censuses or attempt more fixture tuning by guessing.

Goal: locate when the non-strict point first appears and distinguish backend/base
factorization, update-chain reconstruction, phase transfer and postsolve effects.
A small final residual alone establishes no root cause.

- [x] Reconcile available diagnostic events/capture helpers and accepted S6-N
  source/model/options/endpoint. Verify source/test hashes against its accepted
  source pins (new unrelated diagnostic files need not match that old inventory).
  No new unobserved control solve; endpoint equality with saved control is a
  limited check, not full trajectory equivalence.
- [x] Design a read-only observer for one original Float64 solve, same constructor
  and defaults, via existing _solve_diagnosed with SimplexDiagnostics. Record
  stage/event, model identity/shape/exact coefficients, basis indices/states,
  primal/dual/prices, relevant original/working bounds and perturbation status at
  phase/refactor/pivot/certification events. Whitelist owned small-array snapshots;
  avoid retaining mutable workspace references as historical states.
- [x] Never invoke extra solves, factor refactors, perturbations, certificates or
  mutating getters inside observer. Validate callbacks safely handle non-workspace
  states. Record source and snapshot field coverage explicitly. Certification event
  occurs BEFORE checks; distinguish attempt from successful returned certification.
- [x] One bounded guarded observed solve. Compare exact final point/objective/
  status/iterations/refactors against saved S6-N Float64; preserve mismatches and
  exceptions. Recompute original residuals offline and identify the first observed
  event containing the deviation. No historical x64-path equivalence claim.
- [x] If event resolution cannot locate the arithmetic operation, plan a separate
  minimal factor-component replay using captured immutable basis/RHS/permutation/
  scaling metadata. Inspect backend contracts before replay; do not assume UMFPACK
  internal scaling/pivot behavior from max coefficient or final gap. No serialized
  opaque factor pointers, no wholesale solver rerun, no production instrumentation.
- [x] Final independent numerical/work review, publish accepted coverage and next
  focused plan; original strict equality remains unchanged. No implementation until
  concrete evidence supports a separate RED/GREEN change.

One Julia/BLAS1,heap2GiB,VM8GiB,RAM6GiB,swap1GiB. Fresh separate host boot/start_ticks/
command and previous runner/child/driver absence before edits or launches. Preserve
raw evidence/user files/old environments; large inputs forbidden, CI stays disabled.

## Result

One observed solve matches saved S6-N endpoint;11events,5assertions,24gates,611pins.
First exact equation residual is auxiliary pivot1, while the first original-bound
violation is certification after private original-bound refactor/recompute. Backend
operation not isolated. See S6-POINT-PROVENANCE.md. Independent final review pending.
Deferred comparator minor from S6-O/P was implemented in preflight:517matching
source/test/environment/runtime/launcher pins plus model/options/policy/threads.
No old driver edits or repeated accepted census. Next separate S6-R replay plan.
