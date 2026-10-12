# S6-H: dual recovery reachability census

> **For agentic workers:** Use superpowers:executing-plans inline, sequentially.

**Goal:** Reconcile the 48 historical dual-pivot recovery CI assertion failures
with current source behavior before proposing any solver or test change.
**Architecture:** Use the unchanged four-row exact-duplicate fixture and original
oracle; record actual dual ratio/direction consistency and recovery events using
separate matched fixtures. No forced row output, altered policy or production hook.
**Tech stack:** Julia Test/TOML, existing guarded runner, independent source/pins.

## Existing evidence and scope

Read test/dual_pivot_consistency_tests.jl, the historical inventory in
results/S6-A/ci-inventory-1.json, and diagnostics/adaptive-degeneracy/
dual-pivot-consistency.md. Historical focused851/851 includes216 assertions in
this file and broad semantic/corpus evidence is accepted; do not repeat that
corpus. Later CI1.13.1x64 fails48 assertions in recovery/cancellation groups.
Source-identical CI runs do not establish a source regression. Local AArch64
passes are not x64 proof. S6-F/G controlled artificial-row fixture is independent.

## Tasks

- [x] Inventory exact failing predicates/evaluated values by testset and manager
  using preserved CI logs. Reconcile prior local diagnostic source/options before
  claiming the original duplicate fixture is portable or recovery is reached.
- [x] Map dual_iteration! ratio, FTRAN/BTRAN agreement, transactional rejection,
  observer wrapping, candidate/recovery budgets, refresh and publication ownership.
  Determine which failure assertions require a particular event to occur. Keep
  exact duplicate/singular-basis rejection distinct from recovery-path coverage.
- [x] Create a bounded current-source census on the unchanged small fixture:
  four managers, four rejection modes and cancellation after refresh. Preserve
  behavior-driving callbacks in both twins; only passive event recording differs.
  Record selected state, terminal/exception identity, event counts, work budgets,
  scratch rejection sets and factor update count. Independent fresh-fixture
  direction/row/ratio probes run after the twins, never perturb their scratch.
  Run exact original selected oracle once; preserve a failure as evidence.
- [x] Audit final process/exit, whole independent pins, actual source and selected
  equality/failed-predicate counts. Report unknown CI numerical path honestly.
  If a concrete reproducible cause emerges, write a separate bounded RED/GREEN
  subplan; do not weaken assertions or modify production in this census.
- [x] One fresh independent numerical/work/memory review before diagnostic closure;
  publish STATUS and precise next action. No full S6 pass from this subset.

## Resource and acceptance constraints

One numerical Julia with Julia/BLAS1, heap2GiB, VM8GiB, availableRAM6GiB and swap1GiB
under the existing guard; no big/largo/AnyMOD or aliases. Before launch/editing
pins, independently verify previous runner/child/driver absent using host identity.
Retain all failed attempts/user files and keep CI disabled. No accepted medium,
HH/scalar, S0 or whole-corpus repeats. No same-size symbolic reuse or working-model
certificate transfer. This diagnostic adds no production cost and claims no speedup.

Closure:20pairs/108original oracle,17gates601pins; independent review no findings.
Reports S6-DUAL-RECOVERY.md and S6-DUAL-RECOVERY-REVIEW.md. S6-I remains qualification.
