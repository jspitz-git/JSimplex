# Refining a reliable native BTRAN after a price discrepancy

Base: `c0db99f` on `codex/adaptive-degeneracy`.
This continues the FT/SS mod010 failures left after
[artificial-bound normalization](artificial-bound-normalization.md).

## Cause and independent checks

With native mod010 permuted using seed 1, Forrest–Tomlin still stopped at
iteration 266 and Suhl–Suhl at 265. Observational captures reproduce those same
endpoints and retain both the updated and freshly factorized mismatches.
The selected prices after refactorization were respectively
`-5.551115123125783e-17` and `6.832141690000964e-17`; FTRAN-implied prices were
approximately `-6.27e-67` and zero.

Unlike the earlier [price-recovery defect](native-price-recovery.md), both fresh
objective BTRANs satisfy the ordinary compensated residual criterion:

| Manager | Maximum absolute residual | Componentwise relative residual |
| --- | ---: | ---: |
| FT | 5.551115123125783e-17 | 2.7755575615628914e-17 |
| SS | 6.83214169000096e-17 | 6.314393452555595e-16 |

Passing the linear-solve threshold does not guarantee enough accuracy for a
price whose true value is zero. Independent dense 256-bit solves give zero for
both selected prices. Correcting FTRAN alone produces a certified direction but
does not reconcile either cached price. The existing BTRAN recovery refuses
both cases because their residuals are already classified as reliable.

One native compensated-residual BTRAN correction makes the FT dual exact.
For SS it leaves homogeneous artifacts around `1e-32`; the existing cleanup,
using its correction-based cutoff and full residual certificate, removes those.
Exact `Rational{BigInt}` residual checks then verify both corrected Float64 duals.
Production candidate selection on each corrected capture reaches auxiliary
optimality without changing its iteration count. Higher precision and exact
arithmetic are diagnostic references only.

## Small core change

The existing price/direction rejection still triggers at most one recovery
attempt across both candidate-search passes. That recovery may now also refine
a reliable fresh BTRAN when its compensated residual is nonzero.

`_native_cleanup_solve!` gains an opt-in `force_refinement` keyword, defaulting to
false. Its usual reliable-solve fast path remains unchanged. The price recovery
explicitly enables the option only for an initially reliable solve. Such a
correction must strictly reduce the maximum absolute compensated residual and
pass the unchanged full-system reliability check before publication. Failure,
unchanged residual and worse residual all leave the input vector untouched.
The established homogeneous cleanup and its full-system check remain mandatory
when the raw correction is unreliable.

Corrected duals and prices stay private until finite, changed prices are ready
and the caller's stop check permits publication. Basis, primal point, costs,
pricing rule, scalar precision and model tolerances remain unchanged. Exact
zero residuals do not trigger work. Unsupported policies, dual workspaces,
refinement budgets and repeated disagreements retain the existing bounded
handling. No new adaptive heuristic or repeated-refinement loop is introduced.

## Portable regression

The integer basis

```
-4 -4 -2
-2 -5  2
 7  9  0
```

has exact dual `[1,1,1]` for basic costs `[1,0,0]`. A combination of the last two
basic columns exposes a false reduced price despite a reliable BTRAN residual.
This reproduces the defect independently of mod010. Before the change, 120
assertions passed and 40 failed; the failures concerned auxiliary completion
and absent correction events, not fixture prerequisites.

The tests cover Float32/Float64 and all four managers. A separate genuine cost
`-1e-30` must remain actionable **after the new forced correction**, verified by
both its step and correction event. Additional cases check a correction that
worsens or fails to improve an already reliable residual, unchanged default
fast paths, cancellation/exception atomicity, policy gates and one-attempt
handling after another injected discrepancy. The new file is included in the
project test entry point.

## Reproduction

Keep one numerical process, one Julia thread and one BLAS thread. Use the
established 8 GiB guard and local `precompile_workload=false`. Local manifests
and binary snapshots are not committed.

- `reproduce/triangular_price_capture.jl` takes the same four arguments as
  `broad_corpus.jl`; the two jobs are retained in the results directory.
  Reproduce the original failure on base `c0db99f`.
- `reproduce/triangular_price_probe.jl PREFIX...` compares native directions and
  prices with independent reference solves.
- `reproduce/triangular_price_correction.jl PREFIX...` is a diagnostic-only
  native correction and cleanup experiment, not production logic.
- `reproduce/reliable_price_regression.jl PREFIX...` replays the production path.
- `reproduce/reliable_price_semantics.jl MOD010_BOUNDARY_PREFIX OUTPUT_TOML`
  runs the new and existing semantic regressions with `--compile=min`.
- `reproduce/broad_corpus.jl` runs the unchanged 30-job paired verification.

Captures and checksums are in `results/reliable-prices/captures.json`; binaries
remain under `.superpowers/adaptive-degeneracy/reliable-prices`. Text results
include the intermediate raw SS correction failure to distinguish it from the
successful correction plus certified cleanup. Runtime and medium are not rerun.

## Verification

The focused suite passes **336 assertions** with both normal compilation and
`--compile=min`. Production-only captured continuations pass another **12
assertions** with normal compilation, including auxiliary optimality certificates.
The two fresh targeted MPS runs already reach verified original optima with
FT in **590 iterations** and SS in **576**, instead of failing at 266 and 265.

This is not a full project-suite pass. The earlier normal-compilation full
project attempt reached its 300-second LLVM compilation guard; see the
artificial-row report. The broader semantic runner here uses `--compile=min`,
while the focused tests above use normal compilation as well.

Final production source SHA-256: `70f3310f964ddd296d56375a0f19cecc4051c466780bb6836c6540d10de31cad`.

The broader semantic runner passes **10,447 assertions** with `--compile=min`,
including the new tests and earlier phase, point, pricing and policy regressions.
Counts include overlap between existing runners and are not distinct test counts.
Independent code review requested the strict residual-improvement gate and
confirmed the implementation; its missing project-runner include was added.

## Whole-model comparison

The final paired 30-configuration run has **28 verified optima and two numerical
errors**, compared with 23 optima and seven errors on the base commit. All five
new optima pass both independent HiGHS objective comparison and original unscaled
primal feasibility checks:

| Configuration | Before | After | Objective |
| --- | --- | --- | ---: |
| mod010 seed 1 / FT | NUMERICAL_ERROR, 266 | OPTIMAL, 590 | 6532.083333333334 |
| mod010 seed 1 / SS | NUMERICAL_ERROR, 265 | OPTIMAL, 576 | 6532.083333333343 |
| boeing1 native / PFI | NUMERICAL_ERROR, 202 | OPTIMAL, 558 | -335.2135675071268 |
| p0201 native / PFI | NUMERICAL_ERROR, 110 | OPTIMAL, 244 | 6875.0 |
| p0201 JuMP / PFI | NUMERICAL_ERROR, 110 | OPTIMAL, 244 | 6875.0 |

The other **25 configurations** retain status, iterations, refactorizations,
phase sequence and objective exactly. The two numerical errors remain unchanged:
native cycle stops at iteration 868 with bounded feasibility recovery exhausted,
and JuMP stocfor2 at 1957 with primal feasibility lost. They are not solved by
this change. See [the complete paired outcomes](results/reliable-prices/models.md).

All cases retain Float64, steepest-edge, native refactorization every 80 updates,
relaxed integrality, 90 seconds and 1,000,000 iterations. Stagnation monitoring,
adaptive pricing, primal/dual perturbations and Phase I are the only enabled
adaptive switches; the separate weak-pivot preference and original-LP restart
are disabled diagnostically. No time limits or harness exceptions occurred.
These results do not establish convergence for arbitrary degenerate problems
or resolve the separately recorded nonzero-RHS Float32 export fixture.
