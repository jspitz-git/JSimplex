from pathlib import Path
import json,hashlib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-SPLIT-ADAPTER-PREPARATION';O=E.parent/'DIRECT-BG-BLOCK-ADAPTER-PREPARATION'
ren=[('BlockBGFactor','SplitBGFactor'),('BGBlockUpper','BGSplitUpper'),('_block_bg_','_split_bg_'),('_bbg_','_sbg_'),('_bgu_','_sbu_')]
s=(O/'MEMORY-WORK.md').read_text()
for a,b in ren:s=s.replace(a,b)
s=s[:s.index('Alias review correction:')]
a=s.index('Task1\'s eight initial');b=s.index('## Test-only work',a)
s=s[:a]+'''The old block candidate's graph margins are historical evidence, not a bound on this new allocator. No numeric graph prediction from that candidate is promoted here. Task1's new ledger and integer geometry model govern split-storage costs. The eight manager fields/base/cache/history types are unchanged; this proves zero additional adapter fields, not a passing memory gate. Fragmentation, row gaps, high-water K/D and slab retention remain unbounded relative to live count. No initial or final-only graph can replace every intermediate checkpoint.

'''+s[b:]
s+='''
## Demand-sized allocation delta (Task1, applied to every update)

This ledger incorporates the unchanged Task1 MEMORY-WORK.md and its complete payload/header/backing and failure/coexistence terms. A free request adds at most6 target-class comparisons then at most32 bin-head reads. Exact fit adds no descriptor. A larger donor adds one initialized descriptor and constant link writes, with no coefficient copy/clear; if capacity must grow, seven new arrays request28*Knew bytes, copy28*Kold, and temporarily coexist at28*(Kold+Knew), plus14 old/new headers. New slab append requests4096 bytes in three256 buffers plus descriptor/directory growth; a subsequent split can trigger a SECOND descriptor growth. Do not fuse their charges.

Active growth preserves ID/handles but copies the old prefix and clears the old extent, each at most31 cells. Monotone growth1/2/4/8/16/32 moves/clears1+2+4+8+16=31 old cells; deletion/merge/refill breaks this lifetime bound. Free split can reduce future C/slab requests, but increases used/K partitions and may increase moves and clears compared with direct growth to32. Nonpower remainders and the no-coalescing rule can strand ample free space. There is no saving guarantee and no O(live) retained-memory bound. The source Task1 empty40x40 column schedule predicts52 allocator callback requests/5048 requested payload bytes/224 copied descriptor bytes/31 relocated and cleared tuples; these are offline predictions for that exact sequence ONLY, not the new differential schedule, real allocations or elapsed time.

Task2 adapter has ZERO changed numerical loops, additional basis solves, full scans, cache fields, or per-RHS scalar conversions relative to its exact renamed block parent. Existing O(n+live entries+blocks+compiled history) work, dirty-column scan, diagonal fallback scans, cache first-use allocation and alias handling remain. Full scans in test oracles are excluded from any future timed candidate. Smaller capacities may change block counts/traversal and cache locality through the U trajectory; source equality is not equal runtime cost.

## New Task2 differential schedule budget (prospective, not execution)

Two new controlled storage pairs, each with one packed constructor and one SplitBG constructor, total4 genuine native factorizations of identity40 plus4 controlled exports; normalization disabled for these storage-only comparisons. These are not true factors of the substituted M and are NEVER solved. Their additional work is separate from seven unchanged fixtures/both backends. No new cost fixture is introduced.

First pair:128 paired scalar assignments (32fill +1second-column +1split33 +16delete +16refill +33clear +9refill). Second pair:21 paired scalar assignments (7tail growth +14delete/refill),3 paired rotations of lengths34/16/40, then one paired source/target row merge (at most39 trailing columns). Each scalar assignment calls one packed helper and one split helper followed by complete tokens/partition checks; no backend solve. Total149 paired scalar assignments,3 rotations,1merge plus explicit capacity checks. The count includes every refill, but allocator request/actual live movement depends on state and is UNEXECUTED. Whole token/invariant checks allocate test-only arrays and scan O(n+C+R+K) per assignment/rotation; fixed-size40 test arrays, trace vectors, snapshots and test result storage are additional. No observer enters candidate kernels.

Inherited tests enumerate setup/copy/refactor allocation refusals over every requested U allocation and require preserved old owners/state. Failed update tests permit earlier edits, require invalid prepared destinations/no success history and refactor before reuse. Task1 separately covers every7-array split failure and row-reserve publication preceding split failure. This composition is source-supported, not an executed cross-product proof of all possible update failure locations. Later Task3 must freeze actual new assertion trees and exact conditional setup/copy/refactor/probe budgets before a run. This Task2 does not create a driver, infer backend-internal work from outer calls, or authorize Julia.

Unnecessary-work review: no avoidable new adapter work/memory was introduced (whole-file rename inverse). The required demand-sized allocator adds target selection, descriptors and possible repeated relocation by design; their cost may outweigh slab savings, especially dense/fragmented cases. Retaining whole original safeguards and arithmetic takes priority. Independent review must assess these costs explicitly; benchmark acceptance is deferred to Task3 under unchanged gates.
'''
with (E/'MEMORY-WORK.md').open('x') as f:f.write(s)
s=(O/'SOURCE-MAP.md').read_text()
for a,b in ren:s=s.replace(a,b)
# Keep historical mapping explicitly as lineage, not false new derivation.
s='''# Task2 three-way numerical source lineage

The table below is the inherited packed numerical-contract map, with only new private identifiers substituted. Exact NEW split-bg.jl inverse removes five identifier renames and reproduces frozen block-bg.jl byte-for-byte. The accepted block adapter's adapter-inverse-reviewed.json additionally reverses all23 explicit edits and identifier renames to its frozen dynamic-bg-reviewed.jl parent. The new source checker verifies both complete inverses without running any old script. Direct packed comparator and lower/export helpers are byte-identical in the new81file stage. The mapped packed branches are separately pinned and reviewed; a textual inverse is provenance, not a runtime equivalence proof.

'''+s[s.index('| New helper/group'):s.index('Ordinary overlay copies')]+'''
New overlay starts from the complete frozen81file block Task2 stage, verifies its membership/hashes, and substitutes five split source/test files plus the two root include names. It retains packed DIRECT BG and genuine lower/export helpers. All other75 paths are byte-identical. Task1 source/oracles/tests remain frozen and are copied byte-exact. fixtures.jl remains byte-exact. No old block candidate remains included or compared numerically. prepare-adapter-overlay.py is a new one-shot text builder; no module is imported.

The new test module preserves every inherited statement under explicit renames, then inserts two allocator-sensitive testsets and a single new entrypoint call. tests-first.json records the exact inserted section and the pre-adapter hash. Whole inverse removing that section/call and undoing renames reproduces the frozen original tests. The original7fixtures/botharms/prepared entering+DSE/copy2/refactor4,8/exception/alias/failure/oracle bodies are retained. New storage-only controlled pairs do not claim valid solver witnesses or call solves after arbitrary mutations.

Runtime-text inventory binds installed Base abstractarray.jl,array.jl,boot.jl for the inherited shared-Memory alias construction and graph-layout discussion. These are read-time source bindings, not actual loaded-path evidence, launch pins, parser/ABI/dispatch validation or native ownership proof.
'''
with (E/'SOURCE-MAP.md').open('x') as f:f.write(s)
with (E/'REPORT.md').open('x') as f:f.write('''# Task2 SplitBG adapter and differential preparation

OFFLINE PREPARATION; Julia tests and candidate remain UNEXECUTED. Current user explicitly authorized Task2 implementation as isolated text and independent review, while forbidding Julia. No Task3 driver/launcher, actual src/test/env/CI/master/STATUS/roadmap change, old checker rerun or numerical allowance.

New SplitBGFactor consumes the frozen accepted BGSplitUpper. Five identifier substitutions are the entire adapter difference from frozen block-bg.jl; numerical loops, policies, export, normalization, fallback, prepared direction provenance, failure order and safeguards are unchanged. All inherited differential tests compare packed DIRECT BG with SplitBG, and two additional storage-only testsets exercise demand growth, split33, suffix reuse, refill, imported nonpower tails, rotations and row merge. All fixtures remain fixed. Tests were saved before adapter creation.

MEMORY-WORK.md inventories retained owners/backing/header terms, cold setup/copy/refactor coexistence, every hot path and allocator delta. Less slab capacity can cost more descriptors and relocations; no speedup, allocation reduction, graph limit, syntax or correctness acceptance is claimed. Task1 structural failure coverage is reused by source binding, not rerun. New ordinary81file stage is text-only and not a launch admission. SOURCE-MAP.md records exact two-hop parent inverses and packed numerical branch mapping.

Independent review and final closure are recorded in separate files. Next possible user-requested work is Task3 offline driver and concrete admission preparation; runtime counts and every launch require a fresh exact review.
''')
print('Task2 ledger, source map, report written')
