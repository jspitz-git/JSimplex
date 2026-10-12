# S4-O: attribution of existing allocation counters

## Result and limits

For the currently installed Julia 1.13.0 aarch64 implementation, SuiteSparse calls
that use the configured `jl_*` allocators **can contribute to the same GC counters
as Julia object allocation**. Successful malloc/calloc with a current Julia task
adds allocator **usable bytes** and one malloc event. Successful realloc with a
current task adds one realloc event and only nonnegative usable-size growth to
allocated bytes. Free does not subtract from those allocated-byte/event totals.
These counters cannot provide live native bytes or complete native allocation/free
balance. Native retention remains OPEN; no hook experiment is selected.

This is a source/instruction interpretation, not a capture of M's actual callbacks,
TLS state, loader slots or per-allocation events. M launch pins include the executable,
SuiteSparse wrappers/native libraries and driver, but **do not include timing.jl,
libjulia.so or libjulia-internal.so** inspected here. Their new hashes are read-time
O evidence, not retroactive M launch pins. M recorded the matching version, but that
is not proof that all newly inspected bytes were loaded in its process. The mapping
below describes the current installed route conditionally; historical category
counts within M remain UNKNOWN. No M artifact, value, timing table or oracle changes.

## Bound source and compiled paths

Installed `base/timing.jl` lines37–72,690–720 defines `gc_num`, `GC_Diff`, the allocation
sum and @timed. Installed `include/julia/gc-interface.h` defines the matching GC_Num
layout. `version_git.jl` names commit d1c37793dd2ab0de6bca636e1d7f2ceb43150a9c. Saved
upstream files from that exact commit supply C field names/semantics; they are not
proof of every installed build option. Saved targeted disassemblies independently
corroborate the relevant compiled branches, sizes, arithmetic and counter writes.
No library is loaded, and no function is invoked. See results/S4-O provenance/hashes.

- Export `jl_malloc` at0x142fc, `jl_calloc` at0x138a0, `jl_realloc` and `jl_gc_num`
  are indirect forwarding stubs in libjulia. Export list and corresponding internal
  implementations identify intended routes; actual runtime slot contents are UNKNOWN.
- Internal `ijl_malloc` at0xeb628 branches to counted_malloc at0x100c68.
  It calls malloc, obtains current task, and updates counters only when both result
  and task are non-NULL. `memory_block_usable_size` at0xea958 branches to
  malloc_usable_size in this build; no allocation headers are read by this audit.
- `ijl_calloc` at0xeb630 checks the SSIZE_MAX/product boundary, then delegates the
  product with count1 to counted_calloc. The latter uses calloc, then the same
  success/current-task condition, usable bytes and **malloc** counter (no separate
  calloc field). Do not extrapolate a portable zero-size calloc policy from this path.
- `ijl_realloc` at0xeb688 reads old usable size for non-NULL input, else old0, and
  calls counted_realloc_with_old_size at0x100598. After libc realloc, non-NULL result
  plus current task is required. It reads new usable size, adds new-old to allocd
  only for new>=old, increments realloc even for same-size/in-place success, and
  accounts shrink separately as freed pressure. Failed nonzero-size realloc adds
  neither allocation bytes nor event; the old block remains live under realloc's
  contract. A NULL result for size0 is not an accounting proof of retention/free.
- `jl_free` is exported directly by **libjulia-internal**, at0xeb658; there is no
  inspected `ijl_free` body or libjulia `jl_free` stub. NULL is a no-op. Otherwise it
  reads usable size and enters counted_free_with_size at0xfe258, calls free, then
  adds free_acc only when a current task exists. This route does not increment
  `freecall`. The latter has other producers (e.g. managed-memory sweeping), and
  cannot be read as a complete SuiteSparse free count.
- `ijl_get_current_task` at0x761c8 obtains pgcstack and returns NULL when absent;
  this establishes the no-current-task bypass. It is not a sampled M thread state.
  Counted wrappers may call maybe_collect before recording success; allocation can
  induce Julia GC. The separate alloc_acc batching threshold16KiB is heap-pressure
  bookkeeping, not the granularity of the allocation-byte counter.
- `ijl_gc_num` at0xfdb30 copies global statistics and calls combine_thread_gc_counts
  at0xf3270 with update_heap0. Source and instructions sum non-NULL registered TLS
  counters; it is not a per-factor or per-callback snapshot. `allocd + deferred_alloc
  + total_allocd` reconstructs allocated-byte traffic across GC counter resets.
  `free_acc` enters freed, which GC_Diff does not use for bytes. Concurrent registered
  threads can contribute; single Julia/BLAS execution settings are not a universal
  attribution guarantee. Unregistered/no-current-task paths can be omitted.

## Mapping to the preserved M fields

`reproduce/hh_symbolic_cost.jl:26,40–44` stores the six fields below. It saves aggregate
stats, not individual malloc/realloc/freecall components. Its `runbatch!` calls full
GC before a measured batch, then runs the same @timed batch helper as warmup. Native
Info reads, endpoint solves, fingerprints and checkpoints occur outside that helper.
No new samples or numerical calls were made to establish this mapping.

| M field | Installed producer / units | Includes under the traced route | Excluded or unresolved |
| --- | --- | --- | --- |
| bytes | GC_Diff.allocd = delta(allocd+deferred_alloc+total_allocd), bytes | Julia allocation plus counted native usable-size malloc/calloc and positive realloc growth | Frees do not subtract; shrink not negative traffic; direct libc/other uncounted paths omitted; historical split UNKNOWN |
| allocations | delta(malloc+realloc+poolalloc+bigalloc), events | Successful counted malloc/calloc and realloc, plus Julia pool/big allocation | Not every attempt, not frees, not uniquely native or Julia object count; historical components not saved |
| gc_seconds | delta(total_time)/1e9 | Runtime GC time in counter bracket, including GC triggered by counted native requests if it occurs | No allocator-only duration; explicit prebatch/checkpoint GC outside; old M zero stays zero |
| seconds | time_ns elapsed/1e9 around batch expression and timer teardown boundary | Batch refactors and in-window runtime/native/GC work | External GC, endpoint/audit work and whole object lifetime excluded; not kernel-only attribution |
| compile_seconds | cumulative compilation counter difference/1e9 | Reported compilation within its own macro bracket | Not whole-process setup or proof of no earlier specialization |
| recompile_seconds | cumulative recompilation difference/1e9 | Reported recompilation within its own macro bracket | Not native allocation attribution |

The allocation snapshot begins before time_ns/compile bookkeeping and ends after
teardown, while elapsed time is captured at the start of teardown. The brackets are
not perfectly identical. Equal helper/counter overhead in M does not turn them into
pure native-kernel measurements. Freed memory, reusable blocks, pointer ownership,
allocator metadata and OS release require other evidence; no subtraction of RSS,
Info sizes or graph sizes can fill those gaps.

## Clarification for readers of M

Read M's labels “Julia bytes/events” as **values of Julia's aggregate GC allocation
counters**, which can include GC-counted native allocation. Do not interpret the
labels as exclusively Julia-managed object/array/wrapper allocation. M already states
that the counters do not measure all native malloc/free traffic; this clarification
makes inclusion as well as exclusion explicit. Neither the total native fraction
nor the symbolic-only fraction is identifiable from the saved aggregates. No revised
performance ratio or new measured improvement is asserted.

## Work, validation and continuation

No production/test/CI change, runtime calls, GC, hooks or numerical tests. Numerical
behavior is unchanged. Only read-only ELF/source inspection and offline Python checks;
no unnecessary production work, allocation or retention introduced. Failed exact
source URL gc.c (404) and empty guessed free selectors are preserved. Versioned source
and installed evidence are separately identified; no runtime launch or retroactive pin.

Choose ONE remaining S4 roadmap obligation: define an inclusive fixed-basis-history
lifecycle cost contract, because M deliberately excluded explicit GC and only timed
repeated refactors of symmetric bases. The separate S4-P source-only contract plan
must freeze a genuinely new nonsymmetric history and all implicit work before any
future launch, without rerunning E–M or installing allocator hooks. It cannot close
native balance with RSS/GC. Broader S4/S6 gates and all previous rejections stay open.
