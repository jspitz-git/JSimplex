# S6-J: permanent explicit dual retry boundary candidate

Status: REJECTED after independent final review. Master remains 8516e0d.
The exact GREEN candidate is preserved in results/S6-J/green-1-rejected-test-source.jl;
the permanent test file has been restored byte-for-byte to HEAD.

Two recovery test groups explicitly invoke transactional retry through a test-only
entry helper. The helper preserves public stop wrapping, initial cancellation,
auto-pricing preparation, finite/weight recovery, basis iteration measurement and
exception handling. It changes the selected boundary, not the production retry,
ratio calculation, numerical safeguards, tolerances or budget policies.

The unchanged duplicate-column fixture remains numerically ill-conditioned. Names
and comments declare explicit retry scope rather than natural public entry. Both
public duplicate-column safety and consistent-small-pivot test groups are byte
identical to the pre-change file. Four recovery callsites change; every original
numeric, state, cancellation and callback assertion remains. Each case owns a Ref
counter incremented immediately before retry after all entry guards.

## RED / GREEN evidence

RED keeps original public calls: 108 original assertions pass and exactly 20 new
entry-counter assertions fail. No other failure or error: seven audit gates pass.
The frozen RED source, failed log and process are preserved in results/S6-J.
This is a deliberate boundary-contract RED, not reproduction of historical CI.

GREEN redirects four calls and adds successful and entry-guard controls. Full file
passes 292/292 (48 public duplicate, 96 explicit bounded retry, 60 public small
pivot, 32 explicit refresh cancellation, 56 successful/entry controls). Exit zero,
all eleven audit gates, independent whole pins, pin manifest hash and actual source/
test hash verified. Run: .superpowers/simplex-core-architecture/S6-J/green-1.
Portable evidence: results/S6-J/green-1-*. Julia 1.13.0 AArch64, Julia/BLAS one.
Runner 377979, child 377981 and driver 377970 separately absent after completion;
no Julia on boot 20de7dde-704e-41c8-bee7-b8511c0a86b0.

The 56 added controls cover four managers: one actual successful pivot compared
with public iteration and original feasibility; initial cancellation with unchanged
selected state; exact stop-exception identity; invalid finite entry returning
NUMERICAL_ERROR. The entry counter is one for success and zero for rejected entry.

## Limits and review obligation

Explicit retry still performs native arithmetic. Historical CI had 16 state
mismatches per run that differ only in refactor count (one versus two). Direct entry
alone does not prove downstream work assumptions portable. Final review must judge
whether the candidate establishes a useful bounded contract or merely relocates
platform dependence. Local GREEN is not actual x64 CI success, nor proof that all
48 historical assertions are repaired. No workflow is enabled or dispatched.

No production computational work, allocation or retained-memory change. Test-only
entry repeats existing public guards and uses one scalar Ref per owned case; the
new successful controls allocate small independent workspaces and compare selected
state. No new production cache or scan, no performance benchmark or speedup claim.

## Final disposition

Independent final review found a blocking P2: the helper enters retry with
basis_refreshed=false, and retry still invokes ordinary native row/direction
checks. Those may legitimately refactor irrespective of max_recovery_rounds=0;
discard retains that work. Therefore zero-added-refactor and exactly-one-refactor
assertions remain platform dependent. The entry counter does not prove their
precondition. The four redirects also remove public recovery/callback integration
coverage that the two retained public safety groups do not replace.

Accept the finding. Reject permanent substitution, retain all evidence, and restore
only this task's test changes. No test-only commit or master integration occurs.
A future fixture must control the actual downstream rejection/refactor cause while
retaining public integration coverage; no count relaxation or safeguard removal.
The qualification remains local evidence, not a permanent-test acceptance gate.
See S6-DUAL-BOUNDARY-REVIEW.md. Next: independent S6-K tolerance-status census.
