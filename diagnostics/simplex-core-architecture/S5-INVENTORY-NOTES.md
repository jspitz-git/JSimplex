# S5 static phase and cleanup handoff inventory (partial)

Inspected production master4143dad / architecture8701a58. Read-only preparation
while S0 owns the numerical guard. No new measurement, implementation or reuse
claim. S5's parent inventory checkbox remains open for complete owner/exception
mapping and independent review.

## Boundary contracts

| Boundary | State carried | Rebuilt or separately checked |
| --- | --- | --- |
| Presolve/scaling -> working solve, solver.jl | Owned transformed problem, scaling/progress context, shared original clock and outer budget | Working minimization costs and simplex initialization; the working certificate uses working tolerances and coordinates. |
| Working optimum -> original postsolve | Unscaled primal then postsolve stack; restored basis if available | Original feasibility is independently checked even without presolve reductions. Reduced models or failed unscaled points require original cleanup/retry; absent basis requires retry. |
| Original cleanup initialization | Original problem/options/progress, restored basis, prior iteration/refactorization counts, optional target primal | Fresh workspace/factors/scratch; restored basis is refactorized/recomputed. A supplied point is only a projection hint until original-model certification. |
| Feasible cleanup -> primal optimization | Certified original-model workspace and current basis | Temporarily selects algorithm=:primal so native primal safeguards follow the actual phase, resets dual_devex_fallback, emits cleanup/primal phase events and restores original options in finally. |
| Generic phase I -> original-dimension phase II | Explicit PhaseOneMap maps structural/slack columns; artificials map to0 | Validated exchanges remove basic artificials (tiny nonzero artificials require actual movement); fresh original-dimension workspace/basis is refactorized and checked before adoption. Index remapping invalidates old weight/history meaning. |
| Legacy primal phase I -> phase II | Private auxiliary workspace remains; original objective is restored | Artificial upper bounds and objective entries change; native artificial-bound normalization precedes transition; original costs restored and normal recomputation retained unless feasibility-recovery policy owns it. |
| Precision transfer | Copied/converted working problem, costs/bounds/basis and perturbation journal; shared consumed-work budget/original progress semantics | New factor/scratch/primal/prices, recomputation, finite/basis-quality checks and rebuilt weights. Old numerical state stays owned by the source; attempted factor work counts remain consumed. |

## Cleanup projection is not state adoption

_project_postsolve_basis! verifies target length/finiteness and original feasibility.
A native infeasible target may be privately clamped only as a basis hint. It builds
[target; A*target], bound states and displaced columns. Each selected exchange
uses a FTRAN, checks finite direction/pivot, updates basis/factors and may refactor
at the existing update limit. Final reconstruction and original-primal checks are
mandatory. Native cleanup correction can recover a valid basis whose reconstructed
point loses feasibility. Coordinate equality with the supplied target is not
required for native legacy cleanup on a degenerate face; certification decides.

If projection fails, cleanup restores the supplied original basis and recomputes.
If projection/preserved-point cleanup later returns infeasible, unbounded or
numerical error, it retries without the target hint while retaining consumed work
and deadline. Callback exception identity propagates. Numerical failure is not
permission to silently reuse the projected point or renew the time budget.

The final solver rechecks original primal feasibility and objective evaluation.
No cached working-model success transfers across scaling, postsolve or an altered
objective. A phase label naming dual origin does not imply cleanup executes dual;
_cleanup_primal_feasible! explicitly runs primal.

## Artificial removal and pricing state

Generic phase I copies CSC columns and appends artificial columns without a dense
m-by-k artificial matrix. PhaseOneMap owns original/phase maps. On removal, each
basic artificial is normalized if needed, then selected exchanges use checked
BTRAN/FTRAN, independently priced rows and validate_pivot!. Tiny artificials are
not treated as exact zero: the actual movement is reconstructed and verified.

Only after successful original-dimension reconstruction, finite/basis reliability,
primal feasibility and original-primal checks does _adopt_phase_basis! replace
costs,bounds,basis,point,prices,weights,factors and scratch. Caller progress/model/
options and monotonically consumed work remain with the original workspace.
Devex is reset and only a safe pricing rule is inherited; old indexed weights and
progress history cannot follow a changed column numbering. Auto pricing resets.
Failure leaves the original numerical state intact and retains work done privately.

Precision transfer already constructs a factor directly for its transferred basis;
it does not rely on a temporary default slack factor. It separately copies owned
bounds/costs and rebuilds precision-dependent recovery weights. This existing
path is a reference for ownership, not permission to transplant its certification
or exception rules into native cleanup unchanged.

## Concrete cost candidates, not accepted optimizations

The ordinary cleanup_original branch first calls initialize_workspace, which builds the default slack
factor, recomputes primal/prices and emits refactor_initial. It then installs the
restored basis and calls recompute!(refactorize=true). initialize_from_basis also
currently starts with initialize_workspace before installing/refactorizing the
supplied basis; replacing one caller with it alone removes no initial work.
The generic phase export similarly initializes a fresh original workspace before
installing the mapped basis. These are cold boundary costs: initial factorization,
FTRAN/BTRAN, RHS and price traversals may become redundant if a direct-basis
constructor can preserve validation, counters, diagnostics, weights and failure
ownership. That contract and a focused work comparison are still required.

Projection adds a matrix-vector product, N-length target/state storage, displaced
column list, exchanges, and a final reconstruction. A successful projected basis
may differ from the hint. Avoid optimizing target copies at the expense of aliasing
with the original result, and do not attribute all cleanup time to entry: lazy
primal weight initialization and ordinary steps are separate consumers.

Next: finish mutation/observer/exception ownership, inspect existing native cleanup
and phase regressions, and select one conservative boundary subplan. Reuse the two
preserved cleanup origins for entry/ordinary attribution; do not rerun their
completed baseline measurements without a changed implementation or hypothesis.
Any new numerical validation waits for the sole S0 reference to finish.

## Independent review additions

Dual auxiliary-box restoration is a separate handoff. _make_dual_feasible!
(dual_simplex.jl) remaps nonbasic states to original bounds, prepares a private
trial with its own factor/refactor-policy, reconstructs and performs required
flips/dual-feasibility checks. State publishes consistently before pending events
are replayed; unsuccessful attempted factor work remains counted. Do not confuse
this boundary with primal artificial-column removal or postsolve projection.

_run_original_objective_terminal! (simplex_driver.jl) restores original objective
costs/bounds after owned perturbations and re-verifies terminal outcomes in at
most three passes with the same consumed-work/time budget. A certificate for
perturbed costs/bounds cannot survive restoration unchanged. This loop is distinct
from original-model postsolve cleanup and must be mapped before a reusable handoff.

Artificial removal is not always an exact zero step: a small nonzero artificial
requires movement=primal[leaving]/column[row], consumes an iteration and must be
reconstructed/checked before export. The potential redundant default-basis
initialization concerns the ordinary cleanup branch; precision boosting and
LP refinement use their separate initialization path.

Independent static review accepts the map as partial after these additions.
No new runtime work/retention is introduced and no numerical experiment was run.


## Initialization events, counters and failure ownership

`_initialize_workspace_state` already separates allocation/default slack factor
construction from `_finish_workspace_initialization!`, which reconstructs values
and then emits refactor_initial. This is an existing seam, not an invitation to
publish zero scratch as an initialized point. simplex_start_guard_tests explicitly
observes the first reconstructed slack at refactor_initial and checks its stored
BigFloat precision even under a lowered ambient precision. Callback-visible
initialization order is therefore part of the regression contract.

Ordinary cleanup assigns prior iteration/refactorization totals only after its
initial default workspace returns, then checks the original shared deadline and
installs the restored basis before recompute!(refactorize=true). Generic phase
helpers explicitly inherit work on private attempts. A direct-basis constructor
must specify when an owned workspace exists if factor construction throws and
which work total recovery receives; returning a new factor alone does not solve
that failure boundary. Keep attempted and completed work distinctions explicit.

`initialize_from_basis` additionally checks basis shape/state consistency, rejects
free nonbasics with finite bounds and states naming absent bounds, invalidates
basis checkpoints, reconstructs and checks finite/basis solve quality, then resets
Devex. These safeguards differ from merely replacing `workspace.basis`. Existing
simplex_start_guard_tests cover singular inputs, invalid nonbasic states, overflow
fallback, callback failure provenance and stored precision. A cleanup-only change
must not silently alter this broader initializer or precision/crash entry paths.

A minimal future hypothesis could avoid only an unobserved discarded default
reconstruction while retaining its factor owner; a broader direct-basis constructor
could also avoid default factor construction. They have different savings and
failure/event contracts. Neither is selected or implemented here. Before choosing,
use the existing cleanup-entry attribution, name eligible observer/policy cases,
and count the actual factor/solve/RHS/price work removed. Full phase handoff reuse
still needs model/order/cost/bound/weight ownership and original certification.
