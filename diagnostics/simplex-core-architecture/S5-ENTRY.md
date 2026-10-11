# S5-A: ordinary original-cleanup entry census

Production source: master3220118, architecture403de44. Diagnostic only; no production
change and no elapsed-speed claim. The bounded paired census completed184 exact pairs; all20 independent audit gates pass.

## Ownership and observable boundaries

| Entry / boundary | Current owner and contract | Consequence for omitted initialization |
| --- | --- | --- |
| Default construction | `_initialize_workspace_state` creates costs, concatenated bounds, slack basis, factor, scratch, zero point/prices and unit weights. Costs/bounds/basis are independent of the restored basis. | Retaining this constructor retains its setup allocation/factor work. Zero scratch is not an initialized point. |
| Ordinary finish | `_finish_workspace_initialization!` reconstructs default point/prices before `refactor_initial`. | An observer can inspect all initialized arrays and stored precision. A callback can throw; its `DiagnosticObserverFailure.cause` must survive. |
| Native / no observer | Default reconstruction is overwritten by restored reconstruction on normal continuation. | This suggests discarded arithmetic only on successful entry, not permission to remove failure/deadline semantics. |
| Checked / recovery enabled | `recompute!` calls `_remember_verified_basis!`: reliability checks, independent basis/cost/bound copies, pre-publication callback, then checkpoint storage (maximum two). | A default checkpoint survives until replacement/eviction. Its original model/phase identity is required; a transformed-model checkpoint cannot substitute. |
| Expired context | Ordinary initialization completes, prior totals are assigned, then `_SolveDeadline(context)` is checked. | TIME_LIMIT publishes a checkpoint diagnostic event with the initialized default state; its returned result has no primal/objective/basis. An observer can distinguish zero scratch. The no-observer result alone does not prove intermediate state equality. Initialization's internal solve clock may use options.time_limit before the outer context check. |
| Restored handoff | Cleanup copies restored indices/states then `recompute!(refactorize=true,caller_guard=...)`; validates basis, constructs factor, increments completed refactor count and emits refactor event before reconstructing point/prices. | No restored array aliases caller state. On exceptions the owned workspace and consumed counters determine recovery/result. |
| Singular restored basis | Outer cleanup catches only owned numerical errors; ordinary `_recover_original_failure` returns the numerical result unless precision boosting/refinement is enabled. | The checked default checkpoint exists, but this outer singular-refactor branch does NOT itself try ordinary checkpoint restoration. Do not claim observed use merely from checkpoint availability. |
| Refactor logger throws | `recompute!` stores exact caller exception in the shared guard; enclosing cleanup rethrows it. | Reordering/removing refactor work must not swallow caller failure as a solver error. |
| Projection success | Hint is checked for shape/finiteness/original feasibility (native hardware floats may privately clamp an infeasible hint); exchanges/reconstruction/original checks still run. | Supplied point is not adopted as a certificate; reconstructed optimum may differ from hint. |
| Projection rejection | Cleanup copies restored basis again and reconstructs again before solving. | Failed hint does not waive restored-basis work or original certification. |
| Ordinary solve/recovery | Owns subsequent pivots, weight initialization, terminal and recovery checks with inherited counters/deadline. | Entry work is a cold boundary, not per-iteration cost. Default checkpoint availability can affect later recovery; bounded successful fixtures do not exhaust that path. |
| Precision boosting/refinement, lowered ambient BigFloat precision | Separate `_precision_initial_workspace` / `_precision_finish_initialization!` execute under stored working precision; existing start-guard tests specify behavior. | Excluded from this census and any proposed ordinary-path shortcut; four scalar types at their normal precision do not qualify this separate contract. |
| Other handoffs | Generic artificial removal, auxiliary box restoration, crash and `initialize_from_basis` have separate validation/ownership. | Not covered by cleanup-only equivalence. |

Source anchors: solver.jl::cleanup_original/_project_postsolve_basis!;
simplex.jl::_initialize_workspace_state/_finish_workspace_initialization!/recompute!;
simplex_recovery.jl::_remember_verified_basis!/_recomputed_basis_reliable;
simplex_precision_recovery.jl::_recover_original_failure. Existing S5 inventory
maps the excluded handoffs and original certification requirement.

## Work accounting and scope

The census parses and wraps unchanged production bodies in one diagnostic process.
All plain controls execute before installation. Every counted solve must match its
plain outcome and all observer snapshots exactly. Unobserved controls match final
results and caller-owned basis; there is no claim of a plain intermediate snapshot
where there is no observer. No timings or allocation measurements are inferred from
these instrumented runs.

Counters distinguish checked FTRAN/BTRAN requests from raw refinement solves. The
initial and first restored recomputations are separated from later recomputations;
subsequent projection/solver work must not be attributed to discarded initialization.
The refactor request counter describes recompute's request, not every direct factor
operation elsewhere. Publication counts record `_store_basis_checkpoint!` calls;
checkpoint-attempt counts alone are not successful publication evidence.

For m rows, n original columns, N=m+n and z CSC nonzeros, an initial reconstruction
validates m basis indices, clears/scans N mask/state entries, clears m RHS values,
scans N states and original nonbasic-column nonzeros, performs one checked FTRAN,
writes m primal/cost-RHS values, performs one checked BTRAN, then recomputes prices
across n columns/z entries/m row prices and zeros m basic prices. Checked recovery
adds basis/RHS assembly, finite/reliability work and independent checkpoint copies.
The default factor constructor occurs before this scope. Removing only finish's
reconstruction would not remove constructor storage, factor setup or restored work.

## Reused long attribution

Accepted old-source counted dual initialization0.883s / handoff refactor7.863s /
projection11.709s versus ordinary cleanup1737.949s and21418steps. Primal initialization
0.928856291s / handoff refactor5.269829135s / projection4.701423045s versus ordinary
cleanup1545.349544564s and18422steps. These scopes describe the old reference, not
current-master savings; no repeat or whole-solver speedup is justified here.

## Accepted bounded evidence and ruling

`census-1`: exit0,334.177s process wall time (includes compilation/instrumentation,
not a cost result), independent source/inventory/manifest/script pins verified.
160cases cover four scalar types × two requested algorithms × two HH backends ×
two policies × five modes (unobserved/observed/expired/projection/bad hint). Another
24Float64 cases cover singular restored basis, initial observer exception and
refactor logger exception with both algorithms/backends/policies. All184 exact
pairs pass; all normal outcomes are original-feasible OPTIMAL objective−16.
Exception cause identity and input basis preservation pass. Expired cases retain
prior7iterations/3refactorizations and publish no primal/objective/basis in the
result. Observer snapshots retain the reconstructed default state.

| Scope | Checked FTRAN/BTRAN/pricing requests | Basis validations | Checkpoint attempts/publications | Refactor requests |
| --- | --- | --- | --- | --- |
| Native initialization (92cases) | 1/1/1 | 1 | 0/0 | 0 |
| Checked initialization (92cases) | 1/1/1 | 5 | 1/1 | 0 |
| Normal native first restored reconstruction | 1/1/1 | 2 | 0/0 | 1 |
| Normal checked first restored reconstruction | 1/1/1 | 6 | 1/1 | 1 |

Expired/initial-observer failures have one recomputation; singular/logger failures
have two, with the second incomplete. Singular restored refactor makes no checked
solve/pricing request; the default checkpoint is retained in checked cases but
not used by this outer ordinary failure handler. Native successful projection has
four total recomputations; checked projection has nine after rejecting the changed
coordinates. Ordinary no-hint cases have seven, rejected length hints eight. These
are whole bounded-case totals, not per-iteration kernel costs or medium estimates.

Peak VM2615600KiB, sampled RSS1954108KiB, minimum available20881760KiB, swap0.
Guard/launcher pins enforce Julia/BLAS1 and the existing memory limits. The log
retains two global-binding world-age warnings for diagnostic counter access from
main after method installation; current Julia1.13 finishes and exact comparisons
pass. Future Julia/Revise portability is not qualified. Do not repeat accepted
numerical work merely to remove diagnostic warnings.

**Ruling: reject unconditional omission of default reconstruction; do not start a
production implementation from this evidence.** Observer state, deadlines and
checkpoint ownership are concrete counterexamples to general reuse. An infinite-
budget native/no-observer subset is only a hypothesis: the census does not prove
that skipping initialization preserves all numerical failure behavior, alternate
precisions or fallback state. A new eligibility scan or direct slack arithmetic
would be a distinct hypothesis needing its own work/failure contract and cost
evidence, not an O(1) flag justified by these tiny cases.

No production computation, allocation or retained memory is added. The diagnostic
recorder deliberately allocates snapshots, excluded from production/cost claims.
The source census identifies discarded work on successful paths but does not prove
it unnecessarily incurred under the complete failure/observer contract. No speedup
is claimed. No current-master medium run is needed to make this conservative ruling.
Next: objective/bound restoration ownership under a separate S5-B diagnostic plan;
no working-model certificate transfer. S5/S6 remain open.
