# Construct exact zero when a bound equals its shift

Round 99 changes the shared `_shift_bound_exact` helper in `src/presolve.jl`.
The existing zero-shift, unbounded-endpoint, and zero-bound shortcuts remain.
For a nonzero finite bound, the helper converts the stored value exactly and
compares it with the exact shift. Equal operands produce an exact rational zero
directly; unequal operands retain subtraction. The candidate still passes
`_represent_exact` before a bound is returned.

This avoids subtracting identical arbitrary-precision rationals. Basic
elimination, free-doubleton substitution, and sparse equality aggregation all
use this helper. Exact representability rejection, stored precision on unchanged
bounds, candidate staging, matrix/objective updates, and restoration are
preserved. No caller-specific behavior is changed.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 98 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Every target exactly cancels 128 nonzero lower endpoints; upper endpoints start at ten.
Basic probes eliminate fixed `x[i]=2` from rows `c*x[i]+y` bounded by `[2*c,10]`,
with `c=±2`. Sparse probes use independent row pairs `2*x[i]+y[i]=4` and
`c*x[i]+3*y[i]` bounded by `[2*c,10]`, with `x[i]` in `[1,3]` and `c=±2`.
The doubleton probe eliminates free `x` from `2*x+y=4` and 128 rows
`2*x+3*y` bounded by `[4,10]`. All eliminated variables have zero cost, retained
variables have cost two, and the objective constant is seven.

The control is the positive-coefficient basic probe with row bounds `[1,10]`,
so both finite endpoints use the existing unequal-bound subtraction.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Basic, coefficient 2 | 581,040 | 552,256 | 4.95% | 15,172 → 14,532 |
| Basic, coefficient -2 | 582,832 | 553,728 | 4.99% | 15,172 → 14,532 |
| Sparse, coefficient 2 | 1,894,432 | 1,866,336 | 1.48% | 48,581 → 47,941 |
| Sparse, coefficient -2 | 1,910,480 | 1,882,128 | 1.48% | 49,093 → 48,453 |
| Free doubleton | 737,760 | 708,496 | 3.97% | 18,712 → 18,072 |
| Unequal-bound control | 594,704 | 594,912 | — | 15,556 → 15,556 |

Each target removes 640 allocations (five per cancelled endpoint), reducing
allocated bytes by 1.48–4.99%. The control retains its allocation count; byte differences
on unchanged paths alone establish no benefit.

| Model | Basic before → after | Basic allocations before → after | Doubleton before → after | Doubleton allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 1,392 → 1,392 | 15 → 15 | 1,072 → 1,072 | 3 → 3 |
| adlittle | 2,928 → 2,928 | 15 → 15 | 2,208 → 2,208 | 3 → 3 |
| kb2 | 1,680 → 1,680 | 15 → 15 | 1,664 → 1,664 | 3 → 3 |
| sc50a | 17,760 → 17,760 | 60 → 60 | 1,808 → 1,808 | 3 → 3 |
| flugpl | 1,056 → 1,056 | 15 → 15 | 800 → 800 | 3 → 3 |

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 44,160 → 43,776 | 843 → 843 | 219,688 → 219,608 | 4,987 → 4,987 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 177,712 → 178,240 | 2,843 → 2,843 |
| kb2 | 111,312 → 111,536 | 2,060 → 2,060 | 162,048 → 162,112 | 2,836 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 302,432 → 302,016 | 6,647 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 218,760 → 218,376 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 734,920 → 734,200 | 869,144 → 869,672 | 846,984 → 847,416 | 0 |
| adlittle | 3,356,400 → 3,356,048 | 4,145,472 → 4,146,080 | 4,422,496 → 4,423,232 | 0 |
| kb2 | 10,683,608 → 10,681,912 | 11,136,232 → 11,136,168 | 11,149,432 → 11,150,152 | 0 |
| sc50a | 2,854,912 → 2,855,936 | 3,201,728 → 3,201,632 | 3,154,432 → 3,153,872 | 0 |
| flugpl | 1,204,136 → 1,203,864 | 1,313,360 → 1,313,472 | 1,357,776 → 1,358,208 | 0 |

All five reference fixtures retain their allocation counts in basic, doubleton,
singleton, sparse, full presolve, and whole primal/dual solves. This round shows
a benefit on the targeted cancellation probes only.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`cancelled-bound-shift-allocations-before.toml`](cancelled-bound-shift-allocations-before.toml)
and [`cancelled-bound-shift-allocations-after.toml`](cancelled-bound-shift-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=cancelled-bound-shift-basic-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=cancelled-bound-shift-doubleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=cancelled-bound-shift-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function cancelled_bound_shift_probe(kind; count=128)
    coefficient = kind in (:basic_negative,:sparse_negative) ? -2.0 : 2.0
    if kind in (:basic_positive,:basic_negative,:unequal_bound)
        A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
        problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
            row_lower=fill(kind == :unequal_bound ? 1.0 : 2coefficient,count),row_upper=fill(10.0,count),
            column_lower=vcat(fill(2.0,count),nothing),column_upper=vcat(fill(2.0,count),nothing))
        return problem,JSimplex._presolve_basic
    elseif kind == :doubleton
        A = sparse(hcat(vcat(2.0,fill(2.0,count)),vcat(1.0,fill(3.0,count))))
        problem = LinearProblem(A,[0.0,2.0];objective_constant=7.0,
            row_lower=fill(4.0,count+1),row_upper=vcat(4.0,fill(10.0,count)),
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        return problem,JSimplex.substitute_free_doubleton
    end
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),ones(count),fill(coefficient,count),fill(3.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 0.0 : 2.0 for i in 1:2count];objective_constant=7.0,
        row_lower=[isodd(i) ? 4.0 : 2coefficient for i in 1:2count],
        row_upper=[isodd(i) ? 4.0 : 10.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end
for kind in (:basic_positive, :basic_negative, :sparse_positive,
             :sparse_negative, :doubleton, :unequal_bound)
    problem, pass = cancelled_bound_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 833 assertions and failed the
five target allocation guards. The basic probes measured 15,217 / 15,180 allocations against a 14,850 limit;
sparse probes measured 48,589 / 49,101 against 48,250 / 48,750; doubleton
measured 18,720 against 18,400. The unequal-bound control passed.
All 838 new assertions now pass as part of 17,140 targeted assertions
covering presolve and all three callers. Existing allocation budgets were not
relaxed.

Direct helper coverage includes Float32, Float64, BigFloat, and Rational{BigInt};
positive, negative, signed-zero, binary, and nonbinary stored values shifted by
their exact representations. Neighboring Float32/Float64 values remain distinct.
Stored 256-bit BigFloat bounds are checked at ambient precision 32/64 for exact
cancellation and tiny nonzero residuals, preserving the input value and precision.

All three callers are checked with cancelled lower, upper, or both endpoints and
both coefficient signs. Tests compare reduced matrices, bounds, objectives,
primal restoration, and unchanged inputs. Tiny BigFloat residuals survive in all
three callers under reduced ambient precision. Existing zero-bound-shift tests
retain coverage of zero-shift/unbounded identity and unrepresentable shifts.

Independent read-only review found no issues. It passed 6,614 assertions:
838 focused assertions plus 5,776 additional checks against AST-renamed baseline
helper/callers. Differential validation covered 346 helper cases, 276 models,
and 1,104 basis restorations, with source/shift/basis immutability checks, exact
objective and primal restoration, identity controls, tiny BigFloat residuals,
and cancellation staged before a later rejection and subsequent valid candidate.

The full repository suite passed **42,025 / 42,025** assertions in 5m10.2s
(exit status 0).
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
