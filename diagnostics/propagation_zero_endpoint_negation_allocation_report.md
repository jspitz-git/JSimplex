# Negate other activity for zero row endpoints

Round 80 replaces general subtraction `0 - other_activity` with negation of
the exact other activity when constructing candidate bounds. The shortcut
covers both lower and upper candidates for positive and negative coefficients.
The existing zero-other-activity shortcut stays first, followed by this new
zero-endpoint branch; exact cancellation and unequal subtraction retain their
previous paths for nonzero endpoints.

The zero check uses the exact rational row endpoint. Tiny nonzero BigFloat
inputs remain nonzero, including candidates that cannot be represented at the
working precision. Negation does not mutate its operand. Finite-bound flags,
division shortcuts, candidate checks, caches, worklists, and postsolve retain
their previous behavior.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 79 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

The three targets contain 128 rows `c*x[i] + 3*y = 0`, with each `x[i]` initially
free and shared column `y` fixed at one. Coefficients `c` are two, minus two,
or one. Each numerator is `0 - 3`, and the `x[i]` columns are fixed at `-3/c`.
The nonzero-endpoint control uses coefficient two and row endpoint five, fixing
each `x[i]` at one. The zero-other-activity control fixes `y` at zero and uses
coefficient two and row endpoint four, fixing each `x[i]` at two. All objectives
are ones.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero endpoint, coefficient 2 | 619,560 | 547,736 | 11.59% | 16,087 → 14,295 |
| Zero endpoint, coefficient -2 | 617,016 | 544,744 | 11.71% | 15,959 → 14,167 |
| Zero endpoint, coefficient 1 | 533,896 | 461,608 | 13.54% | 13,783 → 11,991 |
| Nonzero-endpoint control | 667,688 | 668,872 | — | 17,623 → 17,623 |
| Zero-other-activity control | 532,416 | 533,552 | — | 14,036 → 14,036 |

Each target removes 1,792 allocations. Both controls retain their allocation
counts. Small byte differences on unchanged paths reflect cross-process
exact-arithmetic variation; no benefit is claimed for those cases.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 91,128 → 90,808 | 2,437 → 2,437 | 794,144 → 782,320 |
| adlittle | 676,008 → 646,392 | 18,971 → 18,243 | 3,453,456 → 3,379,528 |
| kb2 | 513,400 → 470,152 | 14,312 → 13,262 | 10,875,560 → 10,759,352 |
| sc50a | 234,872 → 223,896 | 6,312 → 6,064 | 3,031,080 → 3,028,504 |
| flugpl | 136,064 → 124,552 | 3,556 → 3,297 | 1,281,104 → 1,264,632 |

Four direct propagation passes remove allocations; kb2 removes 1,050. Afiro
retains its count, so its small byte reduction alone does not establish a benefit.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 930,320 → 918,288 | 908,320 → 896,576 | 294 |
| adlittle | 4,242,976 → 4,169,208 | 4,519,760 → 4,445,032 | 1,765 |
| kb2 | 11,327,416 → 11,211,544 | 11,339,752 → 11,226,152 | 2,805 |
| sc50a | 3,376,632 → 3,375,432 | 3,329,432 → 3,327,688 | 28 |
| flugpl | 1,390,648 → 1,374,560 | 1,435,288 → 1,419,072 | 399 |

Full presolve and both whole solves remove allocations on all five fixtures,
from 28 for sc50a to 2,805 for kb2. Paths without presolve retain their counts,
with byte differences from -192 to +320; no benefit is claimed for these
unchanged paths.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-zero-endpoint-negation-allocations-before.toml`](propagation-zero-endpoint-negation-allocations-before.toml)
and [`propagation-zero-endpoint-negation-allocations-after.toml`](propagation-zero-endpoint-negation-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-zero-endpoint-negation-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_zero_endpoint_negation_probe(kind; count=128)
    coefficient = kind == :negative ? -2.0 : kind == :unit ? 1.0 : 2.0
    fixed = kind == :zero_other ? 0.0 : 1.0
    endpoint = kind == :unequal ? 5.0 : kind == :zero_other ? 4.0 : 0.0
    A = sparse(vcat(collect(1:count), collect(1:count)),
        vcat(collect(1:count), fill(count+1, count)),
        vcat(fill(coefficient, count), fill(3.0, count)), count, count+1)
    return LinearProblem(A, ones(count+1);
        row_lower=fill(endpoint, count), row_upper=fill(endpoint, count),
        column_lower=vcat(fill(nothing, count), fixed),
        column_upper=vcat(fill(nothing, count), fixed))
end
for kind in (:positive, :negative, :unit, :unequal, :zero_other)
    problem = propagation_zero_endpoint_negation_probe(kind)
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

All three target allocation guards failed on the original implementation:
16,132 exceeded 15,200, 15,967 exceeded 15,100, and 13,791 exceeded 13,000.
The other 404 assertions passed, including both controls. All 407 new assertions
now pass as part of 5,125 targeted propagation and presolve assertions.
Whole-pass budgets use allocation counts to avoid unstable exact-arithmetic
byte totals. Existing allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; both signs
of coefficient and other activity; unit-coefficient and nonzero-endpoint
controls; both and one-sided row bounds; source-bound preservation; changed
flags; postsolve; and full/incremental activation of later nonzero rows.
Stored 256-bit BigFloat endpoints `±2^-200` produce candidates slightly different
from `-3/coefficient`; their rejection at ambient precision 32/64 ensures that
tiny nonzero endpoints are not incorrectly treated as zero.

Independent review found no issues. The focused file passed all 407 assertions;
a saved-baseline differential check passed 14,260 assertions across 1,056 paired
cases. It covered both activity signs, all four numeric types and candidate
branches, unit/general coefficients, controls, unbounded activity and
contradictions, immutable inputs, incremental propagation, primal/basis
restoration, and tiny or unrepresentable BigFloat endpoints.

The full mandatory test suite passed **25,826/25,826 assertions** in 4m58.0s
with exit code zero.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
