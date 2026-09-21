# Lazy row-bound copies in basic presolve

Round 21 delays working copies of row bounds in `_presolve_basic`. The pass used
to copy both bound vectors immediately, even if it returned the original model,
rejected every candidate, or only eliminated empty columns.

The pass now reads the original bounds until it accepts an elimination with
staged row updates. Immediately before committing the first such updates, it
copies both vectors. Later accepted eliminations accumulate their shifts in
those same private vectors. Rejected candidates never write their staged values.
Reduced-model construction retains independent bounds through the existing
slices and model constructor.

No reduction arithmetic, exactness checks, row/column selection, failure
diagnostics, or postsolve mapping changed.

## Method

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native
basis factorization with PFI updates. Each case was warmed twice and sampled
three times, with setup outside measurement and garbage collection before each
sample. Tables show minimum allocated bytes. All 32 measurements per run recorded
zero compilation time. The baseline includes the preceding 20 allocation rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation, so no runtime-speedup claim is made. These are bytes
allocated per call, not peak or retained memory.

## Measurements

| Synthetic dense 128 × 128 CSC input | Before | After | Reduction |
| --- | ---: | ---: | ---: |
| No reduction, unit objective | 8,320 | 4,080 | 50.96% |
| First column fixed at zero and eliminated | 690,448 | 690,608 | -0.02% |

The unchanged probe reduced allocation count from 21 to 15. The fixed-column
probe still needs row-bound working copies because the accepted elimination
stages row writes, even though its value is zero. Its allocation count stayed at
3,692; the 160-byte difference is reported without a byte-saving claim for this
path. It appears as `shifted` in the machine-readable files.

| Model | Basic pass before | Basic pass after | Reduction | Full presolve before | Full presolve after | Reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| afiro | 2,448 | 1,392 | 43.14% | 1,186,456 | 1,183,128 | 0.28% |
| adlittle | 5,008 | 2,928 | 41.53% | 4,898,376 | 4,892,120 | 0.13% |
| kb2 | 3,216 | 1,680 | 47.76% | 13,195,552 | 13,189,024 | 0.05% |
| sc50a | 19,616 | 17,760 | 9.46% | 4,325,296 | 4,318,096 | 0.17% |
| flugpl | 1,792 | 1,056 | 41.07% | 1,514,144 | 1,510,176 | 0.26% |

Whole solves with presolve enabled allocated 0.06–0.31% fewer bytes. The unchanged
paths with presolve disabled varied by 0 to +272 bytes with identical allocation
counts; these small differences are not attributed to the change. Isolated
basic-pass measurements give the clearest evidence of removed copies.

All ten model snapshots (five fixtures × basic/full presolve) matched exactly:
CSC arrays, objective and constant, objective sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations (five fixtures,
primal/dual, presolve on/off) remained `OPTIMAL`; status, objective, complete
primal vector, and iteration count matched the baseline exactly with `isequal`.

Machine-readable results are in
[`lazy-row-bounds-allocations-before.toml`](lazy-row-bounds-allocations-before.toml)
and [`lazy-row-bounds-allocations-after.toml`](lazy-row-bounds-allocations-after.toml).

## Reproduction

The existing audit covers the basic pass, full presolve, and whole solves:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=lazy-row-bounds-audit.toml
```

For the synthetic probes, run from the repository root with the same Julia flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays

unchanged = LinearProblem(sparse(ones(128, 128)), ones(128))
fixed = LinearProblem(sparse(ones(128, 128)), ones(128);
    column_upper=[0.0; fill(nothing, 127)])
for problem in (unchanged, fixed)
    println(measure_allocations(_ -> JSimplex._presolve_basic(problem); samples=3))
end
```

## Regression coverage

The allocation budget failed before the change at 8,320 bytes against a
5,000-byte limit and now passes at 4,080 bytes.

The 79 new checks cover cumulative shifts from multiple accepted eliminations,
rejected inexact candidates with already staged row updates, rejection after an
earlier accepted elimination, unchanged identity returns, empty-column removal,
independent result bounds, unchanged source bounds after result mutation,
infeasibility metadata, and postsolve reconstruction. Numeric coverage includes
Float32, Float64, BigFloat, and Rational{BigInt}.

Independent review found no issue. Its 360 differential cases across six numeric
types, including 57 failures, decimal exactness refusals, and explicit
selections, matched baseline outputs and metadata. Source bounds stayed
unchanged, and reduced models owned independent bound arrays.

The complete mandatory suite passed **16,220/16,220** tests, including the 79 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
