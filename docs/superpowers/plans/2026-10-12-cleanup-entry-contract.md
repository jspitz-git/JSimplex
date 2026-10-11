# Original cleanup entry contract and work census plan

> **For agentic workers:** Use superpowers:executing-plans inline and sequentially.

**Goal:** Qualify one conservative S5 boundary before proposing state reuse: ordinary
original-model cleanup's discarded default-basis reconstruction.
**Architecture:** First map and count the existing initializer and restored-basis
reconstruction separately on portable fixtures. Keep original-model certification,
projection, precision handoff and fallback unchanged. No production optimization is
part of this census plan; a separate RED/GREEN implementation subplan follows only
if the census and eligibility contract justify it.
**Tech Stack:** Julia diagnostics and existing guarded runner; English reports.
**Spec:** ../specs/2026-10-11-simplex-core-architecture-design.md

## Constraints and selected boundary

Master3220118, Julia/BLAS1,heap2GiB,VM8GiB,RAM floor6GiB,swap ceiling1GiB.
No excluded large inputs/aliases; no repeated completed medium references. Preserve
raw attempts, all old worktrees and user environments. No tolerance/precision change.
Standing user authorization chooses inline continuation without approval pauses.

Select ordinary cleanup_original -> initialize_workspace -> restored basis,
not generic phase-I/artificial removal, auxiliary dual-box restoration, crash entry,
initialize_from_basis, LP refinement or precision-boost initializers. Existing
S5-INVENTORY-NOTES.md records why these have different ownership contracts.

The narrow hypothesis removes only default-slack reconstruction when its state
cannot be observed or used; it does not remove the default factor owner. Broader
direct-basis construction is a separate design. No eligibility heuristic is selected
before the census. Existing native/checked recovery settings remain unchanged.

## Review focus / non-negotiable contracts

- refactor_initial observers see reconstructed default slack values with stored
  working precision; callback/logger numerical exceptions retain caller provenance.
- Expired entry returns the same owned TIME_LIMIT state/counters; no zero scratch
  may be returned as an initialized primal point.
- Recovery can retain a verified default basis: skipping reconstruction must not
  erase a fallback checkpoint used after a singular/restored-basis failure.
- Prior work counters, shared original deadline, restored basis ownership and
  target-primal projection hints are preserved across exceptions and retry.
- A working-model certificate is never accepted for the original model. Costs,
  bounds, ordering/scaling, price/weight validity require fresh original checks.

## Task 1: current behavior and counted work

Create reproduce/cleanup_entry_census.jl and results/S5-A/ evidence. Read current
src/solver.jl::cleanup_original, src/simplex.jl initialization/recompute functions,
src/simplex_recovery.jl checkpoint ownership and src/simplex_start.jl initializer
validation. Use Test fixtures from postsolve_cleanup_performance_tests.jl,
dual_entry_phase_tests.jl, simplex_start_guard_tests.jl and presolve_tests.jl.

- [x] Complete ownership table with observer/no-observer, recovery on/off as already
  configured by each policy, expired entry, singular restored basis, projection
  success/failure and precision-boost/refinement exclusion. Cite concrete branches.
- [x] Count `_finish_workspace_initialization!` and subsequent restored recompute
  separately in process-local diagnostic wrappers around unchanged function bodies.
  Record FTRAN/BTRAN/pricing/refactor kernels, checkpoint publication, basis/primal/
  cost/price/weight state and event order; never infer a cost from iteration count.
- [x] Use Float32/Float64/BigFloat/Rational{BigInt}, both algorithm options, and
  HH native/Markowitz. Restrict additional manager cases to failure/ownership
  contracts not covered by these; no broad repeated benchmark by default.
- [x] Verify original feasible optima on normal tiny fixtures, exact same state/
  outcome between instrumented and plain controls, expected deadline/callback/
  failure provenance. Separate cold initialization from projection/ordinary cleanup.
- [x] After normal exit, independently audit pins/source, complete case keys and
  outcomes. No medium rerun; reuse completed old entry/ordinary attribution.

## Task 2: eligibility ruling and next implementation gate

Create S5-ENTRY.md; update S5 inventory, STATUS and parent plan.

- [x] Decide whether a bounded predicate can avoid default reconstruction while
  preserving every contract above. If recovery/observer/deadline semantics prevent
  material savings, reject this hypothesis explicitly instead of weakening them.
- [x] State removed/full-vector scans/solves versus added eligibility work and
  retained state. No production-code change or speedup claim in this census.
- [ ] Fresh independent numerical/work/memory review, diagnostic commit/push.
- [x] Only if accepted, write a separate implementation subplan with focused RED,
  exact state/result gates, sparse/dense cold-entry cost pairs and unchanged full
  cleanup regression. Whole S5/S6 remain open until their own acceptance gates.

Outcome: census184 exact pairs/all20audit gates accepted; unconditional omission rejected.
The conditional implementation-plan item is not applicable: no production shortcut
is qualified. See S5-ENTRY.md. Final review/push pending.
