# Simplex core architecture: progress and continuation

Updated: 2026-10-11. This is the entry point after interruption.

## Current state

**S1-A, S3-A and S4-A integrated; master `d8ad4ec` pushed. S0-L counted dual reference audited; S2-A candidate qualification active.**
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
| S0 | Frozen baseline and coverage plan | Active | Counted dual long reference audited; plain elapsed and primal-origin coverage pending |
| S1 | State ownership and validation reuse | Integrated | Inventory and local S1-A contract; master beb161b, report S1-ENTRY.md |
| S2 | Audited incremental primal maintenance | Active | Private audited-flip prototype: control1000, matrix960, safety139; cost and final review pending |
| S3 | End-to-end exact sparsity support | Active | S3-A integrated at masterd8ad4ec; RED/GREEN, matrix1645, focused3214+LP70, cost120, reviewed; broader S3 pending |
| S4 | Refactorization memory lifecycle | Active | S4-A integrated at master4143dad; RED/GREEN, focused4366, paired cost60; broader attribution pending |
| S5 | Phase/cleanup handoff contract | Active | Partial static phase/cleanup ownership map; no implementation |
| S6 | Broad validation and final comparison | Pending | Requires accepted production chunks |

Allowed execution states: Pending, Active, Blocked (reason required), Verified,
Integrated, Rejected (evidence required). Mark an optimization Verified only after
its acceptance gate. Record individual chunks separately when a stage is partial.

## Exact next action

S3-A production cd91a1a -> masterd8ad4ec5651225a512d5f533f48ce7d8fc8f90cc is reviewed,
integration-tested1645/1645 and pushed. Diagnostics milestone1c6ee5d is pushed.
Main user-file preservation checks passed. S0 counted dual long reference audit
passed; separate plain elapsed and primal-origin coverage remain pending.

Continue docs/superpowers/plans/2026-10-11-primal-flip-audit-prototype.md.
S2-A control census passed80cases/1000assertions. Work RED passed6state checks and
failed2 intended solve-count assertions8/4 versus5/1. Work-green-1 failed only in
module loading; fixed explicit Symbol entries. Work-green-2 passed12/12 including
mandatory endpoint refresh, retained basis/prices, original certificate and5/1work.
Private prototype is reproduce/primal_flip_prototype.jl; no production change.
It clones six exact source definitions into a private module with source hashes,
AST anchors, context-owner checks and no overwritten production methods.

candidate-matrix-1 passed960/960 across80cases. safety-contracts-2 passed139/139;
the first attempt's erroneous generation expectation is preserved and corrected
from recompute! source. Current sole numerical job: S2-A/focused-1, existing
primal-update/point/direction-price regressions. Verify current.json start_ticks
and boot identity; inspect final process.json and separately confirm host absence
before any next Julia or pinned edit. New unexecuted drivers are primal_flip_dirty_entry.jl
and primal_flip_cost.jl; run dirty-entry then cost after focused completion.
Cost qualification and independent review remain open; no speedup or production
qualification claimed. Latest pushed checkpoint845aadb precedes these additions.

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
  Milestone commit: `150aea5fea0a441160fd6338efa0de80c201d4a8`, pushed to
  `origin/codex/simplex-core-architecture` and verified with `git ls-remote`.
  Automatic approval initially distinguished diagnostic pushes from the standing
  production-fix authorization; the user then explicitly approved this branch
  push. The refusal is resolved. Master remains at `fe839aa`.
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

### Published continuation checkpoint

The initial local milestone is committed and pushed as `150aea5`. This small
follow-up records the confirmed remote identity and is pushed on the same branch.
The next task is the first unchecked S1-A characterization gate. No numerical
runner is active; do a fresh host process check before any Julia launch. Long
phase-II measurement remains pending; no prior measurements need repetition
until a new instrumentation or production-change hypothesis requires comparison.

## S1-A execution started

Preflight on 2026-10-11: HEAD 94442cf, master/origin at fe839aa; no numerical
process on host. Characterization completed. New contract tests and dedicated
work-count probe written before production changes. First guarded RED attempt
is about to run under `.superpowers/simplex-core-architecture/S1-A/red-1`.
No other Julia launch is allowed while this attempt owns the guard.

S1-A RED completed: process exit1, unchanged pins, 25 passes / 3 intended
work-count failures (9 vs 7 checks for two pivots). Candidate changes are limited
to dual_simplex.jl and three context-only deadline call sites in solver.jl; new
contract tests are included in runtests.jl. Candidate source patch/new files are
retained with green-1. The first normal-compilation focused attempt is still
running under its 600-second guard; inspect its process.json before any next
launch or pinned-source edit. No production commit/merge has occurred.

S1-A green-1 ended at the 600-second wall limit, exit -15, pins unchanged.
The termination stack identifies Julia type inference/backedge storage in
`simplex_precision_recovery_state_tests.jl:58`; no test-failure output. This is
incomplete evidence, not a passing suite or numerical failure. Host confirmed no
remaining Julia. Next: normal focused tests with per-file output, a separate
compile=min precision-recovery semantic run, then work counts and paired timing.
Static independent review found no production correctness or unnecessary-work
defect; four validation gaps are being closed. Raw attempts remain preserved.

S1-A validation checkpoint: green-2 was deliberately interrupted after about
280 seconds via its verified runner identity. Four completed normal-compilation
files passed 469 assertions (242 new contract, 71 weights, 125 residual, 31
certificate reuse). The remaining dual-entry file was compiling in LLVM at
line 85; guard cleanup ended with -9, pins unchanged. semantic-1 separately
passed precision-recovery-state (30) and dual-entry-phase (182) under compile=min,
exit0/pins unchanged. No timing claim is drawn from semantic mode.

count-1 passed all 41 assertions, exit0/pins unchanged. Two ordinary pivots use
7 instead of 9 finite checks: steepest-edge/Devex visit 112 instead of 144 vector
elements; Dantzig 84 instead of 108. Successful price repair retains its first
entry check; auto/existing-state/adaptive-policy exclusions retain check counts.
The counter sums lengths at each actually executed hardware-float scan, whose
loop visits every element; skipped arrays contribute zero.

paired-1 is now running baseline and candidate in independent modules in one
guarded Julia process, with identical sparse/dense fixtures and all five managers.
It compares full event/state fingerprints separately from three interleaved warm
plain timing/allocation pairs. Both source trees and all shared scripts are pinned.
Inspect its process.json before editing any pinned file or starting another job.

paired-1 deliberately stopped: author found a diagnostic comparator defect.
Baseline used ()->false rather than its real context clock closure. Earlier
state/hash matches are useful, but timings are rejected as production before/after
evidence. Process exited via owned guard cleanup (-9), pins unchanged; old scripts
are saved inside the attempt. The corrected helper uses each revision's actual
context-only stop factory and tests expiry equivalence before measurement.
Next runs: broad semantic boundaries, then corrected paired-2.

Boundaries-1 passed 780 assertions, exit0/pins unchanged. External-1 is active
under a 900-second guard, using the frozen five-case external manifest, both
algorithms, all five managers and native/Markowitz factorization. Its source and
measurement scripts are also copied into source-snapshot/ before later edits.
Measurement review accepted the corrected real-clock comparator but requests
trace/plain cross-checks and complete event-name/count/refactorization metadata
before paired-2. Production source has not changed since the focused tests.

External-1 completed normally: all 100 combinations OPTIMAL, original-primal
certified and reference-objective matched (305 assertions), pins unchanged.
Process group and runner confirmed absent on host before diagnostic edits.
The benchmark review fixes now compare trace/plain entry and final states,
steps/refactorizations and complete event names/counts scoped to the measured
kernel. Unused prototype scripts are retained under unused-prototypes/.

Baseline-precision-1 is active: original project/source at preserved 7d6a8e1,
normal compilation, only the unchanged precision-recovery-state file, 300-second
guard. This control determines whether the earlier compilation problem also
occurs without the candidate; no numerical benchmark is concurrent. Actual test
file and helper outside the baseline test tree are explicitly pinned. The local
launch helper is preserved as attempt-launcher.py for reproducibility.

Baseline-precision-1 ended at its 300-second wall limit, exit -15, pins unchanged.
The old production source also stalls in type inference (precision-recovery-state
line 31; candidate combined run had reached line 58). This reproduces an inability
to finish bounded normal compilation without the candidate; it does not establish
equal compile costs or a full-suite pass. No original checkout file was changed.
Paired-2 is active with the corrected deadline comparator and reviewed metadata
checks, 600-second guard. Both baseline/candidate source trees are pinned.

Paired-2 passed all 10 sparse/dense manager cases, 30 interleaved timing pairs
plus separate traces, exit0/pins unchanged. All entry/final/completion states,
event sequences/counts and step/refactorization counts match; trace/plain checks
also pass. Allocation bytes/counts equal, measured compilation zero. Tiny-case
timing scatter is reported without a universal speedup claim in S1-ENTRY.md.
Medium-dual-1 candidate prefix is active, 600-second guard, 4000 HH/native320
steps plus a separately warmed census with actual vector-element counting.
A new baseline run is justified by this new element metric and production change;
the old report only counted helper calls. No sampling/profiler run is repeated.

Medium-dual-1 completed, exit0/pins unchanged. The 4000-step HH/native320
candidate plain and census runs have identical hashes/events and zero measured
compilation. Candidate also exactly matches the historical baseline status,
iterations, event/state hashes, event counts and input hash. Finite-workspace
calls are 12004 versus historical 16004; actual candidate vector visits are
26287751664. This remains ITERATION_LIMIT, not a solved LP.
Medium-dual-baseline-1 is active on the preserved old source with the same new
element counter; this closes the missing baseline element metric. Runtime dual
paired validation and final acceptance/integration remain pending.

Medium-dual-baseline-1 completed exit0/pins unchanged; its long warm-up did not
hit the guard. Fresh baseline/candidate plaintext and census trajectories match.
Actual element visits: 35047415664 -> 26287751664, saved 8759664000 (24.994%).
Runtime-dual-baseline-1 is active (512-step prefix, old source, 600-second guard);
then run the candidate with identical input/scripts/options and compare hashes.
No production source edits since focused validation; no master integration yet.

Runtime-dual-baseline-1 completed exit0/pins unchanged. On resume the candidate
attempt had not started; runtime-dual-1 is now the sole guarded Julia process,
600-second limit. See its current.json and resources.jsonl. All 507 source/test
files still match seven accepted candidate-validation pin sets. Remote master
is fe839aa and diagnostic branch 94442cf. Final independent review accepts local
integration conditional on the runtime gate; no new blocking finding.

Runtime-dual-1 completed exit0/pins unchanged. Its four-way trajectory comparison
passed, with 62230448 fewer actual element visits; only finite-workspace calls
change (2055 -> 1796). Independent review and all S1-A local gates are complete.
All 507 source/test files match eight candidate validation pin sets. No Julia
process remains; source files can now be committed. Full normal-mode project
suite remains incomplete (old-source compilation timeout also reproduced).
Do not repeat numerical measurements without a new reason.

## S1-A integrated milestone

Architecture production commit 8e0a7c7; master cherry-pick beb161b, pushed. Only
two production files and three test files were integrated; diagnostics remain
on the architecture branch. Final staged whitespace check removed one trailing
blank line from the test helper after the main validation; production code did
not change. integration-1 passed all 242 new contract assertions directly from
master under compile=min, exit0/pins unchanged. No numerical process remains.

Portable results include 15 attempt records and source digests; full raw evidence
is preserved locally. 1807 accepted validation assertions plus 242 integration
assertions passed; no complete normal-mode suite or whole-medium solution claim.
Next: S0 long-run diagnostic subplan, implementation and calibrated short runs.

S0-L started after integrated S1-A: concrete subplan
docs/superpowers/plans/2026-10-11-simplex-long-instrumentation.md. First launcher
call failed before Julia because the new stage directory did not exist; corrected.
counts-red-1 then failed as intended on missing counter implementation, exit1,
pins unchanged. Count-only implementation/tests are uncommitted; normal guarded
counts-green-1 is next. No long solve or calibration acceptance yet.

S0-L counts-green-1 passed 39 assertions with normal compilation, exit0/pins
unchanged. Count-only pilot calibration is next: a new instrumentation test,
not another S1 baseline/candidate benchmark. Sparse/dense HH, five interleaved
pairs of 32 prepared kernels, separate trace verification. L2 chronology and
medium/both-algorithm calibration still pending. Production remains unchanged.

Active S0-L attempt: count-pilot-1, guarded 300 seconds on preserved baseline
7d6a8e1. Inspect process.json/current.json before edits or any Julia launch.
The count-only pilot does not qualify long-run instrumentation; L2 windows and
full calibration remain mandatory. Published diagnostic milestone is 1fcaa16;
master remote verified at beb161b. Current S0-L files are diagnostic-only.

## S0-L2 stopped checkpoint

window-pilot-1 completed exit0/pins unchanged. Sparse chronology overhead 11.90%
exceeds the 5% gate; dense 2.02%. Final state/step comparisons and zero measured
compilation checks passed, but these do not override the performance rejection.
All source/script pins verified again; runner and child absent, no Julia process.
Tests/results/failed attempts and the exact next hypothesis are recorded in
S0-LONG.md. No S0 production changes; no long reference. Stop follows the user's
explicit instruction to continue only until encountering a problem.

Resumed after explicit user request. Preflight: master/origin beb161b, architecture
4070155, user environments/dirt preserved, no Julia or guard process. New
event-ablation-1 isolates none/counts/noop/recorder in one baseline module, with
rotated order and identical operation counts/state. It asserts no cold regions
or periodic writes occur in the measured sparse batch. This tests event overhead
instead of repeating the failed whole-recorder pilot unchanged.

## Static work during the sole L3 process

S3-INVENTORY-NOTES.md maps current exact-support propagation, dense rebuilds,
manager fallback/invalidation and dense consumers. Partial map independently
reviewed; numerical counts and S3 subplan remain pending. S5-INVENTORY-NOTES.md
records phase/cleanup ownership and potential redundant initial reconstruction;
review accepted the partial map; full inventory still pending. Neither document changes pinned code.

S2 bounded proposal docs/superpowers/plans/2026-10-11-primal-flip-audit-prototype.md
has passed independent design review: unchanged-basis flips only, every candidate independently
point-certified, original reconstruction/fallback and mandatory endpoint refresh.
No incremental flags, default change or unsupported forward-error estimate. A1
context/hook/alias ownership and endpoint state table are resolved; freeze, branch
characterization and RED remain pending before implementation. S2 broader
pivot controller remains open. All numerical work waits behind the active L3 job.

S2-A design is independently accepted. New unexecuted control fixtures and
characterization driver cover80 planned cases (Float32/64,5managers,2backends,
4branch recipes). Static review confirms API/reset and scheduled-refactor setup;
its requested reason-specific assertion records exactly one limit refactor and
no other refactor reason, separated from final certification. The census is NOT
run or accepted, and no prototype implementation exists. Execute only after the
current S0 process exits and its host identity is confirmed absent.


S3 static writer review found two pending safety cases: accepted refinement into
an AbstractVector view does not invalidate the owned parent support by identity;
LP witness projection writes rho after refactor_other allows an observer to build
metadata for the fresh zero scratch. New diagnostic pipeline_boundary_regressions.jl
prepares whole-vector/no-metadata controls and view/observer cases. NO Julia run,
RED evidence or production fix yet. Prioritize this narrow reproduction at the
next free serial slot; do not interrupt or modify the active S0 reference.


Diagnostic e519fbe is pushed. Static review accepts the S3-A reproduction and
small subplan 2026-10-11-pipeline-boundary-invalidation.md; its first numerical
step remains RED on unchanged production after S0 releases the guard. The S3
writer map now explicitly qualifies view aliases and observer-created metadata.
S0 partial-attribution snapshot: iteration125952,90247 phase-II steps, no final
certificate. Pins matched at snapshot; raw prefix and compact report preserved.
Refactorization178.2594s includes157.4598s GC, so it is not an arithmetic timing.


Next-slot command is prepared but MUST NOT run before S0 release:
`python3 /tmp/jsimplex-s3-attempt.py boundary-red-1 <active>/diagnostics/simplex-core-architecture/reproduce/pipeline_boundary_regressions.jl smoke --seconds 600`.
The new helper targets S3-A, freezes src/test/environment/scripts and uses the
same existing guard/launcher. It was Python syntax-checked only. Check process.json,
then host runner/child/driver absence in a separate call before launching.
S5 inventory now records callback-visible initial reconstructed state, prior-work
assignment timing and constructor failure ownership; no S5 source change.


## Automatic continuation and live cleanup checkpoint

Diagnostic checkpointbb1bdd5 is pushed. The attached-thread heartbeat
`pokra-ov-n-v-voje-jsimplex` is ACTIVE, checking every5minutes to continue after the
sole numerical job releases its guard. It is instructed to remain quiet while
unchanged, audit final evidence first, then execute the reviewed S3-A RED and
subsequent plan autonomously. This scheduling is not another numerical process.
Respect any newer human stop/scope instruction; disable the heartbeat on completion
or when actual user intervention is necessary. Check app automation state rather
than assuming this local scheduling follows the repository to another host.

The live reference reached original-model cleanup at iteration234380. Completed
phase-II windows and their counters/sections are preserved in
results/S0-L/medium-dual-counted-1-phase-two-end.json with the raw prefix digest.
This remains running partial evidence, NOT an accepted final medium certificate.
Pins matched at capture. The same runner268789/Julia268790 remain active; do not
launch S3 or change pinned files until final report and separate host absence checks.


## Completed S0-L medium dual counted reference

medium-dual-counted-1 exited0, pins unchanged and independently reverified.
Post-exit long_audit JSON passes every gate: OPTIMAL, explicit original primal
feasibility, observed internal optimality certification,256 complete windows with
exact counter sums,198675 actual dual phase-II steps (3634.343694575s).
Total255798 steps includes21418 original-model primal cleanup steps.
Counted elapsed5926.881033309s includes0.022926199s compilation and503.750702521s
GC; this is not a compilation-free or authoritative plain timing comparison.
Objective2.2389455645278454e7; final primal digest and exact baseline source,
allowed medium hash, final reports and phase totals are preserved in
results/S0-L/medium-dual-counted-1-audit.json and companion raw report copies.
Separate plain elapsed and primal-origin references remain pending; no speedup
or whole-S0 completion is claimed. Guard/Julia/driver268789/268790/268787 were
confirmed absent in a separate host call after the final process report.
Next: execute the prepared S3-A boundary-red-1 before any production edit.

S3-A B1 confirmed both hypotheses: boundary-red-1 has27pass/5intended failures,
no errors; controls pass and corrected dense values/certification pass. Exit1,
pins unchanged; host runner/child/driver absent. Minimal invalidation changes
applied after RED; identical smoke GREEN next, no production commit yet.

S3-A identical smoke GREEN passed32/32,exit0/pins unchanged; runner280264/
Julia280265 and driver absent. Extended production regression covers250
precision/manager/backend/destination combinations, all six scratch aliases,
no-cache/rejected-write/model-alias contracts and witness callback provenance.
Extended matrix is prepared, not yet accepted.

S3-A boundary-matrix-1 passed1645/1645 with normal compilation; pins unchanged.
All5precisions/5managers/2backends supported in this fixture. Existing focused
pipeline/refinement/projection/guard regressions are now the sole numerical job
(boundary-focused-1). Production/test changes remain uncommitted pending gates.

S3-A focused-1 completed3214pass/0fail/3errors,exit1/pins unchanged. All three
errors are UndefVarError(lp_recovery_fixture) in lp_refinement_state_tests: the
diagnostic driver omitted its lp_refinement_recovery_tests dependency. Source
unchanged. Ruling: add the missing include and rerun only the LP recovery/state
group, retaining the3214 passed assertions; no repeat of the completed broad
solver matrix. Runner280590/child280591/driver absent before driver repair.
Cost driver additionally asserts actual cache/no-cache setup before timing.

LP recovery/state follow-up passed70/70,exit0/pins unchanged. Cost-1 failed
before producing a report: its measurement row inferred Dict{String,Real} and
could not accept later String labels. No accepted timing evidence from that
attempt. Fix only report container type to Dict{String,Any}; new cost-2 attempt
keeps the measurement workload unchanged. Exit1/pins unchanged, host process
absence confirmed before editing.


## Historical S0/S4 handoff snapshot (superseded)

S0-L2 current calibration gates pass for the actual L3 environment. Kernel10
passes sparse4.64385%/dense2.96326%; full suite3's five other gates pass, while
its medium-primal5.90404% remains explicitly FAIL. The reviewed process-isolated
follow-up completed all12 serial samples, ratio-of-medians0.24214%, compile0,
matching results/options/policy and exact counted window sums, retained2880B.
All process reports are exit0/pins unchanged. Host verified final runner266320,
child266321 and orchestrator264004 absent. Subsequent smoke passed and L3 is
now active as recorded below.
Read results/S0-L/isolated-primal-calibration-1.json and provenance/attempt records.
Independent L2 review accepts this deployment-matching calibration. The isolated
prefix driver returned empty primal_hash/objective=nothing, so matching result
metadata is not a new exact final-state hash check; full suite3's earlier separate
trace gates remain the state evidence. Smoke subsequently passed; long medium certification remains open.

S4-A is integrated and pushed: architecture8701a58 -> master4143dad27581cf1230fa74203306f956b89109a6.
RED6pass/2intended failures, GREEN344pass, normal focused4366pass, paired cost60
records, master integration344pass; all completed pins unchanged. Independent
review accepts the local memory fix, with no unnecessary work/retention finding.
See S4-SCRATCH.md. Same-size allocation cost unchanged; obsolete four-vector
capacity released after dimension changes. No timing speedup or whole-S4 claim.
Master remote identity verified; old worktrees, local environments and main user
files preserved. No S4 runner remains.

driver-smoke-1 passed: exit0/pins unchanged, OPTIMAL/original-primal feasible,
certificate observed,7 phase-II steps,5 complete windows and exact counter sums.
Its JSON chronology_reference_success=true. Host verified runner268482/child268483
absent. Calibration and smoke permit long launch, not a medium-success claim.

Current sole numerical job: S0-L/medium-dual-counted-1,43200-second guard,
counted dual medium, step cap1000000, old planning baseline. Runner268789
(start_ticks16921100), child268790 (start_ticks16921182), boot ID
20de7dde-704e-41c8-bee7-b8511c0a86b0; verify current host identity, not PID alone.
Pins digest a24597f2ddb774e72ade444c01c3f25f255b2c55b40ba4a1a47556f257f5fa7e.
Raw reference.toml/windows/current/resources/process are under the attempt path.
current.json reason=launch_error is the runner's pre-launch placeholder, not a
final outcome; inspect host identity/resources and final process.json.
Do not edit any pinned old src/test/env or active diagnostic Julia file, and do
not launch another numerical process while it runs. Read only completed windows;
no final status/certification is inferred before process exit and JSON audit.

Diagnostic checkpoint8f87306 is pushed. The current diagnostic checkpoint includes S4 inventory/subplan/results,
suite3 attribution and isolated-calibration evidence. Main user dirt and all
worktrees/environments remain intact. S2 static prerequisite mapping is reviewed;
the bounded flip design is accepted for private qualification; pivot controller and numerical work
remain pending. S4 broader attribution
is also pending; the integrated fix concerns four private solve/preparation vectors.

Long reference is now active. Its guarded baseline is the preserved
7d6a8e1 checkout (productionfe839aa), allowed medium hash, live1024-step windows,
1000000-step cap and external12h guard. Preserve every limit/failure as incomplete.
A separate plain elapsed run and primal-origin reference remain later serial work.
User explicitly requested continuous execution through diagnostic failures.

S1-A production commit `8e0a7c7def505604ccfe50cdbc2cf9cee453092d` was integrated
as master `beb161b310afd9dc7126eca98e3c15898a69efbf` and pushed. Its accepted behavior remains in the subsequent S4-A production
tree. Diagnostics/experiments are separate on the architecture
branch (published S1 evidence: 1fcaa16). All worktrees and local environments,
including main's modified .vscode/settings.json, remain preserved.
Read [S1-ENTRY.md](S1-ENTRY.md) for accepted local savings and coverage limitations.



## S3-A integrated milestone

Productioncd91a1a -> masterd8ad4ec; reviewed and pushed. Smoke32,extended1645,
focused3214 successful assertions plus missing-fixture errors closed by targeted
LP70, cost120, allocation-attribution28, master integration1645. All attempts and
failures preserved; no source change after first smoke GREEN. WholeVector body
unchanged, measured0B/0events; timing mixed, no speedup. Alias invalidation adds
bounded6metadata checks and necessary later support rebuilds. Generic view
benchmark boxing and nonspecialized single-call overhead explicitly documented.
No broader S3 completion or whole-medium improvement claim. Next S2-A census.


S2-A control-census-1 is active under the guard; runner282455 (start_ticks17692061), Julia282456 (start_ticks17692145), boot20de7dde-704e-41c8-bee7-b8511c0a86b0. Verify current identity. No S2 candidate exists.
A new unexecuted primal_flip_work_contracts.jl specifies the first intended RED:
four actual flips, certified final optimum, target5FTRAN/1BTRAN including mandatory
endpoint refresh versus the unchanged control expected8/4. Run only after census
acceptance and separate host absence; no private candidate before that RED.

S2-A control-census-1 completed1000/1000 assertions and80/80rows,exit0/pins
unchanged; source hashes verified. Host runner282455/child282456/driver absent.
Next work-red-1 on unchanged control; no candidate implementation yet.

S2-A work-red-1 produced the intended RED:6state/certificate checks pass,
2work assertions fail (actual8FTRAN/4BTRAN versus target5/1),0errors,exit1/pins
unchanged. Host runner282737/child282738/driver absent. Private AST-clone
implementation may now begin; production remains unchanged.

S2 work-green-1 failed at module loading (unspaced bang-symbol Pair syntax in
RENAMES evaluated an undefined target name), before numerical tests. Exit1/pins
unchanged, host absence verified. Replaced only the rename dictionary entries
with explicit Symbol constructors; work-green-2 next. Production unchanged.

S2 candidate-matrix-1 passed960/960 across80cases,exit0/pins unchanged.
Host runner283268/child283270/driver absent. Flip->pivot reduces4/3solves to3/2;
flip-chain8/4 to5/1; scheduled flip unchanged2/1; flip->unbounded increases3/1 to4/1
due required endpoint refresh and repeated direction. No timing saving claimed.
Two private context-dispatch hooks now allow tests to inject apply/certificate
failures without replacing any production helper. Default hook bodies call the
unchanged helpers. Next safety/unsupported/exception qualification.

S2 safety-contracts-2 passed139/139 (118 fault/publication +21 scope/precision),
exit0/pins unchanged; host runner283985/child283986/driver absent. Successful
rejection reconstruction, before-write overflow, time/iteration limits and owned
callback/numerical exception provenance passed. BigFloat and Rational Int64/BigInt
use the original8/4 path. Injected reconstruction exception is not coverage of
all ill-conditioned recovery failures. Next focused existing regressions.
