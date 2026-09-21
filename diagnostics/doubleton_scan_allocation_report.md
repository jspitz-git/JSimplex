# Compact row detection for doubleton substitution

Round 32 replaces complete row-entry vectors in `substitute_free_doubleton`
with one array of four-integer records. Each record stores the columns and CSC
positions of the first two nonzero entries. A third entry permanently marks the
row as ineligible; explicit zeros and inactive CSC capacity are ignored.
Candidate rows and columns retain their original order. Coefficients are loaded
only after a two-entry row passes the equality-bound checks.

Exact arithmetic, candidate rejection, matrix updates, and postsolve logic are
unchanged. The two candidate terms form a tuple. Filtering that tuple preserves
the previous `ArgumentError` for a raw CSC row containing duplicate entries in
the same free column, preventing a self-referential substitution. Base's error
text now mentions an empty tuple rather than an empty collection.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 31 rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

Both probes contain 128 rows with upper bounds of one and free columns. The wide
probe has 128 nonzero entries per row; the inequality probe has two entries per
row in disjoint columns. Both return the original problem without substitution.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Wide rows | 273,744 | 4,312 | 98.42% | 389 → 4 |
| Two-term inequalities | 14,672 | 4,312 | 70.61% | 261 → 4 |

The standalone doubleton pass on all five reference models also exercises the
scan without successful substitution:

| Model | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 3,744 | 1,072 | 71.37% | 59 → 3 |
| adlittle | 11,008 | 2,208 | 79.94% | 117 → 3 |
| kb2 | 8,272 | 1,664 | 79.88% | 91 → 3 |
| sc50a | 6,352 | 1,808 | 71.54% | 104 → 3 |
| flugpl | 2,448 | 800 | 67.32% | 41 → 3 |

| Model | Full presolve before → after | Dual solve before → after | Primal solve before → after |
| --- | ---: | ---: | ---: |
| afiro | 1,137,480 → 1,132,136 | 1,273,496 → 1,268,856 | 1,252,216 → 1,247,528 |
| adlittle | 4,755,048 → 4,737,736 | 5,545,896 → 5,527,656 | 5,822,696 → 5,803,624 |
| kb2 | 13,143,040 → 13,128,720 | 13,595,872 → 13,582,448 | 13,610,112 → 13,597,296 |
| sc50a | 4,133,472 → 4,124,656 | 4,478,976 → 4,471,024 | 4,432,080 → 4,424,432 |
| flugpl | 1,499,336 → 1,494,520 | 1,609,200 → 1,604,560 | 1,653,808 → 1,648,944 |

Whole solves with presolve remove 88, 216, 174, 174, and 106 allocations,
respectively. Their allocated-byte reductions are approximately 0.09–0.37%.
Small cross-process byte differences remain: unchanged solves without presolve
vary from -624 to +32 bytes with identical allocation counts.

All ten model snapshots (five fixtures × doubleton/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`doubleton-scan-allocations-before.toml`](doubleton-scan-allocations-before.toml)
and [`doubleton-scan-allocations-after.toml`](doubleton-scan-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-scan-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for kind in (:wide, :inequalities)
    count = 128
    A = kind == :wide ? sparse(ones(count, count)) :
        sparse(repeat(collect(1:count), inner=2), collect(1:2count),
               ones(2count), count, 2count)
    problem = LinearProblem(A, ones(size(A, 2)); row_upper=ones(count),
        column_lower=fill(nothing, size(A, 2)))
    println(measure_allocations(_ -> JSimplex.substitute_free_doubleton(problem); samples=3))
end
```

## Regression coverage

Both allocation budgets failed against the original body: 273,744 bytes against
a 10,000-byte wide-row limit, and 14,672 bytes against an 8,000-byte inequality
limit. Both now pass. The duplicate-CSC regression also failed with the initial
direct tuple indexing and passes with tuple filtering.

The 112 new assertions cover these budgets, identity returns, signed zeros,
empty/single/double/triple-entry rows, first- and second-candidate selection,
bounded and inexact candidate rejection, numeric outputs, bounds, names, maps,
postsolve primal values and basis indices, and input preservation. Successful
substitution covers Float32, Float64, BigFloat, and Rational{BigInt}. Additional
cases exercise empty matrix shapes, inactive CSC capacity on the identity path,
and duplicate entries. Successful matrix copying with padded CSC buffers remains
outside this change; the existing Julia copy limitation is unchanged.

Independent review found no remaining correctness issue and passed all 112 new
assertions. Its 360 canonical-CSC differential cases across six numeric types
included 33 substitutions and explicit zeros. Another 144 duplicate variants
matched baseline outcome types, including 18 `ArgumentError`s. Empty-shape
allocation probes did not regress.

The complete mandatory suite passed **17,682/17,682** tests, including the 112
new checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
