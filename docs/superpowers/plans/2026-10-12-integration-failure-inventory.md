# S6-A: integration failure and coverage inventory

> **For agentic workers:** Use superpowers:executing-plans inline, sequentially.

**Goal:** Identify the actual blockers to broad validation from existing CI and
local evidence before selecting a bounded current-source reproduction.
**Architecture:** Read-only evidence collection, classified by source/environment
and test family. No solver or workflow behavior changes in this subplan.
**Tech Stack:** GitHub CLI, Python, existing Julia test sources and saved logs.
**Spec:** ../specs/2026-10-11-simplex-core-architecture-design.md; roadmap S6.

## Constraints and order ruling

CI stays manually disabled; never dispatch a workflow. No old reference repeats,
forbidden models or aliases. Preserve raw attempts/user environments. Any later
Julia uses the existing single-process guard/limits and separate host absence
check; no Julia is needed for this inventory. Historical failures are not current
source reproductions. Broader S2/S3/S4/S5 remain open; early S6 triage makes existing
validation blockers visible before further optimization.

## Review focus

Distinguish infrastructure/timeout from assertions and numerical errors; partial
suite coverage from a full pass; older source/runtime from current source/runtime;
local accepted subplans from historical CI; solver certificate failure from a test
oracle defect. Every inventory row must name its evidence and unresolved scope.

## Tasks

- [ ] Read disabled workflow configuration and latest completed failed run plus
  last failed master run metadata. Save immutable raw logs/metadata under
  .superpowers/simplex-core-architecture/S6-A/ci-inventory-1, with SHA256 manifest.
- [ ] Extract every failure/error, exact assertion/source line, source revision,
  Julia/platform, elapsed/timeout reason and final summary. Compare the two runs;
  do not infer root cause from an assertion name. Write S6-FAILURES.md and compact
  results/S6-A/ci-inventory-1.json with raw digests and GitHub links.
- [ ] Check relevant test/src changes since each failed revision and existing
  current-source diagnostics. Mark covered, stale or unknown explicitly. Do not
  classify an unexecuted later test as passing after an earlier suite exception.
- [ ] Select the first minimal still-unexplained failure with a concrete hypothesis
  and write a separate reproduction subplan (exact files, environment, guard and
  expected oracle). No production fix without reproducible RED and cause.
- [ ] Self-check all extracted counts/links/hashes and scope, update STATUS/roadmap,
  commit diagnostic-only evidence, update continuation automation. No numerical
  benchmark for this documentation/read-only inventory.

Self-review: this bounded read-only task does not claim S6 completion or resolve
any original-model certificate failure. User standing authorization supplies inline
execution and publication; no additional confirmation is needed.
