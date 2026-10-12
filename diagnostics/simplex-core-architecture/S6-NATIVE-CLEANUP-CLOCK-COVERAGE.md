# S6-AM: cleanup interruption coverage decision

**Decision:** a narrow native active-bound-journal entry-interruption obligation
is not asserted by the ten mapped testsets. Qualify two new public driver entries
(callback returns true; callback throws the same numerical-shaped exception),
using a separate reviewed S6-AN plan. This is added contract coverage, **not a
repair of the older three CI failures** and not a controlled clock-expiry claim.
No Julia, test, production or workflow change occurs in AM.

## Evidence binding

`results/S6-AM/coverage.json` contains exact source blocks, locations, lexical
assertion counts, source hashes and explicit coverage classifications for ten
named testsets. Counts are statements in source, not loop-expanded runtime totals
and not additional historical failure records. The new offline map has 21 passing
source/evidence checks and 528 input hashes. It does not execute any old parser,
auditor, numerical driver or test. All 513 tracked src/test/workflow files match
master354bb1f; six user hashes are preserved. Fresh host refs match pushed3d57291
and master354bb1f, and prior runner425975/child425976/group425967 are absent on
boot20de7dde-704e-41c8-bee7-b8511c0a86b0, with no Julia process.

The native target and full primal-perturbation integration file match both
historical sources4914cbb/b720674. Helper/monitor/target match AL's preserved exact
extractions. The accepted S5-C focused run1463/1463 is reused only where its
executed-file list AND pinned source match. All five mapped test files match S5-C
pins, but simplex_driver_tests.jl and native_cleanup_recovery_tests.jl were NOT in
that focused run. Their coverage below is source-only; being pinned is not proof
of execution. AL supplies the separate new7/7 successful native lifecycle.

## Precise coverage

`P` below means primal_perturbation_integration_tests.jl, `D` simplex_driver_tests.jl,
`N` native_cleanup_recovery_tests.jl, `B` primal_perturbation_tests.jl, and `C`
simplex_perturbation_integration_tests.jl. All paths are under test/.

| Source | Policy and entry | Journal / interruption boundary | Asserted outcome and work | Evidence reused |
|---|---|---|---|---|
| P:81 | Native arithmetic, adaptive setup; public driver | Owned bound journal; callback becomes true **after** phase_cleanup | TIME_LIMIT, original bounds, retired journal, workspace/budget iterations equal; no explicit payload/kernel assertion | S5-C aggregate/source |
| P:96 | Native arithmetic, adaptive setup; public driver | Active bound journal at iteration limit; separate exact-arithmetic case has no perturbation | ITERATION_LIMIT, total2, perturbation1/cleanup0, bounds remain active; no payload/kernel assertion | S5-C aggregate/source |
| D:78 | **Checked/adaptive** helper; public driver | No journal created by fixture; zero-time or zero-iteration options | TIME_LIMIT or ITERATION_LIMIT, zero iterations; no journal/payload/kernel oracle | Source only |
| D:136 | Checked/adaptive; auxiliary phase | Observer tracks phase_auxiliary; callback then returns true or throws ZeroPivotException | Entry seen, TIME_LIMIT or identical exception, zero iterations and synchronized refactors; no journal/payload oracle | Source only |
| D:160 | Checked/adaptive; replacement workspace | No journal in fixtures; shared iteration budget | First OPTIMAL/consumed1, second ITERATION_LIMIT/total2; no finite-time expiry assertion | Source only |
| D:298 | Checked/adaptive; replacement workspace | Observer reads inner solve clock; existing test assigns budget120s | OPTIMAL, clocks nonempty, inherited start/limit, options restored; no expiry or active journal | Source only |
| N:43 | Native/legacy; **direct private recompute** | No perturbation journal; callback true/throw at third callback, or bad factor/dual | false or identical SingularException, selected values unchanged, iterations0; no public driver/payload oracle | Source only |
| P:180 | Adaptive setup replaced by default native; public driver | Owned active bound journal, false callback | Six original success predicates; AL adds actual clock/state/work provenance, below30s | S5-C aggregate/source plus AL7/7 |
| B:156 | Native arithmetic/adaptive; checkpoint restore | Same active journal/buffer aliases retained, false callback | Journal/aliases/values/cooldown/levels preserved; no entry interruption | S5-C aggregate/source |
| C:108 | Native arithmetic/adaptive; public driver | **Cost** journal; iteration limit and callback after phase_cleanup | ITERATION_LIMIT2 or TIME_LIMIT3, cost journal retired/zero costs on cancellation; no native bound-entry/payload oracle | S5-C aggregate/source |

The word `:deadline` in N:43 denotes a callback-triggered stop; no elapsed-time
threshold is created there. The checked helper in D is an explicit profile choice,
not a synonym for default native arithmetic. The existing120-second assignment in
D:298 is only source evidence for inheritance assertions; it is not permission to
increase the native cleanup fixture's30-second limit. No mapped test asserts all
of: default native policy, an already-owned active **bound** journal, cancellation
or caller-exception at the first public cleanup guard, unchanged selected state,
no new kernel work, and absent result payload. This is a scoped map, not a claim
that every possible test elsewhere was exhaustively disproved.

## New boundary and bounded work hypothesis

Only the entry boundary is needed; do not repeat AK's full return-path analysis.
After AL's real setup and initial optimizer, `ws.perturbed` and the active bound
journal force the original-objective route even though native recovery is off.
`src/simplex_driver.jl:108–139` installs the same budget clock, synchronizes work,
temporarily installs remaining options, then checks the guarded callback **before**
`_verify_driver_basis!`. Expiry short-circuits callback evaluation. For the new
qualification, exactly one observed caller-callback invocation is therefore a
mandatory gate; a timeout before that callback cannot masquerade as its outcome.

A first callback returning true is predicted to return TIME_LIMIT with message
`time limit reached during feasibility recovery`. No restoration is attempted for
that status. `_internal_solution` emits one checkpoint and creates no primal,
objective or basis payload. The selected state and owned active journal remain.
A first callback throwing a precreated SingularException is predicted to rethrow
that identical object, with no result/checkpoint. The guarded callback records
exception provenance, preventing ordinary numerical recovery from consuming it.
In both branches the `finally` synchronizes budget and restores options.

Predicted driver-window work is zero FTRAN/BTRAN/refactor/pricing and zero new
iterations; zero kernels is not zero total work. Existing policy/options/budget
bookkeeping and the normal-return checkpoint/result construction remain. No
factor wrapper, observer, mutation injection, direct private retry, certificate or
quality probe is needed. This boundary is not exercised by AL's false-callback
success, by post-restoration cancellation, or by private correction rejection.

## Acceptance and limitations

The original native successful test/helper and its six predicates stay untouched.
The two future interrupted cases have their own declared oracles; they do not
weaken or retroactively replace the original OPTIMAL oracle. AL is a saved local
reference, not a new matched-control run or evidence of observer neutrality.
There is no justification here to reset clocks, warm up numerical paths, extend or
remove the30s limit, alter tolerances/precision or change production safeguards.

If a future case expires before the callback, preserve its failure and stop; do
not retry, wait out timing, increase time or substitute a forced private call.
Measured brackets and callback count identify the new declared route, not any
historical private clock check. The old three failures still have no captured
status/message/elapsed. S6-AK's TIME_LIMIT inference and S6-AL's successful native
cleanup remain distinct. S6 and actual x64/full-suite gates stay open; disabled CI
and S2-A/S6-J/wholeAF rejections are unchanged.

AM adds zero production scans/solves/allocations/retained state. The source-only
map is bounded to ten selected blocks. Future diagnostic work is capped at two
fixed1x1 lifecycles with a few owned boundary snapshots; no benchmark or cost
rerun is warranted. This review cannot support a speedup or historical fix claim.
