# S5-B: original objective and bound restoration contract

Base master3220118 / architecturefb56929. Diagnostic-only qualification; no
production change, cost benchmark or certificate-reuse claim. Census-2 accepted144pairs/all21audit gates; final review pending.

## Existing evidence reused

Read cost_restore_allocation_tests.jl, simplex_perturbation_integration_tests.jl,
basis_recovery_tests.jl, partial_pricing_integration_tests.jl and the working-proof
fixtures in simplex_driver_tests.jl / primal_perturbation_integration_tests.jl.
These specify cost storage ownership, actual perturbation retirement, phase/model
checkpoint rejection, partial pricing invalidation and original terminal proofs.
Accepted S4-C/master current-source runs exercise HH backend/extraction tests; S3
and S2 focused launchers exercise pipeline and primal-update groups. They do not
establish that the four named restoration suites passed on current production.
Historical full CI is failing, not accepted S6 evidence. The new census adds bounded
handoff probes; it does not rerun these full suites or accepted medium references.

## State, ownership and ordering

| Operation | Mutation/publication contract | Work and validity consequence |
| --- | --- | --- |
| Journal publication | Journal records workspace object identity, independent original/active costs; active working costs become workspace costs. Owned bounds similarly retain original/active buffers. | Distinguish identity alias from merely equal contents; detached workspace buffers remain legal at restoration. |
| restore_perturbations! | Checks owner/length, returns early if no active cost/bound state. Copies original costs into workspace and active journal buffers, restores owned bounds, restores perturbed flag, retires activity, updates cooldown, invalidates checkpoints, resets stagnation, then emits restore event. | Copies happen before callback. Callback failure leaves already-written arrays and journal state; no transactional rollback is promised. Prices/primal are not reconstructed by these copies. |
| _retire_perturbations! | Clears workspace journal only after restoration returns. | A throwing restore observer can leave the inactive journal attached. Preserve exact exception cause and partial-publication order. |
| _restore_original_costs! | Retires journal, resets automatic pricing/history, invalidates checkpoints, copies authoritative problem objective and zero slack costs; may emit another restore event if perturbed remains set. | No certificate is implied. It uses problem objective even if an earlier journal saved another working objective. Repeated phase invalidation is visible to observers and is not silently removed. |
| Checkpoint invalidation | Drops sparse/hypersparse caches (recursing staged scratch), invalidates partial pricing pool/generations, empties checkpoints/rejections, increments phase generation. | Checkpoint matches require original model identity, dimensions, costs object identity and phase generation. Same dimensions alone are insufficient. |
| Pricing reset | Drops stagnation owner, retires temporary mode/history; invalid framework requests reset_devex!, fills weights/reference, preserves/reset fields per existing pricing policy, emits pricing_phase_reset. | Cannot copy weights across an arbitrary basis/order or suppress framework reset based solely on cost equality. |
| Terminal loop | Up to three passes share budget. Owned bound changes require original restoration before accepting optimum/infeasibility/unboundedness. Altered unowned bounds invalidate infeasible/unbounded proof. Cost shifts require appropriate original-cost re-evaluation. | No working certificate transfers across altered costs/bounds. Stop/iteration limits keep consumed work; cleanup does not restart the clock. |
| Already-original state | Driver still checks ownership/validity as required by policy; explicit restoration would invalidate phase even if costs compare equal. | Equality of values is not proof that restore is a no-op on metadata or observer events. |

## Census design and limits

Controls run before probe installation. Counted methods retain parsed original
arithmetic bodies, with copyto! calls in restoration routed through a counting
forwarder. Counters report requested copy calls/elements, not elapsed time, bytes
allocated, raw refinement solves or complete per-entry scan lengths. Scans are
counted as function invocations and may short-circuit. No second copy is removed.
Only restoration-region copyto! calls are intercepted, not every solver copy.

144cases = Float64/RationalBigInt × requested primal/dual × HH native/Markowitz ×
native/checked policy ×9modes: already original, owned cost alias, detached cost
buffer, unowned cost, owned bounds, alien unowned bound, expired budget,
cancellation after restoration, throwing restoration observer. Journals are
explicit controlled initial states; exact rational perturbation is not claimed
to occur naturally in the solver. Tests exercise validity/provenance, not natural
frequency. Pricing framework begins invalid to expose the mandatory reset.

Snapshots compare selected recorded values/metadata/event order and identity
relationships, not exhaustive bitwise workspace/factor equivalence. Foreign-model
checkpoint rejection and phase invalidation are asserted. Objective0 at original
primal[0] is the bounded normal oracle. Unowned infeasible bounds must not become
an original infeasibility certificate. Expired/cancelled outcomes cannot publish
an optimum. Caller input model remains unchanged. No model/order/scaling transfer,
large input, full manager/precision matrix, update-chain scaling or future Julia
compatibility follows from this census.

## Candidate for a separate implementation gate

When workspace.costs === journal.active_costs, the two cost copyto! calls in
restore_perturbations! target the same owned Vector and same source consecutively.
Owned bounds can similarly alias active bound buffers. Identity checks are O(1);
value equality would require O(N) and would not prove ownership. A candidate may
skip the immediately consecutive cost copy only when destinations are identical
AND the original source does not overlap that destination: repeated partial-overlap
memmoves need not be idempotent. Base.mightalias for Vector can provide a conservative
constant-time guard; verify it in a separate implementation/cost gate. Bound copies
are excluded from that first change because intervening writes complicate source
cross-aliasing. Preserve detached/overlapping copies, failures, events, phase
increments and all reconstruction/certification. No cache, tolerance change or certificate reuse
is needed. This remains a hypothesis until observed copy counts, focused RED/GREEN,
cost evidence and independent review qualify a separate implementation subplan.

## Accepted census and preserved failure

Census-1 failed in the unowned-bound oracle before instrumentation. Probe-1 on the
same fixture reported original-feasible OPTIMAL for both algorithms/profiles: its
upper-below-lower mutation did not require a numerical-error result if an original
optimum was independently certified. Both raw attempts, source, logs, exits and
pre-edit independent pin audits are preserved. The intended negative proof case
now uses the existing simplex_driver_tests fixture: original row_lower1/column_upper2,
working column_upper0. This has consistent column bounds but infeasible working
rows; accepting its infeasibility as an original-model proof would be incorrect.

Census-2: exit0,86.060s process wall including compilation/instrumentation (not
a cost result),144exact selected-representation pairs,21audit gates true.80normal
OPTIMAL/original-feasible objective0,32TIME_LIMIT,16NUMERICAL_ERROR for alien bound
proofs and16preserved observer exception causes. Foreign-model checkpoints rejected
in144cases; required phase invalidations and monotonic budget checks pass. No
world-age warnings in this diagnostic. Julia/BLAS1 recorded; source/script/whole
pin inventory independently verified. Peak VM2095372KiB/RSS1736612KiB, minimum
available21074060KiB,swap0. Last runner363940/child363945/driver363931 absent.

| Restoration mode | Calls/elements copied inside restore scope | Checkpoint invalidations | Auto pricing resets |
| --- | --- | --- | --- |
| Owned cost, aliased active buffer | 3 / 5 | 2 | 1 |
| Owned cost, detached active buffer | 3 / 5 | 2 | 1 |
| Unjournaled altered costs | 1 / 1 | 1 | 1 |
| Owned bound journal | 7 / 13 | 2 | 1 |
| Throwing restore observer | 2 / 4 before throw | 1 | 0 |

Here N=2,n=1: journal copies each touchN; authoritative objective copy touchesn.
Fill! writes are not included. These restore scopes perform no recompute/FTRAN/
BTRAN requests; subsequent solver work is outside the scope and preserved.
Cancellation after restoration has the owned-cost copy counts. Already-original,
expired-at-entry and alien-bound failure cases do not enter original restoration.

The cold cost copy to the same destination is a concrete avoidable-work candidate
under the additional nonoverlapping-source predicate, not evidence that any safety
scan/event/reconstruction is redundant. No new production work, allocation or
retained memory is introduced by this census. Recorder allocation is diagnostic
only. Bound-copy deduplication is deliberately excluded from the first candidate.
Separate S5-C plan2026-10-12-restore-alias-copies.md defines RED/GREEN, overlap/failure
contracts, changed-source cost pairs and integration review. No optimization is
accepted or speedup claimed by the census itself.
