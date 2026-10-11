# S2-A: independently audited primal bound-flip prototype

> **For agentic workers:** Use superpowers:executing-plans sequentially.

**Status:** Control census1000, work RED/GREEN12 and candidate matrix960 accepted.
Private fault/scope qualification active; no production/default change.

**Goal:** Test whether an unchanged-basis bound flip can avoid reconstructing
both primal values and unchanged prices when an independently certified predicted
point is cheaper than reconstruction. Preserve all native legacy safeguards.
This is the first bounded S2 chunk, not the pivot error-controller design.

**Parent:** 2026-10-11-simplex-core-architecture.md, S2; design spec and
S2-INVENTORY-NOTES.md remain authoritative. Communicate Czech, repository English.

## Constraints and prerequisites

S0-L medium-dual-counted-1 has completed with an accepted audit. Inspect the
latest S2 process report and separately confirm host runner/child/driver absence
before each next numerical test or pinned-source edit. Keep every pinned file
unchanged during a run; raw attempts and source snapshots remain preserved.
One guarded Julia/BLAS thread, heap hint2G,8GiB VM,6GiB available RAM,1GiB swap;
exclude big/largo/AnyMOD and aliases. Preserve every attempt and local environment.

The existing incremental flags bypass native direction-price, row and point
protections. Do not enable those flags. A local update-roundoff sum is not a
forward-error bound for an ill-conditioned direction solve. This prototype
therefore uses an independent full point certificate on every proposed skipped
reconstruction; no heuristic accumulation interval or weaker tolerance.

## Selected scope and alternatives

Start with bound flips only. A flip leaves the basis, factors, objective costs,
reduced costs and selected direction unchanged. The legacy direction-price and
step/bound checks still execute before mutation. Primal prediction uses the
existing apply_primal_flip! kernel, which validates every predicted value before
writing. Pivot operations and their complete reconstruction path remain intact.

An incremental pivot would additionally require price/objective-dual ownership,
condition-sensitive error control and the native point-retention/row safeguards.
That is a separate later design. Existing scratch.rho cannot be treated as a
persistent objective dual after it has been reused as a pivot/weight row.

Retaining all reconstructions is the control. Enabling incremental_primal or
incremental_primal_pivots is rejected as a comparison because it changes guards.
A fixed every20 audit is rejected as an unexplained certificate gap. If the full
point certificate costs more than the avoided work, reject this prototype rather
than weaken its check or raise precision to improve a timing comparison.

## Private experimental seam

Keep production sources unchanged during qualification. In a private diagnostic
module loaded from a frozen source snapshot, clone the selected native
primal optimizer/iteration/retry functions with an explicit context parameter.
Transform the flip branch, final reconstruction choice and dirty endpoint handling.
Assert exact expected AST/source matches and fail closed if layout differs.
The diagnostic module owns its options, policy, clock and observers. Do not add
a public switch, modify the default policy, or use a process-global workspace map.
A later production subplan is required if the private experiment passes.

Eligibility is deliberately narrow: Float32/Float64, native legacy primal kernel,
nonstaged workspace, finite nonzero signed change, explicit finite opposite bound,
no externally supplied stop callback/observer/logger with workspace access, and
no recovery/precision/incremental flags. All excluded cases use the original
source branch. The model, bounds and objective are owned and unchanged during
the operation. The default other-precision paths remain byte-identical.

Preserve selection, FTRAN and finite validation, _validate_primal_edge!, native
direction-price agreement, ratio/step guards and stop semantics before applying
the flip. The only candidate mutation uses apply_primal_flip! once; do not also
advance the basis generation or change nonbasic state in the original branch.
Leave pricing weights and factor/update history unchanged. Record actual work.

After the normal step count/refactor bookkeeping but before the completion event,
check scheduled refactorization. If required, use the original reconstruct/refactor
path, never bypass it. Otherwise check the predicted point with the existing
_legacy_primal_point_certified at the current problem precision and unchanged
tolerances. This checks finiteness, all stored bounds, original/owned working-model
feasibility and equation consistency, with its existing enclosure/exact fallback.
It is an independent acceptance test of the current point, not an estimate of
forward error or an optimality certificate.

On certificate success, skip only this step's routine recompute!. Reduced costs
are retained because basis/costs are unchanged; no price arithmetic is performed.
On certificate failure, nonfinite/inconclusive result, or internal numerical
exception, reconstruct on the already accepted flipped state using the original
recompute! and native point-recovery path. Preserve the predicted basic point
for recovery without applying the movement twice. Do not reuse
_legacy_primal_point_candidate after apply_primal_flip! if that would predict a
second step. Callback/observer exception provenance must still propagate unchanged.

Completion events occur after an applied step and its certification/reconstruction
attempt. Preserve the original completion even when point recovery returns a
terminal failure: completion records applied work, not a certificate. Deadlines must not expose the basis
state flip with stale values. Preserve mandatory reconstruction at refactorization,
phase/cost/bound/model/precision changes, recovery, apparent optimum/unboundedness
and final certification. Limits/exceptions return without extra reconstruction as
resolved below; they never publish successful solutions. An endpoint after any skipped flip must first recompute
and reprice independently; this is additional private controller state to design
and test, not an existing legacy guarantee. Use one owned dirty flag, set only
by accepted skipped flips and cleared only after successful reconstruction.
Do not confuse a clean flag with a certificate that outlives external mutation.

## Work and memory accounting

Potential saving per accepted skip: one recompute!, its primal FTRAN and objective
BTRAN, nonbasic RHS construction and price reconstruction. Costs depend on m,N,
A nonzeros and update-chain length; do not infer elapsed savings from solve counts.
Added work: prediction-before-write m pass plus m update pass in the existing
flip kernel, full point finite/bound scans, row-activity/enclosure traversal and
possible exact fallback, plus a dirty-flag branch. Existing point buffers are
owned/reused; account for their first allocation and retained dimensions.
A preserved fallback candidate may require one m-sized copy; prefer an existing
owned trial buffer only after proving it is not aliased by the certificate.

Count ordinary flips, eligible flips, certificates, accepted skips, rejection
reasons, recomputations, FTRAN/BTRAN, RHS/pricing matrix visits, recovery and
endpoint reconstruction. Measure scalar/vector work and allocation bytes/events
separately from warm plain elapsed. Detailed validation hashes run outside timing.
Use bounded counters/reason enums; no per-step retained snapshots or global cache.
The observer must own no live workspace after its run.

## Sequential tasks and gates

### A1: resolve design details before RED

- [x] Independently review eligibility, exact injection points, endpoint dirty
  state ownership and certificate/fallback scratch aliasing against source.
- [x] Identify each endpoint that needs reconstruction before declaring optimum
  or unboundedness, and every successful recompute that clears dirty state.
- [x] Specify a concrete private owned context and kernel hook signature before
  implementation; verify no public closure/callback gains trusted ownership.
- [x] Freeze raw baseline, module construction, options/input and guard commands.
  The S0 reference must have released the numerical slot first.

### A2: behavior and work characterization, then RED/GREEN

- [ ] Build deterministic fixtures with an actual nonzero bound flip followed by
  another step, multiple/degenerate flip chains, a scheduled refactor and both
  endpoints. Assert that each fixture executes the intended branch.
- [x] Add a failing work assertion for an eligible independently certified flip:
  the control reconstructs; the candidate should avoid exactly one routine
  reconstruction while retaining required endpoint/refactor reconstruction.
- [ ] Inject finite-but-infeasible predicted points, inconsistent rows, failure
  of native certification, failed reconstruction and deadline/observer exceptions.
  Verify fallback and completion visibility, including no double application.
- [ ] Cover zero/overflow/unsupported precision, staged/external-callback and
  changed cost/bounds cases as conservative original-path fallbacks. Existing
  primal-update and legacy point/direction-price regressions remain mandatory.
- [x] Run RED on the unchanged private control under the serial guard. Implement
  only after its intended failure and host-confirmed process exit. Run GREEN.

### A3: reject or qualify the private experiment

- [x] All five public managers, native/Markowitz where supported, Float32/64;
  other supported precisions explicitly retain original behavior. No experimental
  direct manager promotion. Validate original feasibility, objective and certificate.
- [ ] Separate trace state comparisons where arithmetic is unchanged from changed
  predicted trajectories. On changed trajectories compare valid outcomes and
  independent certificates; never claim fewer iterations as kernel savings.
- [ ] Warm separately; at least three interleaved pairs on representative sparse
  and dense flip histories, including a rejection-heavy case and update chains.
  Count the full certificate and fallback cost, setup/compilation separately.
- [ ] Reuse existing medium/runtime evidence only where it actually covers this
  path. Long phase-II and both cleanup origins remain mandatory before general
  S2 acceptance; avoid rerunning unrelated completed baselines.
- [ ] Independently review work/memory and numerics. If no repeatable net saving,
  preserve the rejection with no production change. If qualified, write a small
  production-integration subplan preserving the same guarded contract; do not
  automatically merge private source rewriting or instrumentation.

The parent S2 controller checkbox stays open: this subplan deliberately resolves
only unchanged-basis flips. Pivot error accounting and broader acceptance remain
separate. No production or elapsed-time improvement is claimed by planning.

## A1 design-review resolution

Concept accepted for private qualification. No merge/default change is implied.
The private seam must include _primal_optimize!, _primal_iteration! and its core,
_legacy_primal_iteration!, _legacy_primal_reject_candidate! and
_primal_iteration_unchecked!: two branch edits alone cannot handle dirty returns.

Use a private `FlipAuditContext{W}` with owner::W, dirty::Bool and fixed scalar
counters, created by `run_flip_experiment!(ws, owned_run_config)` for exactly one
optimizer invocation. The owned run config constructs its own deadline and private
observer, rejects external callbacks/loggers, and sets explicit fixed pricing and
perturb_degenerate=false identically for control and candidate. Eligibility also
excludes auto/adaptive pricing, active perturbations, recovery/precision policies
and model/cost/bound changes during the invocation. Do not infer ownership from
an arbitrary Function or closure. Unsupported configurations invoke the original
optimizer without a context. Public solver callbacks remain untrusted.

Private cloned function signatures take ctx first; their recursive calls pass the
same ctx. Every private entry checks `ctx.owner === ws`; a mismatch is a harness
error, never implicit adoption. Existing numerical helper functions stay unchanged.
The context is local to the invocation; nothing exports it or retains its owner
in a global registry, observer result, task or historical sample. Returning a
terminal result drops the context. Thus retries share dirty state and unrelated
workspaces cannot inherit it. Public full-solver integration is a later subplan;
initial qualification invokes this private optimizer on owned fresh workspaces.

Dirty is set before the completion event only after a successful audited skip.
Clear it only after reconstruction AND successful _finish_legacy_primal_point!
return, not merely after recompute!. Conservative extra endpoint reconstruction
is acceptable if an unchanged helper performed recovery without the context;
count it rather than guessing its resulting certificate state.

On audit rejection after application, copy the already updated basic values to
_pivot_quality_buffers(ws).trial only when fallback is required. Point certificates
use separate primal_point_buffers. Recompute then call the unchanged finish helper,
which already preserves candidate before native correction can overwrite trial.
There is no second movement, basis-state change, generation increment or iteration
increment. Before-application internal failure uses the original flip branch;
after-application failure reconstructs the flipped state. Test an explicit local
applied flag boundary, and never catch a callback/logger exception as numerical
rejection. No successful skip allocates a fallback candidate copy.

At dirty apparent OPTIMAL or UNBOUNDED, preserve current basic values, reconstruct
and finish recovery, then rerun entering selection and ratio computation using
the same remaining budgets. Do not return the pre-refresh decision. Native retry
and optimizer loops must honor this result; an early finite/feasibility failure
on a dirty point likewise reconstructs once when time remains before deciding
whether it is a real numerical failure. No repeated unbounded retry is introduced.

TIME_LIMIT, ITERATION_LIMIT and caller exceptions trigger no reconstruction in
finally and never mask the existing reason/provenance. An applied, independently
certified flip remains a coherent completed step even if a subsequent deadline
ends the run. No OPTIMAL/UNBOUNDED certificate is published from dirty state;
non-success output carries no accepted primal solution. The private context is
then discarded and cannot be used to resume a run. Failed or interrupted point
recovery does not clear dirty or turn into success.

Expanded cost accounting from review: _legacy_primal_point_certified includes
finite scans of primal/reduced-cost/cost and relevant weights, all bound checks,
copying structural primal values and traversing A. Its exact fallback can allocate
m-sized row_slot, BigInt activities and another CSC pass; model and equation
checks can require separate fallback work. Rejection adds these costs to full
reconstruction and recovery. Measure both acceptance and rejection-heavy cases;
no inexpensive-certificate assumption is made.

The explicit signatures/AST whitelist and endpoint state table are independently
accepted. A1 freeze and A2 fixture characterization remain open. The long S0 job
still holds the numerical slot; no RED or implementation has started.

## Concrete private seam and state table for implementation review

Owning diagnostic files to create after this design is accepted:
reproduce/primal_flip_prototype.jl (context/clone construction),
reproduce/primal_flip_contracts.jl (regressions),
reproduce/primal_flip_characterization.jl (control branch census),
reproduce/primal_flip_cost.jl (separate trace/plain cost driver).
Production src remains unchanged throughout private qualification.

Private method map, each retaining the original trailing/keyword arguments:

| Original | Clone signature prefix |
| --- | --- |
| _primal_optimize! | _flip_optimize!(ctx, workspace, stop_requested, ...) |
| _primal_iteration! | _flip_iteration!(ctx, ws, stop_requested, ...) |
| _primal_iteration_core! | _flip_iteration_core!(ctx, ws, stop_requested, ...) |
| _legacy_primal_iteration! | _flip_legacy_iteration!(ctx, workspace, stop_requested, ...) |
| _legacy_primal_reject_candidate! | _flip_reject_candidate!(ctx, workspace, entering, ...) |
| _primal_iteration_unchecked! | _flip_iteration_unchecked!(ctx, workspace, stop_requested, ...) |

Build a parsed-AST whitelist of these six definitions from the frozen source.
Rename only those definitions/calls and prepend the lexical ctx argument. Keep
all numeric/helper bodies and the original methods available for control/fallback.
Assert exactly one source definition per expected explicit method (account for
Julia default-argument expansion at evaluation, not source matching), expected
flip/endpoint/reconstruction anchors and zero unresolved calls to the old six
names inside the private clones. Never broadly text-replace numerical expressions.
Record source/rewritten hashes for each attempt; any mismatch fails before Julia
numerical work. Context owner checks are constant-cost, no vector equality scan.

| Current state / event | Action | Resulting dirty state |
| --- | --- | --- |
| clean or dirty / eligible nonzero flip validates before-write | Apply existing kernel once; normal bookkeeping, then independent full point audit if no refactor scheduled | Not yet cleared or set until audit result |
| audit accepted / no refactor | Set dirty before completion, retain unchanged prices/basis/factors | dirty |
| audit rejected or numerical exception after application | Copy current basic values to trial; reconstruct flipped state, finish existing recovery | clean only if finish succeeds; otherwise terminal dirty |
| prediction fails before any write | Execute original legacy flip mutation/reconstruction once | clean only after successful original finish |
| scheduled refactor after an already applied flip | Copy current basic values to trial; reconstruct and finish recovery without predicting a second movement | clean only after successful finish |
| ordinary pivot | Preserve original candidate prediction, reconstruction and point recovery | clean only after successful finish |
| dirty / entering==0 | Preserve current basic point, reconstruct+finish, restart entering selection with same tolerance/budget | clean after successful finish; no stale OPTIMAL decision |
| dirty / apparent unbounded ratio | Same refresh; restart entering and ratio selection before recession certification | clean after successful finish; no stale UNBOUNDED decision |
| dirty / early optimizer finite or primal-feasibility failure | One reconstruction+finish if not expired, then re-evaluate checks | clean only if successful; otherwise original terminal error |
| dirty / rejected native candidate with fresh-basis recovery | Preserve original recovery/retry, pass ctx through recursion | clear only at observed successful finish; unknown helper recovery leaves dirty conservatively |
| TIME_LIMIT / ITERATION_LIMIT / caller exception | Preserve reason, work and provenance; no finally reconstruction | context discarded on return; no successful solution export |
| changed owner / model or unsupported config | Reject private invocation or select original optimizer before entry | no context transfer |

Control/candidate owned fixtures initially use an already primal-feasible basis.
A deterministic two-column fixture A=[1 1], c=[-2,-1], row_upper=[5],
column_lower=[0,0], column_upper=[1,10] is intended to exercise one bound flip
then a pivot; characterize its actual branch sequence before relying on it.
A separate all-upper-limited fixture is needed for an apparent optimum immediately
after dirty flips. Add a case with a genuinely unbounded column and a dirty flip
prefix; no fabricated branch-count assumption qualifies as characterization.

Additional operation assertions: exactly one basis-generation advance, state
flip and iteration increment; successful skip has zero fallback-candidate copies;
endpoint/refactor/rejection counts include every added reconstruction. For a lone
flip that reaches optimum, mandatory endpoint refresh can consume the would-be
saving: report zero net savings instead of hiding endpoint work.

Characterization preparation: scheduled refactorization depends on factor update
count, not flip count. An ordinary flip-only chain cannot naturally reach a new
refactor limit. Seed a real pivot under the original policy, then lower the owned
workspace refactor interval before the measured/test invocation. Record this
fixture preparation separately; no production scheduling rule is changed.

## Control census execution

control-census-1 passed1000/1000 assertions across80cases,normal compilation,
exit0/pins unchanged. All returned rows and source hashes verified. All five
managers and native/Markowitz support the four characterized recipes in Float32/64.
Actual flip-chain work is8FTRAN/4BTRAN; scheduled-refactor assertions pass.
Host runner282455/child282456/driver absent separately verified. This establishes
control behavior, not an optimization. Next run primal_flip_work_contracts.jl on
unchanged control: target5FTRAN/1BTRAN for four flips including endpoint refresh,
with accepted state/branch checks expected to pass and work assertions RED.
Degenerate, rejected, exception and unsupported-path qualification still pending.

## Private work RED/GREEN checkpoint

work-red-1:6state/certificate checks pass,2intended work failures8/4 versus5/1.
work-green-1 failed at module load before numerical execution; explicit Symbol
Pair entries repaired that diagnostic parser issue. work-green-2 passed12/12,
with four audits/skips, one endpoint refresh/reconstruction, no fallback and final
dirty=false. All exits/pins read and host process absence separately checked.
candidate-matrix-1 now qualifies the80characterized recipes; broader fault/
unsupported-path tests and all cost/acceptance work remain pending.

Ruling: the private public-facing diagnostic entry constructs its own workspace,
options, observer and deadline from type/fixture identifiers, accepting no supplied
workspace/callback/logger. This is narrower than the planned ws+owned-config seam
and eliminates ownership inference from arbitrary callbacks. Internal cloned
methods still take ctx first and enforce owner identity. Cost if inadequate:
qualification must add a new explicitly owned fixture constructor, never weaken
production callback contracts. Counters called direct_recomputations count only
the cloned direct reconstruction calls and endpoint helper; real kernel counters
include helper recovery work. Do not label the direct count a global solve census.


Ruling: generation assertions include applied flips plus actual direct recompute!
calls. Source simplex.jl recompute! invalidates the pool with basis=true; this is
independent of flip application. safety-contracts-1 passed111 and failed7 solely
on the omitted reconstruction increments. Correct the test, preserve the failure;
otherwise a valid fallback would be mislabeled double application.


Safety-contracts-2 passed139/139, normal compilation, exit0/pins unchanged. The
first failed generation expectation is preserved. Twelve fault/limit contracts
plus scope/overflow/unsupported precision pass. Dirty-entry corruption repair
has a separate unexecuted driver; existing primal-update/point/direction-price
regressions run as focused-1. These are prerequisite coverage, not cost acceptance.

Cost fixture preparation is explicit and outside optimizer timing:64 finite flips
on sparse256-row or dense64-row matrices, with0 or8 actual PFI pivot updates.
For seeded history only, temporarily zero owned flip costs during preparation,
restore the final immutable costs and reconstruct before measured invocation.
All final costs/bounds stay unchanged during candidate/control execution.
Three interleaved warm plain pairs and a separate counted pair are planned for
each precision/density/history/rejection combination. Reject-all executes the
real full certificate before forcing its failure. Report initialization, warmup,
compilation, allocations and endpoint work separately. No retained growing trace.
This is a bounded PFI cost probe, not all-manager or whole-medium performance.
