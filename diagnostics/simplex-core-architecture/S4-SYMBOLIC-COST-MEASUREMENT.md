# S4-M: bounded whole-HH refactor cost observations

One new guarded run, cost-1, exit0. Four NEW Float64/Int64 native HH factors on
sparse/dense96 dyadic fixtures (nnz474/9216), 231 runtime checks, 24 postexit audit
gates,554 unchanged launch pins,10 separate author checks. No production/test/CI
change; master0eb75c3 unchanged and native HH symbolic reuse remains disabled.
This is measured refactor-window evidence, not production or native-retention
acceptance. Raw report SHA256:
`bba1cc33f5b8a478c97758cdc0bf4fc11f3da345b54c9c4d9c0861db6cf46fef`.

## Frozen protocol and numerical coverage

The exact S4-M plan, driver, inverse-equal three-routing-name/Float64-keyword clone,
inputs and runtime/native sources were pinned before launch. The reference calls
production refactorize!, candidate routes only through that clone; no method was
overwritten. All input arrays are independent between sides. Source matches the
current master. All20,148 coefficient/RHS entries were independently rebuilt offline
from the plan and compared with frozen binary64 inputs, including L's accepted
hashes/RHS without rerunning any L script.

Actual counts:4 constructors,128 warmup+512 measured refactors,44 FTRAN+44 BTRAN.
No factor copies, updates, workspaces, public solves, solver iterations, certificates
or observer callbacks. Constructor/solve/refactor entry counters increment before
calls; the equal refactor counter overhead is inside each timed loop. Eight warmup
batches and32 measured batches,16 calls each. Rounds use phase00110011 and alternating
RC/CR order, each phase twice in each order per fixture. No extra warmup or retry.

SOURCE-DERIVED work:644 numeric/extraction entries,322 reference symbolic entries,
2 initial candidate symbolic entries,320 candidate guard scans. Internal orientation
validation is bounded by644 additional native solves, not observed instrumentation.
Default q/control/IRSTEP0 unchanged. Guard index comparisons O(n+nnz) remain real
work; the two same-type conversions return the input by source dispatch and do not
copy CSC arrays. No finite-value scan or extra basis solve is added to production.

All88 captured solves satisfy the PRELAUNCH exact rational scale bound
`||M*z-b||inf <=64*2^-52*max(1,||M||inf*||z||inf,||b||inf)`.
Every one has a NONZERO exact residual. Symmetric inputs deliberately limit general
transpose coverage. All16 measured pairs agree in captured forward/transpose bits
and HH-owned L/U/p/q/scaling fingerprints. These are batch endpoint comparisons,
not captures of every intermediate factor, hidden arithmetic or a solver trajectory.
No solve on an original LP, certificate or objective was involved.

## Cost observations

All32 measured windows have compile_time=0 and recompile_time=0. Explicit full GC
is outside each measured window; natural in-window GC is included (recorded0 here).
Input construction, endpoint solves/scans/hashes, graph traversals and serialization
are outside the refactor timer. No component-only replay or subtraction attributes
all savings to a particular native kernel. Julia allocation events/bytes do not
measure all native malloc/free traffic.

| Fixture | Reference median ms /16 | Candidate median ms /16 | Paired median ratio | Pair range | Ratio MAD | Side-median ratio |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| Sparse96 | 0.72470 | 0.50140 | 0.66579 | 0.62688–0.93650 | 0.02668 | 0.69187 |
| Dense96 | 3.57505 | 2.75785 | 0.75772 | 0.52678–0.80944 | 0.03274 | 0.77142 |

| Fixture | Reference Julia bytes /16 | Candidate Julia bytes /16 | Reference events | Candidate events |
| --- | --- | --- | ---: | ---: |
| Sparse96 | 2,364,976–2,365,152 | 1,740,080–1,740,128 | 1632 | 1184 |
| Dense96 | 17,821,888–17,823,808 | 13,502,368–13,502,432 | 1664 | 1200 |

All eight paired ratios per fixture are below1 in this run, supporting lower
observed whole-refactor-window cost on these inputs. Short windows, one process,
fixed environment, GC placement and limited fixtures restrict generalization.
This is not an end-to-end/current-master solver speedup, universal symbolic quality
proof, full allocation/free lifecycle comparison or a production acceptance gate.
All absolute samples, pair ratios, medians/ranges/MAD and bytes/event differences
are retained in cost-1-audit.json; no sample was omitted for timing reasons.

Constructor timer totals:0.0011873s,3,032,496 Julia bytes,634 events.
Warmup timer totals:0.0433347s,70,866,448 bytes,11,609 events. Both report0 compilation
inside their timed regions; compilation before entering those regions is excluded,
so this does NOT mean the entire process required no compilation. Process wall time
was about6s and includes startup and all outside-window diagnostics. No old timing
was compared with these results and no extra numerical run was performed.

## Memory observations and limits

The four-current-factor Julia graph was920,424B at all three checkpoints (after
warmup/round4/round8). No retired native owner, old base or shallow factor copy is
stored in records. Forty-four endpoint pairs retain8,448 Float64 elements until
post-window conversion to output bits. Additional control/info/hash/counter records
are bounded; fingerprint IO buffers and residual temporaries add diagnostic work
outside timing. Controls and native info are copied as data, never owner references.

Native SIZE_OF_UNIT was16B. On all checkpoints the reported symbolic/numeric final
sizes per factor were sparse463/893Units (7408/14288B) and dense323/5174Units
(5168/82784B), equal between routes. Algorithm peaks were4557/33802Units; symbolic
estimates and VARIABLE_PEAK are separate fields in raw records. These are reported
algorithm/object sizes, not live allocation balances; old unreachable objects can
await finalizers. Candidate symbolic-origin fields describe its retained initial
analysis, not fresh symbolic work in every sample.

RSS KiB was563372,563340,563340 at the three checkpoints; after the owning function
returned and explicit GC,562316. VmHWM580452 and VmPeak1220604 stayed fixed in those
snapshots. Root release is a source-scoped ownership property, not observation of
individual native frees. RSS and Julia graph stability do not prove absence of a
native leak or allocator retention. **The native-retention obligation remains OPEN.**
A later source-only feasibility contract must establish whether safe, supported
allocation/free accounting is possible before any instrumentation experiment.

## Provenance, work review and limits

Six guard samples:minimum available RAM22,796,936KiB, swap0; one Julia/BLAS thread,
heap2GiB/VM8GiB/wall600 limits preserved. Runner15915/start670009/group15914 and
child15916/start670093/group15916 both complete groups absent after exit, no Julia,
boot dade7243-9103-4398-bb45-fa28fbc0be72. All554 pins rehashed twice by author;
actual source/clone/input bits/native library and raw/portable4 matched. Auditor
was written after exit, has its own SHA, and is NOT a retrospective launch pin.

No unnecessary production computation/allocation/retained memory introduced because
production is unchanged. The diagnostic guard overhead and bounded endpoint/graph
work are explicit. Native-retention, other consumers/control/scalar/platform gates,
fullsuite/x64/historical failure causes and prior rejections remain open. Frozen
M driver/clone/prepare/auditor/independent scripts must not be rerun or edited.
Fresh independent numerical/work review is recorded separately before acceptance.
