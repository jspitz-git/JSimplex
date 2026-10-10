# Simplex time budget implementation plan

> Execute inline using the executing-plans workflow; review the final evidence independently.

**Goal:** Attribute current medium primal/dual costs without changing numerical behavior.

**Architecture:** Diagnostic-only AST wrappers count nested inclusive/exclusive time,
allocations and GC. Independent sampling and uninstrumented reference runs expose
probe overhead. Reuse historical cleanup handoffs as explicitly labelled replays.

**Constraints:** Master fe839aa; Float64, HH/native320, legacy steepest-edge,
partial pricing off; one numerical process, one Julia/BLAS thread; existing
8 GiB VM / 6 GiB RAM floor / 1 GiB swap guard. No excluded inputs. No source changes.

**Review focus:** Double counting, compilation, instrumentation perturbation,
historical-state representativeness, phase/cleanup boundaries and missing results.

- [x] Build nested accounting with a synthetic nested/exception probe; verify
  that exclusive totals reconcile with outer elapsed time.
- [x] Measure medium primal 2,000-step and dual 4,000-step prefixes plus 256-step
  cleanup continuations from each saved origin. For each, warm short path, run
  reference, sampling profile, then census. Compare event/state fingerprints.
- [x] Separate read/setup/presolve, ordinary iterations, certificates and recovery;
  report counts and non-overlapping totals, compilation, GC, allocation, dimensions.
- [x] Inspect dominant stacks and source traversal bounds. Expand only if the
  initial evidence cannot distinguish the principal costs.
- [x] Audit, independently review, document limitations and prioritized findings;
  commit diagnostic evidence. No production optimization in this task.

Ruling: cleanup replays preserve their historical options (HH/native160), while
new prefixes use HH/native320. They diagnose distinct phases, not a controlled
interval comparison. Export the actual serialized options separately.

Execution note: sampling completed for both prefixes. The first cleanup sampling
attempt stalled and was preserved with exit137 and thread observations. Both
cleanup reference/census comparisons then completed without starting Profile;
this explicit diagnostic fallback does not change solver sources. The final
independent review approved the evidence with the long phase-II coverage gap
and instrumentation limitations retained.
