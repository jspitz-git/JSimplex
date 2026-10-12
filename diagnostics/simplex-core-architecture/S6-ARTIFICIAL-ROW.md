# S6-D/E: artificial-row recovery reachability

Status: current-source census and exact-row counterfactual audited and independently reviewed.
Production and permanent tests are unchanged from mastera465da5.

## Existing coverage and historical failures

The test and simplex_phase_one/native_cleanup_recovery/native_phase_transfer/
simplex_numerics source are unchanged since the failed CI4914cbb revision. The
original3df48ec change has264 accepted focused assertions in normal compilation
and compile-min, recorded under diagnostics/adaptive-degeneracy/results/artificial-row.
Earlier logs identify Julia1.13.0AArch64. Those old local passes are not evidence
for Julia1.13.1x64 CI. Neither accepted old reference nor cost measurements repeat.

S6-A accounts for96 failures in the seven-mode/four-manager budget/cancellation
family in both CI runs:20 return expectations (16true-vs-false and4true-vs-exception),
20 original-state preservation,20 zero-iteration,20 zero-artificial-removal and16
missing correction-event expectations. This pattern alone does not measure the
CI unit-row residual or establish its exact cause.

## Current local census

S6-D/census-1:28 control/observed pairs, original named oracle168/168,exit0,
13audit gates, independent whole pins/source/test hashes. Julia1.13.0AArch64.
The control retains the original behavior-driving observer for cancel/exception;
only passive event recording changes. Selected numeric state/work/outcomes agree
using Julia isequal. This is not observer-free or whole-workspace bitwise proof.

Independent fresh-fixture probes run after both attempts, so no extra pre-attempt
BTRAN or quality scan can alter their scratch/work. All28 initial rows are finite
but unreliable: absolute error3.4066698932426226e-16, relative0.0012391830724484952.
Same values occur for all four managers. Row correction is enabled only for native
primal mode with positive budget. Budget/checked/dual reject with0iterations and no
correction; cancel/exception/pivot record correction, preserve original state and
consume0iterations. Exception preserves the exact callback exception object.
Point mode consumes1exchange and records artificial_removed, then rejects export
against infeasible original bounds and preserves the original numerical state.
Original/phase work remains charged by the wrapper's finally path.

## Qualification and work

No production diff and no new production scans/solves/allocations or retained state. Diagnostics
perform28pairs of small fixture executions plus28 independent row probes and the
original28-case oracle. Each isolated probe adds setup, one BTRAN and a quality
scan; post-state feasibility checks and copied selected snapshots are explicitly
diagnostic-only. No timing or whole-solver speedup inference is made.
Selected bound representations are strings; they do not prove underlying object
identity. Existing source/test byte equality and assertion output supplement the
snapshots. Source and test hashes are in each attempt, full pin inventories local.

## Next hypothesis

The fixture relies on naturally arising homogeneous roundoff to enter correction.
A reliable row is permitted to skip that branch. S6-E tests whether an exact valid
row is a sufficient mechanism for the historical assertion pattern. It does not
establish which row or backend behavior occurred on CI. No permanent assertion,
tolerance, policy, production kernel or workflow changes are authorized here.

## Exact-row counterfactual (S6-E)

Exact-3 uses uniquely named AST clones of current removal and its callback wrapper.
One insertion replaces the local first-row solve output with[1,1,0,0,0,0], checks
B' * rho == unit and reliable zero-residual quality. No production method is
replaced. All downstream candidate/pivot/point/export validation and finally work
inheritance remain in the clone; this is explicitly a counterfactual intervention.
Generated clone text and its SHA256 are saved with the result.

28 passive-recording twin pairs agree. All28 independent row probes are exactly
reliable. The redirected original assertion body reports72pass/96fail/0errors,
exit1 as expected. All17 qualified audit gates pass, including source/pins/clone.
The failure-line/expression multiset exactly matches CI:20 each at65,66,68,71;
16 at70. All76 non-state evaluated values also match. Full evaluated-state equality
was initially hypothesized and REJECTED: current counterfactual adopts structural
column1, whereas the saved CI tuple adopts original slack7, with additional
signed-zero differences. One raw evaluated-state line interleaves stderr; preserve
it. The rejected full-detail comparison is saved separately. No numerical rerun.

In all four managers, budget/checked/dual/cancel/exception modes succeed in one
exchange, publish original state and never signal correction_attempt. Thus the
cancellation/exception callbacks waiting for that event never trigger. Pivot mode
still rejects (0exchanges); point mode exchanges once then rejects infeasible
original bounds. Reliable row alone is sufficient to produce the same failed
predicates, but not the exact CI trajectory or actual CI row. The original-model
export safeguard remains effective in the negative fixture.

Exact-1 failed before any cases because the parser did not unwrap the documented
function node. Exact-2 failed before cases on a missing ternary separator space.
Their source/log/process/pin audits are preserved. They are not numeric evidence.
Exact-3 process373223/child373224/driver373214 separately absent; no Julia,
boot20de7dde-704e-41c8-bee7-b8511c0a86b0. S6-D prior372735/372736/372727 also absent.

## Decision and remaining work

Do not change the solver to reject a reliable row or relax any acceptance guard.
Do not declare CI fixed. A durable test repair needs a deterministic test-only
unreliable-row fixture that exercises the unmodified production removal wrapper,
including budget/unsupported/cancel/exception/pivot/original-bound cases. Qualify
that test seam separately before changing assertions; no new production hook or
AST clone is acceptable as the permanent assertion target. Preserve naturally
arising roundoff cases as additional numerical coverage, not required event oracles.
Current stage changes are diagnostic only, with no master integration needed.

Independent final gpt-6-astra review accepts with no critical/important finding.
Two minor publication clarifications are incorporated: this work inventory includes
84 exact-clone invocations (56twins+28oracle), each additionally assembling an owned
basis, multiplying B' * rho, allocating separate quality scratch and evaluating
quality. These O(n+nnz(B)) diagnostic checks and bounded snapshots are not production
costs or performance evidence. Plans now distinguish passive-recording twins and
post-attempt separate-fixture probes. No numerical or implementation fix was needed.
See S6-ARTIFICIAL-ROW-REVIEW.md. All accepted numerical attempts remain unrepeated.
