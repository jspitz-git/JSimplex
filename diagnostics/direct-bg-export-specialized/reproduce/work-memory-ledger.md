# BG specialization Task1: work and memory ledger

Offline source/test preparation only. No Julia parser, loading, compilation,
numerics, allocation measurement or timing has run. The new stage is an ordinary
83-file copy of the frozen 79-file stage plus four separately named sources.
The packed DIRECT reference and the original workspace candidate remain available.
Three adapted test modules use the actual accepted GREEN2 source paths; the amended
import test retains `sum(...;init=0)`. New boundary tests are a fourth module and
have no automatic call. Existing source comments saying Task1/Task2 are inherited
verbatim through the inverse, not claims that the new sources were executed.

## Source delta and execution frequency

Seven helper families (nine signatures including export overloads) now have a
thin keyword facade and a positional, explicitly parametric core. Nine facade
calls are added at the corresponding existing helper entry points; only those
facades and the import core have `@inline`. Compiler elimination is unproven.
No helper body is duplicated. Complete inverse records restore every original
byte after reversing the nine header/facade edits and namespace substitutions.

| Existing phase | Retained work | New algorithmic work |
| --- | --- | --- |
| Construction | one factorize, one export, one import or fallback initializer, one lower backend and one BG inner | none; same transient build owner and wrapper |
| Refactorization | busy guard, private build, optional hook, mandatory type check, single publication, catch/finally cleanup | none; extra facade/core call boundary only |
| Checked export | two triangle checks O(n+l+u), two permutation checks O(n), scaling scan O(n) | no new scan or repeated check |
| Nonunit native orientation | original scaling/selection/finite scans, at most one backend solve, four triangular multiply operations and two tolerance scans | no new solve, copy, scan or changed arithmetic |
| Import | diagonal lookups, two order maps, n column constructions, u index/value operations, rejection refill if needed | no new array request, conversion, division or pass |
| Ordinary update/FTRAN/BTRAN/copy/query | exact previous forwarding definitions and original packed algorithms | none |

Scratch misses still request one BitVector and zero/two/four orientation vectors
according to the original path. Cache hits eliminate only eligible requests, not
validation or orientation work. Native extraction still allocates fresh export
matrices and uses native storage; Markowitz extraction retains its original
triplet and sparse assembly costs. Fallback remains an ordinary backend, not a
claim of bounded native storage. The original importer allocates 2*n+3 requests
without normalization and 2*n+4 with normalization (including D even when later
rejected); variable-length payload is 16*u+16*n plus optional8*n, plus outer
column records, maps, headers and metadata. No normalization temporary returns.
The same tuple result and all exception prefixes remain.

## Complete retained graph and peak

The four-field workspace, three-field factor wrapper and one-field transient
build owner have exactly the previous layouts. The inner still contains owned
lower CSC, row/scaling/diagonal arrays, lower work, packed upper columns and their
shared row-order maps, column order/inverse positions, work/spike, active and
recycled BG update storage, incidence rows/affected IDs, full row cache/prepared
destinations, optional sparse cache, shared-prefix count and validity fields.
No field or additional owner was added. Capacity and prepared destination
reachability are charged even when their logical lengths are small.

The policy budget is unchanged: P0=16*(l+u)+8*(n+1),
B=min(1048576,fld(P0,16)); charge512+8*cld(n,64), optionally32*n.
Checked arithmetic, exact-size reuse, dimension/budget eviction and all-or-none
orientation attachment are unchanged. These are policy charges, not exact Julia
object sizes. Copies have no workspace and share only the existing lower data
and immutable update prefixes; mutable upper/work/cache containers remain private.

Refactor peak remains the union of old factor, private new factor, any saved
copies, ordinary backend, extraction/CSC/triplet temporaries, retained or transient
scratch, result metadata and garbage awaiting collection. Dropping scratch is not
immediate freeing. Native allocation/free balance and OS retention are unproved.
The source transformation adds no payload to this graph. It may change heap
materialization of existing small objects, stack usage, compiled method instances,
code size and startup compilation. Specializations depend on owner/backend/hook
and input types, not n, nnz or scalar values. These costs require later measurement.
No zero-allocation or speedup claim follows from the source inverse.

## Test-only work and storage

The three renamed suites retain every original assertion and algorithm after
namespace inversion. Their prior work ledgers are bound inputs, not fresh executed
coverage. They include real factorizations, updates, solves, injected failures,
source-backend mutation, synthetic orientation, graph snapshots and exact rational
oracles. Task2 must inventory all these calls and derive actual assertion counts;
7935 must not be reused as a guessed new total.

The NEW fourth module has three entry tests, each naming a behavioral failure:

| New test | Prospective explicit work |
| --- | --- |
| request equivalence | 12 paired-side synthetic paths including failures1..5;14 checked-export entries including warm repeats; at most12 orientation helper entries and8 synthetic solve calls. Five importer inputs times two normalization modes:20 successful imports plus134 injected import attempts, from the fixed sum of request counts67 per side. No genuine factorization here. |
| hook order | 24 wrapper setups and24 refactor attempts, across two sides/two policies/six stop positions. Four factorize hooks throw before the backend:44 real factorize API entries,40 underlying exports,36 imports,32 inner initializers. No added solve/update/copy. |
| default versus explicit hooks | 48 builds across two sides/two policies/three shapes/two normalizations/two routes;48 factorize/export/import API entries,96 solves (48 FTRAN,48 BTRAN), plus8 importer calls for two rejected-division controls. No update/copy. |

Thus the new tests add92 factorize API entries (including empty setup entries,
not92 nonempty native kernels),96 explicit factor solves,24 refactor attempts,
246 importer entries including failing attempts, and8 synthetic orientation
solves. At most44 genuine native orientation solves are an upper bound from native
export entries, not an observed count; actual empty/all-unit paths skip them.
Backend internals remain additional. These tests execute no public LP solve.

Recording allocators have fixed256-entry `(element_type,length)` arrays;218
allocator instances are constructed over the full new suite. The maximum importer
request list is10 (n=3 normalized), and synthetic workspace requests are5. The
256 capacity is a diagnostic refusal bound, not a candidate cache. Hook logs have
five Symbol entries;24 logs total. Views/copies of initialized prefixes, detached
CSC/packed/bit snapshots, owner tuples and reflection graph traversal add cold
O(n+l+u+history+cache) work and GC roots. Synthetic64x64 stored-zero triangles
are constructed separately per side/case. No graph snapshot or log is inside a
candidate helper or any future timed cost window. Test assertions have their own
storage. This is a source schedule and payload account, not a peak/GC-event bound.

The two candidate types never share test owners. Failure assertions compare each
thrown object with its own injected sentinel; cross-side output comparisons use
bits/modes/request signatures and the same original inner type. Default-versus-hook
build comparisons exercise default hooks with a recording allocator, then explicit
default hooks with the same allocator class. Allocator-free hot import controls
separately exercise the default allocator. No claim is made that a recording
allocator has identical compiler escape behavior to the real default allocator.

## Deferred qualification

Task1 accepts only source/preparation correctness after independent review. Task2
must prepare exact drivers, loading/module paths, call and storage budgets, world-
age handling, guards and admission before Julia. Allocation RED expectations are
conditional on that concrete driver. Task3 retains all eight previous time, event,
byte, graph, compilation and numerical gates. No automatic profiler, cost rerun,
annotation tuning, master integration, dependency update or CI activation follows.
