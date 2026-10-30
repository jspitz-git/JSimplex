# Dual Recovery Devex Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native inline implementation. Steps use checkbox (`- [ ]`) syntax for tracking. Request fresh independent reviews at the task boundaries; do not delegate implementation without explicit authorization.

**Goal:** Allow a verified private Float32/Float64 dual-recovery trial to decline inconclusive steepest-edge geometry and finish with the existing Devex rule.

**Architecture:** Preserve one strict refinement kernel and expose opt-in fixed-size outcome metadata. An explicit actual-algorithm argument enables only the dual transactional-retry route; private mode preparation and a cold trial result carry the transition to existing recovery publication without adding callbacks.

**Tech Stack:** Julia, SparseArrays/LinearAlgebra, existing JSimplex factor interfaces, ordinary Test; no new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-30-dual-recovery-devex-fallback-design.md`.

## Global Constraints

- The current deliverable is PLAN ONLY: no candidate, Julia query/parser/import/compile, test execution or numerical launch now. Tasks1–3 are subsequent isolated source/test preparation; runtime steps occur only after Task4 concrete admission.
- Preserve all solve/pivot/primal/dual/certificate tolerances and existing policies, arithmetic order, cleanup behavior, safeguard/fallback limits, callback ordering and original public return types. No new precision or retry allowance.
- Actual Float32/Float64 **dual transactional retry** only. Unknown/primal/direct legacy repair/restore, independent feasibility-driver repair, precision transfer, other types and ordinary refactorization remain strict by default.
- Production baseline is master `c0fa748ffa61ccb7c1caaf248c40324f60bc737b`; source decision `028b3efc8a60c880ddb863fb08537d0c8cc1ece1`. Rebase/review a changed baseline explicitly before execution, without rerunning frozen artifacts.
- No production method overwrite, full-module clone, custom Test recorder, benchmark LP replacement, old-driver rerun or modification of frozen evidence. CI remains off; HH reuse remains disabled.
- One Julia at a time; Julia/BLAS1, gcthreads1,0, heap2GiB, VM8GiB, available RAM>=6GiB, swap<=1GiB, compiled-modules=existing. Fresh boot/start_ticks/command and all prior groups AND sessions/noJulia/refs before any launch. New exact manifest and independent concrete admission required.

## Review Focus

1. Finite final SolveQuality can hide nonfinite intermediate work: Task1 must retain the underlying cause, including a discarded nonfinite cleanup proposal.
2. A late failed row leaves a valid DSE prefix: Task2 must reset the complete framework or reject, never reinterpret the prefix.
3. Temporary Dantzig and stale algorithm state: Tasks2–3 must distinguish selection mode, maintained mode and actual caller route.
4. Stop/observer/logger exceptions before publication: Task3 must preserve live solver-owned state and original exception identity while retaining consumed work.
5. Valid reconstruction does not prove a fast or correct new trajectory: Task4 must exercise actual Devex update/pivot/certification and report incomplete coverage and time uncertainty.

## File map and task boundary

- Modify `src/simplex_numerics.jl`: private outcome cause/type and result adapters, leaving SolveQuality unchanged.
- Modify `src/simplex_recovery.jl`: shared refinement result mode, weight-rebuild outcome, private Devex preparation, cold trial result and publication support.
- Modify `src/simplex_pivot.jl`: pass the actual retry algorithm to recovery.
- Create `test/refinement_outcome_tests.jl`, `test/recovery_devex_fallback_tests.jl`; add their includes beside numerical/basis-recovery tests in `test/runtests.jl`.
- Reuse but do not broaden `simplex_pricing.jl` transitions. No changes to `simplex_driver.jl`, `simplex_precision.jl`, workspace/scratch field layouts, scoring, ratio or certificates in this plan.

Tasks1–3 prepare separate candidate/test text under a new diagnostic preparation directory, inverse-bound to the baseline. They do not edit actual src/test until later integration. Each ends with fresh independent numerical/work-memory source review. Do not mark runtime steps passed by static inspection.

### Task 1: Preserve exact refinement refusal provenance

**Interfaces:**
- Define a private UInt8 enum `_RefinementCause`: reliable, nonfinite_initial_quality, nonfinite_quality, nonfinite_correction, nonfinite_trial, nonfinite_trial_quality, stopped, unchanged, not_improved, limit, not_observed. The not_observed value means detailed outcome metadata was not requested (including skipped refinement or a legacy refinement that did run); it is not a statement about numerical work and is not a new numerical return path. Enumerator constants use the `_refine_` prefix (for example `_refine_not_improved`), avoiding generic module names.
- Define `_BasisRefinementOutcome{T}` with `quality::SolveQuality{T}`, `cause::_RefinementCause`, `invalid_seen::Bool`.
- Existing `refine_basis_solve!(...;transposed=false)::SolveQuality{T}` stays unchanged externally. New `_refine_basis_solve_outcome!(destination,ws,rhs,policy,stop;transposed=false)` returns the outcome. Both invoke a single numeric kernel specialized by `Val(false)`/`Val(true)`; false returns quality directly and constructs no outcome/sink.

- [ ] Write ordinary testsets **Refinement outcome matches legacy quality** and **Finite result retains hidden refusal**. Use the same real small sparse/dense factor and identical owned workspaces for both APIs. Compare every quality field, destination bits, RHS, policy, scratch ownership, stop/solve/event counts. Cover initial reliable/unreliable, unchanged correction, no improvement, zero/exhausted configured limit, stop before correction and before adoption, each nonfinite branch and thrown sentinel. Float32/64 focus; small BigFloat/Rational smoke tests pin unchanged old API.
- [ ] Implement cause reporting at existing return sites without repeating arithmetic, quality evaluation, array scans or stop calls. Preserve short-circuit order. Keep `invalid_seen` sticky when a nonfinite cleaned proposal is discarded and a finite previous quality later returns. Its scope is nonfinite correction/trial/quality proposals observed by this kernel, not internal residual-evaluation intermediates safely handled by the unchanged quality fallback. Exceptions propagate without becoming outcomes. Preserve `_record_refactor_quality!` on the actual quality exactly once.
- [ ] Define source-bound RED assertions against the original API/body and the later GREEN assertions; do not run Julia during preparation. Review the numerical inverse and explicitly count any extra scalar/boxing work. Any added normal-path array pass, solve, Ref allocation or persistent field is a rejection.

**Deliverable:** independently reviewed isolated common-kernel candidate plus outcome tests. This task alone changes no pricing behavior.

### Task 2: Classify a failed weight row and prepare owned Devex state

**Interfaces:**
- Define a private UInt8 `_RecoveryWeightReason` enum (constants prefixed `_weight_`): complete, not_needed, finite_inconclusive, stopped, nonfinite_attempt, invalid_norm, ineligible. `_RecoveryWeightResult`: fixed-size `(ok::Bool, fallback_ready::Bool, failed_row::Int, reason::_RecoveryWeightReason, refinement_cause::_RefinementCause)`; no vector or mutable ledger. The two causes distinguish a bad norm from the actual refinement terminal cause; not_observed identifies absent detailed refinement metadata, whether a legacy numerical call ran or was skipped. `ok=true` means complete DSE rebuild or no DSE needed. Eligible inconclusiveness returns `ok=false,fallback_ready=true`; it never prepares or publishes Devex itself. All other refusals have both flags false.
- `_rebuild_recovery_weights_result!(trial,stop;algorithm::Symbol=:unspecified)` retains original row loop/refinement/norm/floor behavior, using Task1 detail only in eligible new scope. Existing `_rebuild_recovery_weights!(trial,stop)::Bool` remains a strict wrapper using unspecified scope; precision transfer is untouched.
- `_prepare_recovery_devex!(trial)::Nothing` is a **private state-only** operation: no new observer/logger/event emission. Caller must establish owned recovery trial, core validity and eligible mode first.

- [ ] Add testsets **Recovery weight failure classification**, **Partial DSE prefix is discarded**, **Fixed auto and temporary pricing transitions**, **Unknown route and unsafe work stay strict**. Declare outputs only on new private test-factor types after forwarding the genuine solve; record fixed pre-call counts. Failed row1 and a later row must stop the loop, with no row k+1 solve. A valid rebuild stays DSE with original weights/floor. Nonfinite/zero/overflow norm, callback stop/throw, unknown causes, stale algorithm and nonfloat types never become fallback-ready.
- [ ] Permit fallback-ready only for algorithm=:dual, T exactly Float32/64, maintained weight mode=:steepest_edge, absent or actual-dual pricing state, finite returned quality, refinement_cause in {unchanged,not_improved,limit}, and invalid_seen=false. Before returning fallback_ready, evaluate the existing `dot(direction,direction)` and require its original finite/strictly-positive norm guard. Zero/underflowed or overflowed norm returns reason=invalid_norm with fallback_ready=false, even if quality is finite. For real Float32/64 self-dot with unchanged IEEE/no-fastmath semantics this also rejects NaN/Inf components; do not add a redundant standalone all(isfinite,direction) scan. This dot is new only on the previously early-returning finite-inconclusive branch; reliable rows retain their original single dot. Do not infer eligibility from options or final finite quality alone. The Task3 constructor performs one post-classification stop before fallback validation/preparation; a true/throw aborts, and the classifier adds no duplicate stop. Exceptions from original row/refinement checks propagate. A reliable result retains all original norm checks and does not trigger fallback.
- [ ] In the Task3 constructor, before accepting fallback, rerun `_finite_workspace(trial)` and `_recomputed_basis_reliable(trial)` after the weight attempt, while scratch.rho still holds recomputed basic-cost prices. This catches invalid core changes during existing correction callbacks. No additional solve/factor is allowed; reject if the precondition on rho/core ownership cannot be source-proved. No general guarantee against callbacks deliberately mutating live memory is claimed.
- [ ] Reset all weights to one and Devex references to the new basis, not just the failed/prefix rows. With pricing state, reuse `_unreliable_pricing!` plus reset/framework primitives; cancel temporary trials, set active/return Devex, restore framework validity and update the existing counters once. Fixed nonauto mode sets dual_devex_fallback; preserve options and unrelated flags. Retire owned pool indices. Do not call `_reject_auto_weight!`/`_switch_dual_pricing_to_devex!` directly here because they emit callbacks/logs. `recovery_active=true` must suppress the reset callback as in existing source.
- [ ] Review all mode fields, counter changes and O(N) resets against current fixed/auto semantics. Keep numerical checks and complete failed-result evidence; do not test the declared test-factor corruption as native backend accuracy.

**Deliverable:** isolated weight-result/state-preparation candidate and differential controls; no live publication yet.

### Task 3: Enable only actual dual retry and publish the mode transactionally

**Interfaces:**
- Add `algorithm::Symbol=:unspecified` to repair_basis!, its private repair helper and restore_checkpoint!, forwarding the same value through repair's checkpoint-restore fallback. Validate {unspecified,primal,dual}; old calls remain unspecified/strict.
- `_retry_simplex_step!` passes its actual `algorithm`; that is the only existing external production call site newly opting in. Leave the feasibility-driver's repair call and precision-transfer helper unchanged.
- Define `_RecoveryTrialResult{W}` with `workspace::W`, `devex_fallback::Bool`, `failed_weight_row::Int`.
- `_recovery_trial_with_pricing(ws,c,stop;algorithm=:unspecified,build_factor=_build_recovery_factor)` is the common cold constructor returning result-or-nothing. Retain `_recovery_trial(ws,c,stop)` as a strict compatibility wrapper returning workspace-or-nothing. `_build_recovery_factor(B,options)` defaults to existing `_basis_factorization` and runs inside the existing single timing/count/finally boundary.
- Add `_publish_recovery!(ws,result::_RecoveryTrialResult,reason,stop)` forwarding metadata to the original workspace publisher with default keywords `weight_fallback=false,failed_weight_row=0`.

- [ ] Add testsets **Explicit dual retry scope**, **Cancelled or throwing fallback publication**, **Fallback publishes mode with the basis**, **Legacy and precision routes remain strict**. Default/unspecified/primal/feasibility-driver/precision-transfer routes must retain old outcomes. Ensure repair's restore fallback preserves the explicit route rather than guessing options/pricing.algorithm.
- [ ] Move the existing constructor body into the common cold path without duplicating factorization/recompute or changing their ordering/counts. Use the Task2 classifier after the existing core checks. For complete/skip results retain the original post-rebuild stop and finish normally. For fallback-ready results perform one corresponding stop, then core revalidation and `_prepare_recovery_devex!`, then return a marked result; other refusals return nothing. Do not call stop a second time merely to finish metadata. Incomplete DSE rows return reason=finite_inconclusive; invalid_norm/stopped/nonfinite_attempt/ineligible results are never reconsidered as fallback. Successful fallback result remains private until `_publish_recovery!`; no partial mode change reaches live state on refusal or stop.
- [ ] For deterministic tests, the private cold `build_factor` seam may construct exactly one genuine new factor then wrap it in a declared test factor of the live workspace's **same concrete F type**. No Any field, backend switch or production factory method overwrite. Public APIs do not expose/forward this seam. Use it to test the real constructor, prechecks, failed weight, reset and publisher together; public normal-path tests exercise ordinary real factories and algorithm forwarding. Preserve the original attempted-factor charge even if the factory throws.
- [ ] Keep existing recovery observer order/call count and workspace payload. Existing :repair/:restore_checkpoint/:checkpoint observers see the pending Devex mode. Introduce no new logger or observer invocation. Only after state/factor adoption, record existing :pricing_weight_rejected and :pricing_devex using callback-free `_record_recovery!`, once each; retain existing reset/recovery/checkpoint records. These new records are commit-only and are not new observer notifications. If observer delivery requires a different policy, stop at design review rather than silently adding callbacks.
- [ ] Assert stop/throw at failed-row handling, reset boundary, existing recovery observers and final prepublication stop keeps live solver-owned basis/factor/values/weights/reference/mode/pool as before. Match original sentinel identity/wrapping. Preserve consumed factor/solve work and allowed original diagnostics; do not claim full rollback or observer neutrality. An observer may inspect the proposed state; cancellation must not publish it.

**Deliverable:** complete isolated candidate and lifecycle tests, with fresh source review. No production promotion is implied.

### Task 4: Ordinary guarded RED/GREEN, cost qualification and integration gate

- [ ] Prepare a small ordinary test entry using `using JSimplex,Test` and `include(...)`, with no custom recorder/Test stack. Bind candidate source overlay, extracted tests and exact original reference. Seal concrete fixtures/counts/commands/guards and obtain fresh independent numerical/work-memory admission before Julia. Existing frozen drivers, failed expectations and raw outputs are never reused as launches.
- [ ] Use at most four new sequential guarded processes for initial qualification: original RED, candidate GREEN, normal-path reference cost and candidate cost. All share one1800s total ceiling and one Julia at a time; reserve identities/output directories and freshly close each process before the next. Concrete admission fixes exact assertion/call budgets after candidate preparation; do not invent aggregate counts in this plan. Time-only failure follows the user's longer-limit preference via a separately frozen reviewed continuation, never an unrecorded retry; other failures stop.
- [ ] RED must exercise the existing strict weight boundary on a declared finite-unreliable test-factor result and preserve its numerical refusal, while failing the new recovery-success expectation. Candidate GREEN must show that the old strict helper still refuses and only the explicit dual-recovery entry succeeds via Devex. Missing outcome-type/API assertions may supplement this behavioral RED, but an undefined binding, world-age or environment error is not an accepted RED. Checks must specifically detect missing cause provenance and missing finite-unreliable-to-Devex transition. GREEN runs new tests plus unchanged numerical/recovery/dual-weight/adaptive-pricing/partial-pricing regressions. Suggested ordinary entry after admitted load: `using JSimplex,Test; include("test/refinement_outcome_tests.jl"); include("test/recovery_devex_fallback_tests.jl")`; include existing basis_recovery_tests, dual_weight_validation_tests, adaptive_pricing_tests before adaptive_pricing_lifecycle_tests, and partial_pricing_edge_tests. The actual sealed entry uses only ordinary Test and exact required helpers.
- [ ] Verify one actual post-fallback Devex update/pivot on a known small LP and independent original primal/optimality certificate. Test a genuinely invalid basis/core/row remains rejected and an inaccurate selected row cannot pass by changing pricing. Keep original tiny-component and all old allocation-test expectations unchanged; no new percentage-based allocation tolerance or waiver.
- [ ] Qualify unchanged normal API on Float32/64 sparse/dense fixed64-dimensional reliable and finite-unreliable cases: three warm and seven recorded calls per case, same owned fixture preparation on reference/candidate, compile/recompile recorded separately. Record whole-function time, bytes/events, array-owner/work/solve counts and outputs. Separate processes are not temporal interleaving; report timing uncertainty and do not infer universal speedup. Reject any extra normal-path scan/solve/retained array or systematic outcome/sink allocation in the default API. No full-module clone or method overwrite to create the reference.
- [ ] Separately record fallback preparation/revalidation/reset costs and actual avoided weight rows on the small failure fixture. Label the changed pricing trajectory. Record complete preparation and retained scratch; a shorter incomplete DSE loop is not a successful DSE benchmark. Saved large runtime witnesses may be inspected offline; any additional large numerical comparison needs its own concrete plan/admission and is not part of these four processes.
- [ ] Obtain independent result review and preserve any failures. Only a passing, reviewed candidate may proceed to a separate production commit/integration and master-verification plan. Push to master follows standing authorization and verification, not this unchecked plan alone. Keep CI off.

## Work and memory acceptance ledger

| Frequency | Intended additional work/storage | Required check |
|---|---|---|
| Existing normal refinement | Compile-time return-mode plumbing only; no extra vector pass, solve, mutable sink or persistent field | Same outputs/guards/solve counts/owners; warmed whole-function allocation/time comparison |
| Eligible recovery weight row | Fixed-size outcome and scalar cause classification; original numerical work unchanged | Report any compiler boxing; no O(m) status array or repeated quality just to obtain status |
| One finite-unreliable fallback | One self-dot reduction plus original finite-positive scalar guard; original finite/core revalidation including O(N+nnzA) RHS construction and O(N+m+nnzB) basis validation/assembly; two original quality checks; O(N+m) reset/pool retirement | All consumed work retained; existing scratch/revalidation allocations measured; zero new factorization/basis solve |
| Cold constructor/publication | Fixed-size result metadata, one default factory call, two commit-only diagnostic records | Same concrete factor F and private ownership; no new callbacks/logs; metadata dies after publication/discard |
| Later iterations | Existing Devex maintenance instead of DSE; changed trajectory may add pivots/refactors | Whole public correctness and honest uncertainty; no end-to-end speed claim from avoided weight rows alone |

N=m+n. Current k-row rebuild already pays O(k*(N+m+nnzB)) validation/assembly plus solves/quality/dots; the full m-row contribution is O(mN+m^2+m*nnzB). General correction ceiling is k*policy.max_refinements, default3k. Never describe cached basis storage as zero-work validation.

## Self-review and current status

- [ ] Before candidate work, confirm every proposed interface and scope gate against current source and accepted spec; resolve independent review findings while preserving the reviewed previous text.
- [ ] Tasks1–3: isolated code/tests prepared and reviewed, not executed.
- [ ] Task4: concrete admission/tests/costs/results review.
- [ ] Separate production/master verification.

At plan publication all implementation/runtime checkboxes remain unchecked. No production or numerical admission exists here.

## Preserved plan-review correction

The initial review found that finite direction/quality alone did not enforce the promised zero/overflow norm exclusions. The exact earlier design/plan are preserved in diagnostics/dual-recovery-devex-plan/2026-10-30/design.before-review.md and plan.before-review.md. Eligibility now executes the original self-dot finite-positive guard on the finite-inconclusive branch, and both ledgers charge that O(m) reduction instead of a redundant standalone finite scan. Separate weight/refinement reason enums make this refusal explicit. Initial review and document-check bindings to the old design/plan paths map ONLY to those exact preserved before-review bytes; current documents are separately final-review/closure bound. No Julia or candidate changed.
