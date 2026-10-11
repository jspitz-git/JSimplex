# Simplex Core Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans`
> to execute sequentially, task by task. Steps use checkboxes for tracking.
> This is a staged roadmap: each architectural stage starts with a small,
> evidence-based implementation subplan before its production edits.

**Goal:** Reduce repeated work in both simplex methods without losing numerical
stability, and retain enough evidence to resume safely after interruption.

**Architecture:** Establish mutation/validation ownership first, then investigate
incremental primal maintenance and end-to-end sparsity. Treat factorization
memory lifecycle and phase handoffs as independent later stages; merge only
individually verified changes, keeping unsuccessful prototypes isolated.

**Tech Stack:** Julia, existing JSimplex numerical types and basis managers,
Test, Python diagnostic runners, native and Markowitz factorization.

**Spec:** [Design and constraints](../specs/2026-10-11-simplex-core-architecture-design.md).

## Global Constraints

The spec's Constraints section applies to every task. In particular: one guarded
numerical process; no weakened protections, dropped coefficients or routine
precision promotion; no excluded model or alias; preserve local environments.
Controlled comparisons disable performance heuristics, not numerical protection.
Do not edit sources, runners or environments pinned by an active numerical job.

[STATUS.md](../../../diagnostics/simplex-core-architecture/STATUS.md) is the
continuation entry point and authoritative stage ledger. This plan tracks
accepted deliverables, not partial or failed attempts. Update both at milestones.

## Review Focus

- Mutation through aliases, callbacks or failed updates must never leave a stale
  validation reusable. Covered by S1 ownership/invalidation tests.
- Degenerate pivots, flips and small steps can accumulate error despite benign
  local values. Covered by S2 independent reconstruction and recovery tests.
- Signed zero, cancellation and sparse/dense transitions can corrupt support.
  Covered by S3 exact-support and alias tests.
- Changing matrix patterns or update-chain lengths can retain excessive memory
  or reuse stale symbolic data. Covered by S4 lifecycle tests and memory traces.
- Phase changes and postsolve mapping can invalidate an apparently good point,
  weights or certificate. Covered by S5 handoff/fallback tests.

## Order and decision gates

Execute S0, S1, S2, S3, S4, S5 in that order, then S6. S2 and S3 depend on the
ownership findings of S1. S4 can proceed independently if an earlier experiment
is rejected; S5 depends on the state contract. Record any reordered work with
its reason. Do not ship all stages as one rewrite.

Each production chunk follows: failing regression or work-count test, minimal
implementation, focused correctness and cost measurement, broader validation,
independent numerical/performance review, commit, integration. A rejected
experiment is a valid investigation result, not a completed optimization.

Later stages deliberately do not freeze new Julia APIs before the mutation and
cost inventories exist. Their first deliverable is a concrete subplan specifying
exact signatures, owning files, invalidation paths and named tests. This gate
prevents speculative caches and duplicate mechanisms already present in core.

### S0 — Freeze evidence and close the relevant measurement gaps

**Inspect:** `diagnostics/simplex-time-budget/{README,RESULTS,REVIEW}.md`,
`diagnostics/simplex-time-budget/reproduce/{run.py,measure_counted.jl,counters.jl}`,
`diagnostics/basis-selective-preparation/reproduce/external-inputs.toml`.
**Create during execution:** `diagnostics/simplex-core-architecture/BASELINE.md`
and stage-specific scripts under `diagnostics/simplex-core-architecture/reproduce/`.

- [x] Verify branch, master/origin state, local dirt, active processes and previous
  reports. Record baseline source/environment/input hashes and exact options.
- [x] Write BASELINE.md separating measured prefixes/cleanup from missing long
  phase II; record actual executing algorithm and working dimensions per slice.
- [x] Prepare a guarded runner with exclusive numerical-process ownership,
  immutable per-attempt directories and pre/post digest checks. Test its refusal
  of concurrent runs, changed pins and existing output directories without Julia.
- [ ] Define low-overhead chronological timing and operation counters for a real
  long medium phase-II run. Preserve live pricing/recovery state; do not call
  reconstructed event snapshots faithful checkpoints. Calibrate instrumentation
  on paired short runs before requesting its timings as evidence.
- [ ] Obtain a phase-II reference before claiming a whole-medium improvement in
  S2. Existing prefix evidence is sufficient to begin the local S1 work.
- [x] Freeze representative sparse/dense kernel inputs and the external manifest;
  include both algorithms and all five public managers over subsequent validation.
  Resolve inputs and check hashes to exclude forbidden aliases.
- [x] Commit the baseline/harness evidence and update STATUS with the next task.

**Gate:** The next experiment has a reproducible starting state, measured work
counts and explicit coverage limitations. A missing long run remains pending;
it does not prevent local validation or become a fabricated successful result.

### S1 — Mutation ownership and reusable validation

**Inspect/modify in small chunks:** `src/{simplex,dual_simplex,primal_simplex,
primal_updates,simplex_recovery,simplex_phase_one,simplex_pivot}.jl`.
**Tests:** existing `test/{dual_weight_validation,native_residual,
primal_certificate_reuse,simplex_precision_recovery_state}_tests.jl`;
new `test/simplex_state_validity_tests.jl` if a shared contract is introduced.

- [x] Inventory every write to basis identity/factors, primal values, reduced
  costs, objective costs, bounds, weights and scratch support. Include recovery,
  callbacks, phase changes, exceptions and in-place mutation through aliases.
- [x] Save `diagnostics/simplex-core-architecture/S1-OWNERSHIP.md`: for each check,
  list exact dependencies, producers, consumers and invalidation rules. Identify
  which repeated scans are provably redundant and which validate different data.
- [x] Write the S1 implementation subplan. Choose the smallest owned validation
  contract justified by that inventory; do not add a global version framework
  where local reuse already suffices. Specify rollover and exception behavior.
- [x] Add tests where an unchanged state reuses validation and every dependency
  mutation forces checking; include NaN/Inf injection, alias/callback access,
  failed updates, dimension changes and generation rollover if counters are used.
- [x] Implement one consumer at a time, starting with repeated dual finite-state
  checks. Preserve independent row/direction residuals unless reuse is proved.
- [x] Compare event/state hashes and work counts with baseline; measure avoided
  scans, counter overhead and retained metadata on sparse and dense inputs.
- [x] Review, commit and integrate only passing chunks; record links and results.

**Gate:** No reusable result outlives its inputs; no material new per-candidate
scan or allocation. Demonstrate saved work and unchanged arithmetic trajectory.

### S2 — Incremental primal state with controlled reconstruction

**Inspect/modify:** `src/{primal_updates,primal_simplex,simplex_numerics,
legacy_primal_point,legacy_primal_pivot,simplex_recovery}.jl`.
**Tests:** `test/primal_update_tests.jl`, `test/legacy_primal_*_tests.jl`,
`test/native_primal_completion_tests.jl`, `test/native_certificate_recovery_tests.jl`,
`test/simplex_strategy_separation_tests.jl`.

- [ ] Map existing incremental operations and audit paths to the protections in
  the working legacy path. List guards bypassed by current incremental flags.
- [ ] Write the S2 subplan defining error accounting in problem precision,
  mandatory reconstruction points, failure fallback and test instrumentation.
  Quantify the cost of the estimator itself before adopting it.
- [ ] Add tests for accumulated drift over degenerate chains, bound flips,
  small/correlated pivots, inconsistent prices, phase transitions and failed
  reconstruction. Retain the regression that motivated each existing safeguard.
- [ ] Implement a private experimental path using existing update kernels and
  S1 ownership rules. Do not change the default or public switch merely to test it.
- [ ] Measure reconstructions/solves/scans per accepted step, drift against an
  independent reference, repair frequency, allocations and warm elapsed time.
- [ ] Run broad validation including runtime primal/dual, medium phase II and
  both cleanup origins. Compare valid outcomes and certificates, not identical
  fingerprints when arithmetic differs. Report changed trajectories separately.
- [ ] Review and integrate only if safety is retained and total saved work
  survives required audits; otherwise preserve the prototype and rejection reason.

**Gate:** Correctness across the supported precision/backend combinations and
historical failures, with a repeatable cost benefit. A frequently reconstructing
or fragile error controller does not qualify just because one model is faster.

### S3 — Preserve sparsity support across the iteration pipeline

**Inspect/modify:** `src/hypersparse*.jl`, `src/sparse_pricing.jl`,
`src/{simplex_pricing,primal_updates,dual_simplex}.jl` and manager solve interfaces.
**Tests:** `test/indexed_vector_tests.jl`, `test/hypersparse*_tests.jl`,
`test/sparse_pricing*_tests.jl`, plus paired core trajectory tests.

- [ ] Trace support creation/invalidation through FTRAN/BTRAN, pricing, value
  updates and DSE updates for every public manager. Count dense support rebuilds.
- [ ] Write the S3 subplan specifying exact support ownership, solve-result
  interfaces and dense fallback. Reuse existing generation/accounting mechanisms.
- [ ] Add tests for empty/full support, exact cancellation, signed zero, aliasing,
  workspace reuse, overflow and sparse-to-dense-to-sparse transitions.
- [ ] Implement one end-to-end path, retaining arithmetic order where promised.
  Classify any changed reduction order explicitly as changed arithmetic.
- [ ] Measure support bookkeeping and full scans avoided across sparse and dense
  cases and different chain lengths, including PFI/HH/FT/SS/BG independently.
- [ ] Verify original feasibility/certificates and review precision semantics;
  commit/integrate accepted paths. Leave learned sparse/dense switching policies
  to a separately evaluated adaptive strategy.

**Gate:** Exact support, no coefficient pruning, no hidden full scan that cancels
savings, and no material dense-case regression concealed by sparse-only timings.

### S4 — Refactorization workspace and memory lifecycle

**Inspect/modify:** `src/{factorization,triangular_factorization,
huangfu_hall_factorization,markowitz_factorization,refactorization_policy}.jl`.
**Tests:** `test/basis_matrix_reuse_allocation_tests.jl`,
`test/basis_recovery_tests.jl`, `test/refactorization_*_tests.jl`,
`test/huangfu_hall_precision_tests.jl`, existing manager allocation tests.

- [ ] Attribute live factors, reusable scratch and temporary allocations per
  backend; distinguish arithmetic from GC charged inside refactorization.
- [ ] Write the S4 subplan for one backend first, defining ownership, allowed
  capacity reuse, pattern invalidation and bounded retained memory.
- [ ] Add tests for changing dimensions/patterns, repeated refactorization,
  exceptions, rollback and long/short update chains with all supported precisions.
- [ ] Implement reuse without aliasing live factors or keeping obsolete large
  buffers indefinitely. Do not assume symbolic reuse from matching dimensions.
- [ ] Measure allocations, peak/retained memory, GC and warm arithmetic on fixed
  basis histories and complete solves; retain baseline heap/guard settings.
- [ ] Review and integrate independently verified backend changes. Include native
  and Markowitz; keep experimental direct FT/SS/BG results explicitly separate.

**Gate:** Lower measured lifecycle cost without stale factors, failed recovery
or unbounded retention. GC relocation alone is not an arithmetic speedup.

### S5 — Explicit phase and cleanup handoff contracts

**Inspect/modify:** `src/{solver,simplex_phase_one,simplex_driver,
simplex_recovery,primal_simplex}.jl`.
**Tests:** `test/dual_entry_phase_tests.jl`, `test/native_cleanup*_tests.jl`,
`test/native_certificate_recovery_tests.jl`, `test/simplex_precision_phase_tests.jl`;
new `test/simplex_handoff_tests.jl` for the shared contract.

- [ ] Inventory handoff state: original/working matrix identity and ordering,
  basis, bounds, costs, primal point, prices, weights, certificates and ownership.
- [ ] Write the S5 subplan defining transferable state and the conditions that
  mandate rebuilding it. Treat original-model feasibility as a separate obligation.
- [ ] Add tests for changed ordering/scaling, artificial-column removal, changed
  costs/bounds, invalid weights, missing metadata and rejected certificates.
- [ ] Implement conservative reuse and explicit fallback; verify restart and
  cleanup cannot accept a certificate for another model or stale point.
- [ ] Measure projection, lazy weight construction, entry and ordinary cleanup
  separately on both preserved medium handoffs and portable small fixtures.
- [ ] Review, commit and integrate verified changes; report entry savings without
  extrapolating them to hours of ordinary iterations.

**Gate:** Valid final original-model certificates, correct fallback and a measured
reduction in initialization work; no silent transfer of incompatible state.

### S6 — Integration and final assessment

- [ ] Run the focused semantic suite and allocation tests separately where
  `--compile=min` is needed; never use that mode to claim allocation performance.
- [ ] Run the external reference set (currently 100 combinations), audit unique
  cases and original feasibility/objectives, and record unsupported combinations.
- [ ] Validate runtime with both algorithms and full medium coverage for changes
  affecting those paths. Record the separately reported test.mps certificate
  failure as an unresolved case unless reproduced and actually resolved; do not
  make it disappear from the ledger after unrelated tests pass.
- [ ] Repeat representative warm timing comparisons at least three times, with
  interleaved baseline/candidate order. Report spread, compilation, GC, work,
  allocations, peak/retained memory and recovery counts, not only the best time.
- [ ] Independently review numerical correctness and AGENTS.md work/memory costs.
  State explicitly whether unnecessary work or retention remains and cite evidence.
- [ ] Commit compact English results and update the ledger. For production
  integration, preserve user dirt, merge tested commits into current master,
  validate the integration and push under the user's standing authorization.
  Record actual merge/push IDs; do not integrate unrelated experimental changes.

## Execution records and restart protocol

Use `.superpowers/simplex-core-architecture/STAGE/CASE/attempt-N/` for local raw
artifacts and `diagnostics/simplex-core-architecture/results/STAGE/` for compact
committed reports. Never overwrite attempts. Each attempt records source and
script digests, environment/options, input hash, command, PID/process group and
start identity, timestamps, exit reason, result/certificate and resource logs.
A PID alone does not establish process ownership after reboot or PID reuse.

Before stopping or after a crash, update STATUS with the last verified commit,
uncommitted files, completed reports, active runner and the exact next action.
On resume, first inspect processes and logs; never launch a second numerical
process. If a runner is gone, preserve the interrupted attempt and verify pins
before creating a new one. A diagnostic snapshot is not a resumable checkpoint
unless completeness was explicitly demonstrated.

For the first task, run these read-only checks from the planning checkout:

```bash
git status --short
git log -1 --oneline
git worktree list
git rev-parse master origin/master
pgrep -a -x julia
cat diagnostics/simplex-core-architecture/STATUS.md
```

`pgrep` exit 1 means no matching process; absence is only one preflight check.
Numerical commands belong to each stage's subplan after its runner and exact
fixtures exist. Do not execute placeholder commands or modify old pinned scripts.

## Planning review

Self-review: all five proposed directions have a task, evidence gate, owning
files and tests. High-risk inputs map to S1–S5; integration and historical gaps
map to S0/S6. No production API is declared implemented. This documentation adds
no runtime work, allocations or retained memory, so no numerical benchmark is
required for this commit. Planning is complete; all execution stages are pending.

## 2026-10-11 local execution checkpoint

S0 preflight and baseline are recorded in BASELINE.md; a Python-only guarded
runner passed review fixes and all 18 safety tests. Fixture recipes are frozen, but materialized numerical
coverage is pending. LONG-PHASE-II.md specifies the method; no calibration or
long reference has run. S0 is therefore Active, not complete.

S1 mutation/check inventory and the owned-deadline S1-A subplan are written.
The inventory does not authorize a global validity cache or removal of independent
residual checks. All production implementation, numerical validation and
integration checkboxes remain pending. See STATUS.md for exact continuation.

## 2026-10-11 S1-A integration checkpoint

S1's local owned-deadline contract is integrated and pushed to master as beb161b
(architecture commit 8e0a7c7). Sparse/dense recipes and the external manifest have
now been exercised across all five managers; the 100-case correctness matrix
covers both algorithms/backends. Evidence: S1-ENTRY.md and results/S1-A/.

The tested chunk saves one finite-state scan on eligible local entries, with no
changed arithmetic trajectory, new workspace cache or independent-guard removal.
Review found no unnecessary added work or retention. All named focused checks,
work counts and broader correctness gates passed in the documented modes.
Normal-mode full-suite completion remains unverified due to bounded compilation
stalls also reproduced on baseline. No whole-medium result or universal elapsed
speedup follows. S0 long instrumentation/calibration/reference is next before S2.

## S0 long instrumentation checkpoint

The diagnostic count-only prototype passed 39 tests and its small HH calibration.
The chronological prototype passed boundary/staging tests, but its sparse pilot
median overhead is 11.90%, above the predeclared 5% budget (dense: 2.02%). S0-L2
is not accepted; no long reference was launched. See S0-LONG.md and the new
2026-10-11-simplex-long-instrumentation.md subplan. Execution stopped at this
concrete problem as requested; S1 production remains integrated and unchanged.

Resumed investigation: owned-observer event sink passed 14 tests and actual
recorder+trace checks. Revised pilot still fails sparse overhead (8.78% > 5%;
dense 1.71%). No long reference. Direct metadata-event/committed-recovery
coverage limitation is documented following independent review. Next: matched
mode ablation before reducing instrumentation density or adopting count-only.
No production changes; all eleven S0-L attempts are preserved and stopped.


## S0 continued calibration checkpoint

Continuous execution was explicitly authorized by the user. Chronology phase
labels, nested attribution and committed metadata coverage were corrected and
reviewed. Fixed counter bounds and streaming serialization reduce diagnostic
costs, but failed overhead gates remain preserved. The current hypothesis omits
8 redundant entry probes while retaining all LONG-PHASE-II required work fields.
Counter40/window19/phase19/stream10 tests and static review support this change;
current kernel/full calibration and driver smoke remain mandatory. S0 is still
Active, not a completed long reference. See STATUS.md and S0-LONG.md for current
attempts. S2 static guard/work inventory is in S2-INVENTORY-NOTES.md; no S2
production experiment or master change has been made.
