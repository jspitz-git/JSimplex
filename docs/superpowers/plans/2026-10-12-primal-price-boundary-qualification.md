# S6-V: qualify an explicit repeated-price recovery boundary

> Execute inline using systematic-debugging; diagnostic-only. No permanent test
> repair until separate RED/GREEN plan and fresh numerical/work review.

S6-U preserves the four original manager cases and 20/20 local assertions. Its
observed one-correction path does not explain old x64 zero-correction failures.
Do not rerun it, the old S2 full file, or any accepted corpus/reference/cost run.
S6-J's uncontrolled downstream native refactors remain rejected.

## Proposed boundary (not yet numerically qualified)

A budget unit test must arrange a demonstrated price disagreement and a fresh
BTRAN with nonzero residual. Mere unconditional retry or direct event injection
would bypass the required guards. Diagnose a deliberately simple dyadic fixture:
six identity basic columns, the same four +/- unit nonbasic columns and zero final
column, basis costs [1,1,0,0,0,0], unit basic primal, equality RHS=ones(6), other
columns at lower zero and the final column upper one. This is a new fixture,
not an equivalent matrix or a repair of the original native arithmetic.

Use analytically declared rho=[1,1,2^-40,0,0,0] to prepare the initial price mismatch.
For the subject only, a test factor adapter should forward the real next cost-RHS
BTRAN, record its owned result, then replace that one output with the declared
rho. All subsequent BTRANs (including residual correction), FTRANs, updates,
invalidations/copies/refactors must forward. Validate exact dispatch/layout and
RHS/one-shot identity before relying on it. Do not fake residual quality, decisions,
correction events, publication, or the second disagreement. No wrapper goes into
production or other tests. Retain original post-publication reduced_costs[7]=-1.

1. Reconcile adapter interfaces and ownership against existing accepted test
   adapters without rerunning their drivers. Establish exact model/basis/price
   arithmetic and expected residual B' rho-cB analytically. Derive the selected
   direction/price disagreement with unchanged default options and tolerances.
2. Before launch, specify three cases per existing manager: exact initial prices
   with real factor; seeded prices with real exact factor; seeded prices with the
   single declared fresh BTRAN output. The first two are new controls, not reruns
   of S6-U. Qualify their predicted statuses/events rather than assuming them.
   Four subjects retain all five original repeated-budget assertions, including
   exactly one correction/publication, zero iterations, empty exclusions.
3. One guarded process, at most twelve iterations on these tiny new workspaces.
   Additional observation is read-only, owned, nonworkspace-safe and performs no
   numerical calls in callbacks. Capture wrapper hits/raw/declared output, residual
   RHS, actual forwarded correction, work/basis/state/stop/publication paths.
   Reject any shortcut that leaves downstream native arithmetic uncontrolled for
   the exact-one/zero assertions. Do not infer portability from a single local pass.
4. Audit process/exit/source/input/options/policy/pins, original assertion text and
   exact residual arithmetic. Keep failed/unqualified controls explicitly. Fresh
   independent numerical/work/memory review, then accept/reject diagnostic scope.
5. Only if qualified, write a separate minimal permanent RED/GREEN subplan. Keep
   native_price_roundoff_fixture and adjacent original native public/integration
   coverage intact; change only the repeated-budget fixture and scoped adapter.
   A deterministic unit test cannot replace the surrounding native stress tests.

Preserve all raw attempts, environments, worktrees and user changes. No solver,
precision, tolerance, safeguard or certificate changes. CI remains disabled;
full-suite/x64/broader S6 unresolved. Single Julia/BLAS1, heap2GiB,VM8GiB,minRAM6GiB,
maxswap1GiB; separate fresh boot/start_ticks/command process absence before each
launch or pinned edit. Do not mutate pinned inputs while running.
