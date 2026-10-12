# S4-X: original-cleanup dual work composition

SOURCE/EVIDENCE ONLY at 975f13a, master 0eb75c3. No Julia, module loading, native calls,
compilation, hooks, cache/environment changes, new LP arithmetic or old script rerun.
The frozen T LP/options and S isolation manifest are unchanged. This is one bounded
composition analysis, not a public experiment or complete runtime work certificate.

## Entry and ownership

cleanup_original can enter _solve_continuous_dual! despite an original primal request.
The wrapper installs dual options and restores them in finally. Native policy disables
global precision/LP recovery, but does not exclude the older local refinements below.
Numerical exceptions retain the existing catch/propagation rules; callback provenance is
not replaced. _recover_original_failure returns the run under this native policy.

In the ordinary original-cost/bound branch, _solve_continuous_dual_once! invokes
make_dual_feasible! once, then one main _dual_optimize! if initialization permits it.
An altered working model instead reaches the original-objective driver. These are local
entry counts, not bounds on every invocation from that driver or the public solver.

Within one _make_dual_feasible! invocation, the initial recompute is F+B. _flip_bounds!
may itself recompute if a bound changed. If prices still fail, at most one auxiliary
workspace is constructed. It copies the HH factor once and recomputes F+B; other copies
include bounds, basis, point, prices, weights, scratch and refactor-policy state. The HH
copy shares extracted base and history prefix, owns solve scratch, and has no native
refactor workspace. It is neither zero work nor a fresh native LU.

The auxiliary optimizer receives perturb_degenerate=false and its iteration/refactor
counts propagate in finally, including failures. Native phase_one=false selects direct
_dual_optimize!, not the checked auxiliary driver. The optional negative-objective branch
checks a recession witness and can create a feasibility workspace: one constructor and
initial F+B, then another F+B after zeroing costs, followed by its own dual optimizer.
This branch is conditional source coverage, not a claim that T's exact optimum reaches it.

The successful auxiliary handoff creates a staged workspace and explicitly makes a SECOND
factor copy from the original workspace before assigning the auxiliary basis. A refactor
and F+B rebuild original-bound state; _flip_bounds! may add another recompute. Publication
occurs only after the original checks; trial refactor counts are retained in finally.
Do not confuse the ordinary staged candidate's shared factor with this explicit handoff
copy, or transfer an auxiliary certificate to the original model.

## Local attempt limits and extra work

| Boundary | Source-local limit per invocation | Work that must remain separate |
| --- | --- | --- |
| _retry_simplex_step! | min(8^2*(2+1),typemax(Int)) = 192 staged attempts under T's policy; attempts increments before forwarding; at most 2 refresh_pending requests | Candidate state copies, attempted solves and failed work; this is not 192 public iterations or all refactors |
| Native retry recursion | policy.recovery=false excludes recursive repair_basis retry; staged mismatch throws rather than recursively entering _retry_simplex_step! | A non-staged mismatch can first enter the bounded staged retry |
| Unchecked dual refresh recursion | With Dantzig, no auto/steepest recursion; dimensions 2/5 exclude partial pricing. Remaining self-retry flips basis_refreshed false to true, so at most one such nested refresh retry per root unchecked call | Refresh recompute, price repair and child body all count; the staged retry has separate roots |
| Native row/direction correction | At most 3 correction solves in the requested orientation | Residual/quality scans, row pricing, private trial vectors |
| Native staged tableau correction | At most 3 B corrections, at most 1 ordinary F for reselection, then at most 3 F corrections | Repeated ratio tests, owned row/direction/flips, borrowed assembly; not prepared FTRAN |
| Legacy _refined_basis_solution | 1 initial backend solve plus at most 32 correction solves = 33 | Up to 33 BigFloat residual scans, coefficient/RHS conversion and solution storage; early exit or throw can lower work |
| Legacy price or direction refinement | One separate lu(B), two 256/512-bit helper calls, hence at most 66 backend solve entries | Separate factor is not the HH refactor workspace and is not charged as HH symbolic reuse |
| Legacy full pivot refinement | One separate lu(B); two row, two price, two direction helper calls, at most 198 backend solve entries | Reselection may change entering column; row/price/direction comparisons, saved prices and rollback |
| Small-pivot stabilization | One separate refinement factor, two price helper calls, at most 66 backend solve entries | For T's native backend the factor is lu(B); Markowitz specialization is outside T |
| Bound flips | At most one pipeline FTRAN with operation=:bfrt for a nonempty flip list; none if RHS validation fails | Sparse RHS assembly and vector updates; conditional on configured ratio test, not one FTRAN per flipped variable |
| Staged discard | If pending_factor_update is set, at most one live-basis refactor per discard call, even after deadline | No stop callback in that restoration; shared factor work survives candidate rejection |

The legacy local refinement helpers are called from Float64 dual-price/direction/pivot
paths without requiring policy.precision_boosting or policy.solve_refinement. They retain
their existing 256/512-bit arithmetic and acceptance tolerances; X neither enables a new
precision mode nor suppresses those safeguards. Native correction quality uses compensated
checks directly. Existing original feasibility/certificate fallbacks also retain their
independent evaluation costs. Backend entry bounds above are not machine-instruction,
native-allocation or latency bounds, nor measured solve counts.

The original-objective restoration tail can add F+B, a conditional refactor+F+B, a price
repair, and then install primal options for _primal_optimize!. It finally checks feasibility
and the original witness/certificate. W's untimed witness BTRAN and certificate categories
remain in force and are not recounted as new evidence here. Public diagnostics=nothing
still does not eliminate internal staged scratch/observer machinery; it is not a request
for an external observer. Additional driver serialization is outside public solve.

## Precise limit of this composition

The source proves finite local loops and monotone refresh flags as scoped above. It does
NOT yet supply a finite COMPLETE public work budget. The specific unsummed transitions are
(1) altered-model _run_from_basis_once! -> forced feasibility modes, with progress resets
and auxiliary/primal calls, and (2) original-cost restoration -> _primal_optimize!, whose
candidate-retry aggregate remains UNKNOWN from W. Invocation multiplicities, all quality/
certificate scans and exception restoration must be composed before a whole-route total
can be claimed. No unbounded execution is demonstrated. Shared clock/iteration limits and
T's conditional exact three-pivot path do not supply the missing derivation.

For reached T basis assembly the expected representation is SparseMatrixCSC{Float64,Int64}.
S's candidate guard is O(m+nnz(B)); only matching-type conversion has the identity argument.
Other representations can duplicate conversion allocation. HH extraction/orientation and
internal update transposes retain W's separate categories. The new exceptional lu(B)
objects are additional lifecycles, not evidence of reuse or native retention safety.

Therefore no counter insertion design, instrumentation, numerical plan or launcher is
produced. Bootstrap/cache/initializer work remain independent OPEN gates; their bounded
investigation is not reopened. This ends the current sequence of controller-budget audits.
The next genuinely different roadmap item is S3-C: source-only DSE consumer support and
arithmetic-order coverage, reconciling existing S3-A/B evidence before selecting any new
implementation or experiment. It will not repeat the accepted support-mode cost census.

## Evidence and computational cost

results/S4-X/source-contract.json contains 18 literal source checks and 558 fresh read-time
hashes; source-excerpts.json preserves 13 exact ranges. These establish source binding, not
an executable call-graph oracle. Search failures for guessed file names are explicitly
recorded in search-note.md; no failed validation was used to authorize publication.
The collector was copied after its successful execution and is not one of its own input
pins. Closure separately binds it and the report/review/next plan.

No production computational work, allocations or retained memory were added. One-time
source reading/hashing and finite documentation are the only new costs. Existing auxiliary
copies, staged retention, local BigFloat conversions, sparse scans and backend solves are
identified rather than optimized or benchmarked. No speedup is claimed. Production/test/
environment/master/CI, S/T/Q evidence, HH-disabled state, native-retention/fullsuite/broader
S4/S6 obligations and all rejected candidates remain unchanged.
