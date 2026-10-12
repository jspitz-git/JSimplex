# S6-K: cross-precision supplied-tolerance status census

> **For agentic workers:** Use superpowers:executing-plans inline, sequentially.

**Goal:** Explain the 30 historical INFEASIBLE versus NUMERICAL_ERROR failures in
Cross-precision status uses the supplied tolerance before changing solver or tests.
**Architecture:** Reuse the exact existing primal fixture and tolerance values;
inspect original-space contradiction, stored precision, conversion/rounding,
presolve and terminal certificate/recovery ownership on current source.
**Tech stack:** Julia BigFloat tests, bounded guarded diagnostic, exact source pins.

## Existing evidence

S6-A records30 failures at bigfloat_integrity_tests.jl:282 on both Julia1.13.1x64 CI
runs. The primal slice has3 working precisions (24,53,256),5 rounding modes and2
refactor intervals, with problem/options constructed at256 bits. gap=2^-24 and
supplied tolerance=gap-2^-80. Do not assume which internal comparison causes the
status difference. Reconcile already completed BigFloat tests before new work;
local AArch64 is not CI environment proof. CI stays disabled.

## Tasks

- [x] Read the complete original test/helper definitions and existing precision/
  certificate diagnostics, inventory exact CI statuses/messages if available.
  Identify existing accepted slices; do not repeat entire integrity/corpus suites.
- [x] Map public solve option adoption, value precision ownership, ambient rounding,
  presolve infeasibility, postsolve/original certificate and NUMERICAL_ERROR paths.
  Preserve supplied tolerances exactly; no widening, precision escalation or
  weakened status assertion to make a comparison pass.
- [x] Build bounded current-source30-case primal census with unchanged constructors,
  options and ambient precision/rounding. Preserve globals after each case; record
  exact input/tolerance representations, terminal status/message, published result,
  original model preservation, actual policy and source. A separate original
  assertion slice must remain unchanged and any failed result is failure evidence.
  Passive observer twins only if observation is needed for path attribution; avoid
  redundant full solves when existing terminal evidence suffices.
- [x] Independently audit process/source/pins, all cases and exact original-model
  reasoning. Distinguish a valid conservative numerical failure from incorrect
  infeasibility or accidental loss of the supplied tolerance. If a concrete cause
  is established, write a separate focused RED/GREEN subplan before any fix.
- [x] One fresh final numerical/work/memory review; publish STATUS, limits and next
  concrete action. No full S6/CI pass or performance claim from this census.

Use one Julia/BLAS thread, heap2GiB/VM8GiB/availableRAM6GiB/swap1GiB guard, and fresh
separate host runner/child/driver absence checks. Preserve every failed attempt,
user environment and old worktree. No big/largo/AnyMOD or aliases and no repeats
of accepted S0 long, HH/scalar costs or broad corpora. Production remains unchanged.

## Reconciliation before census

Existing adaptive-degeneracy/simplex-infeasibility-tolerance.md already proves why
strict inconsistency need not certify infeasibility under independent row/column
tolerances (accepted16099 semantics and104 corpus; do not repeat). Its Float64
1024-row case differs from this 30-case BigFloat supplied-value fixture. Current
presolve_tolerance.jl uses an original tolerance envelope, then unchanged original
LP if the proof is inconclusive; simplex may return conservative NUMERICAL_ERROR.
For this fixture the exact candidate x=gap/2 has row and column violations gap/2,
each below gap-2^-80. This is an analytical hypothesis about the stale expectation,
not a replacement assertion. The census runs the unchanged primal assertion slice
once per case; adds read-only post-solve records/witness checks without a second
solve or observer. All original assertion text is retained and reversibly verified.

Census-1 completed:270pass30originalstatusfail, all19diagnostic gates. Exact g/2
witness and production original certificate accepted in30cases. Options unchanged,
no production/test edits. Final review accepted without blocking findings; do not rerun accepted matrix.
