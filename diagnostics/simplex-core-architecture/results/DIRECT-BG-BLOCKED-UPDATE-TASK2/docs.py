from pathlib import Path
import json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK2'
def put(p,s):
 with p.open('x') as f:f.write(s)
put(C/'adapter-work-memory.md', '''# Task2 adapter work and memory ledger — UNEXECUTED

This is source accounting, not allocation measurement, runtime admission or speedup.
The four Task1 artifacts remain frozen. Read their work-memory-ledger.md for all
20 kernel counters; this ledger adds composition, reference and cold-test costs.
The main adapter owns exactly inner, a concrete optional BGNoCounts workspace and
busy. It does not use the rejected export-workspace/specialization candidates.

## Execution frequency and scalar fallback

Constructor: one unchanged ordinary factorization/export/import, one wrapper,
no panel workspace. Native threshold_one / Markowitz default only, Float64/Int.
Ordinary factory may take its already-existing fallback; the stream tests require
DIRECT mode. Constructor input conversion/normalization/temporary CSC storage is
identical to reference, not asserted free. There is no extra solve or full scan.

Each replacement: original prepare-spike (two-slot provenance), begin, incidence
ensure/old-column replacement, column rotation, one n-element spike zero fill and
one original recycled/allocated steps vector. One final update/history publication
and finish. Probe and cold observation calls are absent semantically for nothing;
actual compiler elimination and allocation behavior remain UNQUALIFIED.

Per prospective panel: original pure-run lookahead, then eligibility's suffix
binary searches and stored-band traversal before workspace allocation. One new
pure-run lookahead per accepted panel duplicates at most its first scalar lookahead;
an ineligible/declined boundary also repeats that lookahead in the scalar suffix.
Worst-case lookahead is O(n) per boundary; no claim that this work is free.
Dimension/density/nonfinite decline ends blocking for the whole remaining suffix.
One private arithmetic/commit rejection at most; at most8 repeated private steps.
An eligibility rejection performs no private arithmetic. Counts are distinguished
by cold events eligibility/panel_begin/panel_pivot/panel_commit/panel_reject and
scalar_suffix. The main route has no persistent event vector/counter dict.

Each accepted panel: h*w zero +2*h*w mask clears, separate gather traversal,
<=b*w FMA sites, <=2*b*w swap value stores, finite tests, masks; commit preflight,
repeated support searches, <=2*h*w explicit index/value stores, <=h*w reserve mask
probes, h sizehint! requests, one ascending n-ID incidence pass and <=h*w pushes.
Kernel counter13 records COMPLETED pair array requests, not pre-forward attempts.
At most2*w new packed arrays; the changed column's complete prefix/suffix is
copied, not just the panel. Existing support uses in-place value writes. At most8
step slots inspected and <=8 chronological nonidentity pushes into the one update
vector, whose retained capacity may grow. No per-panel update record or factor copy.
Across panels p<=floor((n-1)/4), tighter b=8 where width>=64. Dense upper bound
O(n^2 log n/8) lookups, O(n^2) tile/commit/incidence work; sparse rejection still
pays eligibility scans before using original scalar work. This is the experiment,
not a claim of improvement. Pure runs retain the original batched scalar suffix.

Scalar suffix: original loop, arithmetic, strict pivot policy, exact-zero deletes,
rotation batching, incidence searches and partial failure semantics. Source-map
stores the exact original suffix and explicit namespace/type/range substitutions;
only two cold observation sites are added. No new scalar coefficient tolerance.

## Retention / transients / failure

Persistent panel payload72n+16*ceil(9n/64)+4352 bytes includes conservative header
allowance and8 fixed step slots: n96=11480,n256=23360,n4096=308480, below1MiB.
This source charge is not an actual GC graph size. Original BG work/spike/incidence,
updates and compiled/prepared caches are additional and unchanged in ownership.
Steps vector capacity can retain up to O(n) steps per update; history O(chain*n)
and compiled row-operation storage remain original BG costs, not within scratch cap.

First eligible use allocates one values matrix, two BitMatrix containers/buffers,
one8-step vector and workspace object; actual runtime allocation events unmeasured.
No workspace on cheap rejection. Same-dimension refactor retains it, ANY dimension
change drops it (including shrink/unsupported); copies always panel-cache-empty.
No factor/update rollback promise. Refactor's original candidate construction may
hold old and new full inner graphs simultaneously; this is unchanged reference work.
Private workspace ownership is the wrapper contract: callers must not independently
mutate its inner while it is busy. All wrapper solves/update/refactor/copy reject
reentrancy during update/refactor. This is synchronous nonreentrant use, not locking
or a new thread-safety guarantee against arbitrary external inner references.

Changed-column commit transient: old+new values/IDs16*(oldnnz+newnnz) logical bytes
for that column coexist; GC can retain multiple abandoned old columns until collect,
so whole-commit worst old/new live payload includes the sum over changed columns,
not merely counter14's largest pair. Hidden array capacity/header and sizehint!
growth/GC retention are additional; Task3 must measure whole graph and transient.
One private tile only; no second dense tile in candidate. Failure drops workspace,
invalidates prepared and sparse/dense upper eligibility and incidence readiness,
clears both prefix flags, resets busy and rethrows original exception. Failed
workspace owner release through GC is not a native-free or immediate collection proof.
A nonfinite declined private panel clears candidate prefix safety persistently even
if scalar fallback later succeeds. Commit exceptions may leave partial live U;
the factor is not promised solvable after failure. No retry after commit exception.

## Cold tests and complete visible API budgets

13 streams: six old-recipe sparse/dense32/96/256 x8updates; dense96 x32updates;
six stress streams x8updates. Total128 replacements/arm, two backends, two sides:
52 constructors,512 replacements,1536 FTRAN and512 BTRAN entries. These are explicit
public entries, not complete internal native/Markowitz work. Per pair/update:
2 entering FTRAN,2 DSE FTRAN,2 post-update FTRAN,2 post-update BTRAN. Four exact
pre-update and four post-update residual checks. No extra production solves for
panel decisions. Original B changes only by frozen requested column replacement.
The numerical test returns256 small per-update observations across the two arms;
trace vectors/snapshots below are discarded per update except returned scalars.

Lifecycle functions additionally execute two backends: per backend1constructor,
3refactors(96,64,32),2copies,7 FTRAN entries,2successful replacements; busy tests
attempt1update/1refactor/1copy/1FTRAN/1BTRAN rejected before inner work, and one bad
zero-tolerance update rejected with conservative cleanup. Microcases:2dimensions,
1explicit-zero,1overflow,1zero-diagonal,2nonfinite,3fault points,1reentrancy =11
additional native identity constructors and11 elimination entries; reentrancy
attempts one FTRAN rejected. These microcases accept synthetic post-rotation H,
not public basis-column correctness/positive public route evidence. Future harness
must count actual entry attempts and failure prefixes; no numerical allowance here.

Cold Trace: original H, floating shadow, exact rational T, panel rollback copies
of shadow/T, detached original lower/scaling/permutation/diagonal snapshots, plus
O(n) event/pivot arrays. Exact relation materializes rational U/H and T*H, at most
O(n^3) rational work and O(n^2) big-integer storage per update; rational bit length
is NOT bounded by the Float64 workspace charge. Exact solve residuals materialize
rational B, vector x/RHS, plus product; O(n^2) dense visits per check. Copy graph,
row-incidence validation, bit arrays and Test result storage are additional. These
are untimed correctness costs; a future300s admission must account for them and
may not silently skip required checks to fit. No claim current full roster fits300s.

Fault kernel is a separate exact-inverse module with fixed Ref state and three
throw sites: gather after owner binding, reserve after sizehint!, writeback after
one committed column. OutOfMemoryError is a sentinel simulation, not a real
allocator exhaustion or allocation-attempt accounting proof. Fault clone never
replaces main kernel dispatch and is not timed. Exceptions propagate by identity.

## Numerical obligations and limits

Independent original-B exact residuals and chronological H-to-U relation use the
accepted128*n*2^-52 bound. Trace independently computes strict abs pivot decisions,
row action, ordinary subtraction or FMA and compares stored history action, U bits,
unchanged lower/base and incidence. H is captured AFTER spike/rotation. Negative
nonfinite cases deliberately do not use the finite relation oracle. Separated
exact stream requires pivot agreement; near-tie trajectories may differ. Input
stress names are recipes, not proof a given backend selects a near-tie pivot.
Positive panel gates cannot skip on ineligibility. No solver/certificate/public
integration, allocation or speedup conclusion is made before separate execution.
''')
put(Q/'REPORT.md','''# Task2 blocked BG adapter preparation

Prepared a separate BGPanelFactor adapter, ordinary scalar suffix, cold lifecycle
and differential test source,13 frozen streams (128 replacements per backend per
side) and ordinary source overlay. Nothing has been parsed or executed by Julia.
No driver, launcher, runtime admission, expected RED count or performance result
has been created. Frozen Task1 code and production/source/test/env/CI/master and
global continuation documents remain unchanged.

The wrapper owns typed optional scratch and busy state, preserves ordinary
factorization/export/import/solves, appends one final update history, and falls back
from the original panel boundary. Rejected private nonfinite arithmetic leaves
prefix safety false; exceptions drop scratch and invalidate caches without
claiming whole-factor rollback. Source counters are distinguished from allocations.

Tests check original-basis residuals, independently replayed policy/arithmetic and
H-to-U/history relation, prepared entering/DSE provenance, copies/refactors, explicit
zeros/nonfinite values, late fallback, zero pivots, reentrancy and isolated fault
injection. All tests are UNEXECUTED. Future admission must freeze the full test
schedule/entry counts and include expensive exact oracles; no300s-fit claim here.

The four original32/96 streams match saved ordinary input bits/steps exactly;256
extends the original pure recipe. New stress input bits are fixed before execution.
Both current-src original root and private overlay are hash bound with exactly two
ordinary direct factory/export includes inserted. Top-level loading order is
manifested, but no runtime/world-age/cache-confinement acceptance is inferred.

See reproduce/adapter-work-memory.md for work, logical memory and cold-test costs,
fixtures.json/toml for frozen data, adapter-source-map.json for ordinary suffix and
fault-clone inverses. Initial test text hashes were saved before adapter creation.
One new author correction script stopped on an incorrect expected lexical count
(two instead of three positions references), before candidate mutation. Its source,
failure and all prior candidate text were preserved; a separate correction fixes
the selector, incidence oracle and copy-divergence test without executing Julia.

Independent review and final closure are recorded separately. Next permissible
step after source acceptance is separate concrete RED/GREEN harness/admission
preparation, not automatic Julia execution or production integration.
''')
with (Q/'docs.py').open('xb') as out:out.write(Path(__file__).read_bytes())
print('Work/memory ledger and report saved')
