# S6-AL: native cleanup return and shared-clock provenance

One new local Float64/PFI lifecycle passed the six original native cleanup
predicates and the original helper perturbation assertion: **7/7, exit 0**.
This is bounded provenance, not a repair or a reproduction of the older three CI
failures. Production, tests, master and workflows remain unchanged.

## Scope and source binding

The driver extracts the exact `primal_stalled_monitor` and
`shifted_primal_workspace` definitions from current tests without evaluating any
neighbor. Entry counters precede exactly one helper, one initial
`_primal_optimize!`, one `SimplexRunBudget` constructor and one `run_from_basis!`.
The actual initial terminal is retained before checking its original OPTIMAL
predicate. The final result is retained before the original combined status/point,
original-bound, journal-retirement and disabled-feasibility-recovery predicates.
No extra solve, iteration, factor, quality or certificate entry was added.

Preflight binds the actual helper/target/driver, 14 contract source files, 513
tracked source/test/workflow files equal to master `354bb1f`, and six user hashes.
627 old AG pins match; its sole changed pin is the known integrated AI dual test.
The new launch independently pins 628 files. Runtime helper hashes agree with the
extracted sources. All 31 new offline audit gates pass, including 102 binary64
bit/rational checks. This audit is exclusive-write and must not be rerun.

## Actual state and work

The helper returns a real PFI factor, basis `[1]`, point `[0,0]`, an owned active
bound journal and adaptive setup policy. Its numerical initialization/refactor/
recompute/perturbation happens before kernel timing is enabled. Its zero kernel
counters do **not** mean zero setup work; setup already records two refactor events
and workspace refactor counter 1.

The initial optimizer returns OPTIMAL on working bounds, basis `[2]`, states
`[AT_LOWER,BASIC]` and point `[x,x]`, where
`x=-8500259669165361/9444732965739290427392` (bits `beae32f0ee144531`).
This is exactly minus nine represented primal tolerances. The working equation
`x-s=0` holds exactly; original structural lower-bound violation exceeds tolerance.
The stored adaptive policy is replaced by the actual default native policy.
Five adaptive flags turn off and refactor timing turns on; the full values are
saved. Native recovery, refinement, precision boosting and hypersparse remain off.
No working-model certificate is transferred to the original model.

| Window | FTRAN | BTRAN | Pricing kernels | Refactor kernels | Iteration delta |
|---|---:|---:|---:|---:|---:|
| Initial optimizer after setup | 2 | 3 | 2 | 0 | 1 |
| Native cleanup driver | 2 | 2 | 0 | 0 | 0 |

These are observed production kernel entries, including the existing `finally`
attempt accounting. No throwing path occurred, so this run is not a new throwing
accounting proof. They are not counts of internal quality checks. Quality checking
can short-circuit after the primal check (the deferred AK shorthand stays deferred).

The driver returns OPTIMAL, message `optimal solution found`, public primal `[0]`,
objective 0, basis `[2]`, iteration/refactor totals 1/1. Actual final workspace point
is exactly `[0,0]`, original bounds are restored, perturbation flag is false and
journal is absent. The four new events are, in order, `restore_perturbations`,
`pricing_phase_reset`, `phase_cleanup`, `certification`. No checkpoint or failed
certification is recorded. Model/options/scaling, ambient precision/rounding and
thread counts are preserved. This is an original-model public result from this
new driver call, not an independently added certificate invocation.

## Clock interpretation

All four workspace snapshots and both budget snapshots retain start_ns
`247097172706848`, time limit 30 seconds and iteration limit 20. There is no clock
reset, warmup, raised limit or tolerance/precision change.

The initial optimizer bracket is 0.099266799 to 7.432490917 seconds after start.
The driver bracket is 7.501187517 to **16.137016355** seconds after start; therefore
expiry is excluded throughout that bracket under the monotonic-clock assumption.
This does not capture any private clock check. The helper bracket begins before
the progress clock is constructed, so its negative relative start is expected and
must not be interpreted as time spent under an already-existing shared budget.

Call durations include first-call compilation: helper 2.754673772 s, initial
optimizer 7.333224118 s, driver 8.635828838 s. These are not steady-state timings or
speedups. Four capture brackets take 0.083734699, 0.000021100, 0.000020000 and
0.000041100 s respectively; bookkeeping and compilation outside those brackets
also consume shared time. The diagnostic enables kernel timing only after setup,
has no observer, and makes owned tiny snapshots. Timing neutrality is not proved.
Serialization and rational/bit conversion occur after the final numerical window.

## Evidence and limits

Raw and portable `provenance-1-{report.toml,process.json,pins.json,run.log}` and the
exact driver live in `results/S6-AL`. Resource guard uses one Julia/BLAS thread,
heap 2 GiB, VM 8 GiB, available RAM >=6 GiB and swap <=1 GiB; prohibited inputs are
pinned as forbidden. Separate host checks verify runner425975, child425976 and
launch group425967 absent on boot20de7dde-704e-41c8-bee7-b8511c0a86b0. No Julia
process remains. Independent pin hashes and actual source are checked after exit.

The older historical eight-event sequence ending in checkpoint is still only
source support for a TIME_LIMIT hypothesis. This new successful call supplies no
historical status, elapsed time or CI cause. It neither retroactively accepts AF
nor reverses S2-A/S6-J rejection. Full-suite, x64 and broader architecture gates
remain open; CI remains disabled. No production work or retained memory is added.
The diagnostic copies only tiny fixed-fixture state, bounded event rings and
counter dictionaries at four boundaries, with no per-solve observer or snapshots.

Next decision is source/evidence only: reconcile current cancellation/deadline
coverage before justifying any further native-cleanup experiment or test repair.
This local pass does not justify extending/removing the timeout or resetting clocks.

The first independent supplement incorrectly expected 32 audit keys; its false
`audit32` result and exit-1 note are preserved. There are exactly 31 keys, all true.
A separate corrected supplement verifies that count without rerunning the audit or
numerical lifecycle. This clerical failure does not replace any numerical oracle.
