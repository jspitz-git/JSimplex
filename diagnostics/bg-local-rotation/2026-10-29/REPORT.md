# Endpoint-localized BG diagnostic

Private candidate passes1,368 ordinary tests,113 offline checks,32 cold trajectories and160 measured windows. No production method overwrite, permanent test, environment, CI or master change.

## Change

Original BG moves the replaced column to the end of U and eliminates adjacent subdiagonals through n-1. The private method instead finds the last exactly nonzero spike row, moves the column there, limits elimination to last-1, and gives the pure-swap batching helper the same bound. Trailing incidence/elimination operations are retained. Adjacent magnitude pivot rules, tolerances, zero-pivot exceptions, finite checks and original update record types remain. The extra backward endpoint scan is inside update timing; invalid endpoints fall back to original preparation/update and are not assumed free.

Shortening only the elimination loop would be wrong. For identity3 and replacementcol1=[1,1,0], moving the column to3 but eliminating only the first subdiagonal leaves a nonzero in(3,2). Rotation, elimination and pure-swap bounds must agree. Two3x3 component inputs exercise exact F/Bsolutions, full triangularity, unchanged inputs and immediate copied-history solves on both backends/modes. Explicit a[1]==0 is only an input property; actual zero prepared-spike diagonal after backend permutations was not asserted. Future copy/update/refactor alias safety is not established.

## Results against original BG

Ratios are localized/original at the same interval/backend/input, five measured interleaved arm rotations after warmup. Whole cycle includes actual basis assembly, initial factor/export/normalization, all updates/enteringFTRAN/RHSFTRAN/BTRAN, scheduled refactors, fresh buffers, finite guards and uniform nested timers. Lower is better.

| Input/backend | Interval | Whole ratio (paired range) | Bytes ratio | Events ratio | Final graph ratio |
|---|---:|---:|---:|---:|---:|
| band/native | 128 | 1.007 (0.954–1.129) | 1.000 | 1.000 | 1.000 |
| band/native | 64 | 1.006 (0.938–1.094) | 1.000 | 1.000 | 1.000 |
| band/markowitz | 128 | 1.039 (0.937–1.056) | 1.000 | 1.000 | 1.000 |
| band/markowitz | 64 | 1.024 (0.870–1.374) | 1.000 | 1.000 | 1.000 |
| blocks/native | 128 | 0.531 (0.514–0.587) | 0.444 | 0.814 | 0.365 |
| blocks/native | 64 | 0.576 (0.549–0.638) | 0.648 | 0.893 | 0.521 |
| blocks/markowitz | 128 | 0.558 (0.490–0.681) | 0.491 | 0.925 | 0.421 |
| blocks/markowitz | 64 | 0.621 (0.558–0.668) | 0.729 | 0.968 | 0.587 |
| sparse/native | 128 | 1.022 (0.977–1.046) | 1.000 | 1.000 | 1.000 |
| sparse/native | 64 | 1.000 (0.886–1.028) | 1.000 | 1.000 | 1.000 |
| sparse/markowitz | 128 | 0.982 (0.899–1.018) | 1.000 | 1.000 | 1.000 |
| sparse/markowitz | 64 | 1.000 (0.891–1.162) | 1.000 | 1.000 | 1.000 |
| dense/native | 128 | 1.050 (0.972–1.209) | 1.000 | 1.000 | 1.000 |
| dense/native | 64 | 0.984 (0.871–1.008) | 1.000 | 1.000 | 1.000 |
| dense/markowitz | 128 | 1.028 (0.901–1.080) | 1.000 | 1.000 | 1.000 |
| dense/markowitz | 64 | 0.979 (0.964–1.030) | 1.000 | 1.000 | 1.000 |

Blocks whole cycles improve38–47%, bytes27–56%, allocation events3–19%, final reachable graph41–64%. At interval128 native newly nonzero history coefficients fall3569→1981; Markowitz3498→1959. Markowitz U peak increases1248→1472, confirming U nonzeros alone are an inadequate cost target. Candidate spike endpoint is before64 in128 of256 block exchanges; it is64 in every observed nonblock update. All nonblock final numeric factor/history fingerprints match original; bytes/events/graph are essentially unchanged and timing ranges cross1. Small timing regressions from the added endpoint check cannot be excluded; no universal speedup claim.

## Correctness, limits and work

All8,192 cold updates satisfy full logical U triangularity, finite/nonzero diagonals, valid endpoints, unchanged input and independent selected-RHS residual bounds. No invalid-endpoint fallback occurred on those observed cold paths. Two diagonal lookups per column (up to2n) are performed by a redundant cold check; excluded from hot timing. Every hot output/midpoint/factor-history endpoint matches its own cold arm, final solves rechecked. No complete hot-prefix, global conditioning, all-RHS, recovery, callback, full solver or future copy mutation/lifecycle proof. Different region/permutations may change representation, actual pivots and rounding even though pivot RULE is preserved. Float64 n64 exact-dyadic synthetic bases only.

All160 measured compile/recompile values are zero. Three measuredGC windows remain included: localized band/Markowitz/64/r5=3.581ms, sparse/Markowitz/64/r4=3.928ms, dense/native/128/r2=3.454ms, total10.962ms. No outlier/sample removal.

Exact budget:224 main replays,448 refactors,672 underlying main builds; plus8 component builds,8 copies,8 updates,24 FTRAN and16 BTRAN. Overall680 builds,57,352 updates,114,712 FTRAN,57,360 BTRAN; measured160 replays480 builds. Internal backend/export/orientation work is additional, not a complete PREforward/native ledger. Cold scans/graph/oracles/fingerprints are detached and disclosed. Original94-pin draft is preserved unexecuted; canonical99 pins select driver-2/replay-core-2 with extra fullcoldshape checks.

Guarded process32.07s inclusive, maxRSS690,036KiB, minimum availableRAM22,121,464KiB, swap0; postflight709groups AND sessions absent,noJulia. Graph size is reachable Julia objects, not allocator capacity or native/free accounting; processRSS includes compiler/diagnostics.

Independent review accepts exploratory evidence and finds substantial avoidable original BG work/history in these block trajectories. No unnecessary NEW production work/memory introduced; the extra endpoint scan is charged. This is contiguous endpoint localization, not general graph-local/Reid elimination. No production promotion or proof of superiority to SS follows. Next meaningful qualification would use realistic exchanges, numerical stress and future copy/update/refactor lifecycle coverage.

See [SS/FT/BG options decision](../../triangular-structural-options/2026-10-29/REPORT.md). All original sources, earlier experiments, draft pins and raw records remain unchanged. Postexit analyzer is not a launch pin.
