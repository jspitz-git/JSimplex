# S4-F: conditional native symbolic boundary qualification

NEW component experiment after S4-E source contract and independent review.
No production/test change. This first native API gate does not qualify the HH
publication/copy/prepared-cache or public solver integration. Do not enable HH
reuse, change tolerances/precision/controls/backend or rerun accepted measurements.

## Fixed cases and budget

Native Float64/Int64 canonical CSC only, six independent reference/candidate
pairs. Build each side with a fresh lu(B0), never copy(F). Default controls and
q=nothing throughout; snapshot original control values once and assert unchanged.
Reference calls lu!(F,B1;reuse_symbolic=false). Candidate calls existing
_same_umfpack_pattern BEFORE lu! and uses that Boolean; no HH method overwrite.
All input values below are exact dyadics. Dense-pattern cases explicitly construct
CSC colptr[1,3,5],rowval[1,2,1,2] so stored zeros are retained.

| Case | B0 | B1 | Candidate reuse |
| --- | --- | --- | --- |
| changed values | [4 1;1 3] | [5 1;1 4] | true |
| value-sensitive pivot | [1 2;3 4] | [2^-20 2;3 4] | true |
| stored zero becomes nonzero | [4 0;1 3], full stored pattern | [4 2;1 3], full pattern | true |
| changed pattern | [4 1;1 3] | diagonal[4,3] | false |
| changed dimension | [4 1;1 3] | diagonal[2,3,4] | false |
| singular same pattern | [4 1;1 3] | [1 2;2 4] | true |

Exactly12fresh setup LU calls +12lu! attempts. On each of the10successful target
factors, one forward solve and one transpose solve for rhs=collect(1.0:n), total20
solves. No setup solves, HH extraction, workspace, public solver, updates,
certificates, refinement probes, observer, adapter, micro/control/retry calls.
Singular case catches SingularException and never solves from failed factor.
No empty/nonfinite case in this first batch; those remain required before a later
HH candidate can qualify. No random matrix search or broad sweep.

## Preconditions and evidence

Fresh separate host call confirms prior runner/child/group absent by boot/start/
command and no other numerical process. Pin actual src/test, Project/Manifest/
LocalPreferences, driver/launcher, Julia executable, umfpack.jl, LibSuiteSparse.jl,
SuiteSparse_jll.jl and resolved libumfpack/its loader dependencies before launch.
Read existing launcher rather than substituting a new runtime. User dirt preserved.
Runtime record VERSION/architecture/Julia+BLAS threads, actually loaded native
library path and hash; verify against prelaunch pins. No retroactive old runtime
pin claims. No version query via a separate Julia process.

One guarded process, Julia/BLAS1, heap2GiB, VM8GiB, RAMavailable>=6GiB, swap<=1GiB,
wall600s. Forbidden big/largo/AnyMOD and aliases. No warmup or cost benchmark.
Preforward counters count all setup/refactor/solve attempts, including throws.
Write partial records after each completed pair; stop on unexpected failure,
preserve exit/raw/source and mark remaining cases unexecuted. No silent rerun.

Record canonical input bits/CSC, initial control snapshot, actual reuse decision,
status/exception, symbolic identity before/after (retain old symbolic object while
checking identity; pointer reuse alone is not proof), and new numeric identity.
No mutation of controls/q. Symbolic object must remain identical for true-path
cases; do not assert a numeric allocation address must differ without retaining
its old owner. Drop instrumentation references after each pair, including failed
factors; no retained collection of native factors.

Successful factors: collect the native combined L/U/p/q/Rs representation once,
validate permutations and independently check the wrapper's documented
L*U == (Rs .* B1)[p,q] convention with exact-rational residual reporting plus a
fixed numerical bound: norm(E,Inf) <=64eps(Float64)*max(1,norm(L,Inf)*norm(U,Inf),
norm((Rs .* B1)[p,q],Inf)). Solve bounds: norm(B*x-rhs,Inf) <=64eps(Float64)*
max(1,norm(B,Inf)*norm(x,Inf),norm(rhs,Inf)), likewise transpose. These are diagnostic
bounds only. Record paired factor/permutation/scaling/solution equality as data,
not a required bitwise match. Do not enlarge bounds after observing failure.

Input ownership: before solves/metadata, compare native CSC arrays to the intended
zero-based structure/values and assert arrays are not aliased to B1 arrays. After
owning B1 snapshot, overwrite its values and row indices with sentinel contents
without changing lengths, then perform the planned solves against the owned
original B1. This directly exercises borrowed input lifetime without extra solves;
metadata equations also use the owned snapshot. B0 remains independently owned.
Singular failure: record before/after dimensions/CSC/status/symbolic/numeric and
exception; discard mutated F. Never require backend rollback or claim this proves
HH old-base/saved-factor preservation. Original source-only HH mapping stays separate.

Report allocation bytes/events/GC/elapsed/compile separately for setup, refactor
and solve using existing Julia measurements once per call; cold single samples
are work attribution only, no speedup/overhead inference. Collect one reachable
object graph summary per successful side after old identity references are dropped,
and native numeric Info fields with their exact documented meanings if available.
Otherwise mark native bytes unavailable. Graph fields are not native retained/RSS
bounds; serial small cases cannot prove asymptotic retention. Resource samples
remain separate and do not attribute native allocations to a call.

Postexit: process.json/exit, independent full pin rehash, actual source and user
hashes, raw/portable identity, exact case/call accounting and all predicates.
A new exclusive audit, fresh independent numerical/work/memory review and STATUS/
continuation update precede any follow-up. No permanent repair/integration yet.
A later separate HH-level plan must cover extraction, failed publication, saved
base/history/prepared-state preservation, actual borrowed assembly, empty/nonfinite
eligibility and retention before any optimization proposal. CI stays disabled;
original-model certificates and S2-A/S6-J/wholeAF rejection stay unchanged.
