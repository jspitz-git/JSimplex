# S4-Q: nonsymmetric fixed-history lifecycle measurement

One new guarded cost-1 completed: exit0, 6,176 runtime checks, 40 lifecycles, 28 audit
gates and 558 launch pins. All960 exact residuals pass the prelaunch64eps scaled
bound; all960 are NONZERO, max residual/bound0.06196430492264961. All96 measured
windows (32 outer,64 nested) have zero compile and recompile time. Production, tests,
CI and master unchanged; native HH symbolic reuse remains disabled.

The inclusive lifecycle observation does not establish a consistent elapsed-time
improvement: paired outer medians are0.981266 sparse and1.015527 dense, with both ranges
crossing1. Explicit GC dominates those windows. Nested ordinary refactor medians are
lower on these fixtures, but the dense second-refactor outlier is preserved. No
end-to-end, universal, pure-symbolic, native-free or memory-retention claim follows.

## Numerical and ownership scope

Prelaunch plan: docs/superpowers/plans/2026-10-12-hh-history-lifecycle-cost-measurement.md.
Exact P inputs retained unchanged, SHA256
85874a35de281a9de4ce4d49c7f17f176d37a1597fc557ae64469202fcfd9b06.
Two NEW finite nonsymmetric48 CSC inputs: sparse142/dense2304 nonzeros. Seven bases,
columns[3,17,31,31,17,3], exact row dominance/pivot margins from P. Q inputs.toml binds
all19,138 stored coefficient/RHS/incoming/knownsolution values without regeneration
or old-script reruns. Eight warmup and32 measured lifecycles follow the exact alternating
order. All16 measured side pairs have equal captured output bits (24 outputs per side).
This is endpoint agreement, not hidden backend trajectory/factor identity capture.

Actual pre-call counts:40 constructors,80 refactors,240 updates,240 prepared FTRAN,
360 ordinary FTRAN and360 BTRAN. Prepared outputs are immediately used by replace_column!;
additional diagnostic equality scans assert the cache match, no corrected-direction
fallback intended. Ordinary F uses the non-preparing helper. Histories reach3 before
each refactor and0 afterwards, all private. Default control bits agree throughout;
IRSTEP0, default q by source construction. Runtime ownership checks cover current native
CSC versus input storage; no saved retired owner references or per-step factor snapshots.

Source-derived work, not observed native instrumentation:120 numeric/extraction entries,
60 reference symbolic entries,20 candidate initial symbolic entries,40 candidate pattern
checks,240 update-internal unit transposes,1200 HH update applications, and AT MOST120
native orientation validation solves. Candidate guard takes the source-matched same-
pattern route, but no runtime symbolic pointer identity or complete native-call ledger
was captured. Same-type conversion may be identity; wrapper CSC copies remain.

Each of40 histories has two refactors and two sets of3 private updates. Captured pool
records [u-pairs,u-entries,v-pairs,v-entries] after the first/second refactor:
sparse [3,51,3,48]/[5,113,3,48], dense [3,138,3,96]/[5,188,3,96], on both sides.
These describe Julia-owned packed pools, not hidden native memory. Pool retention is
bounded here and can grow with packed entries; retirement scans records separately.

## Windows and measured values

All rows below use candidate/reference paired ratios,8 pairs per fixture. Windows are
nested: do not add inner costs to outer or interpret subtraction as isolated free cost.
No samples were removed or repeated; no extra warmup or numerical retry occurred.

| Fixture / window | Ratio median | Full range | MAD |
| --- | ---: | ---: | ---: |
| sparse outer lifetime+GC | 0.981266 | 0.878046–1.023718 | 0.020984 |
| dense outer lifetime+GC | 1.015527 | 0.941117–1.097955 | 0.031717 |
| sparse refactor1 | 0.741388 | 0.650538–0.789474 | 0.032331 |
| sparse refactor2 | 0.637864 | 0.605166–0.764706 | 0.022398 |
| dense refactor1 | 0.762519 | 0.684717–0.905972 | 0.041726 |
| dense refactor2 | 0.725739 | 0.668493–5.757909 | 0.024434 |

Dense round5 candidate refactor2 was418.6us versus reference72.7us, ratio5.757909.
Compile/recompile/GC fields for that inner window are zero. Cause is unmeasured; do not
label it noise and discard it or attribute it to a native operation without evidence.

| Fixture / side | Outer median ms | Outer GC median ms | Outer bytes | Outer events |
| --- | ---: | ---: | ---: | ---: |
| sparse reference | 31.165594 | 30.916244 | 231056 | 416 |
| sparse candidate | 30.645944 | 30.439544 | 195888 | 356 |
| dense reference | 30.439695 | 29.954595 | 1037776 | 439 |
| dense candidate | 31.165395 | 30.693245 | 892288 | 377 |

Outer bytes/events were constant per side/fixture in these measured samples. Inner
medians in microseconds (reference/candidate): sparse1 37.8/28.65, sparse2 25.55/16.65,
dense1 83.15/63.2, dense2 72.85/52.65. All inner GC fields zero. Inner byte/event ranges,
absolute time/GC ranges and side dispersions are fully preserved in audit.json and raw.
Dense candidate refactor1 bytes varied249592–249624; no constant-byte claim for that row.
These fields are Julia aggregate GC traffic potentially including native jl_* activity,
per O. They neither identify pure Julia objects nor count live native allocations.

## Diagnostic work, GC and limitations

Inside outer windows: constructor, solves, updates, refactors, pre-call counters,
prepared equality scans6x48/lifecycle, controls capture/checks, scalar state/pool/alias
checks, nested timer records and post-owner-return explicit GC. The owner body is
non-inlined and returns nothing; both nested and outer timer values are nothing.
No factor/native wrapper/base/history is retained in output records. This is a source
ownership property, not evidence of successful finalizer/native-free completion.
Explicit GC entries40 before timers and40 inside after owner return; natural GC is
additional. Final GC may service other pending objects/finalizers. Raw GC fields describe
runtime timing, not an object-specific free interval.

Outside windows:28 prebuilt independent input CSCs, RHS/incoming storage,960 distinct
length48 output vectors (46,080 Float64 values/368640 payload bytes plus headers), one
length48 residual scratch, runtime960 matrix-vector residual evaluations, input-bit
checks, hashes and final serialization. Outputs are written in place, no per-solve
output copies. Runtime opnorm/finite checks are additional outside-window diagnostics;
exact post-exit rational checks are not Julia/native solves. Earlier output vectors
remain alive and are scanned by GC; timing therefore includes diagnostic-root overhead
and is not a measurement of the factor in isolation. Same bounded allocation/order
scheme applies to both sides. No production work or memory overhead introduced.

Native retention remains OPEN: no full native allocation/free balance, successful free
capture, RSS substitution, manual finalization or allocator-hook experiment. Neither
these GC-dominated lifetimes nor M's accepted ordinary windows qualify every consumer,
platform, precision, public controller or original-model certificate. All safeguards
and original-model boundaries remain unchanged.

## Evidence and continuation

Raw report SHA256d33e04007dd9c3f7afee9983b9dce845d9b1115545ef4c66a422c2a1ec1f6387.
Process ran about7.012s;7 resource samples, minimum availableRAM22742788KiB, swap0.
Runner23256/start984453/group23249 and child23257/start984535/group23257; both full groups
and PIDs absent after exit, boot dade7243-9103-4398-bb45-fa28fbc0be72. Actual source,
clone inverse, native library, user6 files and all558 pins verified independently by
author. Auditor was written AFTER exit and has a separate hash; it is not a launch pin.
Native loaded path/hash captures the observed UMFPACK library, not every loader decision.
Read-only installed atomic add/sub1 disassembly corroborates nested compilation timing;
no new native call was made for that check.

Fresh independent numerical/work review pending. No accepted raw artifacts changed,
no production promotion or CI restoration. Next ONE source-only S4-R contract:
2026-10-12-hh-public-controller-reuse-contract.md, to assess a safe bounded public-
controller qualification seam. No automatic public-solver or hook experiment; native
retention, other consumers/controls/precisions/platforms/fullsuite and broader S4/S6
remain open. S2-A/S6-J/whole S6-AF rejections unchanged.
