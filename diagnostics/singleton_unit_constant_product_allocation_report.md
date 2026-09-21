# Signed-unit constant products in singleton aggregation

Round 145 changes only the objective constant product in
`aggregate_singleton_equalities` in `src/presolve_aggregation.jl`. When the
objective ratio or equality RHS is exactly one, the other factor is reused.
For minus one, the other factor is negated. Other nonzero factors retain general
rational multiplication. The preceding zero-ratio and zero-RHS shortcuts remain
in place. The exact constant is still added to the product normally, and the
result still passes through `_represent_exact`.

The checks operate on exact rational values, including the full stored precision
of BigFloat inputs. Near-unit values must not be treated as units. Projection,
candidate ordering, the singleton Float32/64 objective-rounding policy, staged
updates, rollback, and primal/basis restoration are unchanged. Arithmetic uses
public nonmutating operations and preserves source values.

## Method and results

The baseline includes the preceding 144 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 singleton columns and one shared retained column, with
equalities `2*x_i+y=rhs`, bounds `[1,3]` on every x_i, and free y. The objective
prices are `2*ratio` on each x_i and two on y, with initial constant seven.
The first two targets use ratio 1 or -1 and RHS four. The other two use ratio
three and RHS 1 or -1. All 128 eliminations succeed, leaving coefficient one,
projected row bounds `[rhs-6,rhs-2]`, retained cost `2-128*ratio`, and constant
`7+128*ratio*rhs`. Measurement includes projection, staging, objective updates,
and reconstruction rather than an isolated arithmetic expression.

The nonunit control uses ratio three and RHS four, retaining general multiplication.
The zero-RHS control uses ratio three and RHS zero, retaining the earlier zero
shortcut. Both controls accept all pivots.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Ratio 1 | 1,029,632 | 986,096 | 4.23% | 27,133 → 25,981 |
| Ratio -1 | 1,030,696 | 994,440 | 3.52% | 27,136 → 26,240 |
| RHS 1 | 1,030,616 | 987,368 | 4.20% | 27,136 → 25,984 |
| RHS -1 | 1,030,696 | 994,280 | 3.53% | 27,136 → 26,240 |
| Nonunit control | 1,030,568 | 1,030,824 | — | 27,136 → 27,136 |
| Zero-RHS control | 888,904 | 888,936 | — | 23,168 → 23,168 |

Allocated bytes decrease by **3.52–4.23%** across the four targets.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

- `ratio_positive` saves **1,152 allocations per call**, or 9 per eliminated column.
- `ratio_negative` saves **896 allocations per call**, or 7 per eliminated column.
- `rhs_positive` saves **1,152 allocations per call**, or 9 per eliminated column.
- `rhs_negative` saves **896 allocations per call**, or 7 per eliminated column.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,560 → 44,720 |
| afiro | sparse | 4,891 → 4,891 | 215,152 → 213,568 |
| afiro | propagation | 2,437 → 2,437 | 92,424 → 92,040 |
| afiro | presolve | 16,217 → 16,217 | 730,328 → 728,168 |
| afiro | dual | 17,032 → 17,032 | 864,408 → 864,200 |
| afiro | primal | 16,938 → 16,938 | 842,808 → 842,392 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,747 → 2,747 | 174,408 → 174,024 |
| adlittle | propagation | 18,182 → 18,182 | 642,904 → 641,624 |
| adlittle | presolve | 82,433 → 82,433 | 3,328,504 → 3,328,648 |
| adlittle | dual | 84,448 → 84,448 | 4,119,224 → 4,117,608 |
| adlittle | primal | 85,246 → 85,246 | 4,396,072 → 4,394,584 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,048 → 461,240 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,392 → 607,728 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,015 → 2,015 | 109,472 → 110,160 |
| kb2 | sparse | 2,836 → 2,836 | 162,464 → 161,680 |
| kb2 | propagation | 12,948 → 12,948 | 456,080 → 454,912 |
| kb2 | presolve | 229,149 → 229,149 | 10,639,712 → 10,638,688 |
| kb2 | dual | 230,351 → 230,351 | 11,093,296 → 11,090,256 |
| kb2 | primal | 230,518 → 230,518 | 11,107,904 → 11,104,368 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,096 → 877,856 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 300,288 → 299,328 |
| sc50a | propagation | 6,020 → 6,020 | 223,184 → 222,064 |
| sc50a | presolve | 67,457 → 67,457 | 2,847,752 → 2,846,344 |
| sc50a | dual | 68,529 → 68,529 | 3,192,728 → 3,192,840 |
| sc50a | primal | 68,474 → 68,474 | 3,145,752 → 3,145,352 |
| sc50a | dual_no_presolve | 961 → 961 | 306,208 → 306,128 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,184 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 210,936 → 210,120 |
| flugpl | propagation | 3,253 → 3,253 | 123,456 → 122,528 |
| flugpl | presolve | 30,791 → 30,791 | 1,171,408 → 1,169,584 |
| flugpl | dual | 31,462 → 31,462 | 1,281,224 → 1,279,512 |
| flugpl | primal | 31,811 → 31,811 | 1,325,800 → 1,324,168 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All 50 reference measurements retain their allocation counts. These fixtures
do not show a measurable benefit from this particular product shortcut.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`singleton-unit-constant-product-allocations-before.toml`](singleton-unit-constant-product-allocations-before.toml)
and [`singleton-unit-constant-product-allocations-after.toml`](singleton-unit-constant-product-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=singleton-unit-constant-product-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function singleton_unit_constant_product_probe(kind; count=128, T=Float64)
    ratio=kind==:ratio_positive ? one(T) : kind==:ratio_negative ? -one(T) : T(3)
    rhs=kind==:rhs_positive ? one(T) : kind==:rhs_negative ? -one(T) : kind==:zero_rhs ? zero(T) : T(4)
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(ones(T,count,1)))
    problem=LinearProblem(A,[fill(2ratio,count);T(2)];objective_constant=T(7),
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end

for kind in (:ratio_positive,:ratio_negative,:rhs_positive,:rhs_negative,:nonunit,:zero_rhs)
    problem, pass = singleton_unit_constant_product_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,034 assertions** and failed only
the four target allocation guards: 27,178 and three cases of 27,144 against
a 26,600 limit. Both control budgets
passed. There are **2,038 new assertions**; existing budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; signed unit,
fractional, zero and nonunit factors; finite and free pivot bounds; sequential
shifts from zero/nonzero constants; projected matrix/bounds/objective; restored
primal and basis; objective equivalence; and normal rational output mutation.

BigFloat tests use stored 256-bit inputs at ambient precision 32/64/256. Values
`±(1+2^-200)` on either side of the product remain nonunit. Inexact constants
reject at lower precision, while exact tiny tails and complete cancellations
remain accepted. The retained column has degree two to prevent unrelated
alternate singleton candidates. Large non-dyadic rational cases cover both
factor positions, signs, and canonical reduction with denominators 5, 7, 15, 21.

The targeted presolve/allocation suite passed **83,430 / 83,430 assertions**
in 1m59.2s, including every new allocation guard.

Independent read-only review found no issues. An AST-renamed baseline passed
**2,485 assertions across 160 differential models**: 24 Float32, 24 Float64,
28 Rational{BigInt}, and 28 BigFloat models at each ambient precision 32/64/256.
Coverage included signed units on both sides, near-units, exact tails and
cancellation, zero/nonunit controls, late cost/constant rejection, rollback
after earlier commits, exact-candidate preference and floating objective
rounding, primal/basis restoration, projected/free/fixed bounds, and source
preservation under ordinary rational arithmetic and output mutation.

The full test suite passed **102,927 / 102,927 assertions** in **6m04.4s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
