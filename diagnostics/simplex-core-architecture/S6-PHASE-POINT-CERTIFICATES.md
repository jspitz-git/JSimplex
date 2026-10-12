# S6-Y: stored phase-point quality and original feasibility

Status: component experiment complete and independently accepted. Production,
tests, master and CI unchanged. Base b326f2f; one guarded `components-1` process.

## Contract and provenance

Three immutable Float32 inputs were deduplicated offline in S6-X: the explicitly
printed CI phase point, local original endpoint, and exact known point
`[1,1,0,0,0,0]`. Input JSON and its TOML transcription preserve UInt32 hex words.
The six-row original matrix, equality row bounds, nonnegative/unbounded columns
and zero costs match the unchanged `artificial_exchange_roundoff_fixture`.
These are structural points, not the historical private export workspace.

Preflight522 hashes passed. The launch pins623 files; all membership and hashes
were independently rechecked, including517 shared source/test/runtime/environment/
launcher files against S6-X. Source is the active checkout. Julia1.13.0 AArch64,
Julia/BLAS1, heap2GiB, VM8GiB, minRAM6GiB, maxswap1GiB. Guard exit0,12/12 input/model/
options/global preservation assertions and all23 audit gates pass. Raw/portable
report, process, pins, log and exact driver are in `results/S6-Y/components-1-*`.
No old solve, corpus or measurement was rerun.

Options exactly match the S6-X Float32/pfi/budget3 case; native policy also matches
that case. The printed CI cases had budget0. This component experiment does not
spend or simulate a refinement budget: `solve_quality!` uses solve_tolerance,
not max_refinements, and `_original_primal_feasible(problem,x,tol)` receives only
the primal tolerance. Both budgets in S6-X have the same stored local point and
tolerances. No claim that the whole budget0 policy or path was replayed follows.

## Results

| Stored point | Primal basis quality reliable | Original primal certificate | Exact equations | Exact original tolerance |
| --- | --- | --- | --- | --- |
| Printed CI phase | true | **false** | false | false |
| Local original endpoint | true | true | false | true |
| Exact known point | true | true | true | true |

The original tolerance is exactly `14073749/140737488355328` (Float32(1e-7));
the relative solve tolerance is `1/32768`. Exact third-row activity residuals are
`256694483/2^51` for the printed point and `192128033/2^51` for the local point.
The former exceeds the original absolute tolerance; the latter is inside it.
All column values are nonnegative. Zero costs and a zero dual give exactly zero
dual equations offline; no extra dual quality call was needed.

Printed-point maximum exact relative indicator is
`256694483/9007199552490003`; local is `2/47413409`. These exact fractions are not
the rounded production quality return. Production reports respectively absolute
errors1.139952487960727e-7/8.53219930263549e-8 and relative errors
3.251362201694974e-8/4.218216176354872e-8. Both pass the internal reliability test.
The native quality/certificate implementation and its compensated/enclosure/exact
fallback behavior were left intact; no attempt was made to instrument its internal
arithmetic or infer which individual fallback operation executed.

This is a concrete distinction between relative equation reliability and original
absolute feasibility, not a reason to weaken either. It does not establish that
the historical private export candidate equaled the printed phase point, that the
same certificate call rejected it, or that any particular backend caused it.

## Work, limits and next action

Exactly3 production primal `solve_quality!` and3 original-primal certificate entry
calls. Each point owns quality scratch; no workspace, basis solve, factorization,
update, observer, public solver or separate row-interval helper call. Counters in
the report describe these statically verified entry calls, not instrumentation of
internal certificate fallbacks. Only three small records and bounded exact rational
postprocessing are retained. No production work/allocation/retention change and no
performance claim or benchmark warranted.

Next S6-Z qualifies a deterministic **reliable zero-budget exchange fixture only**.
It does not replace the native roundoff reconstruction or cancellation/recovery
integration cases. This narrower test has no requirement to manufacture native
roundoff and should exercise an exactly reconstructible exchange. Qualification,
separate permanent RED/GREEN repair, review and integration remain required.
See `2026-10-12-reliable-phase-exchange-fixture.md`.

Actual historical CI cause, the first four scalar-unknown accepted=false failures,
fullsuite/x64 and broader S6 remain open. Accepted S6-X/Y artifacts must not be
modified or rerun. No production/tolerance/precision/assertion weakening is proposed.
