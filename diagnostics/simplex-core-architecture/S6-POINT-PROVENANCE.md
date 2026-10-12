# S6-Q: original Float64 point provenance

Status: observed trace and independent post-exit audit complete; final review pending.
No production/test/tolerance/precision/CI change. One new observed solve, not a
repeat of the accepted four-type census or an unobserved control solve.

## Comparability and integrity

Preflight verifies517 existing source/test/runtime/environment/launcher pins
against accepted S6-N. The driver separately verifies exact original constructor,
model record, default options/policy, Julia1.13.0aarch64, Julia/BLAS1 and ambient
BigFloat256/nearest before solve. Options are not injected into _solve_diagnosed.
The single trace has5/5 diagnostic assertions,exit0,24audit gates and611 unchanged
pins with independent resolved-path/hash/inventory verification. Exact final
primal/objective/status/2iterations/1refactor match saved S6-N Float64.
This proves endpoint equality in this attempt, not equal hidden trajectories or
observer neutrality. It does not make the original strict equality pass.

Raw: .superpowers/simplex-core-architecture/S6-Q/trace-1.
Portable: results/S6-Q/trace-1-* and control-preflight.json.
Runner386534/start23085513,child386535/start23085590,driver386526 separately absent;
no Julia on boot20de7dde-704e-41c8-bee7-b8511c0a86b0 after exit.

## Eleven observed events

1. Initial original-bound workspace, slack basis[3,4], zero point.
2. Original phase_dual event.
3. Auxiliary box setup: same scaled matrix, artificial bounds[-1000,1000] on
   structural variables and zero slack bounds; point[-1000,1000].
4–5. Pricing and first pivot proposal.
6. First completed auxiliary pivot, basis[3,2],one eta. Exact working equation
   residual in BOTH rows is125/2^66. This is the first recorded equation error,
   but the structural point is strictly within original row bounds.
7–8. Pricing and second pivot proposal.
9. Second completed auxiliary pivot, basis[1,2],two etas. Original rows remain
   strictly within bounds; this is not the original optimum.
10. refactor_other on PRIVATE STAGED original-bound trial, basis[1,2],no etas,
    with old zero primal/scratch. Source recompute! emits this event AFTER backend
    refactor and BEFORE primal FTRAN and dual BTRAN. Do not interpret its zero
    point as the result of reconstruction.
11. certification on LIVE original workspace, basis[1,2],no etas. Structural
    point equals saved endpoint. Exact original rows[-1,1+2^-47]; working equation
    residual[0,2^-27], since rows were scaled by2^20. This is the first recorded
    original-bound violation. Event occurs BEFORE certificate checks; actual
    returned OPTIMAL follows later and matches saved control.

The scaled matrix is[1 1;1 1+2^-23], row scaling factors2^-20 and column factors1
throughout. Private trial and final workspace use the same recorded matrix identity
and basis/states. Final row_solution equals final structural primal. No eta remains
at refactor or certification. This narrows the interval to original-bound handoff
reconstruction/publication, without proving the particular originating operation.
Source make_dual_feasible! copies the auxiliary basis into a private trial, refactors
it, recomputes, flips bounds if required, validates, then publishes. No intermediate
post-FTRAN event exists. We have not replayed backend solves or captured UMFPACK
permutation/internal scaling; do not call either the proven cause.

Offline primal RHS for basis[1,2] is[-2^20,2^20], derived from AT_LOWER/AT_UPPER
slack states and unchanged bounds. Captured final scratch_row_rhs is[0,-1] because
recompute! reuses it for BTRAN costs; it is NOT the primal RHS. Raw rho/scratch may
be stale or repurposed and is not an independently certified runtime dual witness.
The postsolve analytic witnesses from S6-N/O/P remain separate evidence.

## Observer work and limits

Observer copies explicitly whitelisted, bounded 2x2 model/workspace/scratch arrays,
basis/states and eta values, scalar identities and options/policy representations.
It retains no workspace, mutable buffer or opaque factor reference as history.
It performs no factor getters, basis assembly, solve, certificate or mutation.
Non-workspace handling is probed independently without a solve. Cap512events;
observed11, no truncation. Numeric rational encoding and residual reconstruction
are after the solve. Scalar count-only pricing events have no callback; their
counters are retained separately and are not falsely claimed as snapshots.

No new production work/allocation/retention. Diagnostic copying and exact arithmetic
are justified for this fixed model; no timing or allocation savings are claimed.
No full-state equivalence, historical x64 route, full-suite pass or original test
repair is established. All accepted old measurements remain unchanged.

Next: S6-R minimal factor-component replay on captured immutable B and derived
RHS, with explicit fresh-versus-refactor lifecycle and public backend metadata
contract inspection. No complete solver rerun or opaque factor serialization.
