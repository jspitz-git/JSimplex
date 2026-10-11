# S1-A: owned-deadline dual entry experiment

Status: Integrated and pushed to master as beb161b; architecture commit 8e0a7c7.
Parent: [architecture roadmap](2026-10-11-simplex-core-architecture.md).
Evidence: [ownership inventory](../../../diagnostics/simplex-core-architecture/S1-OWNERSHIP.md).

## Hypothesis and scope

One of the four ordinary dual finite-state checks might be reused *within one
outer-loop call* when the intervening deadline is an internal read-only clock,
pricing preparation is provably a no-op, and the outer feasibility branch did
not repair or otherwise mutate state. Public arbitrary callbacks and every
uncertain path retain existing checks. No reusable validity lives in workspace,
scratch, checkpoint or snapshot; there is no generation or rollover to maintain.

Potential saving per accepted ordinary step: one check of up to four length-v
vectors, with no new basis solves, copies or content hashes. This is an upper
bound, not measured savings. All four baseline checks together cost only 4.589 s
of the recorded dual census; never promise a whole-run speedup from this bound.

## Owned files and provisional private interfaces

- `src/solver.jl`: a private `_SolveDeadline <: Function` with only
  `start_ns::UInt64` and `time_limit_seconds::Float64`; its call delegates to the
  existing elapsed-time comparison. Replace only internal context-only deadline
  closures, after enumerating their call sites. Never wrap arbitrary user code
  and label it read-only. Preserve the present deadline call count/order.
- `src/dual_simplex.jl`: factor the existing caught iteration body into a private
  helper used by both `dual_iteration!` and the owned outer-loop fast path. Exact
  helper signature is fixed after the characterization step below. No public
  keyword that accepts an unverified `already_valid=true` is allowed.
- Outer `_dual_optimize!` can select that helper only on a successful local finite
  check, no intervening repair, owned deadline, and no-op pricing preparation.
  Prove the predicate from `_prepare_auto_pricing!`'s actual branches, including
  temporary modes, scratch.pricing and adaptive policies. Call it again if needed
  to preserve semantics; do not rely on a stale policy/mode observation.
- `test/simplex_state_validity_tests.jl`: focused contract tests.
  Diagnostic work-count/trajectory hooks stay outside production state.

## Sequential gates

- [x] Characterize baseline entry calls, mutation opportunities and actual stop
  closures in solver, cleanup and auxiliary/driver paths. Read the complete
  feasibility helpers in the proposed interval. If any unchecked mutation remains,
  narrow the predicate or reject the experiment before editing production.
- [x] Write a failing work-count test for unchanged owned entry; retain passing
  public-callback regressions with NaN/Inf injected independently into primal,
  reduced costs and costs, plus invalid weights/mode transitions. Validate both
  copied arrays and mutation through retained aliases. Include different vector
  dimensions and all supported scalar families.
- [x] Test deadline expiry at each retained polling point; arbitrary stop/observer/
  logger exceptions retain their type and propagation. Exercise failed update,
  candidate rollback, recovery, phase changes and standalone `dual_iteration!`.
- [x] Implement the smallest helper and internal deadline contract. No counters,
  tolerances, candidate-selection arithmetic, residual tests or precision changes.
- [x] Under the S0 guard run `dual_weight_validation`, `native_residual`,
  `primal_certificate_reuse`, `simplex_precision_recovery_state` and new validity
  tests. Use existing test entry conventions; exact commands and pins must be
  recorded before launching. Never run numerical tests concurrently with timing.
- [x] Compare baseline/candidate event and state hashes on bounded sparse/dense
  fixtures, runtime dual and the known medium prefix **because production changed**.
  This is new paired validation, not a repeat of historical profiling. Count
  actual vector-element visits, not just helper calls. Preserve both algorithms
  and five public managers in broader validation.
- [x] Interleave at least three warm plain baseline/candidate runs. Report probe
  overhead, allocations/retention, per-step counts and timing spread. Use the same
  options/precision and separately report recovery/initialization.
- [x] Independent numerical/work/memory review. Integrate and push only if safety,
  identical arithmetic trajectory and net work reduction are demonstrated. Keep
  experiments separate if the predicate is ineffective or the overhead cancels
  savings. Update STATUS with exact commits and next action.

Long phase-II reference remains mandatory before any S2 whole-medium claim, but
is not required to characterize this local S1 contract. A failed hypothesis is
recorded as rejected; it is not a reason to weaken callback or numerical safeguards.

## Characterization (2026-10-11)

The feasibility summaries read only primal/prices/bounds/basis; they call no
observer/logger/stop and mutate none of the finite-check inputs. Pricing
preparation is a no-op exactly when its `controlled` predicate is false and
scratch.pricing is nothing. Arbitrary closures, driver budget wrappers and all
repair branches retain validation. Internal context-only deadlines occur at
cleanup_original, _retry_original and the main algorithm call in solver.jl.
Presolve's stop closure is outside this optimization and is unchanged.

Ruling: define the deadline type near _StopCallback in dual_simplex.jl and its
SolveContext constructor in solver.jl, because include order loads dual code
first. The same two immutable scalar fields and comparison are retained. Cost:
private type placement differs from the provisional subplan, with no API change.

Private implementation interface: `_dual_iteration_entry!(workspace, guarded_stop,
perturb_degenerate, ::Val{Validated})`. The public/internal standalone
`dual_iteration!` always supplies Val(false). The outer loop can supply Val(true)
only within its current successful check scope, with an owned deadline and
no-op pricing preparation; entering any dual-feasibility repair clears eligibility.
Both paths retain the second deadline poll and pricing preparation call.

Ruling: first reuse implementation is limited to Float32/Float64 and excludes
all adaptive-pricing policies, even some provable no-ops. Generic AbstractFloat
and Rational methods can dispatch to user arithmetic; conservative fallback
avoids extending the ownership claim to them. Their deadline behavior remains
covered by functional tests. Cost: no scan savings in those scalar families.
RED work-count probe: 25 pass, 3 fail, all failures are 9 checks vs expected 7
for two pivots (steepest-edge, Devex, Dantzig). No numerical errors; pins unchanged.

Focused gate result: 469 assertions passed in normal mode, including allocation
assertions; precision recovery and dual-entry-phase passed 212 semantic assertions
under compile=min after normal compilation exceeded useful bounded effort.
Count probe: 41/41, including successful repair/adaptive exclusion and executed
vector lengths. Broad callback/logger/rollback coverage and paired measurements
still gate integration. No complete normal-mode suite pass is claimed.

Paired-2 completed 30 interleaved warm plain pairs across sparse/dense models
and all five managers; all traces and plain results agree, allocations equal,
measured compilation zero. Timing scatter and limits are in S1-ENTRY.md.
External matrix: 100/100 original-primal-certified, objective-matched OPTIMAL
results, 305 assertions. Existing callback/logger/rollback/driver boundaries:
780 additional semantic assertions passed. Normal-compilation precision-test
control also times out on old source; full-suite completion remains unclaimed.
Medium candidate 4000-step prefix exactly matches the historical trajectory and
saves 4000 finite checks. New baseline element census and runtime pair pending.

Final local gate: both medium and runtime baseline/candidate plain/census
trajectories match. Actual finite-check visits fall by 24.994% and 12.60%,
respectively; only finite-workspace call counts change. Independent acceptance
review has no outstanding findings. Source/test hashes match all validation
attempts. See S1-ENTRY.md for timing/compilation limits and the integration ruling.

Integration: master beb161b has identical src/test/Project trees and passed 242
contract assertions directly from its checkout (integration-1, compile=min).
Push completed; diagnostics/raw artifacts and old environments remain separate.
