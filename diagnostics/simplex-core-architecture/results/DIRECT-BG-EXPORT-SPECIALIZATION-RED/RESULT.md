# BG export/import specialization RED300: failed qualification

The exact independently admitted RED300 attempt was executed once. It is **NOT ACCEPTED** as the required three-failure RED qualification. The original allocation predicate failed on sparse32 and dense32; sparse96 stopped at the mandatory measured-compilation gate before its allocation test. No GREEN or retry was executed. This is not a timeout and does not qualify for the timeout-only extension.

## Admission and execution

Diagnostic entry HEAD: `e780e6158ea5365adf5cde36dceaa8032a34fe9c`; master remained `26e2291745999f485a74f643298ca997d65c7205`. The exact seal contains 2111 files; the independent admission binds those and the seal (2112 paths), with 50 passing checks. The first review checker compared its login-shell PATH rather than the actual waiting outer environment; that failed record is preserved. The separate checker checks only the pinned environment keys against the actual outer process. No launch inputs were changed.

The 300-second supervisor / 292-second inner deadline was unchanged. Julia/BLAS one thread, heap hint 2 GiB, VM limit 8 GiB, available RAM floor 6 GiB and swap ceiling 1 GiB remained enforced. The child returned 2 with process reason `exit2`; guard elapsed including launch was 10.619069368010969 seconds, not a benchmark. The outer elapsed including immutable checks and audit was 23.016837471994222 seconds, also not a benchmark. The guard recorded unchanged pins. Original audit is `all_passed=false`, `pure_timeout=false`, error `ValueError('Measured compilation')`; it was not rerun.

## Saved outcome

Fifty of the planned sixty windows were saved: twenty each for sparse32 and dense32, ten for sparse96. The saved Test tree has two failed allocation assertions, no completed third group, and a separate caught fatal driver error. A Test error count of zero does not mean the driver succeeded. Raw `complete=false` and the full fatal stack are preserved.

| Completed cell | Reference median events | Old workspace median events | Reference median bytes | Old workspace median bytes |
|---|---:|---:|---:|---:|
| sparse32 | 1274 | 1279 | 294664 | 292696 |
| dense32 | 1282 | 1291 | 755520 | 742952 |

These use the seven observed samples on each side. Both predicates fail because event counts increase even though byte traffic decreases. They are partial RED observations, not acceptance or a general performance comparison.

The first nonzero measured compilation is `window-3-10.toml`, sparse96 old workspace side, pair 5/order 2: compilation 0.0068022 s, recompilation 0 s, GC 0.031775499 s, elapsed 0.039607799 s, 3280 events and 674792 bytes. The window was saved before the gate. Three warm pairs and the preceding measured windows did not prevent this later compilation. No function-level compilation trace was collected; neither a particular method nor causality between GC and compilation is established. Dropping this sample or adding warm-up after seeing it would change the accepted experiment.

## Scope, work and closure

The reached source loop consists of 50 lifecycle windows, each with one constructor, eight updates, sixteen FTRAN, eight BTRAN and two refactor calls: 50/400/800/400/100 entries, respectively, with 1200 saved solve outputs. These are source-derived reached-loop counts, not complete backend work or exception-attempt instrumentation. Output correctness and unchanged-input flags are stored for each window; the independent diagnostic review separately assesses the saved prefix. There is no complete three-cell qualification, speedup, production integration, native memory release proof or observer-neutrality claim.

No production code was changed; the failed attempt introduces no new production work, allocations or retained memory. The diagnostic driver retains bounded output records and includes its prescribed timing instrumentation; this is not a zero-overhead measurement. Runtime peak/GC traffic do not prove a native retained-memory bound.

Separate after-return `outer-closure.json` covers all 259 prior and new PGIDs AND sessions, including actual outer 116092, guard 116909 and child 116910, on boot `1ecae454-f1f5-4e2e-a95c-7b5474243126`. All are absent and no Julia is present. Future host checks must merge this complete group list; the frozen in-process posthost does not close its own outer caller.

All admission, output, scripts, false audit and review records remain immutable. The result review must explicitly classify diagnostic preservation separately from qualification and must not satisfy the successful RED predecessor gate. Next permissible work is a separate source/log-only analysis of the compilation point and, if supported, a separately reviewed experimental amendment. No replay, tuning, GREEN or candidate changes are authorized by this failed result. The broader plan remains open; CI stays disabled and HH reuse disabled.
