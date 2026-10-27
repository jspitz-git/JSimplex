# Whole-function BigFloat comparison

One guarded attempt: 33807 ordinary assertions PASS, 1160 cells / 20880 measured windows, 170.614s inclusive. All measured compile/recompile times zero. All 490 GC windows and all outliers retained. No numerical rerun.

| Whole function | BF cells | Median paired ratio across cells | Cell median range | Bytes saved range | All pairs bytes/events lower |
|---|---:|---:|---:|---:|---:|
| direction | 180 | 0.9537 | 0.6935–1.0196 | 0.003–26.398% | 180 |
| row | 180 | 0.9163 | 0.7452–1.0568 | 0.000–24.424% | 150 |
| quality | 180 | 0.7557 | 0.5647–1.1344 | 14.825–41.204% | 180 |
| quality_transposed | 180 | 0.7580 | 0.4967–1.1114 | 14.825–41.204% | 180 |
| devex_shared | 180 | 0.5634 | 0.4251–0.7037 | 42.255–61.650% | 180 |
| devex_solved | 180 | 0.8766 | 0.7160–0.9316 | 12.648–29.604% | 180 |

Proposed independent acceptance: all A/B/C, for local whole-function work/allocation reduction with uncertain negative/control timing. No universal or end-to-end speedup. A gains depend strongly on sign. B two negative dense128 cells have paired medians1.1344 (BF64Down normal) and1.1114 (BF64Nearest transposed); preserve and disclose, not proof of universal time reduction. C all360 BF shared+solved cells have lower byte/event costs in every measured pair and cell paired medians<1.

There are80 native/exact control cells; all have equal allocation events.65 have equal medianbytes;15 rational control cells show GMP usable-capacity variation despite unchanged code. Do not call those savings or regressions from this BF-only change.

Complete functions include residual all scans/safeguards/pipeline invalidation, quality alias/finiteness/storedprecision/wide scratch/reliability, Devex shared and actual4row basis BTRAN+price. No real simplex iteration/public solve/end-to-end qualification; sparse/dense dimensions32/128 are kernels, not large LPs. Preparation recorded separately: fixtures, correctness/snapshots, contextGC, cold/warm calls and resets. BF64/128/256 x5rounding + FP32/64/RatBigInt/RatInt64 controls, empty/nonfinite/alias/dimension/custom/view/mixed512/underflow/freshcaps tests. Native/free accounting/complete backend/PREforward/callback-neutrality claims absent.

Production code is still unchanged. Proposed ordinary permanent allocation gates at BF128Nearest dense32 positive, each six whole scopes: fixed3 alternatingpairs, >3percent fewer BOTH bytes/events supported by every original9pairs. No timing assertion/threshold tuning. Baseline RED must fail exactly6 such gates; numerical expectations unchanged. Older failure test line709 and its release-specific exception remain historical; this task does not weaken or extend that exception.
