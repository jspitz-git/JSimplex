# S6-L/M: cross-precision infeasibility fixture repair

Independent final review accepted without blocking findings. Production unchanged.
Test-only commit2c3e0eb integrated as master7fea422; targeted master verification
passed1477/1477 with14audit gates and the master push is remotely verified. Only test/bigfloat_integrity_tests.jl is a permanent edit.

## Validity and unchanged contract

S6-K proved that row_lower=g, fixed-zero column and t=g-2^-80 admit x=g/2 within
both independent tolerances. The new row_lower=4g gives exact contradiction margin
4g-2t=2g+2^-79>0. Column allowance implies x<=t while row acceptance requires
x>=4g-t. Matrix coefficient1 and all options/tolerances remain unchanged. The
construction runs in the original256-bit context; ambient precisions and modes
are unchanged. No production precision escalation or tolerance relaxation occurs.

The permanent change adds the row-bound factor4, its comment and one exact rational
precondition for primal-kind cases. Every existing assertion remains, including
INFEASIBLE. Dual/zero branch constructors and neighboring testsets are unchanged;
reversing only these three text additions restores the original entire test file.
The fixture branch name is primal; actual algorithm remains the default dual.

This robust-margin status case cannot distinguish rounding t to g. Separate
option tests establish stored value/precision preservation; end-to-end last-bit
status sensitivity remains outside this repair. No claim that the complete
precision contract or actual x64 CI is validated.

## Evidence

S6-L qualify-1: diagnostic replacement of exactly one constructor, reversible
source selection,30 cases (3 precisions x5 rounding modes x2 intervals), original
300 assertions all pass. All18 audit gates, independent pins/source/test hash and
exact mathematical margin checked. Every result INFEASIBLE, message empty row1
is infeasible, with no primal/objective publication. Model and option values/
precision unchanged; ambient globals restored. The candidate midpoint is rejected
by exact tolerance comparison and production original-space certificate. Raw and
portable evidence preserved in S6-L; qualification did not edit permanent tests.

S6-M margin-red-1: add the actual exact precondition to permanent test source but
keep old row_lower=g. Driver extracts the actual constructor/precondition for one
case without a solve. Exactly one expected failed assertion, exit1, six audit
gates. Frozen RED test source preserved. The original30 status failures remain
in S6-K and are not rerun for this margin control.

S6-M focused-green-1: row_lower=4g, same extracted margin control passes1/1; both
full original cross-precision and supplied-option testsets pass1476/1476. Total1477,
exit0,13 audit gates, independent pins and actual source/test verified. This new
source regression includes dual/zero branches and supplied-options copy/workspace
checks, without repeating broad corpora. No test failure or error occurred.
Previous runner380922/child380923/driver380910 separately absent, noJulia on boot
20de7dde-704e-41c8-bee7-b8511c0a86b0.

## Work, limitations and next gate

No production work, allocation or retained-memory change. The test adds constant
sized exact-rational arithmetic once per primal-kind construction (30 checks) and
one BigFloat multiplication in fixture setup. No new solves in permanent tests,
no cache, no benchmark or speedup claim. Diagnostic records have bounded exact
value storage; test guard preserves original compilation/solver configuration.

One final independent numerical/work/memory review covers S6-L qualification and
S6-M permanent candidate. If accepted, test-only commit, master targeted1477 check
with actual source/pins/user hashes, push and remote verification follow. CI stays
disabled; other historical failures and the overall S6 gate remain open.

Final review: S6-PRECISION-FIXTURE-REVIEW.md. Deferred minor duplicated diagnostic
rationalization is retained without rerun. The historical plan-state sentence is
clarified as part of documentation publication.

## Integration closure

Master7fea422249442003b53f6f245bb569a5e0cf9bcf has the reviewed test-only change.
Master-1 passed1+1476 assertions, exit0, all14gates, independent pins/manifest,
actual main source, exact candidate test hash and three preserved user-file hashes.
Separate host runner381786/child381787/driver381778 absent, noJulia, same boot.
Master push verified with ls-remote. Raw/portable master results retained.
Next bounded task:2026-10-12-nearly-singular-objective-census.md (S6-N).
