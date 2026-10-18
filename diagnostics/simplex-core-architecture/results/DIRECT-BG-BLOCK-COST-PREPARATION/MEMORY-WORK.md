# Frozen call, memory and work budget

## Numerical entry budget per completed process

| Work | Timed160 lifecycles | Untimed8triple probes | Untimed8policy preflights | Total |
|---|---:|---:|---:|---:|
| constructors |160|24|16|200|
| refactors |320|48|32|400|
| replacements |1280|192|0|1472|
| FTRAN |2560|384|0|2944|
| BTRAN |1280|192|0|1472|
| factor copies |0|0|0|0|

These are explicit source call budgets, not instrumented complete native-entry/attempt counts.600fresh factorization entry sites follow construction/refactor; lower solves, export/normalization, backend internals/initialization and possible fallback work are additional. Policies and genuine backend controls are independently sampled by2constructors+4refactors/cell outside windows. No public solve/workspace or extra residual solver is used.

Auditor exact residual comparisons:160*24+8*3*24=4416 output vectors/process. Warm outputs included. Preliminary residuals in driver are outside timing and use floating arithmetic; independent Python dyadic arithmetic is authoritative for fixed128*n*2^-52*max(1,||M||inf*||x||inf,||b||inf), correct transpose matrix norm. Explicit zero bit differences fail direct pair equality even if residuals pass.

Repeated-row-fill probe:one64x64empty storage build,64nonzero insertions into physicalrow1,64full invariant checks,64post-insertion integer snapshots,64final scalar value checks. No factorization/solve/copy/refactor. It intentionally exercises repeated capped reserve growth; it is a structural workload, not a ninth performance cell or new LP. Its storage and counters are saved in growth.toml.

## Timed and diagnostic memory

Timed factor contains unchanged production-like candidate work/spike/prepared caches/history/lower backend and exact GREEN U. One six-UInt64 clock vector per lifecycle is symmetric.24detached lengthn output destinations/cell live outside both sides' timing. Window output dictionaries/tokens/residual matvecs/full graph scan happen after timing; no old factor owners or per-cell growing row ledger retained.

Probe owns three factors and72detached lengthn outputs/cell.11checkpoint dictionaries contain only detached logical comparisons, graph numbers and array metadata; never retain old factor/slab/backend owners. Full invariant/materialization/graph traversals are deliberate untimed O(n+C+R+K+history) diagnostic costs. The immutable output tokens for4416vectors and checkpoint dictionaries consume process memory; guard RSS includes them, import/JIT and serialization. Julia reachable graph is not native memory/RSS/free proof.

U counts: C=sum actual slab vector lengths; R=sum row buffer lengths; K=seven descriptor array capacity; S=live slab count; D=outer directory capacity. Every checkpoint records live entries/blocks, used/free descriptors, free extent capacity, gap reserve, array logical lengths and *actual backing Memory length/bytes*, each array's reachable graph, upper graph and full factor graph. This includes23top vectors+nrow children+3Sslab children; pointer vectors may have backing capacity beyond their logical lengths. Array graphs overlap through directory references and must NOT be summed. Base.summarysize traverses Array/GenericMemory owners and headers with shared-owner deduplication; it is not allocator malloc size or native graph. Actual backed reserve is recorded separately so length alone cannot hide extra capacity.

Core element payload P=16C+4R+28K+32n+656; outer pointer payload8n+24D. Additional:27-fieldstruct/scalars, Array/Memory headers, backing spare capacities, lower backend, work/spike, row/prepared caches, histories/recycled histories and container headers. Source model216Bstruct and40Bper distinct Vector/Memory owner is explanatory only; actual graphs/backing records govern. No20B/live claim or hard physical heap cap. Graph gates apply EVERY measured final pair and all11untimed checkpoints, not just medians.

## Storage work and coexistence

Untimed renamed probe counts29named integer metrics: explicit allocation requests/requested element bytes (pointer elements use Base.elsize), tuplewrites/row-handle repairs/back repairs, gap moves, row growth and copied bytes, descriptor/directory growth and copied bytes, slab appends, maximum row/descriptor/directory old+new payload coexistence, merge staging reads/writes/moved tuples, deletion/insertion/extent/swap/rotation moves, split32reads/33stagingwrites/33finalwrites. Counts describe logical tuple/request operations, not machine loads/stores/native allocation events. The fixed Dict overhead belongs only to the untimed probe; no counter method overrides timed code.

Row growth copies4*dbytes plus gap initialization and suffix backref repairs, coexist4*(old+new). Repeated-fill cumulative growth can beTheta(f*d+f^2); the64insertion probe validates actual count. Descriptor growth copies seven old arrays (28Kold), zeroes new reserve, coexists28*(Kold+Knew). Directories copy24*S live owner pointer bytes, coexist24*(Dold+Dnew). Slab append initializes4096payload bytes plus descriptors/directories; old coefficient slabs remain and are never copied by append. New array requests include their full new payload, while runtime headers/alignment/boxing/JIT are NOT inferred from requests.

Split reads32old tuples and stages33, then33final tuple/handle writes; deletion may shift31 plus one merge of32=63oldtuples. Extent relocation preserves descriptor handles and does not falsely count a handle rewrite for each copied tuple. Rotation traverses the actual interval and maps. Full import retains fixed validation/count/fill passes; no timing oracle claims those are free.

Copy is not exercised by cost schedule (already GREEN-qualified): source deep-copy budget O(C+R+K+n+D+historycontainers),23+n+3S explicit U Vector requests plus U object, copied backing/reserve and fresh manager/caches/scratch. During copy both retained graphs coexist. Refactor builds new backend/export/normalization/U privately while oldfactor graph persists; no source-derived single arena payload bounds full peak. Peak coexistence includes old+new entire factors and constructor/export/native temporaries; requested payload/local reserve maxima here do not certify physical whole-process peak or native frees. All six existing candidate numerical/safeguard/alias policies remain untouched.
