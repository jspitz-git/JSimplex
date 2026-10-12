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
- [x] Define low-overhead chronological timing and operation counters for a real
  long medium phase-II run. Preserve live pricing/recovery state; do not call
  reconstructed event snapshots faithful checkpoints. Calibrate instrumentation
  on paired short runs before requesting its timings as evidence.
- [x] Obtain a phase-II reference before claiming a whole-medium improvement in
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

- [x] Map existing incremental operations and audit paths to the protections in
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

S0-L2 current checkpoint: kernel10 passes, full suite3 medium primal rejects5.904%
with all traces matching and stable retention; no long reference. A reviewed
single-module process-isolated calibration now tests the specific difference
between the suite's resident two-module/model graphs and actual L3. Preserve
six alternating pairs,5% ratio-of-medians, all samples and old failure.

Ruling: complete S2's static mapping prerequisite during S0 calibration waits,
without starting an experiment or changing production. S2-INVENTORY-NOTES.md
maps bypassed legacy safeguards, factor ownership/rollback, publication and
terminal reconstruction, plus all known independent-audit allocation/scan costs.
Independent review confirms the map after adding basis-reliability RHS/scratch,
indexed copies and residual passes. The subplan/controller and all S2 numerical
gates remain pending. No benchmark is needed for the documentation itself.

Ruling: while serialized S0 process-isolation samples compile/run, prepare only
S4's static ownership/reuse map under the roadmap's independent-stage allowance.
S4-INVENTORY-NOTES.md distinguishes live/shared factors, private scratch, pooled
updates and candidate backends; records existing caps/fixes and missing HH in
older assembly loops. No S4 numerical gate is checked, no API selected and no
production code changed. Completed suite3 windows are reused for attribution,
not remeasured; presolve allocation must not be mistaken for HH storage.

S4-A local scratch chunk accepted after RED/GREEN344, focused4366 and60 paired
cost records. Same-size allocations unchanged, dimension changes release old
four-vector capacity, all factor/solve fingerprints identical. Review found no
unnecessary work or memory cost. Commit8701a58 integrated as master4143dad;
master regression/push currently pending. This does not complete broader S4
backend attribution or whole-solve validation; see S4-SCRATCH.md and its subplan.

S4-A integrated-master regression passed344, normal exit/pins unchanged.
Master4143dad is pushed/remote verified; preservation hashes match. The local
S4-A subplan is complete; broad S4 remains partial. S0 driver-smoke-1 is active.

Reordering ruling during L3: while medium-dual-counted-1 occupies the exclusive
numerical slot, prepare only static S2/S3/S5 inventories and private designs.
S1 ownership findings are already accepted; no later numerical implementation
or acceptance gate is bypassed. S3 and S5 maps are partial, so their inventory
checkboxes remain open. S2-A audited-bound-flip proposal is under review and
avoids unsupported conditioning assumptions; no prototype is running. L2 counter/
chronology definition is now checked after calibrated/reviewed smoke success;
the separate phase-II reference gate remains unchecked until actual audit.

S2-A static design milestone: the private audited-flip context, clone whitelist,
endpoint transitions and fallback alias ownership passed independent review.
The scheduled-refactor branch must copy an already applied current point rather
than predict the movement twice. Control characterization scripts are prepared
but unexecuted while L3 owns the numerical slot. Their80-case matrix includes HH
and explicitly asserts the limit-refactor reason. Design acceptance is not A1
freeze, A2 branch evidence, RED/GREEN or general S2 acceptance.


S3 static writer review identified two reproducible-looking safety gaps before
new reuse: AbstractVector refinement aliases and observer-created LP witness
support. The accepted narrow S3-A reproduction/subplan is
2026-10-11-pipeline-boundary-invalidation.md. Ruling: use the next free serial
slot to test these correctness boundaries before S2 prototype implementation;
S0 remains uninterrupted. No source patch or completed S3 gate is claimed.

S0 live checkpoint: phase II reached original-model cleanup at iteration234380.
Its completed windows are preserved, but final certificate/exit/pins audit and
separate plain/primal-origin references remain open. Attached-chat automatic
continuation watches the existing guarded job and resumes the reviewed S3-A gate
after release; it does not start a second numerical process.


S0-L final counted dual reference audit passed:256 windows,198675 actual phase-II
steps,255798 total steps,OPTIMAL and original primal feasibility with internal
certificate observed. Exact baseline/medium hash and pins verified; see STATUS
and medium-dual-counted-1-audit.json. Separate plain elapsed and primal-origin
long coverage remain pending; counted live timing includes0.022926199s compilation.
Proceed with reviewed S3-A safety RED before source changes.


S3-A narrow correctness prerequisite is integrated: productioncd91a1a ->
masterd8ad4ec, reviewed/pushed; smoke32, matrix1645, existing focused3214 plus
LP follow-up70, cost120 and integration1645. See S3-BOUNDARIES.md for preserved
driver errors and cost limits. Broad S3 optimization checkboxes remain open.
Next execute S2-A control census and its private RED/qualification plan.


S2-A private audited-flip experiment is REJECTED after qualified local numerics
(control1000, candidate960, safety139, dirty-entry26, existing focused10381) and
128cost samples/64warmups. Sparse cases improve but dense accepted cases regress
22–30%, with extra certificate scratch and rejection costs. Independent review
accepts rejection; no production/default change. Preserve all evidence and do not
add an inferred density threshold. Broad S2 pivot error accounting remains open.
Ruling: continue S3 producer/consumer support inventory and work census after
this bounded rejected experiment, following the roadmap's staged investigation;
any future S2 proposal needs a distinct numerical/cost hypothesis and subplan.


S3-B local canonical-support consumer optimization is reviewed, integrated and
pushed: productionb6a4064 -> masterb720674, master regression1611/1611. Evidence
in S3-SUPPORT.md:1900work pairs save992compactions/5156visits,936cost records retain
identical allocations and output hashes,80paired solver traces match exactly.
Two Float32 dense/history8 cost fixtures fail equally before timing and remain
explicit gaps. No new heuristic, arithmetic change or universal speed claim.
Broader S3 stays partial; next close existing S0 plain elapsed gap before further
long comparisons. S4/S5 attribution now uses completed old counted windows with
no repeated solve. No unsafe handoff or factor reuse is inferred from those costs.

S0-L medium-dual-plain-1 is now active under the same43200s guarded old baseline.
This fills missing plain elapsed coverage; no new success/speedup claim. STATUS
contains live identities and distinct plain-mode audit requirements. Primal-origin
long coverage and broader stages remain pending.


S0 dual plain reference accepted:6006.247837068s including compile/GC,OPTIMAL,
original feasible,exact result/configuration match with counted dual; independent
post-exit pin/source audit and separate process absence passed. See plain auditJSON.
Next primal counted long reference as already planned; no dual repeat/current-master
speedup claim. S0 and broad stages remain partial.


S0-L checkpoint: primal counted reference accepted with350complete windows,
263984actual primal phase-II steps,353468total iterations,OPTIMAL and original
feasibility/internal certificate, normal exit and independent pin verification.
Both counted origins are now covered; plain primal remains the next serialized
reference. See STATUS/LONG-PHASE-II and results/S0-L/medium-primal-counted-1-audit.json.
No new production change or current-master performance claim.


## 2026-10-12 S0-L completion

All four frozen old-baseline long references are audited and accepted. The final
plain primal matches counted primal exactly (353468iterations,2240refactors,
objective/primalSHA/options/policy); all18 audit checks and independent pins pass.
Plain13200.181889727s includes compile0.023769598s/GC732.537595438s. See STATUS and
LONG-PHASE-II for full evidence and limits. S0 is Verified; this closes the long
subplan, not the whole architecture roadmap. Next S4 component attribution uses
new small deterministic native HH histories, not a repeat of accepted medium.


## 2026-10-12 S4-B diagnostic checkpoint

Native Float64 HH component attribution passed72 compile-free samples and all13
post-exit audit checks, residual/ownership/failure assertions and independent
review. S4-COMPONENTS.md separates cumulative traffic from Julia-visible retained
objects and native-memory limitations. No production changes or speedup claim.
The broader S4 checkbox remains open for backend/precision coverage; next is a
separate Markowitz attribution slice, not a repeat of the accepted native data.


S4 Markowitz diagnostic slice also accepted:72 compile0 samples,all17 audit gates,
independent pins and review. Dense256 extraction121988864B/16calls dominates this
backend's535280B/16calls. Next measured hypothesis is temporary triplet capacity
reservation; no production change accepted yet. Broader precision/S4/S6 remain open.


## 2026-10-12 S4-C integration

Exact Markowitz HH triplet allocation is accepted: RED/GREEN442,focused4366,
84compile0paired cost samples,8exact whole-solve pairs/121assertions. Fresh final
review found no unnecessary work/retention or numerical blocker; exact count adds
O(k+c²) extraction work while reducing triplet allocation traffic. Mostly-zero256
side-median1.0258 is retained as a timing limit. Production0f2c468 -> master3220118,
integration1294/1294,source/pins/user-file hashes verified,master pushed.
S4-TRIPLETS.md and the triplet subplan contain full evidence. Broader S4 scalar
component cost and S5/S6 remain open; do not repeat completed Float64 attribution
or S0-L references. Next choose a bounded scalar attribution subplan before Julia.


## 2026-10-12 S4-D scalar diagnostic checkpoint

Bounded non-Float64 HH component attribution accepted:360compile0samples,40cases,
10lifecycle/failure cases,all22qualified audit gates,independent pins/source and
fresh final review. BigFloat Serialization hashes rejected as canonical equality;
original failed audit preserved and separate8case exact/canonical probe accepted
without retroactively replacing old hashes or rerunning costs. No production edit.
See S4-SCALARS.md for type/backend mechanism, graph limits and deferred P3 auditor
rerun-preservation minor. Broader manager/history/medium/S6 gates remain open.
Next S5-A ordinary cleanup entry work census/contract, per explicit subplan
2026-10-12-cleanup-entry-contract.md; observer/deadline/checkpoint/recovery semantics
must be resolved before any removal of default reconstruction.

S5-A update (2026-10-12): ordinary cleanup entry census184 exact pairs,20audit
gates; unconditional initialization omission rejected. S5-ENTRY.md records
qualified scope and exclusions; broad S5 checkboxes remain open. Next concrete
subplan:2026-10-12-objective-restoration-contract.md. No production change.

S5-B update: original objective/bound restoration census144pairs/21audit gates,
no production change. S5-RESTORATION.md and separate S5-C alias-copy subplan define
a concrete cold-copy candidate without shared certificate reuse. Broad S5 open.

## S5-C integration and S6-A ordering (2026-10-12)

S5-C bounded cost-copy reduction completed: production88a2411 -> mastere7014fb,
review accepted without findings, master668/668/12audit gates/592pins and user hashes.
Master push verified. See S5-COPIES.md for exact work and timing/byte limitations.
No broader handoff/certificate reuse or whole-solver speedup is established.
Next2026-10-12-integration-failure-inventory.md performs read-only S6-A triage of
already-failed CI before additional optimization. Ruling: make known validation
blockers explicit without redoing accepted measurements; broader S2/S3/S4/S5 and
final S6 coverage remain open. CI stays disabled.

### S6-AO local coverage milestone and pause (2026-10-12)

Test7706c1a -> master0eb75c3 adds two native owned-bound entry interruption cases,
preserving the entire previous test file. GREEN and actual master each72/72 with
fresh numerical/work review and source/pin audits. This extends coverage; it does
not repair the three historical cleanup failures or close S6/full-suite/x64.
The user requested automatic continuation paused after this milestone. No next
work started. Prepared later S4-E source-only native HH symbolic contract follows
S4's independent-stage rule; symbolic reuse remains unverified and disabled in HH.

### 2026-10-12 explicit resumption and S4-E

User resumed continuous execution. Source-only native symbolic contract accepted
with25checks/542hashes and fresh independent review. S4-F has a separate bounded
six-pair native API qualification plan. No production/test change, HH symbolic
reuse remains disabled; historical cleanup cause and broader S4/S6 remain open.

### S4-F native API boundary accepted

Six new native component pairs179checks/24auditgates649pins,12setup12refactor20solve
plus10metadata10graphs. Fresh independent review accepts scoped result; no HH
production change or speedup claim. Next S4-G separately qualifies HH publication/
shared updates/prepared state with a fixed24HHsolve budget. Other S4/S6gates open.

### S4-G diagnostic publication qualification (2026-10-12)

Two new HH lifecycles pass79checks;26audit gates653pins and10independent author
supplements. Fresh gpt-6-astra review no findings/no unnecessary production work
or memory. Diagnostic exact-source candidate only, production still unchanged.
Success prepared invalidation/private suffix retirement and LU-failure live/saved
owned-value preservation qualified for tiny Float64 native inputs. Exact call
boundary2constructors/2copies/6updates/4refactors/24HHsolves, with internal work
explicitly outside that count. No speedup/public-workspace/fullsuite/x64 claim.
Next S4-H actual borrowed basis assembly/recompute source/evidence contract:
2026-10-12-hh-borrowed-assembly-contract.md. Do not rerun accepted G/F/E evidence.

### S4-H closure, 2026-10-12

Borrowed HH assembly source contract accepted after one independent Important
inventory correction (13callers,12outside recompute). No Julia/production/test/CI
change. Original parser failure24/25/exit1 preserved, nine supplement checks and
full526hashes/eight independent checks pass. Review correction RED3/GREEN5; before
report/plan retained. See S4-BORROWED-ASSEMBLY-CONTRACT.md/REVIEW. Source-only work
introduces no production cost. S4-I is the separate two-workspace/28HHsolve gate
in 2026-10-12-hh-borrowed-assembly-qualification.md; other native consumers excluded
by explicit call sequence, not policy assumptions. Native reuse remains disabled,
full-suite/platform/performance/native-retention obligations open. No old reruns.
