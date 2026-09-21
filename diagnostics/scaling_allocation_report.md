# Allocation audit: scaling maxima

This twelfth round removes temporary maxima arrays from power-of-two scaling.
All preceding allocation changes remain in both measurements. Measurements use
Julia 1.13.0 on aarch64-linux-gnu with one Julia thread, PFI updates, and native
refactorization. Each entry is the minimum of three warmed calls; no compilation
was observed in measured calls. These are cumulative Julia heap allocations,
not peak memory.

## Findings and changes

After row exponents have been chosen and checked, row maxima are no longer
needed. Their owned array now becomes the output row-factor array. Filling it
with ones before applying valid exponents preserves unit factors for empty rows
and rows where scaling would be unsafe.

Each column maximum is now computed in a scalar immediately before that
column's scaling checks, instead of storing all column maxima in a vector.
Earlier columns occupy separate CSC storage, so scaling them does not change
later columns' maxima. The reduction order within each column, discrete-domain
checks, and overflow/underflow safeguards remain unchanged.

The initial scalar zero is constructed once and reused across columns. This
avoids introducing repeated BigFloat zero allocations. Coefficients retain the
existing arithmetic and precision rules.

## Results

Scaling zero-matrix Float64 probes with unit objective coefficients:

| Rows | Columns | Before (B) | After (B) | Fewer bytes |
|---:|---:|---:|---:|---:|
| 1 | 1,024 | 117,456 | 109,128 | 7.09% |
| 1,024 | 1 | 91,832 | 83,504 | 9.07% |
| 128 | 128 | 27,536 | 25,296 | 8.13% |
| 0 | 0 | 896 | 832 | 7.14% |

Scaling the original fixture models:

| Model | Before (B) | After (B) | Fewer bytes |
|---|---:|---:|---:|
| afiro | 11,008 | 10,416 | 5.38% |
| adlittle | 31,696 | 30,320 | 4.34% |
| kb2 | 20,256 | 19,456 | 3.95% |
| sc50a | 17,072 | 16,112 | 5.62% |
| flugpl | 7,136 | 6,720 | 5.83% |

Whole solves without presolve:

| Model | Dual before (B) | Dual after (B) | Fewer bytes | Primal before (B) | Primal after (B) | Fewer bytes |
|---|---:|---:|---:|---:|---:|---:|
| afiro | 91,888 | 91,328 | 0.61% | 126,256 | 125,728 | 0.42% |
| adlittle | 466,696 | 465,448 | 0.27% | 618,032 | 616,560 | 0.24% |
| kb2 | 880,672 | 879,920 | 0.09% | 263,328 | 262,688 | 0.24% |
| sc50a | 309,344 | 308,528 | 0.26% | 235,016 | 234,120 | 0.38% |
| flugpl | 43,984 | 43,568 | 0.95% | 96,144 | 95,728 | 0.43% |

With presolve enabled, measured whole-solve savings were 0.01–0.15%. Whole-solve
totals include allocation variation outside scaling; isolated stage measurements
are the clearest evidence of this change's direct effect.

All five scaled fixture models matched serialized pre-change snapshots of their
matrix, objective, bounds, domains, names, and scaling factors exactly. All 20
solve combinations (five models, primal/dual, presolve on/off) remained
`OPTIMAL`; status, objective, complete primal vector, and iteration count matched
pre-change snapshots exactly with `isequal`.

Machine-readable measurements are in
[`scaling-allocations-before.toml`](scaling-allocations-before.toml) and
[`scaling-allocations-after.toml`](scaling-allocations-after.toml). Timings
overlapped other validation, so no runtime-speedup claim is made.

## Reproduction

The existing audit covers scaling and whole solves:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=scaling --output=scaling-audit.toml
```

To reproduce the isolated shape probes, run from the repository root with
`--project=dev`:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

for (rows, columns) in ((1, 1024), (1024, 1), (128, 128), (0, 0))
    problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, rows, columns), ones(columns))
    measure_allocations(_ -> JSimplex.scale_problem(problem); samples=3)
end
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and inputs for comparisons.

## Regression coverage

Both allocation budgets failed before the change: the wide probe allocated
117,456 bytes against a 112,000-byte limit, and the tall probe allocated 91,832
bytes against an 87,000-byte limit. Both pass after the change.

The 91 new checks cover independent column maxima, discrete and empty columns,
owned output arrays, resetting invalid and empty row factors, empty dimensions,
and stored 512-bit BigFloat coefficients at ambient precision 64 bits. Numeric
coverage includes Float32, Float64, and BigFloat. Existing tests for unsafe
scaling, model meaning, and BigFloat integrity remain in the mandatory suite.

Independent review found no issue. Its differential checks matched every model
field and scaling factor for 90 random cases with mixed variable domains, two
unsafe-scaling cases, and stored 512-bit BigFloat input at ambient precision
64 bits. BigFloat result precisions also matched.

The complete mandatory suite passed **15,023/15,023** tests, including the 91
new checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
