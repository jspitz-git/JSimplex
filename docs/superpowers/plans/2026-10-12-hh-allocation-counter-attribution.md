# S4-O: source-only attribution of SuiteSparse allocation counters

SOURCE/EVIDENCE ONLY. Read STATUS and S4-N report/review; verify fresh host full last
process groups, actual refs, user files and source/runtime hashes. No Julia, native
API calls, loading libraries, hooks, compilation, factor/workspace/solver calls,
environment changes, production/test changes, old accepted scripts or cost reruns.

The ONE narrower observable is which allocation events/bytes from SuiteSparse's
installed `jl_malloc/calloc/realloc/free` delegation can enter the **existing M
@timed/gc-counter fields**. This does not measure native live bytes or close retention.
Do not repeat N's helper ABI inventory or L/M metrics/timings.

Trace installed timing macro/GC_Diff fields and the four actual runtime entry points
using installed source/headers plus read-only ELF disassembly. Resolve forwarding
stubs to implementation where possible; distinguish source inference from runtime
capture and code for another Julia version. Use matching versioned upstream source
only for missing implementation, pin provenance/hash and explicitly state any build
uncertainty. Capture exact definitions for allocation events, requested/usable bytes,
realloc success/failure and frees; include non-GC-thread/TLS branches and arithmetic
that can make traffic counters differ from current live allocations. Do not assume
that calling `jl_*` means all native requests are represented by every M counter.

Read M's saved driver/raw records only to bind field names and timed-window boundaries.
Do not recompute performance tables or reinterpret unchanged raw acceptance as a new
measurement. Produce one mapping of field -> observed value provenance -> included
native/Julia categories -> excluded/unknown categories. If required implementation
or runtime state is unavailable, leave the category UNKNOWN rather than infer it.
Report whether M needs a separate prose clarification (preserve frozen M artifacts).

Budget: zero numerical/native calls, zero callbacks installed, zero benchmark samples;
read only the four allocator implementations, timing counter producer/consumer and
necessary directly called helpers. No general allocator survey or hook implementation.
No matrix/RHS or residual oracle applies because no factor/solve will run. Allocation
counter interpretation, not numerical behavior, is the acceptance oracle: each claim
must cite pinned actual source/instructions, or be explicitly conditional/unknown.

Fresh independent contract/work review. Record limitations and one justified next
roadmap action without automatically scheduling a hook experiment. Update STATUS and
roadmap, push diagnostic documentation only. Native retention and HH reuse promotion
remain OPEN; old accepted artifacts and all rejections remain unchanged.
