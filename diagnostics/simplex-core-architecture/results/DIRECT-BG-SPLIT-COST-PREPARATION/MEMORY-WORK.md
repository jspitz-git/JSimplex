# Complete scoped work and memory ledger

## Explicit numerical call sites per completed process

|Work|160 timed lifecycles|8 triple probes|8 policy preflights|Total|
|---|---:|---:|---:|---:|
|construction|160|24|16|200|
|refactor|320|48|32|400|
|replacement|1280|192|0|1472|
|FTRAN|2560|384|0|2944|
|BTRAN|1280|192|0|1472|
|factor copy|0|0|0|0|

These source counts are not complete observed backend/native attempts:600 factorization entry sites, lower solves, normalization/export, backend initialization and fallback internals are additional.4416 stored output vectors receive exact residual comparisons (3840windows+576probes). No public solve/workspace/certificate.70explicit clock reads/35intervals/six48Bclock buckets per timed lifecycle; one symmetric clock allocation. Output destinations24*n Float64 elements per cell live outside both windows. Tokens/residual matvecs/graph scans/serialization occur after each window; no old factor owner or growing window ledger retained.

## Structural work outside timing

Four schedules, no factorization/solve/copy:64row sets;8explicit capacity4 reservations/claims;32monotone sets;1capacity3 reservation/claim plus241sets (one delete then3*80fill/drain). Total337sets and9explicit reservations/claims, with additional reservations inside sets.349 complete invariant checks:64+9+33+243. Logical value checks64+sum(1:8)+sum(1:32)+3*40=748 scalar checks in structural loops.51 full storage snapshots from new schedules (9+33+9), plus final row-growth storage;64 row-growth scalar/counter snapshots. Fragmented schedule checks invariants every operation but only saves initial/claim/delete/full/empty endpoints. Setup helpers are source-exact copies; their explicit zeros/empty row allocations are outside reset operation counters and are not called zero-work. Initial storage records them; source helper work O(n+C+K), accounted as untimed diagnostic setup. None is a performance cell.

83 fixed probe counters include target calls/comparisons and six target bins;32 remainder-capacity bins; free split/exact-fit/new descriptor IDs; slab/directory/row/descriptor allocation requests and requested payload; descriptor copied/new payload and maximum old+new coexistence; relocation count/live tuple copies/old capacity clears; existing tuple/row-handle/back repairs, gap/deletion/insertion/merge/split/rotation movement. Counts measure source requests/logical operations, not physical malloc events or CPU instructions. Allocator payload uses Base.elsize(Vector{T}) including pointer elements. Counter Dict/header are global only to the separate diagnostic type, not a field in measured factors.

Repeated4 on32slots:7splits+1exactfit, remainders28,24,20,16,12,8,4;C32 unchanged,K16,8useddescriptors, rowR16, targetcomparisons24,bininspections120. Monotone32:targets1/2/4/8/16/32,5relocations,31old tuples copied and31old capacity cells cleared. Fragmented initial16*3slots:C48,K16;first required3→target4 appends256, descriptors16→24→36, used25,C304, copiedmetadata28*(16+24)=1120B,newmetadata28*(24+36)=1680B,maxmetadata coexist1680B. These are prospective source-derived oracles, not measurements.

## Complete storage accounting

C=sum slab lengths,R=sum row buffer lengths,K=seven descriptor array capacity,S=slabs,D=outer directory capacity. Core element payload16C+4R+28K+32n+656; outer pointers8n+24D. Every checkpoint includes live/free/active-slack partition, every used descriptor's slab/start/capacity/count/column/links,32bin heads,ncolumnheads/tails, all23top vectors+3Sslab children+nrows, logical AND actual GenericMemory backing lengths/bytes, upper and whole factor graphs. Auditor independently requires no holes/overlap, exact slab partition, used<=C, every descriptor reachable once in matching free/active chains, live/free/slack totals. Runtime full invariant checks additionally verify tuple order, row handles, backlinks, zero padding, maps and unused descriptors.

Additional to element payload:27-field struct/scalars, Array/Memory headers/backing spare capacity, lower factor/backend, work/spike, prepared/row caches, update/recycled histories. Do not sum overlapping per-array graphs:Base.summarysize of the entire factor deduplicates reachable owners. Graphs are not malloc sizes/native heaps/RSS. Memory gates apply each measured final pair and each of88probe checkpoints, not median-only. Probes hold3factors+72*n output elements per cell; detached metadata/state dictionaries remain bounded at11percell. Full checks may sort maps O(n log n), traverse O(C+R+K+history), and allocate sets/owner vectors; column value checks may scan incidence rows. All diagnostic overhead is outside windows but within guard RSS/time.

Descriptor growth copies28Kold and zeroes reserve; coexists28*(Kold+Knew). Row reserve copies4*d, initializes gap and repairs suffixbacks; coexist4*(old+new). Directory growth copies24*S live pointers, coexists24*(Dold+Dnew). Slab append initializes4096B+metadata/directories; no old slab copy. Relocation copies live tuples, preserves descriptor handles, clears old capacity, may require allocation/gap/descriptor work.33rd-entry split32reads33stagingwrites33finalwrites unchanged; merge and deletion retain existing work. Structural zeroing and scratch remain; no diagonal fast path, coalescing, small-coefficient omission or numerical-policy changes.

Cost schedule excludes factor copies (covered GREEN). Full copy source complexity O(C+R+K+n+D+historycontainers),23+n+3S explicit U vectors plus manager/caches; old+new entire graphs coexist. Refactor also retains old entire factor during backend/export/U creation, with native temporaries additional. Local max payload counters do not bound whole-factor peak. Process RAM/swap/RSS/VM guards capture host/process pressure, not native allocation/free attribution. No native-free, observer-neutrality, universal speedup or end-to-end claim.
