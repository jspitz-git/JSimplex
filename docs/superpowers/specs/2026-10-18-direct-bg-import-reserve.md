# Small import reserve for direct BG upper-factor tails

## Purpose, authority and existing evidence

The user requests a plan with independent review and a complete memory/work budget, without implementation or Julia. This is a new import-layout design. It does not reopen the stopped fixed SplitBG cost attempt. Diagnostic entry is a5e21e5d63cca65d8178d56dd27eb3cf0245ecfe; master is 26e2291745999f485a74f643298ca997d65c7205. All old candidates, tests, scripts, raw results and reviews remain frozen. Preserve src/test/env/CI, STATUS/roadmap, user files and existing worktrees. CI stays off, HH reuse disabled, automation paused. Later implementation follows the preserved inline workflow and a new user request.

Read-only evidence is DIRECT-BG-SPLIT-COST-PREPARATION/runs/cost1-300 and DIRECT-BG-SPLIT-COST1 under diagnostics/simplex-core-architecture/results. All eight cells passed correctness; six failed the collective performance gate. No numerical retry or second process follows from this plan. Selected source identities must match that run's sealed inventory; new read-time evidence is not a retroactive launch pin.

Stored nested clocks localize the largest sparse regression to updates: median paired excess update time per eight-update lifecycle is 8.9/10.6 microseconds for sparse32 native/Markowitz and 19.0/24.7 for sparse96. Stored untimed source-inverse probes count 90/91 and 146/171 occupied-block relocations respectively. The first update accounts for 32/33 and 96/97 relocations. Import currently sets capacity=count; short two-entry columns therefore migrate on the first insertion. This is a source-supported cost mechanism, not instruction-level timing attribution. Additional solve indirection and row-gap growth remain. Sparse32 median paired aggregate increases are 1408/832 bytes and 49/66 events; source allocation requests do not equal GC allocation events.

## Scope and chosen policy

Use a distinct private Float64/Int diagnostic type BGReserveUpper and ReserveBGFactor{F}. Derive from frozen BGSplitUpper/SplitBGFactor with exact type/helper renames. Change only initial upper import and a pure capacity helper. The free-block allocator, row-gap growth, descriptors, bin search, slab size, numerical operations and solve loops remain byte-inverse after renaming. No bulk replacement, coalescing, diagonal cache, solve fast path, metadata preallocation, broad bounds-check removal or backend/policy change.

For the final positive-length block of each imported column only:

| Live entries t | Reserved capacity h(t) |
|---|---|
| 1 | 2 |
| 2 | 4 |
| 3 | 4 |
| 4 through 32 | t |

No extent is created for an empty column. Interior full blocks remain 32. A column of length33 has capacities[32,2], length34[32,4], length35[32,4], length36[32,4], length64[32,32]. These examples concern representation only, not new LP fixtures. The rule is based on tail length, never a fixture label, backend, measured result or matrix dimension threshold.

Alternatives: pre-reserving all tails to32 repeats the already rejected excess-capacity problem; growing rows or optimizing solves simultaneously prevents isolating the import mechanism. Bulk spike construction targets a different route and is excluded. The proposed 2/4/4 rule adds at most two slots per nonempty column, preserving the coefficient access pattern while potentially avoiding early reservation/copy/clear cycles. No promised speedup or allocation decrease.

## Exact import contract

Future interfaces: `_rbu_import_capacity(t::Int)::Int` accepts1:32, otherwise ArgumentError; `_rbu_build_with(A::SparseMatrixCSC{Float64,Int},q::Vector{Int},allocate,limit::Integer)::BGReserveUpper`; `_rbu_build(A::SparseMatrixCSC{Float64,Int},q::Vector{Int})::BGReserveUpper`. Existing private APIs become `_rbu_*`; adapter helpers `_rbg_*`, factories `_reserve_bg_*`. No dispatch is added to frozen types.

Let m=length(A.nzval), K0=sum(cld(column_nnz,32)) and Delta=sum(h(t)-t) over nonempty column tails. Initial coefficient capacity C0=m+Delta, used=K=K0, R=m, D=S=1 when m>0 and zero otherwise. Zero entries explicitly present in CSC still count toward m and the tail; preserve every value bit including signed zero, row order and current exact-zero insertion/deletion semantics.

Compute K0 and C0 with checked arithmetic during the existing column-pointer validation pass, without an extra full coefficient scan. Compute C0 and all descriptor/handle/start/end conversions with checked arithmetic before allocation/publication; do not retain the old assumption m bounds every physical index. Since every capacity is at most32, C0<=32*K0: the existing checked32*K0 limit already dominates padded capacity. Preserve that check and input CSC/q validation order; do not invent an input where paddedC exceeds the limit while32*K0 fits, or add repeated per-coefficient capacity checks. Reject checked-size/handle-limit failure before importer buffer allocation. New physical cursor arithmetic is checked at block boundaries, retaining the original valid-input numerical exception contract.

Allocate the same three coefficient arrays once at C0, not at m followed by resize/copy. Fill live tuples directly from the input CSC into the final layout. Build in the existing stable-column-id traversal; a separate checked physical cursor advances by capacity, while the CSC source cursor advances by count. In particular, nonidentity q means physical starts must no longer be copied from the CSC source offset. Initialize all added slack cells to value+0.0,row_id0,row_back0 without first zeroing and then rewriting all m live tuples. Set count to t, capacity to h(t), and the next descriptor start after all reserved slots. Each live tuple still receives one write and reciprocal row handle. No new per-column temporary arrays, padding vectors or copied CSC are allowed.

The added cells belong to their active extent and are not free-bin entries. At import free_capacity=0, active_slack=Delta, live=m. Positive extents exactly partition [1,C0] with no overlaps/holes; unused metadata owns no extent. Handle encoding (descriptor,offset), stable rows/columns, row back-references, maximum block32, append slab256 and 32capacity bins are unchanged. Existing grow/delete/merge/rotate/copy operations must work on imported padded tails without special numerical branches. After mutation, Delta is not a persistent field or a lifetime memory bound.

Import constructs a private object, returns it only when complete and never mutates A or q. Allocation/overflow failure must not publish a partially built factor. Refactor retains the existing old-factor-until-complete-new-factor publication contract. Copy retains capacity and cleared slack with independent backing arrays; it must not silently compact. Failed update retains the existing nontransactional earlier-edit semantics, valid ownership/partition and invalid cache/no success publication; no new whole-function rollback promise.

Preserve normalization/export/scaling, all arithmetic and logical visitation order, prepared entering versus distinct DSE directions, pivot and finite checks, tolerance, policy, exceptions on valid-layout numerical paths, history and cache invalidation. Native threshold_one and Markowitz default only, dense Float64 vectors and Int CSC. Other types/alias contracts retain existing rejection/fallback behavior; no public solver, FT/SS/HH or general precision expansion.

## Memory budget

Representation/field count is unchanged. For actual coefficient capacity C, row capacity R, descriptor array capacity K, directory capacity D and dimension n, core payload is

`P = 16*C + 4*R + 28*K + 32*n + 656` bytes,

plus outer pointer payload8*n+24*D, all vector/Memory/struct headers and backing reserves, lower/backend/export state, work vectors, update history and prepared/row caches. Do not sum overlapping array graphs as a factor graph. Julia reachable graph, aggregate allocation traffic, process RSS and native allocator retention are distinct measures.

At import, 0<=Delta<=2*n, so the new coefficient payload is exactly16*Delta<=32*n bytes beyond the same unpadded input. Three coefficient allocations still occur when m>0, with larger lengths; no additional allocation requests, descriptors, directories or row buffers are introduced by this policy. This is a source request budget, not a guarantee of equal GC events/physical bytes. Cumulative extra import payload for three lifecycle imports is16*(Delta0+Delta4+Delta8), bounded96*n for fixed n. It is not the net lifecycle allocation delta: subsequent growth and GC behavior can differ.

Old and new factors coexist during refactor. The import-headroom contribution can be up to32*(n_old+n_new) bytes, or64*n at equal dimension, in addition to both complete existing graphs, source matrix, normalization/export arrays and backend temporaries. Later mutations may change fragmentation, descriptors, row capacity or slab append counts; neither this contribution nor the unchanged field count caps full peak memory. Copy has two complete capacity graphs and no compaction credit. Track native memory separately and do not claim native-free proof.

Stored import checkpoints permit arithmetic illustrations, not future measurements: initial sparse32 Delta61/63 ->976/1008 additional payload bytes; sparse96 Delta189/191 ->3024/3056. The same fixed rule adds64 bytes to dense32 and192 bytes to dense96 at each stored import. Adding only those payloads to the old dense96 graph would give about1.09587 of the reference graph, close to the1.10 gate. This excludes changed backing/allocation classes and later trajectory storage; it does NOT qualify the new candidate. Full final and all intermediate gates remain mandatory.

## Work budget and falsification

Setup/refactor: retain O(n+m) import work, same existing pointer pass and live-tuple/row-handle construction. Add O(1) tail-capacity arithmetic per nonempty column, O(K0) physical cursor arithmetic in the existing block loop, and exactly3*Delta slack scalar stores across the three arrays. No full coefficient copy/scan beyond existing import, extra factorization/solve/conversion or retained metadata. Count checked arithmetic and zero stores, including time/allocations for the larger initial buffers.

Each later occupied short block can accept the reserved one or two insertions before relocation if intervening deletion/merge/refactor does not replace that extent. No claim that all90/91 or146/171 relocations disappear. New columns still follow the existing demand-sized free allocator, and row storage remains tight at import. Its62/68 sparse32 row growths are not solved by this proposal. Lower bin/descriptor/slab pressure is a hypothesis, not a guaranteed causal allocation delta. A structural matched sequence must show a2-entry imported tail accepting a third entry without block reservation, extent migration or old-capacity clearing; row reserve remains separately counted.

FTRAN/BTRAN: no new scans, solves, caches, conversions or code path changes beyond type/helper renaming; old block/map indirection remains. Replacements/elimination/history work and arithmetic are unchanged. Deletion can expose a larger cleared extent and affect free-list selection; copy/refactor and later fragmentation must therefore be measured, not extrapolated from initial headroom alone. Do not alter arithmetic order or remove numerical safeguards to rescue cost gates.

## Future tasks and acceptance

Task1 is offline storage candidate, structural tests, exact source inverse and complete allocation/peak ledger. Task2 is the renamed BG adapter, differential tests and composition ledger. Task3 separately prepares RED/GREEN and then cost drivers; only later explicit requests and exact independent admission permit execution. No candidate, driver, launcher, Julia/query/parser/import/compile or numerical call is authorized by this planning request.

Retain all previous tests that do not assert the superseded exact-tight import contract. Enumerate every changed initial-layout assertion and replace it with the explicit C0=m+Delta/partition/zero-slack oracle; never weaken unrelated assertions. Expected RED failures must be derived from the new enumerated tests, not inherited10. GREEN must include allocation-failure and overflow/alias/prepared-cache coverage. Do not execute or modify old tests/drivers as a substitute.

Future cost reference is packed DIRECT BG, not a fresh rerun of the stopped SplitBG. Reuse the exact four sparse32/dense32/sparse96/dense96 fixtures and native/Markowitz policies. Eight updates, refactors4/8,3warm+7measured alternating pairs =>48warm/112measured windows. Whole setup/export/normalization/import/solve/update/refactor work and symmetric timers included; counters and graphs outside. Prepare new source-inverse untimed import counters plus original movement/row/descriptor/slab counters and11lifecycle checkpoints, with explicit complete output/call budgets. Saved SplitBG data is historical only, not a matched measurement of the import delta.

Each of all8 first cells: paired median time<=0.95reference, median bytes AND events nonincrease, every measured final and every probe checkpoint factor graph<=1.10reference, compile/recompilezero, all bitwise/input/structural/exact-residual checks and>=3/7faster. Preserve allGC/outliers. Exact residual bound128*n*2^-52*max(1,norm(M,Inf)*norm(x,Inf),norm(b,Inf)), correct transpose norm. Failure stops this fixed design without post-output policy/fixture tuning. A separately requested/admitted opposite-order process may follow only if all8 pass; both process gates and>=10/14faster per cell required. No production promotion from component acceptance alone.

Before every later execution: fresh host boot/start_ticks/command, all historical+new groups ANDsessions, exact refs/source/runtime/env/stage/loaded paths/command/output reservation and independent review. Julia/BLAS1,heap2GiB,VM8GiB,availableRAM>=6GiB,swap<=1GiB; initial outer300/inner292 seconds. Pure timeout may get a separately prepared/admitted600/592 run under the user's standing preference; no automatic rerun here. Planning does not consume or grant a numerical allowance.
