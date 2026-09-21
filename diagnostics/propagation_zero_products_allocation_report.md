# Skip zero-bound products in row propagation

Round 41 avoids multiplying an exact zero bound by a nonunit coefficient when
building minimum and maximum row activities. The existing bound can be retained:
these values are exact `Rational{BigInt}` numbers, subsequent arithmetic does not
mutate them, and bound-cache updates replace entries. Unbounded terms still use
`nothing`; the shortcut checks that case before testing for zero.

Both coefficient signs retain the original selection of lower and upper bounds.
Candidate formation, exactness checks, contradictions, worklists, and postsolve
behavior are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 40 allocation rounds. All 32 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation, so no runtime
speedup is claimed.

The probe has 128 independent rows `4 ≤ 2xᵢ ≤ 12`, initial column bounds `[0,10]`,
and objective coefficients of one. Its control starts at `[1,10]`, making both
activity bounds nonzero. Both passes retain all rows and tighten the columns to
`[2,6]`.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero minimum bounds | 889,520 | 847,808 | 4.69% | 24,001 → 22,977 |
| Nonzero bounds | 992,336 | 993,328 | — | 26,945 → 26,945 |

The zero-bound probe removes 1,024 allocations. The control keeps identical
allocation counts; its 992-byte increase is allocator variation.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 154,192 → 136,608 | 4,029 → 3,613 | 1,058,504 → 1,030,456 |
| adlittle | 901,832 → 805,272 | 24,409 → 22,137 | 4,208,568 → 4,023,416 |
| kb2 | 770,856 → 686,328 | 20,510 → 18,510 | 12,787,424 → 12,616,848 |
| sc50a | 406,960 → 378,656 | 10,592 → 9,920 | 4,035,152 → 3,997,728 |
| flugpl | 196,936 → 195,400 | 5,017 → 4,969 | 1,435,464 → 1,432,584 |

Standalone propagation allocates 0.78–11.40% fewer bytes on these fixtures.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,194,760 → 1,166,616 | 1,173,416 → 1,143,928 | 672 |
| adlittle | 4,999,256 → 4,811,240 | 5,275,256 → 5,088,344 | 4,432 |
| kb2 | 13,237,408 → 13,072,960 | 13,251,360 → 13,086,016 | 3,984 |
| sc50a | 4,380,528 → 4,343,872 | 4,333,600 → 4,296,624 | 904 |
| flugpl | 1,544,544 → 1,541,584 | 1,589,216 → 1,586,176 | 80 |

Whole solves with presolve allocate approximately 0.19–3.76% fewer bytes.
Full presolve removes the same number of allocations as each whole solve.
Unchanged paths without presolve have identical allocation counts, with byte
differences between -112 and +64. Exact arithmetic introduces further byte
variation; the allocation counts give the more stable comparison.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-zero-products-allocations-before.toml`](propagation-zero-products-allocations-before.toml)
and [`propagation-zero-products-allocations-after.toml`](propagation-zero-products-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-zero-products-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for lower in (0.0, 1.0)
    count = 128
    A = sparse(1:count, 1:count, fill(2.0, count), count, count)
    problem = LinearProblem(A, ones(count); row_lower=fill(4.0, count),
        row_upper=fill(12.0, count), column_lower=fill(lower, count), column_upper=fill(10.0, count))
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

Both allocation guards failed against the original implementation. The two
128-row probes, with a zero lower or upper column bound, recorded 24,046 and
24,009 allocations against a 23,500 limit. All 240 semantic assertions passed before
the change. All 242 new assertions now pass, as do all 739 targeted propagation
assertions together. The allocation-count guards avoid unstable exact-arithmetic
byte budgets.

The new tests cover both bound directions, coefficients `2`, `-2`, `1/2`, and
`-1/2`, finite zero terms alongside free variables, all-unbounded activities,
changed-column flags, postsolve values, and input preservation across Float32,
Float64, BigFloat, and Rational{BigInt}. Existing targeted tests additionally
cover incremental caches, restored bases, precision rejection, cancellation,
and failures after tightening an earlier column.

Independent review found no code issues and separately passed all 242 new
assertions. Thirty-two small comparisons with the original implementation
passed 120 assertions across all four numeric types, comparing full results,
metadata, postsolve stacks and values, changed-column flags, and preservation
of inputs. Two additional assertions checked stored 160-bit BigFloat inputs
under 64-bit working precision.

The full mandatory suite passed all 18,959 assertions in 4m49.9s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
