# S6-D: artificial-row recovery reachability

> **For agentic workers:** Use superpowers:executing-plans inline, sequentially.

**Goal:** Explain the 96 historical assertions in the artificial-row recovery
budget/cancellation family before prescribing any test or solver correction.
**Architecture:** Reconcile accepted evidence, map the existing fixture and recovery
entry predicate, then execute a bounded current-source control/observed census.
No production change or relaxed oracle is authorized by this diagnostic plan.
**Tech stack:** Julia Test/TOML, existing guarded runner, Python independent pin audit.
**Spec:** ../specs/2026-10-11-simplex-core-architecture-design.md; S6-FAILURES.md.

## Constraints and review focus

CI remains disabled; no workflow dispatch, full-suite rerun, external model, old
baseline or accepted cost/reference repeat. One guarded Julia with Julia/BLAS1,
heap2GiB, VM8GiB, availableRAM6GiB, swap1GiB. Separate host absence check before
Julia/pinned-file edits. Preserve raw failures and source/environment pins.
No changed tolerances, precision, dropped coefficients or safeguards. Distinguish
naturally platform-sensitive roundoff from an invalid test expectation and actual
recovery defects; local AArch641.13.0 is not CI x641.13.1 validation.

## Tasks

- [x] Read test/native_artificial_row_tests.jl, src/simplex_phase_one.jl and actual
  row-quality/recovery callees. Reuse diagnostics/adaptive-degeneracy/artificial-row-recovery.md
  and S6-A raw inventory. Record exactly which existing tests/results already cover
  the behavior, their revisions/runtime and any differences to current source.
- [x] Map budget, checked, dual, cancel, exception, pivot and point modes across
  the existing four managers. Hypothesis only: the naturally roundoff-sensitive
  row fixture may not enter correction on the CI platform. Identify the actual
  reliability predicate and observer/callback/commit ordering; do not assume this
  hypothesis true from a missing event alone.
- [x] Prepare a diagnostic driver using unchanged existing fixture arithmetic and
  oracle. Run only the unresolved named budget/cancellation testset and matched
  control/observed (same behavior-driving callback) selected-state twins on current source. Record actual
  scalar/runtime/source hashes, initial-row residual/quality predicate from a separate fresh fixture after both attempts,
  events, return/exception, original and phase basis/primal/status, consumed work,
  artificial removal count and original-model feasibility where applicable.
  Additional probes must execute after state recording and cannot repair state.
  Existing callback-dependent cancellation/throw modes need equivalent control
  callbacks; distinguish passive recording from behavior-driving callbacks.
- [x] Audit final process, expected failure or success, all independent pins and
  actual source; exact twin comparisons and complete case accounting. Preserve
  incomplete attempts rather than labeling absent rows as passing. No benchmark
  is required for read-only diagnostics; count any diagnostic added solves/scans.
- [x] Write S6-ARTIFICIAL-ROW.md with confirmed cause or unresolved uncertainty.
  If local fixture passes, do not rerun it or call historical CI repaired. Use the
  saved CI failure expressions and operation-order analysis to choose a precise
  next experiment; platform work requires a separate concrete plan and cannot
  re-enable CI. Any proposed fixture/production correction requires its own
  RED/GREEN plan retaining budget/cancel/exception/publication safeguards.
- [x] One fresh independent numerical/work/memory review, STATUS update and
  diagnostic publication. Whole S6 and other historical failure families remain open.

Numerical/diagnostic tasks and combined final independent review complete; diagnostic publication accompanies this closure. Detailed qualification and rejected full-state comparison: S6-ARTIFICIAL-ROW.md.
