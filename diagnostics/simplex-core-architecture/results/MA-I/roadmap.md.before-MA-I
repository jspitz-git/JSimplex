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

## Current continuation — 2026-10-14

MA-H OFFLINE preparation completed: isolated routing-only candidate SHA256
 dca3d1c7cabfc6ecf8e09832cadd097bcfe4a6e5982e42d914b72333bf853dea.
Structural RED4expected false/GREEN5PASS; exact inverse to MA-E and original source;
helpers unchanged. Old381assertions copied exactly; new266prospective assertions
in28paired full-forward cases (647total). All Julia text UNEXECUTED.29offline
checks PASS/27bindings; no actualsrc/test/Project/env/master/CI change.
See MA-MARKOWITZ-ROUTING-PREPARATION.md and results/MA-H review/closure/publication.
Next MA-I: docs/superpowers/plans/2026-10-14-ma-routing-qualification-admission.md.
FIRST new concrete immutable controls/manifest and fresh independent numerical
admission, THEN one short bounded22process schedule. No launch from MA-H alone.
Standing short-run permission persists; no duplicate question. MA-F performance
remains NOT ACCEPTED, all48cases/target/control gates retained; no integration.
MA-G current STATUS/roadmap hashes in closure/publication/review map ONLY to
MA-H/STATUS.md.before-MA-H and roadmap.md.before-MA-H; older maps unchanged.
All old evidence/scripts/candidates and MA-H input plan frozen. BroaderMA/S2/S3/
S4/S5/S6open, automationpaused/CIoff/HHdisabled; master6f68e24 unchanged.

### Previous S4-AD integration (completed)

S4-AD row-count fusion integrated: production`99da53e` -> master`6f68e24`.
Exactly two files: unchanged qualified constructor candidate plus46-line regression
append/4188-byte original test prefix. Corrected RED20pass/fourexpectedworkfailures;
GREEN722/722 and actualmaster324/324, all8audit gates each, no error/broken assertions.
Initial RED infrastructure failure and120sGREEN timeout are preserved, not passing.
Separate accepted amendments supplied repaired collector and ONE300sGREEN; actual
GREEN278.161s, master13.013s. All44groupsANDsessions absent/noJulia. AB performance
evidence reused without rerun: H redundant length reads removed, narrow retained
Float32/64 benefit, no universal/end-to-end speedup or memory-saving claim.
AC current continuation bindings map ONLY original S4-AD before copies; historical
RED actual source/test pins map ONLY exact S4-AD before-source/test. Older maps intact.
Next already planned point: MA-1 select one production kernel and freeze its scalar
ownership/operation-order contract in a concrete subplan before implementation.
MA remains Pending; no automatic numerical launch or reopening of stopped routes.
Automation paused, CI off, HH reuse disabled; broaderS2/S3/S4/S5/S6 remain open.
See S4-MARKOWITZ-ROW-COUNT-INTEGRATION.md and results/S4-AD-green-bounded reviews.

### Previous S4-AC preparation (completed)

S4-AC offline integration preparation completed: exact S4-AB source candidate,
4188-byte test prefix preserved plus46-line isolated module/24prospective tests.
Four real-constructor work cases expect20pass/fourworkfailures on current source,
324prospective full-file assertions after change; NO Julia/parser/numerical run.
12source/text checks28fresh hashes; source/test/env/CI/master unchanged.
Next S4-AD: prepare exact RED/GREEN/master drivers, public-call schedules, immutable
pins and independent admissions, then execute the concrete integration plan
2026-10-13-markowitz-row-count-integration.md. At most three sequential120s-capped
processes; standing short-run permission applies, no repeated permission question.
No automatic launch from this preparation, no AB rerun/tuning or benchmark repeat.
AB current continuation bindings map ONLY results/S4-AC/STATUS.md.before-S4-AC and
roadmap.md.before-S4-AC; all older maps preserved. Full34groupsANDsessions absent.
Automation paused, CI off, HH reuse disabled, MA pending; broader plan open.
See S4-MARKOWITZ-ROW-COUNT-TEST-PREPARATION.md and results/S4-AC/review.md.

### Previous S4-AB qualification (completed)

S4-AB row-count fusion qualification completed:648/648 predicates, six audit
and seven postcheck gates; one27.021s guarded run,624 unchanged launch pins.
Four work cases confirm removal of H redundant row-length queries.24 paired
lifecycles/four types/two dictionary implementations preserve selected factors,
owners, inputs and saved solves.12cost cases/240windows/168measuredcompilezero;
retained-capacity Float32/64 paired ratios0.932735/0.950450, other timings mixed,
GC outliers retained, allocation events unchanged by side medians. No universal
speedup/memory saving or full solver claim. Production/test/env/CI/master unchanged.
Next: prepare a concrete permanent work-regression/source integration subplan for
this exact change, after independent result acceptance; do not repeat qualification.
MA remains Pending. Automation paused; broader plan open; old stopped routes remain
stopped. Standing short-attempt permission applies with concrete admission/caps.
MA-B current continuation hashes map ONLY results/S4-AB/STATUS.md.before-S4-AB and
roadmap.md.before-S4-AB; all older maps preserved. Full34groupsANDsessions absent.
See S4-MARKOWITZ-ROW-COUNT-QUALIFICATION.md and results/S4-AB/result-review.md.

### Previous MA continuation (completed documentation milestone)

The user added the optional MA implementation workstream to this roadmap.
Its four pending gates below cover site selection, private scratch design,
short correctness/cost qualification and conditional integration. This update
only schedules work. MA-A remains completed diagnostic evidence. MA-A current
continuation bindings map ONLY to results/MA-B/STATUS.md.before-MA-B and
roadmap.md.before-MA-B; all older mappings remain unchanged.

User-requested isolated MutableArithmetics1.8.1 dot benchmark completed:12cases,
BigFloat128/256/512 and Rational{BigInt},n32/n256dense/n256zero-heavy dense storage.
240windows(3warm+7measuredpairs/case,32dots/window),all outputs/ownership/precision
pass; independent exact binary-rounding oracle agrees. All84measured buffered
windows zero counted bytes/events,168compile/recompilezero. Dense256paired
candidate/reference median ratios0.1364/0.1992/0.2587 BigFloat and0.5442 Rational.
GC outliers preserved; oneprocess/synthetic/borrowedprivateoutput,NOTsolver speedup
or permission to mutate shared scalars. Setup separate; no native-free proof.
One120s-capped run exit0,inclusive3.005227993s,6audit/7postcheckPASS,622pins.
Pre-seal field-name failure and fail-closed no-Julia invocation preserved with
separate accepted supplement; no numerical retry. Full32groupsANDsessions absent.
See MA-PRIVATE-SCALAR-KERNEL.md and results/MA-A/result-review.md. No production,
test,actualenv,CI or master change. AA current continuation bindings map ONLY
MA-A/STATUS.md.before-MA-A and roadmap.md.before-MA-A; older mappings unchanged.
MA-A allowance consumed and all evidence frozen. No automatic follow-on variant.
Future short numerical work has human permission but still needs concrete admission.
Automation paused; S3-G/stopped routes stay stopped; broader plan remains open.

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

### MA — Selective MutableArithmetics integration (Active)

**Goal:** Reduce temporary scalar allocations in one measured production kernel
using privately owned scratch for `BigFloat` and `Rational{BigInt}`.
**Evidence:** [MA-A private scalar experiment](../../../diagnostics/simplex-core-architecture/MA-PRIVATE-SCALAR-KERNEL.md)
and its independent result review. MA-A establishes a local warmed dot-product
benefit, not production ownership safety or end-to-end speedup. Its consumed
attempt, driver and evidence remain frozen.

- [x] **MA-1 — Select one kernel and freeze its contract.** Inspect existing
  scalar reductions and select exactly one recurring allocation source with
  private intermediate values. Record its actual source/caller/test paths,
  execution frequency, scalar types, operation/rounding order, exception behavior
  and input/output aliases. Produce a concrete implementation subplan with exact
  interfaces and named tests before changing production. Reject the site if
  ownership cannot be established without changing observable behavior.
  MA-C selects Markowitz forward upper reduction only; source/design review accepted.
  [Contract](../../../diagnostics/simplex-core-architecture/MA-MARKOWITZ-UPPER-CONTRACT.md)
  and [MA-D offline preparation](2026-10-13-ma-markowitz-upper-preparation.md) bind
  private call-local scratch, first-term precision, original division publication,
  scoped-rounding fallback and exception order. No performance acceptance yet.
- [ ] **MA-2 — Implement the smallest qualified candidate.** Give accumulator and
  MA buffers an explicit owner and lifetime; prohibit mutation of borrowed input
  scalars. Define reset/reuse, reentrancy and precision-change rules. Construct
  BigFloat scratch at the required precision/rounding; handle Rational limb
  growth. Charge copies needed for independently retained outputs. Keep a safe
  existing-arithmetic fallback for unsupported types/contracts and preserve the
  hardware-float path. If accepted for integration, declare MA as a direct
  dependency with reviewed compatibility; do not depend on a transitive import.
  MA-D offline candidate/test/fixture package accepted; complete source inverse,
  six prospective testsets and fixed process-paired schedule. Runtime unqualified.
  See [preparation report](../../../diagnostics/simplex-core-architecture/MA-MARKOWITZ-UPPER-PREPARATION.md)
  and [MA-E offline admission](2026-10-13-ma-markowitz-upper-admission.md).
  MA-E independently accepted reviewed admission; the single
  [MA-F attempt](2026-10-13-ma-markowitz-upper-qualification-reviewed.md)
  subsequently failed before RED test inclusion (obsolete Test context API).
  A separately admitted replacement now passes RED/correctness and completes cost;
  six target benefit gates pass but six control gates fail, so no production promotion;
  [final admission decision](../../../diagnostics/simplex-core-architecture/MA-MARKOWITZ-UPPER-ADMISSION-ACCEPTED.md).
- [ ] **MA-3 — Qualify correctness and total cost.** Use the concrete subplan's
  regression and ownership tests, including cancellation, zero/signed zero,
  nonfinite/exception cases where supported, alias attempts, precision changes
  and Rational numerator/denominator growth. Compare exact Rational and sequential
  rounded results with independent oracles. Run short guarded paired measurements
  on representative small/large and sparse/dense calling cases; separate startup,
  scratch creation, steady-state reuse, result copying and recovery. Count added
  scans, conversions, copies and solves alongside time, allocation bytes/events
  and retained scratch. Include Float32/Float64 fallback regression coverage.
  Preserve GC/outliers; do not infer solver speedup from MA-A or zero allocations.
- [ ] **MA-4 — Review and integrate conditionally.** Require independent numerical
  and work/memory review, focused integration tests and repeatable benefit after
  accounting for buffer lifecycle/output ownership costs. Integrate only the
  selected accepted change; otherwise retain the existing path and record why.
  Broader solver claims remain subject to S6 validation.

MA is an independent optional optimization before final S6 assessment; it does
not block other admitted stages. This addition schedules the work; it does not
start an implementation or numerical run. Existing short-run human permission
applies once concrete admission and resource caps are satisfied; no repeated
permission request or multi-hour run. Automation remains paused. No reopening
of S3-G support omission or stopped HH/DSE/controller/import/isolation/cleanup
routes, no changed tolerances/safeguards, and no replay of consumed experiments.

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

### S4-I closure, 2026-10-12

Actual borrowed HH assembly qualification accepted:55runtime/29audit/655pins,
10independent checks; two workspaces/28HHsolves. One Important report provenance
correction RED1/GREEN3; offline auditor postexit hash is not launch pin. Minor six
transient diagnostic copies deferred without rerun. Production remains unchanged
and native reuse disabled. Next S4-J source/evidence-only eligibility boundary in
2026-10-12-hh-reuse-eligibility-contract.md. No old lifecycle repetition, fullsuite,
CI enablement, speedup or native-retention claim. See qualification report/review.

### S4-J closure, 2026-10-12

Source-only eligibility contract accepted:27checks/530hashes/9independent checks,
first parser ValueError/exit1/source preserved; new scoped-anchor parser passes.
Fresh gpt-6-astra noCritical/Important/no unnecessaryproductionworkmemory. Minor
exact scaled residual formula deferred to K prelaunch freeze, before observing
outputs. Closedpath default controls do not imply general q/control/value safety.
C source-matched existing coverage reused; no Julia/production/test/CI changes.
Next S4-K four nonfinite same-pattern refactor cases in
2026-10-12-hh-nonfinite-reuse-boundary.md. Strict failure preservation/no retry;
source-derived and bounded hidden native work remain explicit. No enablement,
fullsuite/speed/native-retention proof. Keep all old raw and accepted scripts.

### S4-K closure, 2026-10-12

Four new same-pattern nonfinite HH cases qualified49checks/26gates551pins,
9authorindependent checks;4constructors4refactorattempts8retainedHHsolves.
All reject before publication, old extracted state preserved; eight exact nonzero
residuals satisfy PRELAUNCH frozen bound (JMinor resolved). Fresh gpt-6-astra no
findings/no unnecessary productionworkmemory; reviewer16pins/raw4/exact8 separate
from authorfull551. No production/test/CI edit or symbolic enablement. Next S4-L
source-only representative lifecycle cost/native-memory measurement contract in
2026-10-12-hh-symbolic-cost-contract.md. No numerical launch or old lifecycle rerun
in L; all broader S4/S6 and original historical rejections remain unchanged.

### S4-L closure, 2026-10-12

Source/evidence-only cost/native-memory contract:36checks527hashes,15author
independentchecks/full527. Fresh gpt-6-astra numerical/work review,30samplehashes,
no unnecessary productionworkmemory. Two Minor regraded Important for future
measurement/classification premise, one offline RED3/GREEN3 fix, before documents
preserved. Native allocation/free balance remains OPEN; no Julia or production
change. Next bounded NEW sparse/dense S4-M plan:
2026-10-12-hh-symbolic-cost-measurement.md. Four constructors,128warmup+512measured
refactors,88directsolves,balanced8rounds per fixture,compilezero+exact residual
gates; native Info/graph/RSS observations do not prove native retention. No old
accepted driver/auditor/corpus reruns, CI enablement, fullsuite or promotion claim.

### S4-M closure, 2026-10-12

One new bounded sparse/dense96 HH run:231checks/24gates554pins/10independentchecks,
4constructors640refactors88solves,32measuredcompile0samples,16equalendpointpairs.
All88exactresidualsNONZEROwithinbound. Pairedmedianratios0.66579/0.75772 are local
whole-refactor-window observations; GC/diagnostics outside, no full-lifecycle or
solver speedup claim. Freshgpt6astra nofindings/no unnecessaryproductionworkmemory;
reviewer33samplepins and all exact inputs/residuals/statistics,authorfull554separate.
StableJulia graph/nativeInfo/RSS do not close native retention. Next source-only
S4-N in2026-10-12-hh-native-accounting-feasibility.md; no Julia or hooks in N.
No symbolic enablement, production/test/CI changes or broaderS4/S6 acceptance.


### S4-N source-only accounting feasibility, 2026-10-12

Installed long-index UMFPACK helpers route through the SuiteSparseConfig callback
slots; actual binary branches checked, not inferred from symbols alone. Installed
SparseArrays initialization delegates to jl_* allocators. Current evidence does not
qualify complete allocation/free balance or safe hook lifetime/drain; native retention
stays OPEN. No native calls or production work. 20 source checks/61 explicit hashes,
separate full 572 read-time inventory/5 checks, all 554 M pins unchanged. Fresh independent gpt-6-astra review found no Critical/Important/Minor and no
unnecessary production work/memory. Reviewer11sample hashes; author full572 separate.
Next ONE source-only S4-O plan: 2026-10-12-hh-allocation-counter-attribution.md,
which binds existing timed fields to allocator implementation; no numerical launch,
hooks or performance rerun. Native symbolic reuse remains disabled.


### S4-O allocation-counter attribution, 2026-10-12

SOURCE/EVIDENCE ONLY: current counted jl_* paths can contribute native usable bytes
and allocation events to the same aggregate counters as Julia object allocation.
Positive realloc growth only; frees not subtracted. M historical category split and
callback/TLS/loader values UNKNOWN, newly read timing/runtime files not M launchpins.
No accepted artifact/value rewritten or numerical rerun. 26checks/592hashes, author
independent full592/5checks, all554M pins unchanged. Freshgpt6astra nofindings/no
unnecessary production work/memory; reviewer15sample hashes/4disassemblies, authorfull592
separate.
Next ONE source-only S4-P:2026-10-12-hh-history-lifecycle-cost-contract.md, to freeze
NEW nonsymmetric fixed histories and inclusive lifecycle work before any future run.
Native retention OPEN; no hook experiment or production promotion.


### S4-P fixed-history inclusive lifecycle contract, 2026-10-12

SOURCE/EVIDENCE ONLY: new nonsymmetric48 sparse142/dense2304 six-replacement histories,
strict dominance and exact pivot>39/40 proof,19,138 frozen input/RHS/direction/solution
entries. 10offlineinputchecks,26sourcechecks/567read-timehashes, author independent11
checks/full567/allinput reconstruction. G source-matched reuse; all554M pins unchanged.
Prospective Q fixes40lifecycles,80refactors,240updates,960solves; native work is source-
derived/bounded, not measured. Outer owned-factor lifetime includes explicit GC and
nested ordinary refactor windows, no double count/native-free inference. Diagnostics
and mixed GC counters explicitly qualified. Freshgpt6astra nofindings/no unnecessary
production work/memory; reviewerall19,138inputs/12selectedhashes, authorfull567 separate.
Next ONE bounded numerical S4-Q plan:2026-10-12-hh-history-lifecycle-cost-measurement.md.
No launch in P. Native retention OPEN, HH reuse disabled, production/test/CI unchanged.


### S4-Q nonsymmetric fixed-history measurement, 2026-10-12

ONE new cost-1 accepted by runtime/exact audit:6176checks/exit0,28gates/558pins,
11authorindependentchecks/full558/P567 unchanged.40constructors80refactors240updates
960directsolves; all960exactresiduals pass/nonzero,96measuredcompilezero windows,
16output-equal pairs. Outerpairedmedians0.981266sparse/1.015527dense withGCdominance,
no consistent inclusive speedup. Inner dense2outlier5.757909 preserved. Complete
work/diagnostic/owner limits explicit, native retentionOPEN. Freshgpt6astra accepted,
no unresolved findings/no unnecessary production work/memory; reviewerallinputs/residuals/
16samplehashes/raw5, authorfull558 separate;
input-file wording finding fixed offline RED2/GREEN3, no numeric rerun/raw change.
Next ONE source-only S4-R:2026-10-12-hh-public-controller-reuse-contract.md. Public
controller/original certificate not qualified by component agreement; no enablement.


### S4-R public-controller reuse seam, 2026-10-12

Source/evidence-only assessment: the three renamed Q routes do not change the public
controller's real refactor dispatch. Method overwrite is disallowed, post-init adapters
miss typed construction/initial work and need factory/recovery integration. An isolated
nested module is plausible but its complete loading/external-method closure is not yet
qualified. No numerical LP/plan or fishing run is authorized. This is a current-evidence
limit, not proof that safe public qualification is impossible.
24source gates/570read-time hashes; author8independent checks/full570/all558Q unchanged,
8selectedG/I source matches. Production/test/env/master/CI unchanged. No new work/memory
cost in production; no benchmark for documentation. Fresh gpt-6-astra review accepted/no findings/no unnecessary production work/memory.
Reviewer28selected rehashes/8G-I/inverseclone/currentgroups; authorfull570 separate.
Next ONE source-only S4-S:2026-10-12-hh-isolated-module-loading-contract.md, exact module
manifest/inverse/imported-method ownership/load-time work. No H caller census repeat or
Q timing rerun. Public numerical/work qualification, native retention, broader S4/S6 and
all prior rejections remain open/unchanged; HH reuse disabled and CI off.


### S4-S isolated loading manifest, 2026-10-12

Source-only conditional solver-core isolation:70original/64selectedfiles per side,
128manifestentries, seven identical root substitutions/one candidate HH keyword;
exactinverse/no function routing renames. Resident production dependency aliases,
fresh nested JSimplex namespaces, explicit MOI/precompile/import exclusions.29selected
external methods own local nominal types;20additional enum-generated signatures.
Methodtable additions/JIT/metadata/regex/input reconstitution are not zero work.
28offlinegates586hashes,author10checks/full586. Bootstrap remains a separate obligation;
runtime loading/public trajectory not executed or proved. Fresh gpt-6-astra review no
Critical/Important; one Minor keyword-lowering count issue corrected offline, originals
preserved. Full586 read-time reviewer rehash and128manifest checks; source inventory
binds BEFORE corrected report/next-plan. Core.kwcall is additional;29+20 not full count.
T must pin native refactor input representation/count conversions (identity only for
matching CSC). No unnecessary production work/memory and no numerical rerun.
Next ONE S4-T source/exact-offline public LP/work contract:
2026-10-12-hh-isolated-public-lp-work-contract.md. No numerical launch or repetition of
H/R inventories/Qcost. Production/test/env/master/CI unchanged, HH reuse disabled,
native retention/fullsuite/broader S4/S6 OPEN and all prior rejections unchanged.


### S4-T exact LP candidate and whole-work gap, 2026-10-12

One exact finite LP has original feasible/optimal witness x=[0,4/3,10/3], objective-47/3,
and three unique conditional Dantzig pivots. Final two ordered bases share CSC pattern;
this is algebraic reachability, not proof of native path/certificate acceptance.11exact
checks,17source checks604hashes,8separate author checks/full604/120exactvertexcombinations.
S inventory correction provenance and all558Qpins unchanged. Whole qualification stays
OPEN: no qualified fresh-process bootstrap and no complete controller attempt budget.
No numerical plan/launch, production/test/env/CI change or cost measurement. Next ONE
source-only bootstrap contract:2026-10-12-hh-isolated-bootstrap-contract.md. S manifest
unchanged; later controller budget must still close before any pair. Review tracked in
S4-ISOLATED-PUBLIC-LP-WORK-CONTRACT-REVIEW.md. Native HH reuse disabled/retention OPEN,
Q evidence/all prior rejections/broader S4/S6/fullsuite unchanged.


### S4-U existing-cache bootstrap boundary, 2026-10-12

Source-only20checks627hashes,author6/full627;67cache metadata records without content
read/parse/runtime validity. Existing permits source fallback; strict errors before
compilecache/source fallback but still reaches cache timestamp touch and dependency
initializers. CLI-only current writable-cache route not qualified; actual cache selection,
write confinement and transitive initializer work remain OPEN. No numerical plan/launch,
cache/env/production/test/CI change, T LP rerun or repeated S/Q evidence. Next ONE bounded
read-only confinement feasibility decision:2026-10-12-hh-readonly-bootstrap-feasibility.md;
no trial mount/import, reject route if unsupported. Review recorded separately. NativeHH
reuse disabled, native retention/wholecontrollercaps/broaderS4S6/fullsuite remain OPEN.

S4-U closure amendment: original8/9/all_passedfalse/exit1 is preserved. The acceptance
phrase crossed a line break; shell continued into ae874717 publication despite the failed
audit. Separate closure-supplement7/7 verifies normalized text and unchanged original
review/full627 evidence. No numerical/script rerun; prior STATUS/roadmap copies preserved.
Further publication is fail-fast. This does not qualify bootstrap or alter its OPEN gates.


### S4-V read-only bootstrap feasibility decision, 2026-10-12

SOURCE/HOST-READ-ONLY:17 checks656 file hashes, author8/full656, all627 U pins unchanged.
Kernel/tool primitives exist, but inspected installed examples and incomplete root/remount
recipe do not supply the required complete JSimplex path/alias/FD/environment policy.
This rejects those launch routes, not the possibility of a custom bubblewrap policy or
runtime namespace admission. No launcher frozen, no trial sandbox/Julia/cache operation.
Stop this bounded bootstrap investigation rather than schedule equivalent audits/imports.
Next independent source-only controller attempt accounting uses the already frozen T LP:
2026-10-12-hh-public-controller-attempt-contract.md. The independent work is reordered to
make progress while bootstrap/cache validity/initializer closure remain OPEN; it authorizes
no numerical plan. Native HH reuse disabled, production/test/env/master/CI unchanged;
Q evidence/retention/broaderS4S6/fullsuite/allrejections unchanged. U original failed closure
and separate supplement preserved; new publication must pass separate closure first.


### S4-W public-controller attempt contract, 2026-10-12

SOURCE/EVIDENCE ONLY: 26 local-bound ledger rows, 22 source checks/556 read-time hashes,
16 exact excerpts; author eight checks/full 556, fresh reviewer full 556/excerpts and seven
supplement hashes. Direct terminal witness BTRAN and iteration-free postsolve projection
are separate work categories. Aggregate public-route caps remain UNKNOWN, including direct
primal candidate retries and selected original-cleanup dual/auxiliary composition.
Two Important findings resolved once offline RED3/GREEN5 with before texts preserved:
post-body round check permits cap+1 nonprogress bodies; selected dual composition is not
the only missing dependency. Final independent review has no unresolved findings and finds
no unnecessary production work/memory. No numerical execution, production/test/env/master/
CI change, old rerun or new LP. Next bounded source-only task:
2026-10-12-hh-postsolve-dual-work-contract.md. It cannot by itself qualify the complete
budget or authorize a numerical plan. Bootstrap investigation stays closed; qualification,
native retention/broaderS4S6/fullsuite remain OPEN; HH disabled/Q/rejections unchanged.


### S4-X dual/auxiliary work composition and S3 continuation, 2026-10-12

SOURCE/EVIDENCE ONLY: 18 checks/558 hashes/13 exact excerpts, author six checks/full hashes,
reviewer full hashes/excerpts and three fix hashes. Source-local staged retry192 and legacy
33/66/198 backend-entry limits expose additional work; two auxiliary factor copies and
post-deadline shared-factor restoration are distinct. No observed path or complete budget.
Original restoration into primal and forced-driver composition remain unsummed; no proof
of unbounded execution. One Minor BFRT guard wording fixed offline RED1/GREEN3 with before
report preserved. Final review has no unresolved findings or unnecessary production cost.

End the bounded HH controller-budget audit sequence. Reorder the independent broader S3
DSE support consumer question next: 2026-10-12-dse-support-consumer-contract.md. Reconcile
existing S3-A/B evidence first, do not rerun or repeat the accepted mode-selection census.
No HH numerical plan/instrumentation/bootstrap reopening. Source/test/env/master/CI and
S/T/Q evidence unchanged; HH reuse disabled, native retention/broaderS4S6/fullsuite and
all rejection decisions remain unchanged. Publication requires separate passing closure.


### S3-C DSE consumer composition, 2026-10-12

Source/evidence-only contract accepted: 16 checks/53 hashes/36 historical comparisons/
9 excerpts, independent author9 and reviewer full verification. Existing DSE recurrence
visits all basic weights in order and retains its floor and finite validation. S3-A/B
reused, not rerun; preserved focused exit1 and HH source mismatch remain explicit.
One unqualified local mixed entering/weight FTRAN route plus replacement composition
selected, not a demonstrated defect. Minor optional-refinement cost omission corrected
once offline RED4/GREEN5 with before report preserved; final review no outstanding
findings or unnecessary new production work/memory. Broader S3 checkboxes stay open.

Next 2026-10-12-dse-mixed-route-qualification.md: bounded offline preparation for at
most ten Float64/native component sequences, all five managers with actual HH fallback,
one prior update. Freeze source seam/inverse, inputs, residual/weight/work oracles and
complete attempt budget; no launch from this contract alone. No repeated S3 census or
HH bootstrap/controller audit. S4/S6 gates, CI off, HH reuse disabled and rejected
candidates unchanged. Separate passing closure before fail-fast diagnostic publication.


## S3-D closure and S3-E continuation (2026-10-13)

S3-D is accepted OFFLINE PREPARATION ONLY; see S3-DSE-MIXED-ROUTE-PREPARATION.md
and its independent review. Eleven exact checks, ten source checks, 69 hashes,
eight author independent checks; reviewer verified all69 hashes, all1,168 binary64/
rational entries, six equations, 32 weight bits and three exact inverse clones.
One existing m16 fixture and ten component sequences are frozen; no Julia executed.
Conditional source budget: ten constructors, twenty updates, sixty outer solves
(40F/20B), separately four internal HH unit calls and <=10 orientation solves.
No complete observed internal-attempt counter seam has been implemented.
No source/test/env/master/CI changes or unnecessary production work/memory.

Next: docs/superpowers/plans/2026-10-13-dse-mixed-route-driver.md, ONE bounded
S3-E driver/counter preparation and independent review WITHOUT Julia. Reject this
qualification route if complete internal accounting needs global method overwrite
or full-module cloning; do not reopen HH isolation or controller audits. No launch
authorization. CI off, HH reuse disabled; bootstrap/cache/init/public-budget/native-
retention/broader S3/S4/S6/fullsuite and previous rejections remain unchanged.


## S3-E route rejection and distinct S5-D continuation (2026-10-13)

S3-E resolves the bounded pre-driver question: REJECT complete observed internal-
attempt accounting for the frozen three-wrapper seam with unchanged dispatch. Post-
return cache counts miss throws and conditional orientation work; HH constructor/update
internals are outside the clones. Stop this qualification route, not a general
instrumentation impossibility or demonstrated DSE defect. Eleven source checks/84 hashes,
author seven checks; reviewer full84/all69 D pins/17 frozen D closure files, no findings
or unnecessary production work/memory. No Julia, driver, old rerun or production change.

Reorder to S5-D precision-transfer journal ownership, already named in S5 inventory
and excluded from ordinary S5-A. Read new plan
`docs/superpowers/plans/2026-10-13-precision-journal-transfer-contract.md`.
ONE source/evidence contract, reconcile prior execution first; no speculative repair,
precision increase or numerical launch. Do not reopen HH/bootstrap/controller/DSE
accounting routes. CI/HH reuse disabled; broader gates and prior rejections unchanged.


## S5-D contract and S5-E offline continuation (2026-10-13)

S5-D accepted: 13 source/evidence checks, 103 hashes, seven groups/1617 passing
assertions in EACH of two failed historical CI runs. Six compared source/test files
match each historical commit; perturbation and runtests full files differ explicitly.
Active journal success21 and no-journal failure19 do not qualify their composition.
Final observer sees fresh state before return guard; source counters/shared diagnostics
are not immutable. Existing nine working/journal vector conversions remain unchanged.
Author five checks; fresh reviewer full103/all14 raw rows/16 comparisons, no findings
or unnecessary new production work/memory. No Julia or production/test/CI changes.

Next S5-E: docs/superpowers/plans/2026-10-13-precision-journal-interruption-preparation.md,
ONE OFFLINE two-case stop/throw ownership-oracle preparation on existing fixture,
no numerical driver/launch or precision increase. Check for existing exact-composition
evidence first. Preserve all prior rejections and S4/S6/fullsuite limitations; do not
reopen DSE counters, HH bootstrap or controller audits. Separate passing closure
before fail-fast diagnostic publication.


## S5-E offline oracle preparation and S5-F continuation (2026-10-13)

S5-E freezes exactly two prospective active-journal final-observer cases: stop and
wrapped throw, using the existing fixture plus detached equal-value working arrays.
No Julia or executable numerical driver, new LP arithmetic or production/test/CI
change. Sixteen source checks/115 fresh pins; six author checks and independent
numerical/work review. Existing active success and no-journal failures are separate
historical rows, not executed composition. Fixed source-before/source-after/fresh
snapshot schema is 88 arrays/215 entries per case; observer only retains one fresh
reference and signals stop/throw. Source pre-detachment checkpoint key is preserved,
not asserted valid for detached costs. Fresh checkpoint/cache are empty. Native
profile does not gate the direct weight-refinement call: up to three correction
BTRANs remain source-possible; no observed count or benchmark claim.

Next S5-F is ONE bounded diagnostic driver implementation/review WITHOUT execution,
per 2026-10-13-precision-journal-interruption-driver.md. Do not add success controls,
warmups, fixture tuning, policy changes, hooks, full-module clones or old reruns.
A future guarded launch requires its own complete reviewed plan. CI off, HH reuse
disabled, S2-A/S6-J/whole-AF rejections, Q GC/outlier and S4 broader gates unchanged.


## S5-F driver preparation and S5-G guarded qualification (2026-10-13)

S5-F accepted offline only. Canonical driver-reviewed.jl implements exactly the
existing fixture's detached-journal stop/throw cases and three fixed snapshot groups
(88 arrays/215 entries each). Initial18 structural checks/170 read-time pins and six
author checks remain preserved. Independent review found an Important raw-outcome
observability gap and Minor import-scope wording; separate amendment RED7/GREEN7,
nine checks/176pins resolves them without new cases, callbacks or numerical work.
Original driver/manifest/evidence and pre-fix report/plan are preserved; no rerun.
Final reviewer full176+original170+five preserved bindings, no unresolved findings.
No unnecessary new production work/memory; no Julia execution or runtime pass.

Proceed to S5-G qualification plan PLUS precision-journal-launcher-admission addendum.
Prepare concrete launcher, independent launch pins and auditor and review them first.
Ensure one Julia process including compilecache behavior; resolve actual wrappers
and supported compiled-modules mode from source/docs, no Julia inspection probe.
Then at most one guarded120-second attempt containing the two frozen cases, no
warmup/trial/retry, unchanged policy/tolerances/128-bit request. Failed attempts/raw
are preserved. All old rejections, CI-off/HH-disabled and broader gates persist.


## S5-G qualification and S5-H permanent coverage preparation (2026-10-13)

S5-G independently accepted for two active-journal detached-buffer final observer
stop/throw transfers. One guarded run,48 result predicates true/exit0,752 pins.
Original auditor62/63/all_passedfalse/exit1 preserved; separate7/7 exact qualified
exception-type supplement, no numerical/auditor rerun. Fresh reviewer full752+176
manifest entries and raw ownership/precision/outcome/work/schema checks. Source
state preserved while shared refactor work advances; fresh observer-retained owner,
active aliases/history reset/empty cache/checkpoint verified. Per-case counted1F/1B/
1refactor plus source-derived untimed weight BTRAN; no complete backend budget,
observer neutrality/certificate/speedup claim. Production/test/master/CI unchanged.

Next ONE S5-H offline minimal test candidate, separate artifact, whole existing test
prefix preserved, exactly two existing fixture stop/throw cases, direct type/identity
assertions and bounded snapshots without diagnostic serialization. Read
2026-10-13-precision-journal-interruption-test-preparation.md. No Julia/test-file edit
or launch in H. Full-suite/historical CI/x64 and broader stages remain open; all
rejections, HH-disabled, CI-off, bootstrap/cache/init/controller/native-retention
limits unchanged. All accepted old/frozen drivers and exclusive audits remain immutable.


## S5-H offline test preparation and S5-I integration (2026-10-13)

S5-H independently accepted without Julia execution or actual test-file edits.
Separate candidate preserves10583-byte original prefix. Two prospective existing
active-journal stop/throw cases carry G ownership/cause/ambient/partial-work oracles
as direct assertions, with31 source copies76 entries and3 detached copies9 entries
per case.18 offline checks,4 missing-coverage structural RED predicates,780 hashes,
10 author-independent checks; fresh reviewer full780/3,576,930,876 bytes and source/
fixture/raw analysis, no findings or unnecessary production work/memory. Structural
RED/GREEN are textual coverage checks, not failing/passing Julia tests. G false
original auditor and separate passing supplement remain unchanged. Runtime pending.

Next2026-10-13-precision-journal-interruption-test-integration.md: first NEW focused
launcher/pins/auditor and fresh independent review, then exact candidate integration;
at most one guarded two-case GREEN and one two-case actual-master check, no old
file/suite or success-control rerun. Prefix and actual extracted suffix must bind,
no F/G driver reuse; guard wall120s inclusive, single Julia compiled-modules=existing,
threads1/heap2GiB/VM8GiB/RAM6GiB/swap1GiB. Fresh process absence before pinned edits
or launches. Preserve any failure without silent tuning/retry. No solver repair,
full-suite/x64/CI-cause/observer-neutrality or performance claim. All broader gates,
CI-off/HH-disabled/rejections/native-retention/bootstrap limits remain unchanged.

## S5-I permanent coverage and S5-J ownership reconciliation (2026-10-13)

S5-I integrated as test fddfa737 -> master513c053: exact H candidate,203-line
append with10583-byte prefix preserved. GREEN and actual master each300/300
(298 permanent+2 driver-only),24/25 audit gates,801/1322 pins,9 independent checks
each. Exactly FOUR new setup/transfer lifecycles total. Prelaunch three Important
findings resolved once offline RED3/GREEN4; preserved before evidence. Fresh GREEN
numerical/work review accepted before promotion; master review is separate. Source/
test511 files match GREEN, all user hashes/raw portable bindings checked. Observed
per transfer1 counted F/1B/1ref and refactor_other1, other deltas0; partial counters,
additional untimed weight unit B and up to3 corrections remain source-possible.
No new production work/memory; cold test68 explicit copies170 entries per pair,
plus fixture/solver allocations. No callback snapshots/extra solves. Direct cause
identity/source ownership/fresh aliases/history/cache/checkpoints/precision covered.
No full-suite, native-work, certificate-transfer or observer-neutrality claim.
Read S5-PRECISION-JOURNAL-INTERRUPTION-TEST-INTEGRATION.md and REVIEW, results/S5-I.
Frozen I/F/G/H scripts/driver/launcher/audits/raw NEVER rerun or rewrite; G original
62/63 FALSE plus separate7 PASS remain. CI off, HH disabled and all prior gates
and rejections unchanged.

Next ONE source/evidence-only plan2026-10-13-dual-auxiliary-handoff-ownership.md.
Reconcile existing exact-composition execution first; no new fixture, Julia or
production/test change and no reopened HH/DSE/controller-budget audit.

## S5-J auxiliary ownership reconciliation and S5-K offline oracle (2026-10-13)

S5-J source/evidence reconciliation:21 literal checks,97 fresh read-time hashes,
eight author-independent checks. Reviewer Minor original-bound terminology was
author-regraded Important for contract scope and fixed once offline RED2/GREEN5;
original report/plan preserved, original independent evidence unchanged. Live
working bounds after restoration are not automatically authoritative model bounds. Sixteen original CI rows/eight named testsets give
237 passing assertions SEPARATELY in each failed run;16 exact blocks/whole test
files match.18 production comparisons16 equal, known simplex_perturbation S5-C
change twice. Existing78 private interruption/resume and19 phase publication tests
reused;19 observer throws at prepublication refactor_other, not pending replay.
Source publishes basis/values/factor before queued observer events; diagnostic work
and earlier live restoration mutations survive. No wholefunction rollback or
auxiliary certificate transfer. ONE remaining composition: throwing observer on
pending pricing_phase_reset AFTER publication, not a defect/neverexecuted claim.
Next S5-K OFFLINE observer-identity/reachability and selected-oracle specification,
no fixture/driver/runtime plan. No Julia/production/test/env/master/CI change,
no new production work/memory or performance claim; all prior gates unchanged.
Read S5-DUAL-AUXILIARY-HANDOFF-OWNERSHIP.md and REVIEW, results/S5-J. Frozen J
source_contract/independent/evidence/excerpts NEVER rerun or rewrite; I/F/G/H and
G false62/63 plus separate7 PASS preserved. I continuation texts saved before-J.

## S5-K pending observer oracle and S5-L offline preparation (2026-10-13)

S5-K offline observer/oracle specification completed:20 literal source checks,
118 fresh read-time hashes and8 author-independent checks. Fresh gpt-6-astra review
independently rehashed all118 (771572094 bytes), accepted with no Critical/Important/
Minor and no unnecessary NEW production work/memory. No correction was required.
The forwarded refactor_other candidate is identified by StageObserver.live === LIVE;
pending pricing_phase_reset additionally requires LIVE state and the adopted trial
factor. Source-supported conditional reachability, NOT runtime qualification.
Selected publication/cause/history/checkpoint/work/event-prefix oracle;20 reference
slots plus3 vector copies/six entries,17 publication element comparisons for the
existing tiny fixture. Counts are schema bounds, not allocations/native retention.
Entry-cost equality remains prospective: auxiliary numerical repairs can change
costs despite perturb_degenerate=false; preserve any failure and stop qualification,
no tuning/solver-defect inference. Existing237 historical PASS per failed run and
78/19 interruption/publication coverage reused, not rerun. No Julia, new LP arithmetic,
fixture/driver/launcher, production/test/env/master/CI change. Next S5-L ONE offline
candidate preparation only, no syntax/import/compile/runtime admission or extra solves.
Read S5-DUAL-AUXILIARY-PENDING-OBSERVER-ORACLE.md and REVIEW, results/S5-K.
First closure.py stopped before output/commit/push on external absolute runtime-path
mapping (ValueError, exit1); original source and tool stderr transcription preserved.
Separate closure-2 corrects ONLY that mapping, with offline RED1/GREEN3 and separate
review. No original closure/collector/auditor rerun or numerical attempt.
Frozen K source_contract/independent/evidence/closure/closure-2 NEVER rerun or rewrite.
J continuation texts preserved before-K; all J/I/F/G/H evidence and G false62/63 plus
separate7 PASS unchanged. CI off, HH disabled and every prior broader gate unchanged.

## S5-L offline candidate and S5-M separate admission (2026-10-13)

S5-L OFFLINE candidate preparation complete:181-line UNEXECUTED candidate,
three byte-exact helpers and two fixture setup blocks with exact indentation inverse.
One prospective original Float64 setup/handoff,40 predicates/15 observations,
19 pricing fields.20 text checks,141 fresh read-time hashes,9 author-independent
checks; fresh gpt-6-astra FULL141 (771852990 bytes)/8 artifact bindings and semantic
review accepted without Critical/Important/Minor or unnecessary NEW production work/
memory. No corrections required. Candidate SHA256
b553d449a0db620bfae1970861806a778bbf45d36465026e8b4a540e4b4f4288.
Root StageObserver identity/refactor latch followed by LIVE adopted-factor pending
reset throw; direct wrapper/cause identity and publication/work/event-prefix checks.
Three explicit copies/six entries,20 selected identity roles plus containers/local
aliases; up to18 cold temporary owner tuples,17 publication element pairs,19 pricing
fields,40/15 fixed-key serialization maps. Not measured allocations or native graph
bound. No callback vector scans/copies/extra numerical calls/growing ledgers.
Prospective entry-cost equality may fail due to auxiliary numerical repair; preserve
failure/stop without tuning, retry or solver-defect inference. Raw write precedes
aggregate acceptance; early failures may have no output and require guarded logs.
No Julia/parser/import/compile/native/new LP arithmetic/test/prod/env/CI changes.
Next S5-M FIRST concrete launcher/pins/offline auditor and fresh admission review;
only then at most ONE guarded attempt. No warmup/probes/old testsets or extra solves.
Read S5-DUAL-AUXILIARY-PENDING-OBSERVER-PREPARATION.md and REVIEW, results/S5-L.
Frozen L prepare/source_check/independent/closure NEVER rerun or rewrite; candidate
not executable until separately admitted. K continuation texts preserved before-L;
all K/J/I/F/G/H evidence, K first closure failure/replacement and G false62/63 plus7
PASS unchanged. Master513c053, CI off, HH disabled and all broader gates unchanged.


## S5-M pending observer qualification (2026-10-13)

One guarded exact-L candidate attempt:40/40 predicates,15 observations,18 audit
gates,756 launch pins and8 independent postchecks pass. One original Float64
setup/handoff, one latch/hit; postpublication DiagnosticObserverFailure has the
same sentinel cause. Work0->1iteration/0->1refactor,7callbacks,2shared phase events,
selected state persists with no later selected work. Entry costs/bounds pass once.
Two offline prelaunch failure-handling amendments and initial rejected review are
preserved; final admission accepted, final result review/closure recorded separately.
No production/test/env/CI/master edit or complete import/backend/performance proof.
Next S5-N is separate OFFLINE permanent-candidate preparation only; no execution
or test promotion. See 2026-10-13-dual-auxiliary-pending-observer-test-preparation.md.
All prior qualification limits, rejected routes, CIoff/HHdisabled and full-suite
obligations remain. M/L/K/J/I/F/G/H evidence and exclusive scripts stay frozen.


## S5-N offline pending-observer permanent candidate (2026-10-13)

Separate candidate preserves19080byte test prefix+181lineappend, all40 M predicates
as explicit assertions and exact original fixture/helper/policy source inverse.
No actual test edit or Julia/parser/import/compile/native execution.19textchecks,
789 fresh hashes,8 independent checks; structuralRED3 is source-only missing
coverage. Three copies/six entries retained; observation/serialization maps removed,
no extra numerical calls. Independent review and closure remain separate evidence.
Next O is a separately reviewed admission/integration stage with one GREEN and one
actual-master case only, no rerun of historical tests. See the O integration plan.
All earlier rejected routes, CI-off/HH-disabled/full-suite and memory/work limits
remain; N/M/L/K/J/I/F/G/H frozen evidence must not be rerun or rewritten.

## S5-O focused integration and distinct S5-P continuation (2026-10-13)

S5-O exact N candidate integrated: testb8615b9 -> master35a6a9f, only181lineappend
with19080byte original adaptive-pricing prefix preserved. GREEN/master each42/42
(40permanent+2driver),24auditgates827/1347pins9/10authorpostchecks. Exactly TWO new
Float64setup/publichandoffs total, one per actual source-root, entries1/1/1; all40
literal predicates and15 fixed observations pass. One rootStageObserverlatch and
LIVEadoptedfactorhit, directDiagnosticObserverFailure/same sentinel, selected
postpublication state/work persists: iterations/refactors0->1,7callbacks,2shared
phaseevents(not2hits), no later selectedwork. Entrycost equality is observed only,
not a general guarantee; trial remains mutable until unwind, no rollback/certtransfer.
Freshgpt6astra prelaunch/GREEN/master reviews accepted/no unresolvedfindings/no
unnecessaryNEWproductionworkmemory. InitialImportant mandatorybindinggap preserved
as rejectedreview/original813; separate requiredpathcorrection RED2/GREEN4 and822
admission accepted. Missing/malformedinput3syntheticcases failclosed. All originals
and amended files frozen, no numericalretry. Coldthreecopies/sixentries percase,
17pubpairs/19fields/fixedmetadata+driverrecords/Teststorage;20rolesNOTgraphcap.
No completePREforward/backend/import/cacheconfinement/speedup/nativefree claim.
Master511src/testidentities anduser6 match. Samples16/17,minRAM21961172/21929716KiB,
swap0,inclusive16.018377/17.024098s NOTbenchmark. Groups63808/63815 and64420/64422
plusolder absent/noJulia; masterrunner64421/start2749445,child64422/start2749569,
bootdade7243-9103-4398-bb45-fa28fbc0be72. Separate publicationclosure required and
recorded independently beforefailfastpush. SeeS5-DUAL-AUXILIARY-PENDING-OBSERVER-
TEST-INTEGRATION.md/REVIEW,results/S5-O. AllO/N/M/L/K/J/I/F/G/HfrozenNEVERRERUN;
Noldtestpin mapsONLYsavedbyteexactoriginal. Mrejectedreview/twofixes,Kfailedclosure+
PASS,Gfalse62/63+7PASSpreserved. Production/env/CIunchanged,HHdisabled/fullsuite/
x64/allpriorbroadergates/rejectionsunchanged.

Next S5-P source/evidence-only supplied-basis initialization contract per separate
plan. This was already a distinct S5 inventory boundary; no old reruns, new Julia,
fixture/runtime plan or automatic optimization. Do not reopen HH/DSE/controller audits.

## S5-P supplied-basis contract and S5-Q offline continuation (2026-10-13)

S5-P SOURCE/EVIDENCE ONLY reconciliation: 22 literal checks,157 fresh read-time
hashes,six exact excerpts,9 author checks; fresh independent numerical/work review.
Forty references: one production definition,34 test calls,3 dev calls,2 isdefined;
no other literal production caller. Sixteen historical CI rows/eight groups sum to
400 PASS separately in EACH failed run; seven direct-call groups388 include crash
assertions,12 adjacent clock/driver assertions are not initializer-stop coverage.
All16 whole test files match,22/24 selected source comparisons match; two known
simplex_perturbation differences explicit. Default workspace/recompute precedes
policy install and owned supplied-basis copy/validation; problem and diagnostics
remain shared, clock/offsets retained. Native refinement/recovery off need not call
stop; checked stop sites are conditional and occur after base solves. Reliability
is not feasibility/certificate. ONE unqualified explicit throwing-stop + supplied
basis + shared progress/checkpoint composition, not defect/never-executed proof.
Cold source counts include default+imported reconstruction4base solve entry sites,
factory+refactor,conditional refinement/checkpoints/scans/copies; not observed
PREforward/backend/import/allocations. No new production work/memory, no benchmark.
Two new offline collector path failures preserved; corrected read/collector separate,
no old rerun or Julia. O827/1347/fullraw9+9/closure20/publication4 reverified; original
O rejected admission+correction and allN/M/L/K/J/I/F/G/H evidence frozen unchanged.
See S5-BASIS-INITIALIZATION-CONTRACT.md/REVIEW,results/S5-P. Separate PASS closure
required before fail-fast diagnostic publication. Master35a6a9f/production/test/env/
CI unchanged,fullgroups absent/noJulia;allHH/CI-off/rejections/broadergates retained.

The prior S5-P next-action paragraph is fulfilled by this stage. Next read the
separate S5-Q offline oracle-feasibility plan; no runtime admission is implied.

## S5-Q offline stop oracle and S5-R preparation (2026-10-13)

S5-Q OFFLINE oracle feasibility: 18 literal checks,178 fresh read-time hashes,
8 author checks; fresh independent numerical/work review. Existing Float64/PFI/
native setup only, recovery=true/refinement=false and sparse/hypersparse retained.
Two historical rows1504/1504 separately in EACH failed CI run cover the entire
source-matched transfer testset, not this prospective stop case. Source-supported
initial/other/checkpoint discriminator arms the original explicit stop immediately
before checkpoint storage; default initialization already consumed work. Expected
original sentinel/guard identity, no return, caller basis ownership/value preservation,
shared problem/progress/clock/offsets7/11, localiter0/ref1 and consumed diagnostics.
Conditional two explicit stops/four observer callbacks/three recorded events,
checkpointcount1/historyempty/phasegeneration1; counted2F/2B/1ref, corrections0.
One factory and backend/hypersparse work additional. Two checkpoint constructions,
10vector containers/36copied entries are source accounting, not allocations.
Prospective instrumentation two basis copies/six entries/nine reference roles plus
aliases/fixed fields; no callback array scans/copies, growing ledgers or extra solves.
Retained workspace mutable until unwind; no rollback/fullstate/certificate/real
expiry/nativefree/PREforward/backend/import budget or speedup claim. No unnecessary
NEW production work/memory. No Julia, candidate, fixture, driver, launcher or actual
test change. Runtime reachability remains UNQUALIFIED; failure must preserve/stop.
Read S5-BASIS-INITIALIZATION-STOP-ORACLE.md/REVIEW,results/S5-Q. Separate PASS closure
precedes fail-fast publication; P-bound continuation texts preserved before-Q.
All Q/P/O/N/M/L/K/J/I/F/G/H frozen records, failed audits/reviews and broader gates
remain unchanged; master35a6a9f, production/test/environment/CI unchanged.

The previous S5-Q next action is fulfilled. S5-R is separately limited to one
unexecuted candidate with exact inverse and review; no launch admission follows.

## S5-R unexecuted candidate and separate S5-S admission (2026-10-13)

S5-R OFFLINE candidate preparation: canonical candidate-reviewed.jl179lines/SHA
 d03fcc9c0d2f70a16437ea2412e56c807babccb99f6df25aec82894b67d51950,
40named predicates,19literalchecks199freshreadtimehashes8authorchecks. Initial
candidate/194pins preserved SUPERSEDED/UNEXECUTED: author found Important missing
NumericalPolicy.numerical_profile field (constructor keyword only); separate one
expression offline RED/GREEN fix4checks preserves setup/policy/assertion names.
Exact original setup inverse, one prospective Float64/PFI/native initialization,
recoverytrue/refinementfalse/sparsehypersparse/Inf/offsets7and11 unchanged. Ordinary
observer stages defaultcheckpoint/initial/importedother/importedcheckpoint; immediate
second explicit stop throws original sentinel before checkpoint store/event.
All Q identity/no-return/ownership/sharedprogress/work/event families concrete;
limited2F2B1ref/localiter0ref1/checkpointcount1/historyempty/phasegen1,4callbacks2stops.
Two explicit basis copies6entries;15fieldprobe/9fieldentry/two14fieldworkcaptures,
40Booltuple/12observations/fivefixedoutputdicts84entries on reached prefix.
No callback arrayscans/copies/growingledgers/extranumerics; aliases/diagnostics/
closure/guard/retainedmutableworkspace graphs NOTmemorycap/nativefreeproof.
Source checkpoint10containers36entries/factory/backend/hypersparse additional;
not completePREforward/native/import/allocations/rollback/certtransfer/speedup.
Fresh independent numerical/work review required before separate PASS closure and
fail-fast publication. No Julia/parser/import/compile/native/launcher/actualtest/
production/env/cache/CIchange. Read S5-BASIS-INITIALIZATION-STOP-PREPARATION.md/REVIEW,
results/S5-R. Q-bound continuation preserved before-R; all older frozen failures/
reviews/raw unchanged,master35a6a9f/allbroadergates/HHdisabled/CIoff unchanged.

The previous S5-R next action is fulfilled. S5-S must meet its separate concrete
launcher/pin/auditor/review gate; R is not runtime qualification.

## S5-S qualified stop and S5-T offline test preparation (2026-10-13)

S5-S ONE guarded qualification-1: exact R canonical candidate SHA
 d03fcc9c0d2f70a16437ea2412e56c807babccb99f6df25aec82894b67d51950,
40literalTRUE/exit0,19auditgates856pins9authorpostchecks; fresh independent result
review. ONE existing Float64/PFI/native supplied-basis initialization; no control,
resume/transfer/crash/extra solves. Original sentinel/caught/guardidentity, no return,
caller/imported/default basis ownership/values, shared progress/clock/offsets7and11,
native recoverytrue/refinementfalse/sparsehypersparse/Inf preserved. Fourcallbacks,
twoexplicitstops/onethrow,threerecordedevents; both14fieldworkrecords2F2B1ref,
localiter0ref1/checkpoint1/history0/phase1/corrections0; no later selected work.
Initial797 admission rejected for timing/undurableguardfailure; separate correction
6source+5refusal+3terminalchecks. Revised811 rejected for auditlog/reservationlinkage;
second separate6source+7syntheticcases. Accepted853 -> actual856, both rejected
reviews/manifests/source preserved. New localguard includes terminal wall120 check;
rawguardinvocation/log/reservation strictly bound; no numerical retry.
Six raw/portable files exact,5resourcesamples minRAM22302144KiB swap0,
5.006940819s including launch/import/compile/polling NOTbenchmark. Runner71825
start3208391/group71824,child71826/start3208508/group71826 and allpriorgroups absent.
Two basis copies6entries/fixed15fieldprobe/9fieldentry/40predicates/12observations/
84outputentries plus formatting/Testfuturecost; no callback scans/copies/extra
numerics/growingledger. Defaultfactory/hypersparse/backend/import additional;
checkpoint10containers36entries SOURCEcounts, no completePREforward/native/import
budget/GC/nativefree/observerneutrality/fullstate/rollback/certtransfer/speedup.
Master35a6a9f, production/actualtest/env/CI unchanged, HHdisabled/allbroadergatesopen.
Read S5-BASIS-INITIALIZATION-STOP-QUALIFICATION.md/REVIEW and results/S5-S.
S5-T ONLY separate UNEXECUTED test-candidate preparation offline; future actual
edit/launch/integration requires separate reviewed admission. All S/R/Q/P/O and
older frozen evidence/scripts NEVER RERUN/rewrite. R continuation preserved before-S.

The S5-S numerical allowance is consumed. Do not repeat it; S5-T is offline only.

## S5-T unexecuted test candidate and S5-U separate admission (2026-10-13)

S5-T OFFLINE permanent-test preparation: separate UNEXECUTED candidate SHA
357a976f5fc984025452ee4b259f2fc1f140885212f5b40ff71e072ebfab3684,
7647-byte actual-test prefix unchanged plus202-line suffix. Exact S-qualified R core
inverse after three explicit test-local renames; forty unchanged predicates returned
and forty explicit @test assertions, one prospective Float64/PFI/native initializer.
Standalone CLI/TOML/twelve observations/five84-entry output dictionaries removed.
Policy/options/tolerances/Inf/offsets7and11, original sentinel/guard identity,
no-return/basis owners/values/shared progress and selected work/events unchanged.
21 literal checks,891 fresh read-time hashes,eight author checks/seven bindings;
structural RED3 missing coverage markers is not failing Julia/CI reproduction.
Fresh independent numerical/work review accepted, no unresolved findings or
unnecessary NEW production work/memory. Two copies6entries,15fieldprobe,9fieldentry,
two14fieldcaptures/expected14/40Booltuple; four post-unwind vector equalities up to
12elementpairs; cold Test storage additional. No callback array scans/copies/extra
numerics/growing ledger. Existing diagnostics/factory/hypersparse/backend/imports
additional; checkpoint10containers36entries SOURCE counts, not complete PREforward
or native/import budget. Retained graph mutable until unwind, metadata not graphcap/
rollback/fullstate/certtransfer/real-expiry/native-free/GC/observer-neutrality proof.
No Julia/parser/import/compile/native/numerical/launcher/actualtest/prod/env/cache/CI
change. Master35a6a9f unchanged. S bound continuation texts preserved before-T;
all S/R/Q/P/O and older frozen scripts/raw/false audits/rejected reviews unchanged.
Read S5-BASIS-INITIALIZATION-STOP-TEST-PREPARATION.md/REVIEW and results/S5-T.
Next S5-U FIRST concrete NEW focused driver/guarded launcher/required pins/fail-closed
failure auditor and fresh independent admission BEFORE actual test edit or Julia.
At most one focused GREEN and one actual-master attempt, one initialization each;
no old testset rerun. Separate plan2026-10-13-basis-initialization-stop-test-integration.md.
HHdisabled/CIoff/bootstrap/cache/init/wholecaps/native-retention/fullsuite/all prior
rejections and broader S3/S4/S5/S6 gates remain open.

The previous S5-T next action is fulfilled; its candidate remains UNEXECUTED.


## S5-U exact test integration and S5-V source contract (2026-10-13)

S5-U integrated exact T candidate: test a39aed1 -> actual master2b546e9, only202-line
append with7647-byte prefix unchanged. Exactly TWO new Float64/PFI/native supplied-
basis initializations total, one GREEN and one actual-master. Each42/42 (40 permanent
plus2 driver),25 audit gates,1489/1512 actual pins,9 author postchecks/14 bindings,
raw8 original/portable and invocation3 identities. Fresh independent gpt-6-astra
admission/GREEN/master reviews accepted with no unresolved Critical/Important/Minor
or unnecessary NEW production work/memory; full actual1489/1512 rehash, source511,
user6, exact candidate/suffix/four-insertion inverse and complete GREEN chain checked.
Initial1446 admission rejected for stage binding; revised1466 rejected for GREEN
raw linkage; separate18/16-check corrections and final1485 admission accepted.
Both rejections/sources/manifests and all synthetic failures preserved. postcheck
source was supplemental admitted/bound, not part of original1485 admission pins.
Original sentinel/caught/guard identity/no return/owned bases/shared progressclock/
policy/options/tolerances/Inf/offsets7and11 preserved. Two stops/four callbacks/three
recorded events; both14-field work records2F2B1ref/localiter0ref1/checkpoint1/history0/
phase1/corrections0 and no later selected work. This is PARTIAL existing wrapper
accounting; defaultfactory/hypersparse/backend/import work additional. Cold two basis
copies6entries,15fieldprobe9fieldentry/two14captures+expected14/40Booltuple/four
vector equalities<=12pairs plus Test storage. Driver bounded counters/scalar records/
serialization only, no callback scans/copies/growing ledgers/extra numerics. Retained
mutable graph not native-free/rollback/fullstate/certtransfer/real-expiry/observer-
neutrality/PREforward/backend/import proof. Each6resource samples, minRAM22278708/
22242836KiB swap0, inclusive6.006539625/6.006393195s NOTbenchmarks. Full20groups absent.
Report S5-BASIS-INITIALIZATION-STOP-TEST-INTEGRATION.md and companion REVIEW; results/S5-U.
All U and older frozen drivers/launchers/auditors/raw/rejected reviews preserved;
T-bound continuation texts saved before-U. No production/environment/CI change.
Next S5-V2026-10-13-crash-fallback-ownership-contract.md is SOURCE/EVIDENCE ONLY:
existing crash fallback/trial ownership/publication and test/log coverage FIRST,
no assumed gap/defect and no new fixture/driver/Julia/numerical admission. Do not
reopen HH/DSE/controller-budget audits. CIoff/HHdisabled/Q GC/outlier/bootstrap/
cache/init/wholecaps/native-retention/fullsuite/broader S3/S4/S5/S6/rejections open.

Separate PASS closure and exact staged-file/blob publication gates remain mandatory before push.


## S5-V crash fallback ownership and S5-W offline oracle (2026-10-13)

S5-V SOURCE/EVIDENCE ONLY: existing crash boundaries reused; one narrower fallback
observer-throw composition remains unqualified, not a solver defect/never-executed
claim. New collector21 literal checks/166 fresh read-time hashes/four exact excerpts;
author9 checks/seven bindings. Twenty-four exact lexical testset slices,48 original
CI rows:511 PASS SEPARATELY EACH failed historical run, including adjacent imported-
start/phase-one groups, not511 fallback assertions. All32 historical whole-file
comparisons equal (five tests and eleven production files per run). Four literal
fallback test references are event-count assertions; existing observer-throw loop
covers phase_crash/crash_pivot/crash_accepted. Existing final-refactor stop/pivot-stop/
precision/partial-phase success remain reused, no equivalent numerical census.
Source: fresh private trial owns containers/factor/scratch and shares problem/progress;
initial work charged before trial constructor, recovery_active only after it. Fallback
merges max counters into INITIAL, records crash_fallback BEFORE observer, then returns.
Observer throw escapes as DiagnosticObserverFailure with cause; initial numerical
vectors not copied from trial. Arbitrary observer mutation/retained mutable graphs
exclude full-state/rollback/native-free/observer-neutrality claims. Partial crash
acceptance not original feasibility/certificate. Existing candidate scans/solves/
refinement/factory/checkpoint work SOURCE counts only, not complete PREforward/native/
import budget. No unnecessary NEW production work/memory; no benchmark or Julia.
Fresh independent numerical/work review accepted, no unresolved findings. U1512/
GREEN1489/T891 and Uclosure24/123/pub6/exact126 committed blobs reread with explicit
historical OLD-test and before-U continuation mappings; no frozen auditor rerun.
U test/master and diagnostics previously pushed/remote verified. Master2b546e9 stays;
production/test/env/cache/CI unchanged. See S5-CRASH-FALLBACK-OWNERSHIP.md/REVIEW,
results/S5-V. V/U and older exclusive scripts/raw/audits frozen; preserve all rejected
reviews/false audits. Full20 prior groups absent, user6 unchanged.
Next S5-W2026-10-13-crash-fallback-observer-oracle.md: ONE OFFLINE oracle specification,
existing final-factorization-interruption fixture/source only, no new LP/driver/
launcher/permanent candidate/Julia or numerical admission. Discriminate INITIAL
fallback after work merge/event recording; specify minimal selected ownership/value/
cause/work observations and costs first. No repeated covered cancellation/success,
no HH/DSE/controller-budget reopening. All prior gates/rejections/CIoff/HHdisabled/
Q GC-outlier/bootstrap-cache-init/wholecaps/native-retention/fullsuite remain open.


## S5-W fallback observer oracle and S5-X preparation (2026-10-13)

S5-W OFFLINE oracle accepted: one prospective fallback-observer throw after trial
final refactor, INITIAL work merge and event recording. All runtime outcomes remain
UNQUALIFIED. Existing exact six-assertion final-factorization block preserved; native
Float64/PFI construction/options/Inf/limits/policy unchanged, refinement/recovery and
kernel_timing false. Final refactor_other is BEFORE native reconstruction, not a
stop-before-solves boundary. Existing6/10/6 historical assertions reused, no old run.
New19 literal source checks/189 fresh hashes/entry14/author8 with8 bindings. V166,
Vclosure12/24/pub7/exact27 and U1512/GREEN1489/T891 lineage reconciled with preserved
before-text/OLD-test mappings, never retroactive launch changes. Fresh independent
numerical/work/memory review accepted; no unresolved findings/no unnecessary NEW
production work/memory. Prospective7 vector copies26 entries,17 entry-owner roles,
21 reference roles plus containers/aliases, six probe scalars/two state refs, fixed
2/7/7 metadata records; no callback vector scans/copies/numerics/growing ledger.
Post-unwind selected values not callback snapshot; retained graphs mutable, not
native graph cap/native-free/fullstate/rollback/certificate/observer-neutrality proof.
Source factory/checkpoint/backend work additional, not complete PREforward/import
budget; disabled kernel counters not observed work. No Julia/parser/import/compile/
native/numerics/candidate/launcher/new LP/test/production/env/cache/CI changes.
Master2b546e9 unchanged; V48771ac previously pushed/verified. See
S5-CRASH-FALLBACK-OBSERVER-ORACLE.md/REVIEW and results/S5-W. Frozen W/V/U and older
exclusive scripts/raw/rejected reviews/false audits preserved. Full20 groups absent,
user6 unchanged. After separate PASS closure and exact publication, S5-X
2026-10-13-crash-fallback-observer-preparation.md permits ONLY an UNEXECUTED separate
diagnostic candidate and offline inverse/cost checks, no launcher or numerical
admission. All rejections/CIoff/HHdisabled/Q GC-outlier/bootstrap-cache-init/wholecaps/
native-retention/broaderS3S4S5S6/fullsuite remain open.


## S5-X offline candidate and S5-Y admission (2026-10-13)

S5-X OFFLINE candidate independently accepted, UNEXECUTED. Exact candidate SHA
5c941e86131ed503149de5a47ac46fc7665507861a25ec16654b6711968fdf18; one prospective
Float64 PFI/native INITIAL setup and one crash call, exact existing construction
inverse/original done latch/stop/defaults. Fifty named predicates; first TRIAL
refactor_other before reconstruction, then INITIAL fallback after max-counter merge
and event record, original SingularException42 wrapper/cause/no-return. All runtime
expectations UNQUALIFIED. New22 literal checks213 fresh hashes/entry17/author9 with
10 bindings, full W189/V/U1512/GREEN1489/T891 lineage and historical maps preserved.
Fresh independent numerical/work/memory review accepted, no unresolved findings or
unnecessary NEW production work/memory. Probe11 fields plus original done Ref;
three owner17-tuples, seven copies26 entries, clock3/work2/refactor2/fallback7/after7,
50-Bool tuple/twelve observations/eight dictionaries90 total entries plus formatting.
Callback no array scans/copies/numerics/growing ledger; endpoint checks <=26 pairs,
retained mutable graphs not graph cap/native-free/fullstate/rollback/cert/observer
neutrality/PREforward/backend/import proof. Raw precedes aggregate assertion when
reachable, early errors need future failclosed logs; output reservation not atomic
in candidate alone. No Julia/query/parser/import/compile/native/numerical call,
launcher/actualtest/production/env/cache/CI changes. Master2b546e9 unchanged. See
S5-CRASH-FALLBACK-OBSERVER-PREPARATION.md/REVIEW and results/S5-X. All X/W/V/U and
older frozen scripts/raw/false audits/rejected reviews preserved. After separate
PASS closure/exact publication S5-Y2026-10-13-crash-fallback-observer-qualification.md
FIRST requires concrete launcher/complete pins/failclosed auditor/offline failure
cases and fresh independent admission BEFORE any numerical attempt. All broader
S3S4S5S6/fullsuite/Q GC-outlier/bootstrap-cache-init/wholecaps/native-retention,
CIoff/HHdisabled and rejections unchanged.


## S5-Y qualified observer boundary and S5-Z offline test preparation (2026-10-13)

S5-Y ONE guarded qualification independently accepted: exact X candidate SHA
5c941e86131ed503149de5a47ac46fc7665507861a25ec16654b6711968fdf18,50 literalTRUE/exit0,
23 audit gates1347 launch pins/1344 admission pins/338required paths/post11 with8
bindings/raw6 originalportable/invocation3. Entry18 and full X/W/U/T preservedmaps.
Fresh admission and result numerical/work/memory review accepted, no unresolved
findings/no unnecessary NEW production work/memory. One source-bound INITIALsetup
and one crash invocation; one TRIAL refactor_other BEFORE native reconstruction,
one INITIAL fallback AFTER maxmerge/eventrecord. Entrywork0/0,refactor2/2,fallback
and after2/2,pivot2/refother1/fallback1/accepted0/callbacks6,nolaterselectedwork/events.
Original SingularException42 -> DiagnosticObserverFailure samecause/noreturn.
All17 entry roles/seven selected values/11 distinct TRIAL roles/sharedproblemprogress
policy/scaling/options-value/clockoffsets preserved. Kernel timingfalse/native
recoveryrefinementfalse/defaults/Inf/interval20 unchanged. Coldprobe11+doneRef/three
owner17tuples/seven copies26entries/fixedrecords/50Bool/12obs/eightdicts90entries;
no callback array scans/copies/numerics/ledger. Endpointnotcallbacksnapshot/retained
trialmutable/notnativegraphcap/nativefree/GC/fullstate/rollback/certtransfer/observer
neutrality/PREforwardbackendimportproof. Five samples,minRAM22199108KiBswap0,
5.0120892799968715s inclusive NOTbenchmark. Runner84688(start3994258,PGID84681),
child84689(start3994307,PGID84689),all22groupsabsent/noJulia/user6unchanged.
Source/project/command pins not hiddenruntime method/loader capture; threadflags
configured notextra runtimequery. Postcheck.py supplementalpostexit NOTlaunchpin.
No production/actualtest/envconfiguration/CI/masterchange;master2b546e9 unchanged.
Sole allowance CONSUMED; allY/X/W/V/U/older scripts/raw/auditors/reviews FROZEN,
NEVER RERUN/rewrite. See S5-CRASH-FALLBACK-OBSERVER-QUALIFICATION.md/REVIEW/resultsS5-Y.
After separate PASSclosure/exactpublication next S5-Z2026-10-13-crash-fallback-observer-
test-preparation.md is ONE separate UNEXECUTED permanent candidate OFFLINE ONLY,
whole actualtestprefix/exact qualifiedconstruction/all50predicates preserved;
no Julia/actualtestedit/launcher or numericaladmission. CIoffHHdisabled/allbroader
S3S4S5S6/fullsuite/rejections/QGCoutlier/bootstrapcacheinit/wholecaps/retention unchanged.


## S5-Z offline test preparation and S5-AA admission (2026-10-13)

S5-Z OFFLINE separate permanent candidate accepted and UNEXECUTED, SHA
ce256932a4bbda14bb9c55678525d6506a8e63732683442def57b22873b0415f.
Whole4774-byte actualtest prefix preserved plus193-line append; three scoped renames,
explicit top-level LinearAlgebra:SingularException import plus byte-exact inverse
of Y-qualified X probe/helpers/core/all50 predicates,50explicit
Test assertions/one prospective Float64PFInativeINITIALsetup+crash. Originaldone/stop/
options/tols/Inf/interval20/refinementrecoveryfalse/kerneltimingfalse unchanged.
CLI/TOML12observations/eight90entryoutputdicts removed. Cold11fieldprobe+doneRef,
three17roleowner tuples/seven vectorcopies26entries/fixedscalarrecords/50Booltuple/
50Testresults additional; callback no array scans/copies/numerics/growingledger.
Retainedtrialmutableuntilunwind/endpointsNOTcallbacksnapshots/nativegraphcap/nativefree/
GC/fullstate/rollback/certtransfer/observerneutrality/PREforwardbackendimport proof.
Initialentry24/source19/readtime1398/author10with8bindings preserved; separate
review-fix8 and pins-reviewed bind canonical candidate-reviewed.jl/append-reviewed.jl.
InitialImportantmissingtop-levelimport and Minorcoveragefileclaim(authorregraded
Important) fixed ONEofflineRED2/GREEN2; original rejectedreview/candidate untouched.
Six final-stop assertions in prefix; ten pivot-stop/six observer-cause assertions
remain in unchanged start-guard file.
 fullY1347/1344/required338/
raw6inv3/closure51/exact53 and XWUhistoricalmaps unchanged. Freshgpt6astra independent
numerical/work/memory review accepted; no unresolved findings/no unnecessaryNEW
production work/memory. First two Python selectors failed before candidate creation
(missingMULTILINE,then52names); sources/failures preserved; separate prepare-3 scoped50
passed. Misnamed original53 key is explained; recorded count52 authoritative.
StructuralREDfourmissingcoverage markers is NOT failingJulia/CIreproduction.
NoJulia/query/parser/import/compile/native/numerical/launcher/actualtest/production/
envconfiguration/cache/CI/masterchange;master2b546e9 unchanged. YallowanceCONSUMED.
AllZ/Y/X/W/V/U and older scripts/raw/audits/reviews FROZEN,NEVER RERUN/rewrite.
See S5-CRASH-FALLBACK-OBSERVER-TEST-PREPARATION.md/REVIEW/resultsS5-Z.
After separatePASSclosure/exactpublication next S5-AA2026-10-13-crash-fallback-observer-
test-integration.md FIRST concrete stage-bound launcher/pins/failclosedauditor/
offlinefailuretests/fresh admission BEFOREJulia or actualtestedit. At most one GREEN
and one actualmaster newcase only after acceptedadmission; no oldtest rerun.
CIoffHHdisabled/allbroadergates/fullsuite/retention/bootstrapcacheinit/wholecaps/Qoutlier/
GC and allrejections unchanged.


## S5-AA integration and S5-AB coverage reconciliation (2026-10-13)

S5-AA integrated exact corrected Z candidate: test c5c3147 -> actual masterd02416c,
whole4774-byte prefix unchanged plus193 lines/50 permanent assertions/explicit
top-level SingularException import. Exactly TWO new Float64PFInativeINITIALsetup+
crash lifecycles TOTAL, one GREEN and one actual-master; each52/52(50+2driver),
33audit gates1468/1493pins10authorpostchecks9bindings/raw8originalportable/inv3.
Fresh independent admission/GREEN/master admission/result reviews accepted, no
unresolved Critical/Important/Minor or unnecessary NEW production work/memory.
Initial1464/required1463/full511sourcepairs and exact five-insertion inverse checked;
master36stagebindings include all23GREENevidence paths. First entry three false
historical continuation gates preserved; separate entry-2 exactmaps38PASS. Preliminary
session/identity/terminal-memory findings fixed with preserved drafts and27 offline
checks;92+15 initial tests and77 reviewer gates PASS, no numerical retry.
All50 predicates/nativepolicy/options/tols/Inf/interval20/originaldone-stop unchanged.
Each entry0/0,TRIALrefactor2/2,INITIALfallbackafter2/2,pivot2/refother1/fallback1/
accepted0/callbacks6/no laterselectedwork; sameSingularException42wrappedcause/no return.
TRIALrefactor before ordinary reconstruction, fallback after maxmerge/eventrecord.
Selected17INITIALroles/sevenvalues/11distinctTRIALroles/sharedproblemprogresspolicy/
scaling/optionsvalue/clock preserved; retainedTRIALmutableuntilunwind, notcallbacksnapshot.
Coldprobe11+done/threeowner17tuples/sevenvectorcopies26entries/fixedrecords/50Bool+
Teststorage; driverfourcounts/fixed90entryrawdicts/serialization. No callback scans/
copies/numerics/ledger. No PREforward/backend/import/kernel budget/native-free/GC/
fullstate/rollback/certtransfer/observer-neutrality/speedup/CIcause proof.
Each6samples,minRAM22137132/22070736KiBswap0,terminal22583232/22516760KiB,
inclusive6.012333269/6.011550007s NOTbenchmarks. Full26groups/sessions absent/noJulia.
All AA/Z/Y/X/W/V/U and older raw/scripts/launchers/auditors/reviews FROZEN after
closure, both AA numerical allowances CONSUMED. Before-AA continuation preserved;
all older historicalmaps/falseaudits/rejections unchanged. No production/env/CIchange.
Reports S5-CRASH-FALLBACK-OBSERVER-TEST-INTEGRATION.md/REVIEW,results/S5-AA.
After separate PASS closure and exact publication next S5-AB2026-10-13-handoff-
coverage-reconciliation.md is SOURCE/EVIDENCE ONLY: reconcile original S5 obligations
against accepted coverage, no new numerical plan/fixture/candidate/driver/launcher,
no old rerun or HH/DSE/controller/isolation reopening. CIoffHHdisabled/all broader
S3S4S5S6/fullsuite/bootstrapcacheinit/wholecaps/native-retention/QGCoutlier/rejections
remain open.

## S5-AB coverage reconciliation and remaining initialization gate (2026-10-13)

S5-AB SOURCE/EVIDENCE ONLY reconciliation accepted: seven original handoff rows
covered at their stated unchanged-contract scope; no equivalent new census selected.
Entry23/full1829 hashes rebinds AA1464/1463/1468/1493/raw8/inv3/closure95/exact99;
41groups/82 original CI rows pass SEPARATELY in each FAILED historical run.
Ten historical test files match;14 selected production files per run have13matches
and known S5-C perturbation difference. C actual9file/1463 execution reused,
8wholefiles+AO unchangedprefix; I/O/U/AA/AC/AO actual-master selected source/test
bindings, AA reliable target distinct from later AC wholefile. Initial10checks/81pins,
source23/111pins,author8/full1883/6bindings preserved. First selector nonexistent
scaling.jl failure preserved; separate transformations.jl version. Important review
wrong S5-O test binding preserved/rejected: unrelated adaptive_pricing_tests.jl was
pinned, actual execution is adaptive_pricing_lifecycle_tests.jl. One separate offline
RED/GREEN supplement8PASS/7bindings plus author5/5bindings binds actual driver,
master pins/raw wholefile/suffix42pass; five other integration records unchanged.
Before-review report and original gates remain historical, not retroactive proof.
Fresh independent gpt-6-astra full named manifests/rows/Git comparisons and bounded
fix review accepted, no unresolved findings or unnecessary NEW production work/memory.
No Julia/query/parser/import/compile/native/numerical/fixture/candidate/driver/launcher/
benchmark/test/production/env/cache/CI change. Masterd02416c unchanged. All old
numerical allowances consumed; all old raw/scripts/audits/rejections preserved.
AA closure/publication and AB initial read-time STATUS/roadmap map ONLY AB.before-AB;
AA launch/admission remain AA.before-AA; older Z/Y/X/W/V/U/T maps unchanged.
Original inventory identity-transform branches may share problem identity; no universal
fresh model copy. Covered rows do not prove cross-products/currentfullsuite/x64cause.
S5 initialization reuse/end-to-end gate remains OPEN; C saves one restoration cost
copy, not initialization. After separate PASS closure/exact publication, next S5-AC
2026-10-13-cleanup-entry-reuse-design-decision.md is ONE bounded source/design-only
eligibility/failure decision on A's existing native/no-observer/infinite-budget
hypothesis. No unconditional omission, numerical/implementation allowance or repeat
of A184/oldmedium/qualified handoffs. HH/DSE/controller/isolation audits stay closed;
CIoff/HHdisabled/broadergates/bootstrapcacheinit/wholecaps/native-retention/Qoutlier unchanged.

## S5-AC cleanup design decision and distinct S6-AP continuation (2026-10-13)

S5-AC SOURCE/DESIGN ONLY decision accepted: omission DEFERRED; the existing
native/no-observer/infinite-context flag gate is insufficient. Native constructor
profile permits explicit policy overrides; no observer still permits diagnostic
events/kernel counts; options and context clocks differ. Zero scratch/default
weights are not reconstructed state. Ordinary initialization failure reaches the
outer handler with workspace=nothing; strict ordinary recovery also returns its
numerical result, so this ownership distinction alone is NOT a demonstrated
changed recovery outcome. Default arithmetic failure equivalence and scratch/cache
initialization remain unproved even for a stricter diagnostics=nothing/infinite-
both-clocks/fixed-hardware subset. No impossibility or new failing fixture claim.
No hidden retry, duplicate work, swallowed logger/observer exception, changed
safeguard or working-to-original certificate transfer is permitted.
Entry20/full1910 hashes, source19/25pins and author8/full1917/6bindings PASS.
AB initial rejection and corrected O provenance, closure35/exact38, AA inventories,
source511/user6/full26groups AND sessions/local+remote refs preserved and verified.
Initial independent review rejected one Important production-pricing-timer claim;
before-report/review/source pins preserved. One offline RED/GREEN amendment6checks/
6bindings corrects only FTRAN/BTRAN timing versus the untimed direct pricing pass.
Three read-only rg guessed-path failures preserved; no Julia/parser/import/compile/
native/numerics/executable candidate/driver/launcher/benchmark/test/production/env/
cache/CI change. Fresh independent gpt-6-astra numerical/work/memory review accepted;
no unresolved findings or unnecessary NEW production work/memory. No new saving:
source-derived target only one cold default FTRAN/BTRAN/pricing reconstruction;
constructor/factor/restored/projection/ordinary/certification remain. A184/B/C and
both old medium attributions reused; no equivalent census/current-master speedup.
AB-bound current STATUS/roadmap preserved ONLY in AC.before-AC; AB initial/read-time
mappings remain AB.before-AB and before-review; all older AA/Z/Y/X/W/V/U/T maps intact.
S5 initialization-reuse/end-to-end gate stays OPEN. Next S6-AP is ONE distinct
SOURCE/EVIDENCE ONLY provenance step for the parent's outstanding user test.mps
certificate/recovery failure, under 2026-10-13-test-mps-failure-provenance.md. No new
numerical allowance, replacement model or inferred backend cause. All old numerical
allowances consumed; all frozen evidence/scripts/rejections remain untouched.
CIoff/HHdisabled/fullsuite/x64cause/bootstrapcacheinit/wholecaps/native-retention/
QGCoutlier and all broader gates unchanged.

## S6-AP provenance and conditional S6-AQ linkage (2026-10-13)

S6-AP SOURCE/EVIDENCE ONLY provenance completed with an unresolved historical
failure. User log88807bytes/817lines SHA22da06e3955a94ffa25fc1f0a0630e933c124aa4a137a25e159b57877030e115
records inconclusive original-objective certificate at255115 and original-LP retry
Harris cutoff failure at aggregate256164/14814.7718616s. User subsequently supplied
test.mps C:\tmp native-reader HH/native320 dual legacy steepest_edge Inf/1000000/
relax_integrality invocation, approximately01:00today2026-10-13/AMD/8BLASthreads.
These are user-reported, not a runtime configuration capture. Commit unknown;
no exact source/default-options/inputhash/witness linkage. Current Windows script
names runtime.mps; current Ctmp/test.mps and referenced capture script absent.
Linux test model hashf60dd96b matches S0/F11 dimensions, not a historical Windows
byte identity. Current-source messages interpreted conditionally; Harris guard
(!exhausted || !eligible_at_cutoff) does not prove all coefficients below cutoff.
No rejecting certificate subpredicate/backend cause/CI reproduction/repair claim.
293.240GiB is cumulative allocation traffic, not peak/live memory or speedup.
Entry15/1947pins, provenance17/21; author original3of4/false literal text gate
PRESERVED plus separate4PASS supplement, full1970 hashes matched. Fresh independent
gpt6astra initial13 checks/FULLnamedpins1977 physical files; user clarification
separate9checks8bindings, preserved initial report/plan/review, final bounded review
accepted/no unresolved C/I/M/no unnecessary NEW production work/memory.
No Julia/model parse/numerics/actualtest/production/env/cache/CI change; masterd02416c.
AC current closure33/exact36 and AP original current continuation hashes map ONLY
AP.before-AP; AP initial report/plan hashes map ONLY AP.before-user-reply when exact
hash matches. All earlier mappings/frozen failures remain unchanged. Next S6-AQ
2026-10-13-test-mps-original-run-linkage.md is conditional on genuinely NEW original
source/runtime/inputhash or saved certificate input; do not repeat answered script
question/search or infer commit from time. No new numerical allowance. All broader
gates/rejections/fullsuite/x64/CIoff/HHdisabled/deferred cleanup omission unchanged.

## S2-B audit-input storage decision — 2026-10-13

S2-B SOURCE/DESIGN ONLY is accepted after one offline review fix pass. It selects
one existing audit-cost prerequisite independently of S6-AQ: an invocation-local
read-only price-audit input wrapper for exact Float32/Float64 nonempty vectors,
with generic/empty vcat fallback. Prediction copies, reconstruction, quality scratch,
residual term order, tolerance and all safeguards remain. No implementation or
Julia/parser/import/numerics occurred. No speedup/default-path saving is claimed.
Initial13 source checks/531 read-time pins and513 src/test/CI master comparisons;
author6 plus4 amendment checks; fresh gpt6astra FULL531/513 then bounded7final/
4intermediate/2original bindings. Important empty-parent resize/alias gap rejected
the initial design; preserved originals/review and one offline4+5-check correction
now enforce nonempty construction, exact scalar dispatch and bit-aware comparisons.
Final review accepts source/design and offline preparation only, no unresolved C/I/M
or unnecessary NEW production work/memory. Candidate costs include at most4empty+
2type constant checks and per-access routing; runtime/cost acceptance remains open.
AP closure40 STATUS/roadmap hashes now map ONLY results/S2-B/*before-S2-B; B initial
report/plan pins map ONLY *.before-review, intermediate fix4 pins to *.after-empty-fix.
All old raw/failed audits/rejections remain untouched; masterd02416c/CIoff/HHdisabled.
Next S2-C: docs/superpowers/plans/2026-10-13-price-audit-values-preparation.md,
OFFLINE candidate/test-source preparation and independent review, no Julia allowance.
S6-AQ still requires new original-run evidence; that wait does not block this step.
Reports S2-PRICE-AUDIT-STORAGE.md / S2-PRICE-AUDIT-STORAGE-REVIEW.md, results/S2-B.

## S2-C offline price-audit candidate — 2026-10-13

S2-C OFFLINE preparation accepted: separate source candidate and test text only,
NO Julia query/parser/import/compile/numerics. Exact whole-source inverse changes
only the two-owner read-only adapter/factory and one vcat assignment. Empty/mixed/
union/other storage materializes; exact Float32/Float64 nonempty parents borrow,
with inner domain checks and both dataids. All arithmetic/safeguards unchanged.
Thirty direct quality pairs (60 entries),20 alias rejection entries and three
byte-identical integration testsets are UNEXECUTED; integration has16 additional
explicit quality entries plus setup/audit/pivot work, not a complete backend cap.
Initial21 checks/535 fresh hashes/513 actual src-test-CI comparisons; author6/five
bindings; fresh gpt-6-astra FULL535/513/B24 and24 review checks/bindings, no unresolved
Critical/Important/Minor and no unnecessary NEW production work/memory. No speedup,
allocation/dispatch/alias/runtime acceptance. No production/test/env/CI/master edit.
B closure24 STATUS/roadmap map ONLY results/S2-C/*before-S2-C; all older mappings
and frozen evidence remain unchanged. Actual masterd02416c, HHdisabled, CIoff and
all prior rejections/broader gates open. No numerical allowance consumed or granted.
Next S2-D: docs/superpowers/plans/2026-10-13-price-audit-values-admission.md,
OFFLINE concrete admission preparation/review only, then separate PASS closure/
exact complete staged blobs/failfast publication. S6-AQ remains separately conditional.
Reports S2-PRICE-AUDIT-VALUES-PREPARATION.md / -REVIEW.md, results/S2-C.
All accepted C scripts/candidates/checks/review/pins FROZEN; NEVER RERUN/rewrite.

## S2-D offline price-audit admission — 2026-10-13

S2-D OFFLINE admission preparation accepted; no Julia query/parser/import/compile,
launcher/guard/numerical execution or actualsrc/test/env/CI change. Ordinary73-file
source overlay changes only exactCcandidate primal_updates; one original reference
function has a byte-exact inverse with four qualifications. Eight fixedFloat32/64
sparse/dense fixtures,655 prospective assertions(90/40/416/34/16/31/28),30directpairs/
60qualitycalls+20aliasrejections. Integration11setups7explicitrecomputes10audits
4iterations16qualitycalls+fourconditionalprivateaudits, NOTcompletebackendbudget.
Cost8setups192windows(64warm128measured)3072wholeaudits1536perside,4warm8measured
alternatingpairs/fixture; freshscratchinside, alltimes/events/bytes/output/compile0
required. No runtime/loading/dispatch/cost/speedup/retention acceptance.

Initial780pins/source16/author6/synthetic25 preserved. IndependentreviewREJECTED
TWOImportant:755aggregate versus655 childsum, and Pythonassert admission gates
removedbyoptimization. Separatevariants fix5PASS +32newsynthchecks, author5/full801;
freshgpt6astra FULL801+original780/final22checks48bindings accepted, no unresolved
Critical/Important/Minor, no unnecessary NEWproductionworkmemory. Originalreport
binding in initialauthor/reviewer maps ONLY D/report.before-review. Both initial
errors and all original PASS records/rejectedreview preserved, no retroactivepass.
Canonical driver-reviewed.jl/common_reviewed.py/launcher-reviewed.py/audit-reviewed.py,
admission-reviewed.md/required-paths-reviewed.json/admission-pins-reviewed.json.
Originalclosure.py is an UNEXECUTED schema draft; closure-final.py uses the actual
review unresolved_findings field. All frozen B/C artifacts remain unchanged.

Cfinalclosure35 STATUS/roadmap map ONLY D/*before-S2-D; Cinitialclosure oldroadmap
still maps ONLY C/roadmap.md.before-whitespace, other older mappings unchanged.
Next S2-E docs/superpowers/plans/2026-10-13-price-audit-values-qualification.md is
CONDITIONAL on explicit human allowance for ONE180second guarded process and fresh
immutable numerical-admission review. No allowance/launchpins exists. Do not treat
this offline acceptance or automation tick as authorization; no repeated audits or
notifications while this condition is unchanged. S6-AQ remains independently
conditional, all old rejections/HHdisabled/CIoff/fullsuite/broader gates unchanged.
Reports S2-PRICE-AUDIT-ADMISSION-PREPARATION.md / -REVIEW.md, results/S2-D.

## S2-E price-audit qualification — 2026-10-13

Human explicitly authorized ONE guarded180second attempt after S2-D. New entry16
checks/full801+780/final22bindings48/closure24bindings127/publication6/exact129;
independent gpt6astra numerical admission35checks830bindings, exact826launchpins,
seal review8checks and separate freshhost7 accepted before launch. Same frozenD
command/stage/output paths identify this new logicalE attempt, not an old rerun.

ONEcandidateprocess completed655/655(90/40/416/34/16/31/28),exit0/admittedaudit21PASS.
Eightfixtures192windows64warm128measured/3072wholeaudits1536perside; alloutputsTRUE,
all128measuredcompile/recompile0 and inwindowGC0. Lowerbytes/events in every measured
pair but mixed time: pairedmedians Float32 sparse32/dense32/sparse128/dense128
1.012887/1.116662/0.898099/1.073180; Float64 0.990180/1.035240/0.932851/1.120635.
All fourdensemediansslower; smallsparseneutral, sparse128locallyfaster. No universal
or endtoendspeedup, no productionpromotion/tuning/retry. Outliers preserved/causes
unknown; zero-dualfixtures/singleprocess/shortwindows limit generality.

Original supplementalpostcheck12/14/exit1/TWOfalsecountgates preserved:15rawportable
files, not16(10Julia+5process/pins/resources/log). Separate6PASSsupplement verifies
all15exactbytes/hashes; admittedaudit and numerics NOT rerun. Admission prose entry
11bindings corrected ONLY separate sealreview to10; boundreview unchanged. Sixty
resourcesamplesminRAM21608940KiB/swap0; terminal22471500KiB/swap0, inclusive60.034391631s
NOTbenchmark. Runner128482/start6285461 and child128483/start6285508, same boot;
fullold26+bothnewgroups ANDsessions absent/noJulia. Ordinaryexistingloader NOT
cache/importclosureproof; sourceentrybudget NOTcompletePREforward/backendwork.

Exact frozenCcandidate removesoneconcat/addsconstantownerchecks+peraccessrouting;
no newscan/solve/cache/precision/safeguardchange, freshscratchinside. Actualproduction
work/memory unchanged; candidate extraaccesscost is NOTacceptedgeneralpromotion.
Fresh independent numerical/work/memory review accepted, no unresolved findings.
Dclosure127 and826launch/admissionreview currentSTATUSroadmap now map ONLY E/*before-S2-E;
Dinitialauthor ANDinitialreviewerreport map ONLY D/report.before-review; C35mapsD
before-S2-D, older mappings unchanged. AlloldD/B/Cscripts/pins/reviews/failedrecords
and newEraw/admission/launcher/auditor/results FROZEN NEVER RERUN or rewrite.

Allowance CONSUMED. Exactcandidate notpromoted; another numerical attempt or source
variant needs its own concrete accepted plan and new allowance. No nextlaunch or
productionintegration authorized here. Broaderplan remainsOPEN; S6-AQ independently
requires genuinely neworiginalevidence, no repeatedsearch/question. HHdisabled/CIoff,
masterd02416c/allolderrejections/fullsuite/x64 remainunchanged. Reports
S2-PRICE-AUDIT-VALUES-QUALIFICATION.md / -REVIEW.md, results/S2-E.

## S3-F ordinary value-update support contract — 2026-10-13

Source/design only, after the human explicitly requested continuation of the
original plan. This is the original S3 value-update item, independent of the
stopped DSE mixed-route qualification. Twelve source gates and 17 fresh hashes;
source/test/CI identical to master d02416c. No Julia, parser/import/compile,
numerics, new LP, production candidate or actual test change.

General support-only omission is not admitted: update_duals! repairs existing
cost violations even on a zero tableau row (existing tests read, not rerun).
Floating update_primals! can change signed zero through a zero product; this is
an analytic scalar example, not a new runtime/trajectory observation. Existing
support access can rebuild O(m) or compact O(s), and matching-cache admission
checks matrix identity plus six buffer owners before up to six lookup checks.
The initial undercounted description is preserved in report.before-review;
a separate five-check amendment corrects it. No new production work/memory.

Next concrete authorized work: S3-G source/design decision in
`docs/superpowers/plans/2026-10-13-rational-primal-support-admission.md`.
Exactly Rational{BigInt} primal updates are only a prospective scope: establish
scalar ownership/exception semantics, alias/order restrictions and inexpensive
read-only support admission, or reject this consumer route. No numerical
allowance or candidate implementation follows from F. Do not wait for S6-AQ to
perform this independent source-only step, and do not repeat F's analysis.

S2-E final closure/publication current STATUS/roadmap hashes map ONLY to
results/S3-F/STATUS.md.before-S3-F and roadmap.md.before-S3-F. Older E-before-D,
D/B/C and all prior mappings remain unchanged. F scripts/checks/raw/review are
single-use frozen evidence after publication; preserve the initial review
finding and correction. Separate independent review and closure/publication
records accompany this milestone. S2-E allowance remains consumed, no tuning or
promotion; S6-AQ still requires new original evidence; all stopped routes,
HH-disabled, CI-off, fullsuite/x64 and broader open gates remain unchanged.

Reports: S3-VALUE-UPDATE-SUPPORT-CONTRACT.md and its REVIEW; results/S3-F.

## S3-G rational primal support admission — 2026-10-13

SOURCE/DESIGN ONLY decision: support-only omission for Rational{BigInt} is NOT
ADMITTED under the existing ownership contract. Stop this consumer route, with
no candidate or next equivalent inventory. Installed Base generated arithmetic
creates fresh numerator/denominator BigInts even when subtracting zero; an
omitted write retains the old owners. Existing support metadata cannot certify
that retaining them is unobservable. Source-derived identity discriminator is
UNEXECUTED; no runtime failure, general impossibility or solver defect claimed.

Fourteen source gates/eighteen read-time hashes include installed gmp.jl and
rational.jl; no retroactive runtime binding. Recompute assigns rational scalar
references and staged copyto! copies elements, not recursive BigInt ownership.
Five review classes have explicit dense-fallback/rejection and prospective
oracles. All original dense ordering, entering addition and exceptions remain.
Source constructor counts are not allocation measurements or native budgets.
No new production work/memory; no Julia/import/compile/numerical experiment,
new LP, candidate/driver/launcher, actual src/test/env/CI or master change.

F current STATUS/roadmap bindings in closure/publication/final review map ONLY
G/STATUS.md.before-S3-G and G/roadmap.md.before-S3-G. Earlier F snapshots still
resolve S2-E current bindings, all older maps and failures unchanged. G's
original plan stays frozen; this decision and independent review complete it.
G artifacts freeze after publication; never rerun collectors/publisher/reviews.

No further equivalent sparse-value ownership inventory is authorized. A genuinely
different concrete permitted step or explicit change of this boundary is needed
before continuing this route. This is not completion of broader S3/S2/S4/S5/S6.
S2-E allowance remains consumed; no tuning/promotion. S6-AQ independently needs
new original evidence; do not repeat searches/questions. All stopped directions,
HH-disabled, CI-off and broader/fullsuite/x64 gates remain unchanged.

Reports: S3-RATIONAL-PRIMAL-SUPPORT-ADMISSION.md and REVIEW; results/S3-G.

## S4-Z offline Markowitz retention admission — 2026-10-13

S4-Y23ac555 accepted an unexecuted diagnostic, not an optimization. S4-Z prepares
one exact guarded attempt with separate launcher/auditor/pins and independent
review. No Julia or numerical permission in this preparation. The next conditional
plan is [Markowitz retention qualification](2026-10-13-markowitz-retention-qualification.md).
Require new explicit human permission, fresh host/manifest and numerical admission
before any one-attempt reservation. Automation remains paused. Y final current
continuation hashes map only Z before-S4-Z copies, older mappings unchanged.

## S4-AA scoped retention result and updated human authorization — 2026-10-13

The single admitted S4-Z attempt completed66/66 predicates,6auditgates8postchecks.
Workspace graph94888B and128 dictionary/maxima owners persisted through both
128→8→8→128cases; sparse active lengths shrink8, dense bypass128. This is a scoped
current-retention observation, not a leak or accepted optimization. No benchmark,
complete backend/import budget or native memory release proof. See
[S4-AA report](../../../diagnostics/simplex-core-architecture/S4-MARKOWITZ-RETENTION-QUALIFICATION.md).

The human explicitly approved this attempt and future short numerical attempts
without asking again, while prohibiting multi-hour runs. New concrete technical
admission/resource caps remain mandatory; frozen consumed attempts and stopped
routes stay closed. Automation remains paused. Z final continuation bindings map
only AA before-S4-AA copies; older mappings unchanged. Broader plan remains open.
