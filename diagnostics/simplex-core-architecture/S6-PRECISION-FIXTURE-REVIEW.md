# S6-L/M final independent review

Fresh gpt-6-astra review, read-only, no Julia or mutations. Verdict: ready for
planned test-only integration; no blocking numerical or implementation findings.
Base542dc8b/master8516e0d at review; integration2c3e0eb -> master7fea422 follows.
Master verification and push are separate gates, not assumed by this review.

## Accepted evidence and contract

Exact contradiction4g-2t=2g+2^-79>0 is sound under independent original row and
column tolerances. Exact-rational precondition checks stored values without
ambient rounding. Reversing boundfactor/comment/precondition reconstructs the
entire original test file; all original assertions and other testsets unchanged.
Production/workflow diffs empty. Options, construction256bits, ambient precision/
rounding, and default dual algorithm preserved.

Reviewer independently verified qualification30cases/300pass/18gates, RED one
expected margin failure without a solve/exit1/6gates, GREEN1+1476pass/13gates,
raw/portable identity and all606 current GREEN pins. Model/options/globals and
actual whole testset extraction checked. Runtime policy is not intercepted.
Latest runner380922/child380923/driver380910 absent and noJulia, documented boot.

## Work and memory

No unnecessary production work, allocation or retained-memory increase. Permanent
setup adds one scalar BigFloat multiplication and two exact scalar conversions
plus comparison per primal-kind construction (30cases), no new solves, full scans
or caches. No production benchmark or speedup claim warranted. Diagnostic records
are bounded and add one post-solve certificate per qualification case.

## Minor observations and disposition

P3 duplicate model rationalization in qualification driver23-24: deferred, as in
accepted S6-K, immaterial for one-variable fixture. Preserve exact accepted driver
and evidence; no rerun or benchmark.
P3 stale "No4g run" sentence in S6-L plan: historical S6-K review state is now
explicitly labeled during required publication reconciliation. No executable edit
or extra test is needed for this clarification.

## Declined-to-judge rulings

Actual x64/full-suite success: unknown, no such run; CI remains disabled.
End-to-end last-bit status sensitivity: unresolved; this robust fixture cannot
separate t from g, and stored-option tests establish only value/precision retention.
Feasibility recovery for old fixture: unresolved; old conservative failure valid.
Performance gains: no claim, production unchanged.
Integration/push success: independently verify after review; not a review assertion.
S6-N behavior: unimplemented continuation plan only, not validated.
All exclusions accepted as explicit limits; none is silently closed by this repair.
