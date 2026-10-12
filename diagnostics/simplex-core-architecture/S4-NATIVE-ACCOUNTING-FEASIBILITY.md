# S4-N: native allocation accounting feasibility

## Decision

The installed binary supports a concrete **SuiteSparseConfig callback boundary** for
UMFPACK's long-index allocation helpers. It does not supply an existing complete HH
native allocation/free ledger. Full native retention remains **OPEN**. No hook is
installed or numerics executed by S4-N. A callback interposer is not qualified for a
future numerical launch by this report.

The immediate narrower obligation is source attribution of the Julia allocation
counters already reported in M: installed SparseArrays initializes SuiteSparse with
`jl_malloc`, `jl_calloc`, `jl_realloc`, and `jl_free`. Those counters must not be
interpreted as exclusively Julia array/wrapper traffic. Whether and how these entry
points contribute to the installed runtime's timed counters needs a bounded source
trace, selected in S4-O. No M timing, raw record, or acceptance oracle is revised.

## Evidence and provenance

Read `results/S4-N/source-contract.json`, `upstream-provenance.json`, saved ELF
symbol tables and disassemblies. All binary inspection is read-only; no dlopen,
ctypes, Julia or allocator calls. Native binaries match M's recorded hashes.
Installed bindings are under Julia 1.13.0 aarch64's SparseArrays `src/solvers`.
The versioned upstream SuiteSparse v7.10.1 files document ABI/semantics, but are NOT
installed source or proof of all build options. Headers were unavailable in L's
searched installation/include locations; no whole-host absence is asserted.
The optional `.h.in` URL returned 404, preserved in provenance. Initial guessed
`umf_dl_*` disassembly selectors yielded no function bodies; the actual exported
helper names are `umf_l_*`. Neither attempt executed library code.

## Installed call path, beyond symbol presence

`umf_l_malloc` at 0x30080 branches to `SuiteSparse_malloc@plt`; the latter loads the
callback at config offset 0 and calls it with `blr`. `umf_l_realloc` at 0x30084 clamps
object count to at least one, checks the signed-index size limit, then branches to
`SuiteSparse_config_realloc@plt`, whose body loads offset 16 and calls it. Overflow
returns NULL before that callback. `umf_l_free` at 0x2fea8 skips NULL, calls
`SuiteSparse_free@plt`; that body loads offset 24 and calls it. The setter at 0x1580
stores the malloc function pointer into the same static config structure.
These are concrete compiled paths, not merely imported names. Dynamic PLT binding,
interposition, other allocator paths/dependencies and actual callback pointer values
in a future process are not captured. This is not complete transitive reachability
or a runtime event count. Symbol tables also expose CHOLMOD dependencies; a full
HH/SuiteSparse/dependency allocation domain cannot be inferred from three helpers.

## ABI, domain, and restoration

| Callback | C ABI | Accountable event if a future shim is qualified |
| --- | --- | --- |
| malloc | `void * (size_t)` | successful non-NULL return adds requested bytes |
| calloc | `void * (size_t, size_t)` | successful return adds checked product; preserve zeroing |
| realloc | `void * (void *, size_t)` | successful replacement updates one allocation; nonzero-size failure retains the old allocation |
| free | `void (void *)` | forwarded callback invocation/completion, not proof of OS page release |

The callback slots belong to a loaded SuiteSparseConfig library instance, not an HH
factor or thread. Setters are plain stores; changing four slots is not an atomic
transaction. All users of that instance are affected. Julia/BLAS thread limits alone
do not prove absence of finalizers, tasks, other SuiteSparse consumers or callback
reentrancy. A hook needs native synchronization and a proven quiescent installation/
restoration domain. No such implementation or proof exists in current evidence.

Installed `LibSuiteSparse.jl` uses `OncePerProcess`, calls SuiteSparse_start for
version >=6, then sets all four callbacks to Julia's `jl_*` functions for version >=7;
it registers SuiteSparse_finish at exit. Initialization exceptions are caught/logged.
This source route does not capture actual successful initialization or pointer values
in M. Restoration must use all four captured prior callbacks, never assume libc
malloc/free, and must not call SuiteSparse_start as a restoration shortcut. Upstream
start resets the configuration; finish currently does nothing. ABI size_t is 64-bit
for the inspected aarch64 ELF; do not substitute Julia Int blindly for arbitrary hosts.

## Ledger requirements and unsupported cases

- Install only after runtime initialization but before all allocations in the intended
  domain. Preexisting pointers later freed/reallocated must be classified as unknown,
  forwarded to the saved allocator unchanged, and excluded from a complete-balance
  claim. Pointer address reuse requires removal/update, not monotonically accumulating
  addresses. A shared native owner must not be charged once per Julia wrapper.
- UMFPACK's helper calls the **raw config realloc**, not SuiteSparse_realloc's
  `ok`-returning wrapper. Nonzero-size failure leaves the old block live; overwriting
  its ledger entry on NULL is wrong. In-place success updates size once; moved success
  retires the old address and records the new. NULL input is allocation. The observed
  helper clamps count and checks overflow before callback; other consumers or direct
  raw API callers may issue zero-size requests. Do not invent a portable zero-size
  realloc rule; reject qualification unless the delegated allocator contract is known.
- Preserve allocator alignment, calloc zeroing, overflow checks, error semantics and
  thread requirements by forwarding exact requests/results to saved functions. Do not
  read allocation headers or use opaque native pointers as Julia objects. Requested
  bytes are not usable malloc size, native allocator metadata, or resident pages.
- A possible C shim must not allocate its bookkeeping through the intercepted path,
  call Julia from callbacks, trigger GC or log through allocating I/O. A preallocated
  address table of capacity C costs O(C) retained storage; open addressing has expected
  O(1) lookup but O(C) worst case per event. Locks/atomics and reentrancy handling add
  work to every allocation/realloc/free. Capacity overflow or missed events invalidates
  accounting while safe forwarding continues; it must never suppress frees or alter
  numerical error handling. No concrete capacity, shim ABI validation, or overflow
  qualification is supplied here. Thus no instrumented-cost claim is available.
- UMFPACK internal memory compaction/reuse within Numeric->Memory is not necessarily
  an allocator event. Its internal garbage collection is distinct from Julia GC.
  `Numeric`/`Symbolic` Julia finalizers call native free and then clear pointer fields;
  `copy(UmfpackLU)` shares native owners. Assigning a new numeric object, discarding an
  HH backend on failure, or collecting a Julia wrapper does not record successful
  native free. Delayed finalizers can run after a measurement window and during drain.
- A future ledger would need to retain callback code/state until all domain owners,
  pending finalizers and in-flight callbacks are drained, check no unknown/overflow
  events, restore exact saved callbacks quiescently, then release bookkeeping.
  Full GC or empty weak references alone cannot establish that invariant. OS allocator
  caches may retain pages even after successful frees; RSS is not a replacement oracle.

## Scope and work verdict

N adds only documentation, read-only binary/source evidence and offline Python checks.
Zero constructors, factorizations, solves, hook changes, GC or native API invocations.
No unnecessary production work or memory is introduced. Proposed callback overhead
would occur per native allocation event and is explicitly unqualified, not free.
M's measured refactor windows and all accepted E–M artifacts stay unchanged; native
reuse remains disabled. No promotion, fullsuite/CI, general control/scalar/platform,
other-consumer or complete native-retention claim follows.

Next: the ONE separate S4-O source-only allocation-counter attribution plan. No new
numerical plan is justified until the actual delegated allocator/counter semantics
and a safe accounting domain are established. This is an unsupported full-accounting
conclusion with a concrete narrower observable, not a claim that interception is
fundamentally impossible.
