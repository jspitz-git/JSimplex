# S6-B: bounded pricing refresh failure reproduction

> **For agentic workers:** Use superpowers:executing-plans inline, sequentially.

**Goal:** Explain the actual control path behind the historical preference-work
failure before changing a test oracle or production recovery.
**Architecture:** Execute only the existing named failing testset in a guarded
process and a separate diagnostic twin with a read-only event observer; preserve
the original failed oracle and report terminal/primal/basis/refactor counts.
**Tech Stack:** Julia Test/TOML/SHA, existing guarded runner and Python audit.
**Spec:** ../specs/2026-10-11-simplex-core-architecture-design.md, roadmap S6.

## Constraints/review focus

No production or existing test edit, CI stays disabled, no old reference repeats.
Single numerical Julia, Julia/BLAS1,heap2GiB,VM8GiB,availableRAM6GiB,swap1GiB.
Separate fresh host absence check first; immutable source/environment/script pins.
Do not infer a CI-platform fix from a local aarch641.13.0 result. A normal returned
iteration is not a terminal certificate. Read-only observer must not be presumed
neutral: compare diagnostic twin state with observer-free state exactly.

## Tasks

- [x] Locate the existing testset by Julia syntax nodes, execute its unmodified
  body inside a parent Test testset; retain failed assertion/error output with
  expected nonzero exit. Avoid other accepted tests and external inputs.
- [x] Before executing the original test oracle, run observer-free and observed
  twins of the fixture from the same actual source. Record returned status or
  nothing, event sequence, consumed iterations/refactors, basis/primal/costs/prices,
  point certificate/original feasibility and FTRAN residual. Record source hash,
  Julia version/architecture/thread counts and whether twin state agrees exactly.
  No claim the injected factor represents the current basis.
- [x] Audit process exit/pins/source and match failure counts, keep failed raw data.
  Trace selected candidate/retry logic using src/primal_simplex.jl and
  src/legacy_primal_pivot.jl (resolve actual source file names first). If a further
  observation is needed, state a new hypothesis without modifying the first run.
- [x] Record cause or remaining uncertainty in S6-FAILURES.md. A proven needed fix
  requires its own RED/GREEN subplan, numerical/work review and integration gate.
  Current reproduction alone never authorizes weakened checks/tolerances.

Completed with preserved harness failures and separate clean oracle. Oracle-1
2pass/2fail/1error,10audit gates. Preference-3 twins agree but its oracle was invalid;
S6-FAILURES.md keeps those scopes separate. No production/test edit or CI repair.
