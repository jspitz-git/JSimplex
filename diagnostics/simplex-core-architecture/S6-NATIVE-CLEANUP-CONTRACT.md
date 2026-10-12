# S6-AK: native bound-journal cleanup termination contract

Source/evidence-only at diagnostic7895198/master354bb1f. No Julia, factor, workspace,
solver/helper, quality or certificate call; no production/test/CI changes. Host
boot20de7dde-704e-41c8-bee7-b8511c0a86b0, prior417368/417369/417360 absent, no Julia;
local/remote refs matched. All518input hashes and user hashes are recorded in
results/S6-AK. The three original inventory entries and raw log lines1428–1464
are preserved as a narrow excerpt, without executing the old parser or auditor.

## What the historical printout actually constrains

Only run38142752357 failed at test/primal_perturbation_integration_tests.jl:187–189.
The failed conjunction does not print run.status, run.message or run.primal. The
next assertion prints the workspace: Float64/PFI/native, A=[1], objective[1], free
row, structural lower0, working structural lower-9e-7, point[-9e-7,-9e-7], basis[2],
states[AT_LOWER,BASIC], reduced costs[1,0], costs[1,0], iterations1/refactorizations1,
iteration limit20, time limit30, zero progress offsets, active bound journal and
native policy with feasibility/recovery/precision flags false. Refactor timing is
true in the replacement policy; the helper's adaptive policy disabled it.

Its event vector is fully shown (8entries,next_event9,capacity64):
refactor_initial, refactor_other, perturbation, pricing, pivot_proposed,
pivot_completed, pricing, checkpoint. The count dictionaries are truncated and
kernel timing is false; printed zero kernel counters do NOT mean no solves occurred.
The vector contains no phase_cleanup, restore_perturbations, certification or
certification_failed event. No wrap or ellipsis occurs inside this event vector.

_internal_solution (dual_simplex.jl:1764) emits certification for OPTIMAL,
certification_failed for NUMERICAL_ERROR, checkpoint for other statuses before
building the returned object. Its OPTIMAL-to-NUMERICAL_ERROR recursion would add
both certification and certification_failed. Thus the vector constrains the
terminal publication category; it cannot by itself name a particular limit status
or locate a private check. Earlier recovery can also emit checkpoint, but native
recovery is disabled here, and the called driver publishes an event on return.
The raw inventory has no error at run_from_basis!, so an uncaught ownership or
callback exception is inconsistent with the recorded subsequent assertions.

An ITERATION_LIMIT path requires work reaching the inherited20limit; the printed
iterations1 and offsets0 do not support that branch. INFEASIBLE/UNBOUNDED with
active bounds first triggers restoration, or unowned bounds convert the proof to
NUMERICAL_ERROR. Neither matches the shown intact journal/no-cleanup event path.
These source constraints favor a TIME_LIMIT return, but this remains inference
from source and a subsequent printout, not captured run.status or elapsed time.
It does not prove historical clock expiration or a backend/compiler cause.

The hex start_ns0x000004a67c5816f9 is an opaque monotonic timestamp. Log wall-clock
times cannot be subtracted from it; no contemporaneous monotonic return time is
recorded. Do not translate the timestamp into duration or infer a30second overrun
from CI slowness. Thirteen of14relevant source/test files equal the failed revision;
only simplex_perturbation.jl has the known S5-C restoration-copy change. Across all
production sources, the other historical difference is HH allocation work, unused
by this PFI fixture. S5-C did not alter the return predicates or deadline ownership.

## Ownership and work through the call chain

| Boundary/source | Owned state and clock | Work and publication contract |
|---|---|---|
| shifted_primal_workspace, test39–55 | Fresh workspace; progress constructor samples time_ns; A[1], free row, structural lower0; iteration20/time30 | Real initialization, basis[1], refactor/recompute, owned journal, one bound expansion. Original problem remains unchanged |
| PerturbationJournal and perturb_primal_bounds!, simplex_perturbation.jl:34,259 | workspace_id=objectid(ws), copies of original costs and bounds; active lower/upper become ws storage | Owner/length checks, finite and monitor guards; bound margin9tol. No certificate transfer; helper assertion shifted==1 |
| Initial _primal_optimize!, test182/primal_simplex.jl:745 | Same adaptive policy and clock; caller stop returns false | Finite/primal/price safeguards, one observed historical pivot, then OPTIMAL assertion. False user callback is not a new deadline; nested source checks may still own deadlines |
| Native policy replacement, test183–185/driver53 | New NumericalPolicy(Float64); same progress start_ns, objective/scaling/offsets/diagnostics and same workspace/journal | No factor, solve or restoration. Required-driver predicate remains true because costs/bounds/journal are altered, even though native heuristics are off |
| SimplexRunBudget, driver31 | Same start_ns and30second limit, inherited completed work and20iteration allowance | No reset at policy switch, constructor or later phases |
| _run_basis_terminal!, driver101–123 | Installs policy with budget.start_ns, same factor/journal, bounded temporary options | Sync counters, min time limit, guard checks _budget_expired OR user stop, no extra time allowance |
| _verify_driver_basis!, driver74–85 | Current working bounds; no model switch | Prepare pricing, real recompute (FTRAN+BTRAN), finite check, two quality checks; fallback native corrections only if unreliable, with owned private candidates |
| Native cleanup fallback, native_cleanup_recovery.jl:86 | Copies basic point/rho and RHS; both corrected states stay private until accepted | Quality/scans; at most configured correction/reconstruction route, all native safeguards retained; successful publication invalidates caches. No assumed entry in this case |
| Bound retirement, driver295–303/simplex225/perturbation80,220 | Only after a proof terminal on an active owned journal | Restore original costs and all bound destinations, deactivate journal, retire scratch pointer, reset pricing/checkpoints, emit restore then phase_cleanup. Restoration itself does not recompute point/rho |
| Next forced feasibility pass | Same clock/budget, now original bounds | Recompute against restored bounds, then original feasibility/optimality certification before successful result publication |
| Driver finally, driver229–233 | Preserves consumed work and original options | Sync counters and restore options only. Does NOT retire journal, restore working bounds, reset deadline or claim a valid original result |

## Return/exception table

The following covers the driver's early exits and delegated terminal classes; it
does not imply every branch occurred. The original callback is always false and
observer is nothing, so cancellation/observer throws are contract alternatives,
not manufactured historical evidence.

| Location / trigger | Result | Bounds/journal and completed work |
|---|---|---|
| Driver setup before try: invalid options/policy/storage | Exception | No terminal publication; cannot explain three subsequent failed assertions without an unrecorded catch |
| driver135/144: deadline/stop before or after first verification | TIME_LIMIT, feasibility-recovery message | Active journal can remain; before-check may do zero verification work, after-check may already do pricing/FTRAN/BTRAN/quality work |
| driver146: verified point and prices classify certify | OPTIMAL internal terminal | Outer active-bound branch restores and continues; it cannot directly certify the shifted model as original |
| driver149: inherited completed iteration allowance exhausted | ITERATION_LIMIT | Active journal retained; no restoration required by this limit branch; printed1/20 contradicts this sufficient condition |
| driver151–179: verification false, phase-one/primal/dual dispatch, numerical exception | NUMERICAL_ERROR intermediate or delegated terminal | Recompute can overwrite scratch/point; work survives. Finite/quality/phase failures are bounded; not automatically a returned NUMERICAL_ERROR |
| driver176/197/211: guard after method/final check/refreshed check | TIME_LIMIT | Work already completed remains charged, possibly factor work; active journal can remain |
| driver177–178: delegated non-OPTIMAL/non-NUMERICAL_ERROR | TIME_LIMIT/ITERATION_LIMIT/INFEASIBLE/UNBOUNDED as returned | Outer active-bound proof terminals restore first; limit terminals leave journal active |
| driver187–200: repeated signature or min(2,max_recovery_rounds) exhausted | final verified OPTIMAL, TIME_LIMIT, or bounded-feasibility NUMERICAL_ERROR | Final success must pass quality and feasibility; history is bounded; rounds reset only on actual iteration progress |
| driver203–215: fresh unreliable solve and recovery enabled | optional refactor/basis repair, then loop | Inactive under default native recovery=false; fresh=true can still refactor on the next ordinary verification |
| driver218–230: numerical throw versus callback/logger or other exception | NumericalError terminal or rethrow | Stop exception provenance retained; ArgumentError owner mismatch is not swallowed as numerical failure; finally restores options/counters only |
| driver295–314: proof terminal with active bounds or altered costs | Restore/retire and continue | Four bound copy destinations remain required; owner failure throws before retirement; no original certificate reuse |
| driver307–311: nonproof terminal or altered unowned-bound proof | Limit/NUMERICAL_ERROR returned | No blanket restoration-on-failure promise; working journal can remain without publishing primal/objective |
| driver318–320: three cleanup attempts exhausted | TIME_LIMIT or bounded-objective NUMERICAL_ERROR | Whatever work/restoration already happened remains, no fresh retry budget |
| dual_simplex1764–1784: final publication | OPTIMAL only with finite/original primal/original optimality certificate; otherwise NUMERICAL_ERROR; nonoptimal no point/objective/basis | Event emitted first; failures preserve safeguard and omit result payload, not reset workspace |
| driver334: precision/refinement escalation | Optional numerical recovery | Both flags false for this native policy; no escalation in this scope |

Normal cleanup is conditional on real recomputation/quality, successful original
certificate and available shared time. A returned limit is not proof that restoration
was attempted or malfunctioned. A normal local pass is not proof about historical
CI ordering or compiler latency. Distinguish public result payload from the still
mutable workspace point printed by a later assertion.

## Exact represented inputs, not decimal arithmetic

The new Python offline analysis has21evaluated checks plus one explicit model
semantics declaration (the free basic row has no bound violation), recorded under
analysis.json.checks; that declaration is not an executed production predicate.
All22entries are true. Binary64 primal tolerance is
944473296573929/9444732965739290427392. The expansion expression at index1/level1 is
rounded9*t, margin8500259669165361/9444732965739290427392. The stored lower and both
printed point components are its negative (hex beae32f0ee144531). In this case the
represented multiplication equals9times the represented tolerance exactly.

With working matrix[1,-1], basis column-1, nonbasic x=-margin and basic activity
s=-margin, x-s=0 exactly. The basic row variable is free; nonbasic structural price1
at its lower bound is dual-feasible. Basis RHS=margin, FTRAN=-margin, basic cost0,
BTRAN0 and prices[1,0] are the exact algebraic solution, not a claim about hidden
runtime factors. Working feasibility and basis equations are compatible with the
printout. Original lower0 is violated by margin>t; working feasibility must not be
reused as an original certificate.

After legitimate bound restoration, the old nonbasic x=-margin is too far below0
for _can_preserve_primal_bound_value; _nonbasic_value must use0. The exact recomputed
point is[0,0], rho0 and prices[1,0], original structural optimum0. This supplies a
conditional normal-path oracle; no production quality/certificate function ran in
AK. Any unexpected actual factor/quality behavior in a future observation remains
raw evidence rather than being overwritten with these exact vectors.

## Selected next observation

S6-AL's separate `2026-10-12-native-cleanup-provenance.md` permits exactly one new
Float64/PFI lifecycle: existing helper once, initial _primal_optimize! once, then
run_from_basis! once with unchanged native policy/default tolerances and original
30second budget. Capture actual status/message/payload, clocks, bounds/journal,
point/basis/state and counted work around those two calls. No observer, wrapper,
synthetic deadline, extra quality/certificate call or matched-control claim.
This is new termination provenance, not a replay of the S5-C focused suite.

A before/after monotonic bracket can prove expiration before entry or exclude it
through return; a crossing bracket cannot locate the private check. Snapshot and
kernel-count instrumentation consume time and may affect deadline outcome; no
neutrality or historical-cause claim follows. Preserve original six test assertions
and helper assertion, including any new failure/exit; do not weaken the success
oracle after observing TIME_LIMIT. No permanent repair is authorized by AK/AL.

No production work/allocation/retained memory changed at any frequency. Existing
copies/quality/certificate work are described, not removed. No benchmark warranted.
S2-A/S6-J/wholeAF remain rejected; CI disabled, x64/full-suite and broader gates open.
Fresh independent source/numerical-contract/work review recorded separately.

## Closure

Fresh gpt-6-astra review accepted this source contract and separate AL plan with
no Critical/Important. One Minor work-description shorthand is deferred: table
"two quality checks" is generally UP TO TWO because unreliable primal quality
short-circuits; both run on the successful path. No runtime claim/count oracle
relies on unconditional execution. See REVIEW. Independent verification has8checks
on hashes/users/exactbit arithmetic/source/master. No old rerun or newnumerics.
