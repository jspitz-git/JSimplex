# Simplex core architecture: progress and continuation

Updated: 2026-10-11. This is the entry point after interruption.

## Current state

**S0 local preflight/harness and S1 static inventory verified; production work remains pending. No production edits or Julia launch.**
The source baseline is `fe839aa72171d7496c9c931d9393278448c7317e`.
Completed diagnostic evidence is commit `6ded1fc`.

Active checkout:
`/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl`
Branch: `codex/simplex-core-architecture`, based on `7d6a8e1`.

Preserved planning checkout:
`/home/jspitz/.codex/worktrees/simplex-time-budget/JSimplex.jl`
Branch: `codex/simplex-time-budget` (unchanged).

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
| S0 | Frozen baseline and coverage plan | Active | Local chunk Verified (REVIEW.md); long-run implementation/calibration/reference pending |
| S1 | State ownership and validation reuse | Active | Inventory/subplan Verified (REVIEW.md); no production changes |
| S2 | Audited incremental primal maintenance | Pending | Existing kernels and missing guards inventory |
| S3 | End-to-end exact sparsity support | Pending | Support propagation and full-scan inventory |
| S4 | Refactorization memory lifecycle | Pending | Backend ownership/allocation attribution |
| S5 | Phase/cleanup handoff contract | Pending | Mapping and reusable-state inventory |
| S6 | Broad validation and final comparison | Pending | Requires accepted production chunks |

Allowed execution states: Pending, Active, Blocked (reason required), Verified,
Integrated, Rejected (evidence required). Mark an optimization Verified only after
its acceptance gate. Record individual chunks separately when a stage is partial.

## Exact next action

Characterize S1-A's owned-deadline interval before any production edit. The local
S0/S1 evidence and Python-only guard review are complete. Read
[BASELINE.md](BASELINE.md), [S1-OWNERSHIP.md](S1-OWNERSHIP.md),
[LONG-PHASE-II.md](LONG-PHASE-II.md) and the
[S1-A subplan](../../docs/superpowers/plans/2026-10-11-simplex-state-entry.md).
No global validity cache is selected. Do not claim the remaining finite checks
redundant: observers/stop callbacks, cost shifts, weights and recomputation
separate them. The simplest local DSE reuse already exists in baseline.

S0 long phase-II instrumentation, calibration and reference remain pending.
No whole-medium claim is allowed. No historical profiling slice was repeated.

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

## Initial execution milestone (2026-10-11)

- Owner: current architecture chat; active checkout above. Last source verified:
  `fe839aa`; documentation base `7d6a8e1`. Source and environment/input digests:
  `results/S0/preflight.json`.
- Host process audit: no Python/Julia numerical runner; all six old attempts
  have process reports. Four measurement attempts exit 0 with matching paired
  hashes; they end at ITERATION_LIMIT. The preserved sampling attempt exits 137.
- Milestone files: baseline, long-run method, ownership inventory, S1-A
  subplan, guard/tests/fixture definitions and compact preflight. Roadmap/STATUS
  record the accepted local deliverables. Local environment copies are untracked and excluded.
- Guard tests: initial 12 absent-runner failures then 12 passes; lifecycle and
  symlink regressions failed before their fixes; final suite 18/18 passed. Two
  independent review findings fixed, no deferred findings; see REVIEW.md. Raw logs live under
  `.superpowers/simplex-core-architecture/S0/`.
- No numerical command has been launched; no production merge performed.
  Commit identity is recorded below after the milestone commit. Push is not
  performed: automatic approval review requires explicit authorization for this
  diagnostic milestone, distinguishing it from authorized production fixes.
- Local baseline pins: `.superpowers/simplex-core-architecture/S0/expected-pins-v1.json`.
  Before S1-A launch, create new pins including its not-yet-written Julia scripts
  and every transitive dependency; this baseline set is not a complete future
  experiment manifest.
- Ruling: retain the plan's committed STATUS as authoritative and preserve all
  raw attempts instead of deleting execution scratch at finish — explicit user
  preservation requirements override generic skill cleanup. Cost: local disk use.
- Ruling: perform local S0 and S1 inventory before the long phase-II run, as the
  roadmap explicitly permits. S0 remains partial. Cost: no whole-medium evidence
  yet; prevents premature S2 performance claims.

### Local acceptance gate

S0-local and S1-inventory: Verified. Independent review found two diagnostic
runner defects; both have failing-before/passing-after regressions. Author ran
all 18 Python tests after fixes. Source hashes and absence of production diff
verified. S0-long and S1-production remain Pending within their Active stages.
No completed numerical experiment was repeated.
