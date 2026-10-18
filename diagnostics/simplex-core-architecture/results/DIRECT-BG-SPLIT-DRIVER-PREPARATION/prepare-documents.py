from pathlib import Path
import json
D=Path(__file__).resolve().parent;O=D.parent/'DIRECT-BG-BLOCK-DRIVER-PREPARATION'
def put(n,s):
 with (D/n).open('x') as f:f.write(s)
s=(O/'ADMISSION.md').read_text()
for a,b in [('Block BG','Split BG'),('block BG','split BG'),('block candidate','split candidate'),('exactly8','exactly10'),('all8 expected failures','all10 expected failures'),('15093','15929'),('14+7 leaf groups','25+9 leaf groups'),('8faca92005efbb65ad7212222b17844a248d208a','73216b71debb99c7515b3d265702e0d68afe7064'),('all234 historical','all240 historical')]:s=s.replace(a,b)
s=s.replace('Current offline host sees foreign user Julia371680; never signal or alter it. Do not launch until a later fresh preflight is clear.','Current fresh offline host records no matching historical groups/sessions and no visible Julia. Inaccessible executable links remain a visibility limit. Never signal foreign processes; every later run requires a new clear preflight.')
s=s.replace('Source arrangement addresses the earlier world-age boundary; actual warning-free loading remains UNEXECUTED. All warnings stay in raw logs for result review.','Source arrangement addresses the earlier world-age boundary; actual warning-free loading remains UNEXECUTED. The new auditor rejects warning/world-age tokens, including on pure-timeout classification. All warning text remains in logs; no suppression.')
s=s.replace('RED runs exactly10 new','RED runs exactly10 new').replace('Expected exit1','Ten symbols are explicitly listed in red.jl and verified absent in RED75/present in GREEN81; the new target/reserve/copy contracts are included, no inherited8-count assumption. Expected exit1')
put('ADMISSION.md',s)
put('MEMORY-WORK.md','''# Prospective work and memory — SplitBG RED/GREEN driver

All Julia text is UNEXECUTED. The new driver changes no candidate, frozen test, fixture, numerical safeguard, policy or actual src/test/env. RED checks10private missing contracts and calls no factor/solve/update. GREEN runs25structural +9adapter leaf groups,15929prospective Test assertions. Internal invariant @assert loops are extra work and can fail the enclosing Test group; they are not counted as Test outcomes. derive-counts.py and assertion-derivation.json are source arithmetic, not runtime proof.

## Call and traversal budget

work-ledger.json gives reference/candidate API attempts: constructors55/125,refactors62/153,copies13/77,FTRAN384/400,BTRAN144/160,replacements118/135. It preserves the inherited per-group counts and appends2controlled storage-only pairs. Six candidate constructor rejections precede backend factorization; genuine factorization attempts are117+272=389, including failures. Export/orientation/internal native solves, normalization and loader work are additional, not inferred from outer entry counts. Three manual RejectBackend sentinel factors remain. Seven original fixtures and both backend policies are unchanged.

Inherited helpers remain108 replace_pair,512 solve_pair,673 pair_state and1024exact Rational residual checks; no new extra solve or residual call. New storage pairs add129paired scalar edits,3paired rotations and1paired row merge, with full partition/token checks after each edit. They use4genuine identity40native factorizations plus4controlled exports and no solves on substituted matrices. Source counts are independently reviewed before runtime admission, not measured allocations.

## Explicit storage allocator probes

Inherited Task1 insertion calibrations now require21,21,14callbacks: empty and singleton short insertions need a second7-array descriptor growth after slab append; full32 split does not. Operations(1+21)+(1+21)+(1+14)=59,failures56. Build1+90 and copy1+69 remain; total220operations/215failures. Callback requests sum N+N(N+1)/2 for N in21,21,14,90,69 =7292. This counts throwing callback attempts, with each failure preventing exactly one allocation from completing.

New structural failure groups: descriptor initial7+helper calibration7+failures1..7 =42callbacks/9operations/7failures. Append initial13+helper calibration13+failures1..13+extra failure7 =124callbacks/16operations/14failures. Row-reserve-then-split failures2..8 sum35callbacks/7operations/7failures. Counted monotone32adds52callbacks/32set operations. Three fill/delete40cycles add60callbacks/240set operations: first40row reserves and20slab/metadata/directory requests; subsequent delete/refill reuses row buffers and freed1/2/4/8/16/32extents. This last count is a source-derived schedule, not a lifetime bound or a Julia measurement.

Task2 setup/copy/refactor:2arms*3operations*(1+29failures)=180operations,174throws,2784callbacks. Two failed updates add2operations/2throws/3callbacks. Total706probe operations (including272new counted sets),419expected injected failures,10392callback attempts,9973completed before throws. Ordinary factories used to create each probe input, test fixture allocation, deepcopy, raw snapshots, Test/runtime objects and backend/native allocations are additional and are NOT in the explicit allocator callback total. The call ledger includes genuine manager/factor work. Neither callback count nor elapsed/RSS establishes performance.

## Memory, retained capacity and coexistence

Task1 and corrected Task2 MEMORY-WORK.md remain bound in entry.json. U payload16*C+4*R+28*K+32*n+656, outer pointers8*n+24*D,23+n+3*Svector containers plus headers/backing/padding. Include27field U,8field manager, lower/backend graph, sharedimmutable histories, work/spike, eleven-field row cache and2prepared entries/four numeric buffers/external destination roots. Owner graphs overlap; union counts must deduplicate shared owners. Copy retains all capacities and holes; refactor coexists old/new/export/native/normalization temporaries before publication. Failed updates can retain partially edited U and unused reserve; no solve follows them before explicit refactor.

Demand splitting adds up to6class comparisons+32bin probes,one remainder descriptor and potential7-array growth; free split changes no coefficients. Smaller slabs/active slack can be outweighed by descriptors/relocation/clearing/fragmentation. K/D and C are high-water, not O(live). No new driver scan/counter enters candidate solve/update methods. Existing diagonal lookup/dirty-column scan/cache initialization remain. No field, mirror, cache or alternative kernel is added.

Tests allocate full invariant arrays/sets/dense materializations/bit snapshots/exact Rational matrices and saved factors; largest structural dense160x160Float64 payload204800bytes each. Full64x64 and40x40 checks repeat thousands of scans. The new three40fill/delete cycles add240invariant/materialization checks; allocator-only descriptor fixtures add their own full checks. These bounded correctness costs are deliberate and excluded from speedup claims. Recorder counts/discards passes, keeps34group records and only failure strings; Python manifests keep hashes, not native objects. Physical allocator/JIT/native retention and OS memory remain unknown. VM8GiB/RAM6GiB/swap1GiB are guards, not predicted peaks.

No unnecessary new production work/memory mechanism is introduced. GREEN elapsed/RSS is correctness evidence only. The8cell time/bytes/events/every-checkpoint graph gates and exact compile-zero cost driver remain a separate future request; none are implemented or launched by this step.
''')
put('REPORT.md','''# Task3 split U RED/GREEN driver preparation

Offline preparation only; no Julia/parser/import/compilation/numerical execution, seal, reservation or run output. Tasks1/2 candidate/test bytes are frozen. New75file RED baseline and81file GREEN stage are exact isolated copies;609runtime/wrapper/library/source files are freshly bound. Actual loaded paths are later observed, not assumed from pins.

RED expects10missing-contract failures with zero numerical calls. GREEN expects15929Test outcomes in34leaf groups (25structural+9differential), plus invariant @assert work. Full source derivation and work/memory budget are saved. Driver includes all definitions at top level before main, preserves raw before aggregate checks, and fail-closed validators reject schema/count/path/membership changes and warning/world-age output.

Initial phases outer300/inner292seconds; pure timeout alone can support a separately requested/reviewed600/592attempt. Each RED/GREEN seal requires fresh host/source/runtime/env/command/fullgroupsANDsessions identity, exact independent admission and one exclusive reservation. GREEN depends on an accepted reviewed RED. Preparation review is NOT numerical admission. No automatic launch/retry, no cost driver, no production/master/CI/STATUS/roadmap edit.

Independent review and closure accompany this record. Next user-requested step may verify and seal ONE RED run, obtain independent exact-stage admission, and only then execute it. All accepted old artifacts and failed history remain unchanged.
''')
put('authorization.json',json.dumps(dict(scope='User next-step request following explicit Task2 next step: Task3 offline driver/admission preparation + independent review. No Julia execution or phase seal.',master_unchanged=True,automatic_continuation=False,numerical_allowance=False),indent=2)+'\n')
print('New driver/admission and budget documents saved')
