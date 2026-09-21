# Shared fixed-column activity sums in bound propagation

Round 140 changes only maximum-activity accumulation in `_propagate_row_bounds`
in `src/presolve_propagation.jl`. Before updating the minimum, the pass keeps its
previous sum. When the maximum has the identical previous sum and identical
nonzero term, it reuses the newly computed minimum sum. Identity checks avoid
extra rational arithmetic/comparisons and permit sharing only when both old
operands match. Existing zero-total reuse stays first in the maximum branch.

Fixed columns already share exact bound conversions and activity products;
this change also shares their accumulated sums. It handles cancellation to the
existing zero seed and later restart. A nonfixed contribution makes the sums
diverge, and subsequent fixed terms continue through the existing arithmetic
unless both operands again match. Matching the old sums is essential: a new
minimum equal to the old maximum does not justify reuse.

Activity arithmetic replaces values rather than mutating them. Unbounded
counters, term arrays, candidate differences and division, representability
gates, worklists, row deletion, failure handling, and primal/basis restoration
remain unchanged. No GMP internals or noncanonical constructor are used.

## Method and results

The baseline includes the preceding 139 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 58 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

All six targets contain 128 independent rows and 384 columns. Fully fixed
integer rows use coefficients `[1,3,5]`, column bounds `[1,1]`, and row bounds
`[0,10]`; fractional variants divide coefficients and endpoints by two. The
maximum reuses both nontrivial additions. All rows are redundant and removed.
Integer rows save fourteen allocations each; fractional rows save sixteen,
including the general addition after the first half-integer sum reduces.

Fixed-prefix targets use the same coefficients, but the third column has bounds
`[1,3]` and the row upper bound is 33/2 (both halved for fractional rows). Only
the second contribution can share the minimum sum. The third causes minimum and
maximum to diverge. Each row saves seven allocations and tightens the third
upper bound to 5/2.

Cancellation targets use `[1,-1,1]`, fixed first and second columns at one, a
third column in `[1,3]`, and row upper bound 5/2. Fractional variants halve
coefficients and endpoints. The fixed prefix cancels, allowing the maximum to
reuse the zero computed by the minimum before the third term restarts both sums.
Each row saves two allocations and tightens the third upper bound to 5/2.

The nonfixed control uses `[1,3,5]`, all column bounds `[1,3]`, and row bounds
`[0,33/2]`. Minimum and maximum diverge at their first nonzero term; the third
upper bound still tightens to 5/2. The unbounded control has three free columns
per row and retains the original model. Input construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Fully fixed integer rows | 676,264 | 616,584 | 8.82% | 19,655 → 17,863 |
| Fully fixed fractional rows | 824,008 | 750,872 | 8.88% | 24,263 → 22,215 |
| Integer fixed prefix | 1,660,376 | 1,630,776 | 1.78% | 50,252 → 49,356 |
| Fractional fixed prefix | 1,895,880 | 1,866,024 | 1.57% | 56,652 → 55,756 |
| Integer cancelled prefix | 1,046,552 | 1,039,496 | 0.67% | 32,204 → 31,948 |
| Fractional cancelled prefix | 1,460,232 | 1,452,808 | 0.51% | 43,468 → 43,212 |
| Nonfixed control | 1,778,936 | 1,779,032 | — | 53,580 → 53,580 |
| Unbounded control | 312,448 | 312,608 | — | 9,635 → 9,635 |

The six targets save **256–2,048 allocations per call**. Allocated bytes decrease
by **0.51–8.88%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,296 → 45,056 |
| afiro | sparse | 4,891 → 4,891 | 214,624 → 214,800 |
| afiro | propagation | 2,437 → 2,437 | 92,456 → 92,536 |
| afiro | presolve | 16,217 → 16,217 | 729,128 → 728,952 |
| afiro | dual | 17,032 → 17,032 | 863,928 → 863,544 |
| afiro | primal | 16,938 → 16,938 | 841,464 → 841,784 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,760 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,751 → 2,751 | 174,904 → 174,376 |
| adlittle | propagation | 18,182 → 18,182 | 641,560 → 641,704 |
| adlittle | presolve | 82,433 → 82,433 | 3,325,928 → 3,326,584 |
| adlittle | dual | 84,448 → 84,448 | 4,117,112 → 4,116,056 |
| adlittle | primal | 85,246 → 85,246 | 4,394,328 → 4,392,024 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,352 → 461,464 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,472 → 607,440 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,240 → 112,272 |
| kb2 | sparse | 2,836 → 2,836 | 162,240 → 161,824 |
| kb2 | propagation | 12,948 → 12,948 | 454,752 → 454,608 |
| kb2 | presolve | 229,194 → 229,194 | 10,639,376 → 10,639,296 |
| kb2 | dual | 230,396 → 230,396 | 11,093,104 → 11,090,896 |
| kb2 | primal | 230,563 → 230,563 | 11,107,040 → 11,103,680 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,064 → 878,176 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,816 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,680 → 299,376 |
| sc50a | propagation | 6,020 → 6,020 | 222,704 → 222,016 |
| sc50a | presolve | 67,457 → 67,457 | 2,846,712 → 2,846,184 |
| sc50a | dual | 68,529 → 68,529 | 3,191,896 → 3,192,088 |
| sc50a | primal | 68,474 → 68,474 | 3,144,712 → 3,144,280 |
| sc50a | dual_no_presolve | 961 → 961 | 306,560 → 306,304 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 210,680 → 209,560 |
| flugpl | propagation | 3,253 → 3,253 | 123,760 → 123,056 |
| flugpl | presolve | 30,791 → 30,791 | 1,170,688 → 1,169,776 |
| flugpl | dual | 31,462 → 31,462 | 1,279,832 → 1,279,112 |
| flugpl | primal | 31,811 → 31,811 | 1,324,312 → 1,323,896 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All five reference fixtures retain their allocation counts in all ten stages,
including standalone propagation and solves without presolve. These fixtures
show unchanged behavior and no allocation-count benefit from this particular
shortcut; the measured savings are confined to the six fixed-row/prefix probes.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`propagation-shared-fixed-sums-allocations-before.toml`](propagation-shared-fixed-sums-allocations-before.toml)
and [`propagation-shared-fixed-sums-allocations-after.toml`](propagation-shared-fixed-sums-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-shared-fixed-sums-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_shared_fixed_sums_probe(kind; count=128, T=Float64)
    name = string(kind)
    scale = endswith(name,"fraction") ? T(1)/2 : one(T)
    fixed = startswith(name,"fixed")
    cancelled = startswith(name,"cancelled")
    coefficients = (cancelled ? T[1,-1,1] : T[1,3,5]).*scale
    A = sparse(repeat(collect(1:count),inner=3),collect(1:3count),
        repeat(coefficients,count),count,3count)
    high = fixed ? ones(T,3count) : kind==:nonfixed ? fill(T(3),3count) : repeat(T[1,1,3],count)
    endpoint = T(fixed ? 10 : cancelled ? 5//2 : 33//2)*scale
    problem = LinearProblem(A,ones(T,3count);objective_constant=T(7),
        row_lower=zeros(T,count),row_upper=fill(endpoint,count),
        column_lower=kind==:unbounded ? fill(nothing,3count) : ones(T,3count),
        column_upper=kind==:unbounded ? fill(nothing,3count) : high)
    return problem,JSimplex.propagate_row_bounds
end

for kind in (:fixed_integer,:fixed_fraction,:prefix_integer,:prefix_fraction,:cancelled_integer,:cancelled_fraction,:nonfixed,:unbounded)
    problem, pass = propagation_shared_fixed_sums_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **598 assertions** and failed only
the six target allocation guards: 19,700 > 19,550; 24,271 > 24,150;
50,260 > 50,150; 56,660 > 56,550; 32,212 > 32,100; and 43,476 > 43,350.
Both control budgets passed. There are **604 new assertions**; existing
allocation budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}, fixed rows,
fixed prefixes, cancellation/restart, nonfixed and unbounded controls, canonical
values, source preservation, incremental worklists, changed-column masks,
infeasibility after an earlier tightening, redundant row deletion, and primal
and basis restoration. A dedicated case makes the newly computed minimum equal
to the previous maximum and verifies that their histories are not confused.
BigFloat tests use fixed stored 256-bit endpoints at ambient precision 32/64/256,
with exact cancellations and exact or nonrepresentable resulting bounds. Large
rational fixed prefixes use numerators derived from `2^300+1` with denominators
5, 7, 15, and 21, with both signs and repeated cancellation.

The combined presolve/basic/doubleton/aggregation/propagation targeted suite
passed **76,603 assertions** in **1m52.9s**, exit code zero.

Independent read-only differential review found no issues and passed
**7,108 assertions across 144 models** (126 successful, 18 infeasible;
17 identity results), exit code zero. It compared 144 full-wrapper results,
378 primal restorations, and 378 basis restorations. Actual extracted update
blocks passed 576 incremental arithmetic steps across 96 scalar sequences,
including 372 shared-sum steps and 144 shared finite-sum steps with differing
unbounded counters. Baseline functions were renamed to keep old arithmetic
independent. Cancellation/restart, divergent sums, source preservation, and
ordinary arithmetic alias safety passed. Capturing the old minimum prevents
confusing a newly computed minimum with the previous maximum.

The complete `test/runtests.jl` suite passed **96,100 assertions** in
**5m53.5s**, exit code zero.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
