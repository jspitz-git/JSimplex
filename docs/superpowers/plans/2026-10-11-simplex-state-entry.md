# S1-A: owned-deadline dual entry experiment

Status: concrete investigation subplan; no production implementation yet.
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

- [ ] Characterize baseline entry calls, mutation opportunities and actual stop
  closures in solver, cleanup and auxiliary/driver paths. Read the complete
  feasibility helpers in the proposed interval. If any unchecked mutation remains,
  narrow the predicate or reject the experiment before editing production.
- [ ] Write a failing work-count test for unchanged owned entry; retain passing
  public-callback regressions with NaN/Inf injected independently into primal,
  reduced costs and costs, plus invalid weights/mode transitions. Validate both
  copied arrays and mutation through retained aliases. Include different vector
  dimensions and all supported scalar families.
- [ ] Test deadline expiry at each retained polling point; arbitrary stop/observer/
  logger exceptions retain their type and propagation. Exercise failed update,
  candidate rollback, recovery, phase changes and standalone `dual_iteration!`.
- [ ] Implement the smallest helper and internal deadline contract. No counters,
  tolerances, candidate-selection arithmetic, residual tests or precision changes.
- [ ] Under the S0 guard run `dual_weight_validation`, `native_residual`,
  `primal_certificate_reuse`, `simplex_precision_recovery_state` and new validity
  tests. Use existing test entry conventions; exact commands and pins must be
  recorded before launching. Never run numerical tests concurrently with timing.
- [ ] Compare baseline/candidate event and state hashes on bounded sparse/dense
  fixtures, runtime dual and the known medium prefix **because production changed**.
  This is new paired validation, not a repeat of historical profiling. Count
  actual vector-element visits, not just helper calls. Preserve both algorithms
  and five public managers in broader validation.
- [ ] Interleave at least three warm plain baseline/candidate runs. Report probe
  overhead, allocations/retention, per-step counts and timing spread. Use the same
  options/precision and separately report recovery/initialization.
- [ ] Independent numerical/work/memory review. Integrate and push only if safety,
  identical arithmetic trajectory and net work reduction are demonstrated. Keep
  experiments separate if the predicate is ineffective or the overhead cancels
  savings. Update STATUS with exact commits and next action.

Long phase-II reference remains mandatory before any S2 whole-medium claim, but
is not required to characterize this local S1 contract. A failed hypothesis is
recorded as rejected; it is not a reason to weaken callback or numerical safeguards.
