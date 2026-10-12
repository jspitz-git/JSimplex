# S4-N: source-only feasibility of native allocation accounting

After S4-M review, SOURCE/EVIDENCE ONLY. No Julia, factor/component/workspace/solver,
new native calls, allocator replacement, environment change, production/test edit,
old scripts or cost/qualification reruns. Verify STATUS, actual host refs/full last
process groups, user/source hashes. Keep CI disabled and HH symbolic reuse disabled.

M supplies bounded local refactor-window timings and Julia/native-info/RSS snapshots;
it leaves native retained allocation/free balance OPEN. Do not repeat L's general
memory-metric inventory or M's representative timings. Determine one concrete safe
instrumentation boundary, or conclude that available machinery cannot support it.

Read installed SuiteSparseConfig/UMFPACK wrapper bindings, loader symbols available
from read-only binary inspection (no loading/calling library), and matching versioned
upstream documentation only if installed headers are unavailable. Separate native
allocator callbacks, UMFPACK internal garbage collection/reallocation, Julia native
owner finalizers and operating-system allocator retention. Trace any allocator-hook
API scope, ABI, process/global/thread effects, default restoration and allocation/
free pairing across changes; a symbol alone is not proof that installed UMFPACK uses
that hook. Do not equate pointer wrapper collection with successful native free.

Assess whether an exact accounting ledger can cover all allocations/reallocations/
frees relevant to one HH native refactor lifetime, including failed realloc semantics,
zero-size requests, alignment, threads/reentrancy, error/finalizer paths, shared
owners, allocations predating interception and instrumentation storage. Count callback
work and retained ledger overhead. No hook installation in N; no claim that instrumented
time measures uninstrumented cost. No opaque pointer dereference or unsafe free.

Select only ONE next bounded plan if justified by source evidence: exact supported
ABI/ownership boundary, fixed new inputs, constructor/refactor/solve bounds, explicit
pre/post-hook allocation domain and drain/restoration behavior, numerical oracle,
stop/preserve rules and guards. If safe full native allocation accounting is unsupported,
state that and select a narrower observable without calling it full native retention.
A lack of feasible hook is a technical conclusion, not authorization to bypass native
safeguards or use RSS as a substitute proof. Avoid repeating accepted E–M boundaries.

Fresh independent work/numerical-contract review; update STATUS/roadmap/continuation,
push diagnostic documentation only. No production promotion or broad S4/S6/fullsuite
closure. Preserve all old evidence, sources and environments; no numerical launch in N.
