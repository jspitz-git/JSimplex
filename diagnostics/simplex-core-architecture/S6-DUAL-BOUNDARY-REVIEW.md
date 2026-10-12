# S6-I/J independent final review and ruling

Reviewer: fresh independent reviewer, read-only, no Julia and no mutations.
Scope: qualification and permanent candidate against 96e18dd; master8516e0d.
Verdict: not ready to merge. S6-I is useful local evidence; S6-J rejected.

## Blocking P2 accepted

Candidate helper line44 invokes retry with basis_refreshed=false. Production
simplex_pivot.jl:337 calls the ordinary kernel; dual_simplex.jl:1182 and1284 can
perform numerical repair refactors independent of max_recovery_rounds. Candidate
discard at simplex_pivot.jl:185 retains those costs. The zero/exact-one refactor
assertions at candidate94-95/133 still rely on native arithmetic. Historical CI's
16 state failures were precisely one-versus-two retained refactors. This proves
an unresolved mechanism, not the candidate's actual x64 outcome.

Ruling: preserve GREEN source/evidence, restore test to HEAD, reject permanent
substitution. Do not weaken work counts or safeguards. Future fixture qualification
must control downstream cause and preserve public recovery/callback coverage.
The two unchanged public groups do not replace the four redirected recovery calls.

## Other conclusions

Entry preparation/exception handling mirror current production. Retry retains
publication, observer wrapping, cleanup and work accounting ownership. Successful
controls exclude unconditional rejection. Exact stop-exception control proves the
initial stop check only, not nested retry-catch propagation.

No unnecessary production computational work, allocations or retained-memory cost:
production unchanged. Test additions own one scalar counter per case and twenty
small control-workspace initializations; snapshots have O(n+m) selected storage.
No benchmark or speedup claim required.

Reviewer checked GREEN292/292, RED108pass20expectedfail, qualification248pass,
603 current GREEN hashes, raw/portable identity, refs and process absence.
Coordinator independently audited11GREEN gates before review and preserved exact
candidate source before restoring the test. Do not rerun old pin matching after
intentional restoration and mislabel that as corruption of the accepted attempt.

## Declined-to-judge rulings

Actual Julia1.13.1x64 outcome/historical cause: accepted as unknown; no such run.
Full-suite readiness: accepted as open; focused evidence only.
Arbitrary precision/adaptive/hypersparse and full-workspace equivalence: accepted
as outside bounded local qualification; no generalized acceptance claim.
