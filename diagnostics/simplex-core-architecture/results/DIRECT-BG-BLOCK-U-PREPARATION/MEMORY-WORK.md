# Task1 complete storage ledger — source accounting, not runtime acceptance

Scope: final block-upper.jl only, with23 vector-valued fields and4Int fields. No manager, basis solve, native call, factorization, cache or update-history code is implemented in Task1. The accepted spec remains frozen. This ledger fixes operational details for later source review; it does not waive its fixed gates. All structural tests remain UNEXECUTED.

## Retained storage: every field/container

Let C=sum(length(values[s]),s=1:S), R=sum(length(rows[r])), K=length(slab), D=length(values), S=slabs, n=dimension. D includes unassigned directory spare cells; K includes free and unused descriptors. The candidate never uses push!/resize! for these buffers; length is its requested initialized backing extent. Any runtime allocator overreservation/rounding is an additional physical-heap term, not silently assumed zero. Free extents/row holes and scratch remain owned until replacement/refactor.

| Fields | Containers | Element payload |
| --- | ---: | ---: |
| values,row_ids,row_backs outer directories | 3 | 24D |
| their initialized slabs | 3S | 16C (8value+4row+4back) |
| slab,start,capacity,count,column,prev,next | 7 | 28K |
| row_order,row_position,column_order,column_position,column_head,column_tail | 6 | 24n |
| rows directory | 1 | 8n |
| rows children | n | 4R |
| gap_first,gap_length | 2 | 8n |
| bins | 1 | 128 |
| scratch_value,scratch_row,scratch_back | 3 | 528 |
| containing object:23refs+4Int | 1 | 216 under recorded64-bit field model |

Total element payload P=16C+4R+28K+32n+656; outer pointers8n+24D. Number of Vector objects V=n+3S+23. Exact symbolic reachable-graph ledger adds the Array/Memory header contributions for all V vectors, struct216, and any shared-empty-memory deduplication. Installed summarysize.jl recursively charges the Array object and GenericMemory header2*sizeof(Int) plus its data. Saved old per-array graphs are payload+40B; recorded64-bit Array24+Memory16 model gives G=P+8n+24D+40V+216 when those child memory owners are distinct. Empty/shared owners can reduce that graph term. This is not malloc byte size, allocator alignment, native memory, process RSS or peak. Physical live storage additionally includes allocator/header/alignment/page retention terms for each allocation, unknown without later authorized measurement; no invented hard physical bound is claimed.

The source owns separate mutable buffers, including the zero-length rows; copy duplicates all requested capacities. Directory spare references stay unassigned and are never read or copied as objects. No shadow CSC, per-entry column IDs, 64-bit per-entry links, retained input CSC or diagnostic ledger exists in BGBlockUpper. Float64 values appear once, apart from the fixed33entry edit scratch and transient copy/refactor overlap.

Initial C=R=m, D=S=1 for m>0, K=sum(ceil(coldegree/32)); for m=0, D=S=K=0. Scratch/bins/maps and n empty row objects still exist for m=0; no fictitious zero-cost empty object claim. Construction has23+n+3S explicit Vector allocation requests plus one BGBlockUpper, regardless of column fill. Runtime allocation events/JIT/boxing can differ and are unmeasured. Original redundant20m initialization bytes were removed: import slabs and row children are allocated undef and filled completely before return; input CSC is never changed. Metadata/scratch initialization remains required by private construction/invariant semantics.

## Saved-fixture arithmetic and stopping condition

budget-final.json lists all8initial cells and88saved checkpoints. Initial modeled U graphs: sparse32=6652B; dense32=15952B; sparse96=16124–16180B (column-degree distribution unknown, K96–98); dense96=108112B. The exact m values are saved exported-slot live counts, not input matrix nnz. Dense full triangular shapes imply K32/192 under the accepted source model. Sparse K is a range even when its endpoints coincide.

Replacing only old U storage gives conditional initial whole-factor estimates10516/27256/26132–26188/189560B, respectively. For dense96 the unchanged1.10reference threshold is190467.2B:907.2B remains under this model. Future manager/header/cache differences and capacity reserves can consume it. Later checkpoints use optimistic C/R/K minima; they are NOT upper bounds, actual candidate trajectory or proof of success. If future field/source facts yield a proven lower-bound failure, stop before numerical admission. Current accounting does not prove such failure.

Original budget.py/budget.json FALSE are preserved: they incorrectly carried the initial slab m across post-refactor checkpoints. Canonical budget-final.py resets the segment to its freshly rebuilt m/K after each refactor;15offline checks PASS. No measurements or old checker were repeated. Original false arithmetic is not retroactively accepted. The final budget pins can precede later test-only strengthening; source-bindings/source-check records bind the final texts explicitly.

## Reserve and transient coexistence

- Row growth: required+min(8,max(1,oldcapacity÷8)); allocate new4Rnew bytes plus one Vector/Memory before publication, while old4Rold remains. Copy d live handles, initialize only gap=Rnew-d zero cells and repair only the moved suffix d-rank+1 reciprocal backrefs; prefix physical offsets are unchanged because growth is entered only when the old gap length is0. Partial reserve success can retain unused capacity if a subsequent reserve fails, but all live values/order/index relationships remain. No whole-update capacity rollback promise.
- Descriptor growth: max(required,Kold+max(Kold÷2,8)); seven private new vectors coexist with all seven old vectors. New request28Knew, copy28Kold and zero28(Knew−Kold), plus7headers. All seven publish together after allocation. Existing descriptors/handles keep IDs. Scalar checked arithmetic validates Knew*32 before allocation.
- Directory growth: Dnew=max(required,Dold+max(Dold÷2,1)); three new directories request24Dnew, copy3S references (24S bytes); old directories24Dold coexist, and referenced coefficient slabs are shared during this temporary directory copy, not copied or charged twice. Unassigned spare entries contribute pointer storage but no objects.
- Slab append:3new vectors of256entries request4096payload bytes plus3headers. Create8descriptors and free-bin links after all allocations; choose the known new bin32 head without a second free-bin search. Existing coefficient slabs are untouched. If descriptors grew successfully before a later allocation fails, unused descriptor capacity can remain; no leaked live handles.
- Relocation: existing block's new extent comes from a free block. Its old extent is returned using the donor descriptor; no fresh descriptor merely for a swap. At most31live tuple copies to the new extent, then clear the old extent. Descriptor/slab reserves are additional and preflighted. Extent exchanges preserve existing encoded handles.
- Copy: full old G plus full new G (all holes/spare initialized descriptor cells/row capacities/scratch), no shared mutable child. _bgu_new(clear=false) avoids redundant clear-before-copy. Every inner buffer is copied once; top-level metadata copied once. Native/lower/history/cache state is absent Task1 and must be added in Task2; do not advertise this as full-factor copy peak.
- Refactor: absent Task1; Task2 must count old U+new U and fresh backend/export/normalization/manager temporaries. Refactor resets slab/row/descriptor highwater to the new export, not original run's m. Old saved factor copies remain additional owners.

Complete source-owned coexistence is current retained storage plus new row/descriptor/directory/slab requests along the reserve chain; objects already published as reserve are included in current storage, not double-counted. OS retention/native heap/JIT/GC roots and test snapshots are outside this bound.

## Work per operation

| Operation/frequency | Traversals/copies/writes and scaling |
| --- | --- |
| Initial build/setup | O(n) CSC pointer pass/K count; O(n+m) q/strict-row validation and degree count; n row allocations; stable-cid O(n+m) fill, final n gap normalization; no sorting, generic insertion or packed intermediate. Input m coefficients read for fill once;3m tuple elements+ m row handles written once, plus descriptor/map initialization. |
| Find, generic set | Linear scan of the selected row until stable cid; an absent nonzero generic set also scans the selected column for its predecessor. O(degree(row)+degree(column)); this is NOT the future elimination hot route. |
| Direct insertion cursor | O(1) neighbor checks with rank/predecessor from Task2, plus reserves, gap movement and block edit. No scan from row or column start; row handles must be reloaded after structural edits. |
| Gap move | One handle moved and one reciprocal row_back repaired per crossed live entry. Zero-gap cursor reposition is scalar only. Row growth adds full-row copying above. Repeated fill has worst-caseTheta(f*d+f²) lifetime copies under capped reserve. |
| Existing-value replace | One value store after lookup; no structural movement. Exact-zero assignment deletes; imported zeros/signed zeros are retained until reference-equivalent mutation. |
| Nonfull insert | Up to31old tuple moves, each3scalar writes plus reciprocal handle update; one new tuple. Relocation may additionally copy up to31old tuples and clear its old extent; these costs compose, not a single32move bound. |
| Full32 split | Stage33tuples in fixed scratch, then33final tuple writes and33row-handle repairs; clear31unused tuple slots across two32extents. Count staging reads/writes separately; no full-column/arena copy. |
| Delete+optional merge | Up to31tuple shifts and one deletion clear, plus one merge staging/writing at most32tuples with reverse handles. Aggregate old moves<=63. Clear keep suffix (at most30) and dropped extent (at most32); those are extra bounded stores, not moves. No cascading merge. |
| Adjacent swap | Merge two row sequences O(da+db); two tuple reads/writes and two reciprocal repairs per common column; four map assignments. Single-row occurrences need no tuple movement. |
| First→last row rotation | For each occurrence in moving row, visit every crossed column entry and shift tuples, then one carried write; O(affected interval entries+row degree+map interval). No singleton blocks or full-U rebuilding. |
| Copy | O(C+R+K+n+D), all requested payload once; allocate23+n+3S vectors plus object. Directory loop copies live child owners into newly allocated independent buffers, not old child aliases. |
| Full invariant/materialization | TEST ONLY scans all descriptors/extents/rows and builds sets/owners/matrix. No calls from candidate; real cost/memory excluded from timed kernels and must remain outside future timing. |

Deterministic clearing of freed extents/split suffixes is not required to release Float64 objects (they are bits), but prevents stale data in copied free capacity and simplifies deterministic structural diagnostics. It is explicit potentially avoidable bounded overhead, not zero-cost or a speedup claim; no unreviewed removal or post-measurement tuning. Candidate commit paths contain no explicit allocation requests after pre-reservation; Julia specialization/tuple-splat/boxing behavior remains UNQUALIFIED until an admitted run. Dynamic Python test models were not used as a substitute for Julia execution.

## Structural test coverage and scope

Named tests cover empty/import, nonidentityq, reciprocal handles, gaps, direct cursor/malformed CSC, split before/interior/after32, swaps/rotations across32, retained-right merge with q, every explicit allocation refusal, synthetic and real maximum widths, signed/explicit zeros/NaN/Inf, repeated fills, fragmented highwater and independent copies. Full logical values and structural invariants are compared after mutations; no reliance solely on mirroring implementation metadata. Failure loops enumerate explicit allocator requests using a control call, then inject each refusal on a fresh structure; this does not prove arbitrary runtime OOM/boxing failure behavior. Runtime assertion count remains unqualified and will be frozen by Task3 after exact source review; static @test count is not an executed count.

No new production work or memory is introduced. Prospective candidate overhead (headers, gaps, descriptor/slab slack, linear generic lookup, bounded movement and additive growth) is fully assigned above, not certified harmless. No test or benchmark was run, and no numerical acceptance follows from this ledger.
