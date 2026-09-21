# Negate exact shifts directly for zero finite bounds

Round 98 changes the shared `_shift_bound_exact` helper in `src/presolve.jl`.
After the existing zero-shift and unbounded-endpoint early returns, a finite
zero bound uses the exact negated shift. A nonzero finite bound retains its
exact conversion and subtraction. The candidate still passes `_represent_exact`
before a bound is returned.

This avoids converting zero to a rational and subtracting from it. Basic
elimination, free-doubleton substitution, and sparse equality aggregation all
use this helper. Exact representability rejection, stored precision on unchanged
bounds, candidate staging, matrix/objective updates, and restoration are
preserved. No caller-specific behavior is changed.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 97 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Every target shifts 128 zero lower endpoints; its upper endpoints start at ten.
Basic probes eliminate fixed `x[i]=2` from rows `c*x[i]+y` bounded by `[0,10]`,
with `c=±2`. Sparse probes use independent row pairs `2*x[i]+y[i]=4` and
`c*x[i]+3*y[i]` bounded by `[0,10]`, with `x[i]` in `[1,3]` and `c=±2`.
The doubleton probe eliminates free `x` from `2*x+y=4` and 128 rows
`2*x+3*y` bounded by `[0,10]`. All eliminated variables have zero cost, retained
variables have cost two, and the objective constant is seven.

The control is the positive-coefficient basic probe with row bounds `[1,10]`,
so both finite endpoints use the existing nonzero-bound subtraction.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Basic, coefficient 2 | 583,200 | 508,000 | 12.89% | 15,172 → 13,124 |
| Basic, coefficient -2 | 585,040 | 509,088 | 12.98% | 15,172 → 13,124 |
| Sparse, coefficient 2 | 1,896,928 | 1,822,928 | 3.90% | 48,581 → 46,533 |
| Sparse, coefficient -2 | 1,912,992 | 1,838,576 | 3.89% | 49,093 → 47,045 |
| Free doubleton | 740,160 | 664,576 | 10.21% | 18,712 → 16,664 |
| Nonzero-bound control | 597,248 | 595,040 | — | 15,556 → 15,556 |

Each target removes 2,048 allocations (16 per zero endpoint). The control
retains its allocation count; byte differences on unchanged paths alone
establish no benefit.

| Model | Basic before → after | Basic allocations before → after | Doubleton before → after | Doubleton allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 1,392 → 1,392 | 15 → 15 | 1,072 → 1,072 | 3 → 3 |
| adlittle | 2,928 → 2,928 | 15 → 15 | 2,208 → 2,208 | 3 → 3 |
| kb2 | 1,680 → 1,680 | 15 → 15 | 1,664 → 1,664 | 3 → 3 |
| sc50a | 17,760 → 17,760 | 60 → 60 | 1,808 → 1,808 | 3 → 3 |
| flugpl | 1,056 → 1,056 | 15 → 15 | 800 → 800 | 3 → 3 |

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 44,272 → 45,056 | 843 → 843 | 221,504 → 220,088 | 5,003 → 4,987 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 178,704 → 178,352 | 2,843 → 2,843 |
| kb2 | 111,376 → 112,304 | 2,060 → 2,060 | 162,304 → 161,968 | 2,836 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 303,312 → 302,032 | 6,647 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 220,008 → 218,168 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 735,624 → 733,864 | 870,648 → 869,784 | 848,408 → 847,976 | 0 |
| adlittle | 3,358,528 → 3,356,544 | 4,146,848 → 4,145,056 | 4,423,888 → 4,421,792 | 0 |
| kb2 | 10,685,208 → 10,681,928 | 11,137,800 → 11,136,200 | 11,151,672 → 11,148,888 | 0 |
| sc50a | 2,857,104 → 2,855,296 | 3,203,008 → 3,201,232 | 3,155,792 → 3,154,048 | 0 |
| flugpl | 1,208,080 → 1,204,216 | 1,317,864 → 1,314,112 | 1,362,248 → 1,358,752 | 80 |

Direct sparse aggregation removes 16 allocations for afiro. All other direct
pass counts are unchanged. Full presolve and both whole solves remove 80
allocations for flugpl; the other four fixtures retain their counts.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`zero-bound-shift-allocations-before.toml`](zero-bound-shift-allocations-before.toml)
and [`zero-bound-shift-allocations-after.toml`](zero-bound-shift-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=zero-bound-shift-basic-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=zero-bound-shift-doubleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=zero-bound-shift-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function zero_bound_shift_probe(kind; count=128)
    coefficient = kind in (:basic_negative,:sparse_negative) ? -2.0 : 2.0
    if kind in (:basic_positive,:basic_negative,:nonzero_bound)
        A = hcat(sparse(1:count,1:count,fill(coefficient,count),count,count),sparse(ones(count,1)))
        problem = LinearProblem(A,vcat(zeros(count),2.0);objective_constant=7.0,
            row_lower=fill(kind == :nonzero_bound ? 1.0 : 0.0,count),row_upper=fill(10.0,count),
            column_lower=vcat(fill(2.0,count),nothing),column_upper=vcat(fill(2.0,count),nothing))
        return problem,JSimplex._presolve_basic
    elseif kind == :doubleton
        A = sparse(hcat(vcat(2.0,fill(2.0,count)),vcat(1.0,fill(3.0,count))))
        problem = LinearProblem(A,[0.0,2.0];objective_constant=7.0,
            row_lower=vcat(4.0,zeros(count)),row_upper=vcat(4.0,fill(10.0,count)),
            column_lower=fill(nothing,2),column_upper=fill(nothing,2))
        return problem,JSimplex.substitute_free_doubleton
    end
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),ones(count),fill(coefficient,count),fill(3.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 0.0 : 2.0 for i in 1:2count];objective_constant=7.0,
        row_lower=[isodd(i) ? 4.0 : 0.0 for i in 1:2count],
        row_upper=[isodd(i) ? 4.0 : 10.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end
for kind in (:basic_positive, :basic_negative, :sparse_positive,
             :sparse_negative, :doubleton, :nonzero_bound)
    problem, pass = zero_bound_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 789 assertions and failed the
five target allocation guards. Basic probes allocated 15,217 and 15,180
objects, exceeding 14,350; sparse probes allocated 48,589 and 49,101,
exceeding 47,750 and 48,250; doubleton allocated 18,720, exceeding 17,900. The nonzero-bound control passed.
All 794 new assertions now pass as part of 16,302 targeted assertions
covering presolve and all three callers. Existing allocation budgets were not
relaxed.

Direct helper coverage includes Float32, Float64, BigFloat, and Rational{BigInt};
signed zero bounds; positive, negative, zero, binary, and nonbinary rational
shifts. Tests verify exact results/rejection and unchanged bounds. Zero-shift
and unbounded cases retain identity, including stored 256-bit BigFloat bounds
under ambient precision 32/64. Tiny nonzero bounds remain distinct from zero;
tiny representable shifts survive, and unrepresentable shifts remain rejected.

All three callers are checked with zero lower, upper, or both endpoints and
both coefficient signs. Tests compare reduced matrices, bounds, objectives,
primal restoration, and unchanged inputs. Half-subnormal shifts explicitly
exercise rejection by each caller; alternative doubleton pivots are bounded
so they cannot mask rejection of the intended candidate.

An independent read-only review found no issues. It reran all 794 focused
assertions and passed 3,360 additional assertions, including 280 helper
comparisons, 156 model comparisons across all three callers, and 624 basis
restorations. It checked signed zeros, tiny nonzero endpoints, underflow/overflow
rejection, reduced BigFloat precision, staged rejection followed by successful
elimination, and unchanged source/primal/basis inputs.

The complete `test/runtests.jl` suite passed 41,187/41,187 assertions in
5m12.4s (exit code zero), including all existing allocation guards.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
