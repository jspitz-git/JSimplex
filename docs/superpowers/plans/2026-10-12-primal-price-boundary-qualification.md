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
   direction/price disagreement with unchanged default options and the original
   `_primal_iteration!(ws, ()->false, 0.0)` call (explicit zero price tolerance).
2. Before launch, specify three cases per existing manager: exact initial prices
   with real factor; seeded prices with real exact factor; seeded prices with the
   single declared fresh BTRAN output. The first two are new controls, not reruns
   of S6-U. Qualify their predicted statuses/events rather than assuming them.
   Four subjects retain all five original repeated-budget assertions, including
   exactly one correction/publication, zero iterations, empty exclusions.
   ADD a budget-sensitive work oracle: exactly one fresh cost-RHS BTRAN during the
   iteration, separately exactly one residual-correction BTRAN, total two BTRANs.
   Count every real forwarded call, including calls after the one-shot replacement
   has been consumed; the adapter replacement hit count alone is insufficient.
   Exclude initialization and identify cost/correction RHS by owned values and the
   declared basis-cost contract. These RHS vectors are distinct for this fixture.
   A wrongly renewed second recovery can return false on exact zero residual before
   emitting correction_attempt; it MUST fail the fresh-cost-BTRAN count oracle.
   Preserve all five original assertions in addition to these new work assertions.
   Include a narrowly scoped budget-renewal negative check in the qualification
   design: prove the count oracle rejects an extra fresh cost solve even when the
   old event/status assertions stay true. This is not a second original control
   run or permission to alter production safeguards; preserve the failed oracle
   evidence in a separate diagnostic record.
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

## Final-review correction

S6-U final review identified P2: the one-shot adapter plus an exact identity factor
could let a broken renewed budget pass the five old assertions. The mandatory
fresh-cost BTRAN count and negative sensitivity check above close the proposed
acceptance gap. This is a corrected diagnostic plan, not completed qualification
or an executable repair. No S6-U evidence or numerical run is changed or repeated.

## Launch contract

Twelve iterations (three modes times four managers), no public solve or old rerun.
All modes use a recording-only forwarding factor; subject additionally substitutes
one declared output after a real cost BTRAN. Seed setup uses production reduced-cost
reconstruction outside callbacks before wrapping. Actual identity B gives exact
raw solves; declared residual is -2^-40 at coordinate3. Controls predict OPTIMAL/
no recovery for exact prices and NUMERICAL_ERROR/one fresh BTRAN/no correction for
seed-only. Subject retains all five original assertions plus budget-sensitive counts.
After freezing each subject record, directly invoke the exhausted recovery function
once as a separate negative component check (four extra BTRANs total, not iterations).
It must return false with no events/state change; the old oracle stays true while
the added work oracle is false. This proves sensitivity to an extra boundary call,
not a captured or simulated faulty production control-flow trajectory.

## Result

Qualification-1:124/124,12iterations+4negativeboundarycalls,exit0,21gates616pins.
All expected statuses/work and exact dyadic residuals qualified locally. The four
negative budget oracles are false as intended while the old five booleans stay true.
Fresh review pending; no permanent test/production changes. See S6-PRIMAL-PRICE-BOUNDARY.md.
