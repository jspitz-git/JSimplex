# Reuse one for coefficients equal to the dependency pivot

Round 62 extends the existing exact-one shortcut in `reduce_dependent_rows` to
every coefficient equal to the original pivot scale. Nonunit normalization
previously reused one only for the pivot entry itself. Equal trailing entries
now share the existing proof seed instead of computing an exact rational
quotient. Unequal and opposite coefficients still divide by the cached scale;
proof normalization and the unit-pivot fast path are unchanged. Arithmetic
replaces dictionary values without mutating the shared rational components.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 61 allocation rounds. All 34 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

The probes contain 128 independent rows and 129 free columns. Row `i` has pivot
`s` in column `i` and trailing coefficient `v` in column `i+1`, with upper bound
three and a zero objective. Equal positive and negative coefficients exercise
the shortcut; unit pivots and unequal trailing coefficients serve as controls.
Every model is retained unchanged.

| Probe `(s, v)` | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Equal positive `(2, 2)` | 366,224 | 323,664 | 11.62% | 6,810 → 5,658 |
| Equal negative `(-2, -2)` | 366,272 | 322,992 | 11.82% | 6,810 → 5,658 |
| Unit pivot `(1, 1)` | 276,400 | 277,296 | — | 4,506 → 4,506 |
| Unequal coefficients `(2, 6)` | 366,272 | 367,296 | — | 6,810 → 6,810 |

Each target removes 1,152 allocations. Both controls retain their allocation
counts; their small byte increases reflect cross-process exact-arithmetic
allocation variation.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 209,728 → 206,064 | 4,557 → 4,440 | 876,400 → 856,112 |
| adlittle | 724,616 → 722,152 | 16,903 → 16,804 | 3,631,736 → 3,625,784 |
| kb2 | 3,490,776 → 3,479,544 | 80,732 → 80,354 | 11,209,704 → 11,181,448 |
| sc50a | 1,420,616 → 1,421,656 | 33,292 → 33,292 | 3,086,792 → 3,087,480 |
| flugpl | 197,920 → 198,016 | 4,158 → 4,158 | 1,339,760 → 1,340,864 |

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,011,344 → 991,328 | 990,416 → 970,384 | 558 |
| adlittle | 4,422,840 → 4,415,080 | 4,699,256 → 4,691,480 | 198 |
| kb2 | 11,659,464 → 11,633,592 | 11,674,040 → 11,647,656 | 756 |
| sc50a | 3,432,408 → 3,432,728 | 3,385,176 → 3,385,480 | 0 |
| flugpl | 1,448,872 → 1,450,072 | 1,493,464 → 1,494,664 | 0 |

Full presolve removes the same number of allocations as each whole solve.
Three fixtures benefit, while sc50a and flugpl retain their allocation counts.
Unchanged paths without presolve vary from -336 to +16 bytes with identical
allocation counts. These controls illustrate the small byte variation between
processes; no improvement is claimed where counts are unchanged.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-equal-pivots-allocations-before.toml`](dependent-equal-pivots-allocations-before.toml)
and [`dependent-equal-pivots-allocations-after.toml`](dependent-equal-pivots-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-equal-pivots-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for (pivot, trailing) in ((2.0, 2.0), (-2.0, -2.0), (1.0, 1.0), (2.0, 6.0))
    count = 128
    A = sparse([collect(1:count); collect(1:count)],
        [collect(1:count); collect(2:count+1)],
        [fill(pivot, count); fill(trailing, count)], count, count+1)
    problem = LinearProblem(A, zeros(count+1); row_upper=fill(3.0, count),
        column_lower=fill(nothing, count+1))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

Both target allocation guards failed against the original implementation:
6,855 and 6,818 allocations exceeded the 6,200 limit. The other 150 assertions,
including both controls, passed. All 152 new assertions now pass as part of
1,890 targeted dependency assertions. Allocation-count budgets avoid unstable
exact-arithmetic byte totals.

Tests cover Float32, Float64, BigFloat, and Rational{BigInt}, positive, negative,
and fractional pivots, equal coefficients present initially and appearing after
elimination, opposite and unequal coefficients, row removal, contradictions,
postsolve, and input preservation.

Independent review found no issues and separately passed all 152 new assertions.
Thirty-two saved-baseline differential cases passed 129 additional assertions
across Float64, Rational{Int}, Rational{BigInt}, and BigFloat. They include mixed
64–224-bit BigFloat precision, equal coefficients arising after elimination,
unequal/opposite controls, feasible and infeasible dependencies, postsolve, and
input preservation.

The full mandatory suite passed all 21,663 assertions in 4m51.4s.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
