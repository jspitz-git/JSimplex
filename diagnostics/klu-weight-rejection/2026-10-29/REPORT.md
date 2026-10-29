# Why the first weight RHS was rejected

The immediate cause is a genuine violation of the existing **componentwise** backward-error contract on homogeneous equations whose computed terms are extremely small. The normwise/absolute residual is small, but the maximum componentwise relative error is exactly 1. The same refusal occurs with native KLU, graph-local KLU and ordinary Julia UMFPACK on the same saved B0 and unit RHS. It is therefore not specific to the graph-local BTRAN implementation.

An ordinary Float64 correction reduces the maximum absolute residual by almost a factor of eight, but leaves the maximum componentwise error at 1. Production refinement requires a reliable result or a **strict decrease of relative error**, and consequently discards that correction. This identifies the refusal gate; it does not authorize weakening it or accepting the weight result.

## Captured case and controlled execution

One saved `runtime-30000/B0`, dimension28453, unit RHS row1. Tape/input provenance, independent B and actual production workspace B match. Matrix hash `7b6ab789d7f49d73ec163eee3e2c5c5e9207dadd5f66a3b31972755b367c6d5c`; no MPS parsing, LP solve, simplex iteration, FTRAN, matrix update or benchmark repetition.

All arms use unchanged default legacy Float64 JSimplex policy: solve tolerance256eps=2^-44≈5.684341886080802e-14, max_refinements3, solve_refinement=false, adaptive_refactor=false, hypersparse=false. KLU uses the frozen tol1/BTF/AMD/sum-scaling settings; ordinary `lu(B)` records its own controls and IRSTEP0. Factorization controls are not claimed identical across KLU and UMFPACK.

Independent admission accepted current driver, actual production sources, guard chain and observation budget before the only launch. Actual launch pins124; original readtime inventory114 and review119bindings are separately preserved. Initial driver metadata issue was corrected before launch: raw term maximum is now captured before compensated replay mutates temporary counts. Original driver remains `driver.before-review.jl`; only its historical inventory key maps there, as documented in ADMISSION-NOTES. No arithmetic or test expectation changed.

The single process completed normally in10.1433s including launch/JIT/diagnostic work; ordinary Test76/76 in4.5s. Three factorizations, three initial BTRANs and exactly three correction BTRANs, one per arm. All pins unchanged; no timeout/kill. Ten resource samples, minimum available RAM22013344KiB, swap0, child maxRSS712720KiB. This is diagnostic process memory/time, not kernel cost or peak native allocation accounting. All725 prior/new process groups AND sessions absent after exit; no Julia.

## Actual quality and correction result

All initial, final, before-correction and trial-correction quality evaluations used production's **compensated** branch, finite=true. The raw global rounding bound2.331468351712883e-14 (maximum105terms) exceeds tolerance/4, so the native compensated residual check is selected. It returns definite rejection; the production wide fallback is not used for these points. An additional137-bit residual-only diagnostic oracle and exact Python Fractions confirm selected equations; factor, solution and correction precision remain Float64.

| Arm | Initial max absolute residual | Initial relative error | Trial max absolute residual | Trial relative error | Actual gate |
|---|---:|---:|---:|---:|---|
| native KLU | 9.843200473452773e-17 | 1 | 1.2522535092207576e-17 | 1 | quality_not_improved |
| graph-local KLU | 9.843200473452773e-17 | 1 | 1.2522535092207576e-17 | 1 | quality_not_improved |
| UMFPACK | 9.833713704443525e-17 | 1 | 1.2522535092207576e-17 | 1 | quality_not_improved |

The trial changes541/542/522 solution entries respectively. It is finite and changed, but unreliable and has no strictly smaller `_refinement_error`, which selects relative_error when available. The real production method therefore returns the original point and original unreliable quality after one attempted correction. It does not exhaust all three possible refinements. One stop call per arm here is inside refinement; the earlier weight consumer had an additional outer stop call, explaining the saved count2.

The diagnostic only adds a method for its new private TraceFactor. It calls the genuine production refinement method and forwards each correction once. The hook copies point/RHS/delta, with no extra solve or quality evaluation inside that hook. After return, ordinary Test verifies actual correction RHS bits, ordered trial reconstruction, inferred gate and actual retained point. Before/trial quality snapshots are explicitly post-return reconstruction, not captured internal quality events.

## A concrete exact equation

For a transposed solve, each residual component belongs to a **column of B**, not a row. Production uses

`r_j = b_j - sum_i B[i,j]*x_i`

`s_j = abs(b_j) + sum_i abs(B[i,j]*x_i)`

and assesses `abs(r_j)/s_j`, with the existing rigorous error enclosure.

UMFPACK's initial column5741 (original basis variable24108) is especially simple: `-x[477]+x[1961]=0`. Stored x[477] is -0.0 and x[1961] is8.234691190530272e-37. From their exact IEEE bits,

`abs(r_5741) = s_5741 = 616192750483167 / 748288838313422294120286634350736906063837462003712`.

The relative error is **exactly1**, despite the residual being about8.23e-37. This is far above2^-44, not a rounding-error uncertainty or an underflow/NaN failure. A common scale factor on the whole equation would not change that ratio.

Native KLU's first bad/max-ratio column582 (basis variable27457) likewise has exact ratio1, with absolute residual about2.6782882093705294e-21. Graph-local KLU's first bad column is582 (ratio≈0.2738133), while a max-ratio column2933 has exact ratio1 and absolute residual≈5.94856e-21. Thus backend arithmetic changes the tiny components, but all three hit the same contract limitation on this RHS.

The correction makes absolute residuals still smaller but shifts the tiny problematic equations. Native KLU's trial max-ratio column2933 has residual/scale≈2.256949445178097e-36 and exact ratio1; graph-local's trial column2106 and UMFPACK's trial column4444 also have exact ratio1. The first bad columns after correction are78/78/1008 respectively. More accurate residual accumulation cannot make these actual stored points satisfy the current componentwise criterion.

No claim is made that every such solution component should be mathematically zero: the exact complete solution was not computed. The diagnosis establishes the exact residual of selected stored equations and the actual rejection decision. It does not prove forward accuracy, pivot safety, an LP certificate, all-RHS behavior, or the cause of an old external solver run.

## Evidence and consequence

`results-1.toml` contains all actual qualities, path/control metadata, correction decisions and complete selected sparse equations as coefficient/solution/RHS bits. A local plain-array witness is retained at the path recorded there:3870038bytes, SHA256 `3e8bf2b4c22471872fc8f72b0c7511b3fca7967139aa01a037b74ce341aaf66d`. It contains initial/final points, before-points, correction RHS/deltas, basis and unit RHS; no native factor objects. The portable equations are sufficient for independent exact rejection proofs without deserializing that witness.

The post-exit offline auditor passes268checks/131bindings, recomputes33 selected equations across12snapshots with exact Fractions, checks controls/budgets/pins/guards/witness and ordinary Test. Exact selected violations independently support refusal in every unreliable snapshot. This accepts the diagnostic classification, not the earlier failed weight benchmark or any production candidate. The earlier failed217controls remain unchanged and rejected.

A further step, if desired, should examine the validity contract and correction acceptance for nearly homogeneous equations, including exact known solutions and genuinely bad directions. Simply replacing KLU by UMFPACK, improving residual accumulation, or repeating the performance benchmark will not address the captured refusal. No tolerance relaxation, coefficient dropping, zero snapping, forced additional correction or policy change is implemented or admitted here.

## Work and retained-memory review scope

No production-code change and no added production work/memory. Observation is deliberately material and bounded: seven basis assembly invocations (one independent plus six production, three of those reusing storage but still refilling it), six actual transpose solves and12snapshots. Each snapshot invokes actual quality, raw/selected-branch replay and a137-bit residual-only pass; quality also runs inside actual refinement. Each correction adds three length-n diagnostic copies. Each arm allocates an O(n+N) workspace and independent scratch; input/basis/library hashes scan their bound data. Exact selected-dot evaluation scales with selected column nonzeros.

The fixed trace has nine length-n Float64 vectors per active arm; the maximum planned copied witness payload264n bytes plus basis/RHS is an upper bound, not a measured allocation count. Actual three-arm serialized witness is3.69MiB including metadata. Factors are not serialized and completed arm contexts/workspaces become unrooted before GC. Snapshot BigFloat intermediates, hash buffers, selected equation records and native factors are additional transient memory. The712720KiB process maxRSS includes JIT/runtime/diagnostics and cannot isolate native retention or prove native frees. No timing/allocation optimization claim is drawn from this diagnosis.
