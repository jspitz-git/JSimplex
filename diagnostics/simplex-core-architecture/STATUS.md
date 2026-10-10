# Simplex core architecture: progress and continuation

Updated: 2026-10-11. This is the entry point after interruption.

## Current state

**Planning only. No implementation or numerical job was started by this plan.**
The source baseline is `fe839aa72171d7496c9c931d9393278448c7317e`.
Completed diagnostic evidence is commit `6ded1fc`.

Planning checkout:
`/home/jspitz/.codex/worktrees/simplex-time-budget/JSimplex.jl`
Branch: `codex/simplex-time-budget`.

- [Implementation roadmap](../../docs/superpowers/plans/2026-10-11-simplex-core-architecture.md)
- [Design and constraints](../../docs/superpowers/specs/2026-10-11-simplex-core-architecture-design.md)
- [Baseline measurements](../simplex-time-budget/README.md)
- [Detailed results](../simplex-time-budget/RESULTS.md)
- [Diagnostic review](../simplex-time-budget/REVIEW.md)

Do not assume master remains at the recorded baseline. Check actual refs and
preserve user changes before creating an implementation branch. At planning,
this checkout contains untracked Manifest.toml and LocalPreferences.toml;
main also has a user-modified .vscode/settings.json. Do not stage those files.

## Stage ledger

| ID | Deliverable | State | Evidence / next action |
| --- | --- | --- | --- |
| P0 | Design, roadmap, continuation record | Done | This documentation; production unchanged |
| S0 | Frozen baseline and coverage plan | Pending | Inspect current refs/processes; write BASELINE.md |
| S1 | State ownership and validation reuse | Pending | Mutation/dependency inventory first |
| S2 | Audited incremental primal maintenance | Pending | Existing kernels and missing guards inventory |
| S3 | End-to-end exact sparsity support | Pending | Support propagation and full-scan inventory |
| S4 | Refactorization memory lifecycle | Pending | Backend ownership/allocation attribution |
| S5 | Phase/cleanup handoff contract | Pending | Mapping and reusable-state inventory |
| S6 | Broad validation and final comparison | Pending | Requires accepted production chunks |

Allowed execution states: Pending, Active, Blocked (reason required), Verified,
Integrated, Rejected (evidence required). Mark an optimization Verified only after
its acceptance gate. Record individual chunks separately when a stage is partial.

## Exact next action

Execute S0's read-only preflight, then prepare BASELINE.md and the S1 mutation
inventory. Reuse the completed time-budget evidence; do not rerun all four slices
merely because the conversation restarted. Prepare the long phase-II coverage
method before making whole-medium claims, but do not block the local S1 inventory
on a multi-hour run. No production edits or Julia launch are required for the
initial inventory.

## Evidence gaps and traps to retain

- Long reduced-model medium phase II is not covered by the prefix/cleanup study.
  Event snapshots are not complete pricing-state checkpoints.
- Fresh prefixes are HH/native320; historical cleanup is HH/native160. Both
  cleanup origins execute primal steps. Their origin labels are not algorithms.
- Existing measurements are mostly single paired timings and HH-only. They are
  not complete cross-manager or cross-solver performance comparisons.
- Sampling perturbed prefix timings substantially and cleanup sampling stalled.
  Preserve the failed attempt; use calibrated counters/plain runs for cleanup.
- Refactorization elapsed time includes substantial GC. Allocation event counts
  include presolve. Neither proves expensive ordinary update arithmetic.
- The user's test.mps HH/native320 dual certificate/recovery failure remains a
  separately reported case; these profiling slices do not establish its resolution.
- Existing paired-FTRAN experiments were inconclusive; do not repeat or promote
  them without a new hypothesis. Do not reintroduce removed adaptive heuristics
  into the numerical core while changing architecture.

## Resume checklist

1. Read this file, the plan, spec and latest stage report.
2. Inspect actual branch/ref/status and local instructions; preserve user dirt.
3. Inspect all numerical processes, runner state and logs. If one is active,
   do not start another or edit its pinned source/environment. A stale PID file
   is not proof of a live owned process; verify start identity and command.
4. Audit finished reports and process exit reasons. Missing reports, timeouts,
   resource kills and iteration limits are not successful solves.
5. Preserve interrupted attempts. Restore execution only after confirming process
   ownership, source/input digests and whether the runner safely supports resume.
6. Continue the first unchecked task. Record a changed hypothesis or order before
   spending another long run. Never repeat a completed experiment without reason.

## Per-chunk record (fill when execution starts)

- Stage/chunk ID and hypothesis:
- Status; current owner and checkout/branch:
- Last verified commit; current source/script/environment/input digests:
- Uncommitted files and purpose:
- Baseline/candidate commands and guarded output directories:
- Active runner identity or confirmed stopped state:
- Completed attempts; incomplete/failed attempts and reasons:
- Numerical evidence, work/allocation evidence and timing uncertainty:
- Review findings; commit, integration and push IDs if performed:
- Next exact action; blocker or rejected approach if any:

Keep portable summaries committed; retain large local logs and snapshots in
`.superpowers/simplex-core-architecture/`. Update this ledger before handoff and
after every verified/integrated chunk. Never store secrets in continuation notes.
