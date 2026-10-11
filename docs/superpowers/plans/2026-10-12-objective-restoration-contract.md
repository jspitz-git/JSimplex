# S5-B: objective-restoration handoff qualification

> **For agentic workers:** Use superpowers:executing-plans inline and sequentially.

Goal: finish the original-cost/bound restoration part of the S5 ownership map before
any shared handoff state or certificate reuse. S5-A rejects unconditional omission
of default cleanup reconstruction; it does not close S5.

No production changes are authorized by this diagnostic subplan itself. Standing
user authorization permits progressing to a separately specified RED/GREEN change
only after identifying actual redundant work and a conservative validity contract.

## Scope and constraints

Inspect simplex_driver.jl::_run_original_objective_terminal! and
simplex.jl::_restore_original_costs!, perturbation retirement, checkpoint phase
invalidation, auto/Devex/steepest pricing resets and original-model certification.
Keep all numerical safeguards, tolerances, consumed-work budget and callback
provenance. One guarded numerical Julia; existing thread/heap/VM/RAM/swap limits.
No repeated accepted medium or component references. CI stays disabled.

## Tasks

- [ ] Map costs/bounds/journal/phase generation/checkpoints/pricing validity before
  and after restoration, including alien unjournaled bound edits and exceptions.
- [ ] Reuse existing cost_restore_allocation_tests, simplex_perturbation_integration_tests,
  basis_recovery_tests and partial_pricing_integration_tests as source evidence;
  determine which exact assertions have already run on current production before
  launching anything. Do not automatically rerun whole suites.
- [ ] Define bounded paired diagnostic fixtures for both algorithms: cost-only
  perturbation, owned bound restoration, unowned bound mutation, already-original
  state, expired shared budget and observer failure. Include changed phase/model
  checkpoint rejection. No certificate transfers from a changed model.
- [ ] Count actual restoration, scans, invalidation and reconstruction scopes with
  unchanged-body control equivalence. Separate cold handoff from ordinary pivots.
- [ ] Decide whether a concrete redundant operation has an owned validity proof;
  reject speculative caches or flags that cannot survive aliases and callbacks.
- [ ] Audit exit/pins/source/outcomes, independent numerical/work review, report,
  STATUS and diagnostic commit/push. Only then a focused implementation subplan
  if warranted. Broader S4/S5/S6 and historical CI failures remain open.
