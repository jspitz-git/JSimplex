# Zero objective constants in sparse equality aggregation

Round 134 changes only addition in the objective-constant update of
`aggregate_sparse_equalities` in `src/presolve_aggregation.jl`. When the currently
committed exact constant is zero, the update now reuses the exact substitution
product instead of adding it to zero. Nonzero constants retain rational addition.
The preceding zero-ratio/zero-right-hand-side and signed-unit product shortcuts
retain their behavior.

The check uses the current constant, including earlier committed changes. The
`_represent_exact` gate still runs after the update. Objective-cost arithmetic,
pivot choice, staging and rejection ordering, matrix/bound updates, model
reconstruction, and primal/basis restoration are unchanged. No input is mutated
and no GMP internals or noncanonical constructor are used.

## Method and results

The baseline includes the preceding 133 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 probe contains 128 independent two-row blocks: equality
`2*x+3*y=rhs` and inequality `6*x<=20`. Variable x has bounds `[1,3]`, y is free,
and objective costs are `[2*ratio,nextfloat(0.0)]`. Four targets use ratios +3,
-3, +1, and -1, rhs four, and initial constant +0.0 for positive ratios or -0.0
for negative ratios.

Each candidate computes a representable constant product, then fails the retained
cost gate: `nextfloat(0.0)-3*ratio` is not exactly representable as Float64. The
retained column has degree one, preventing an alternative pivot. All 128
candidates are therefore rejected, the constant remains zero for the next
candidate, and the pass returns the original model with an empty postsolve stack.
The probes measure discovery, projection, objective arithmetic, and rejection;
they do not measure successful sparse reconstruction. Successful aggregations
and restoration are covered by separate regression and differential tests.

The nonzero-constant control uses constant seven, ratio three, and rhs four.
The zero-rhs control uses constant zero, ratio three, and rhs zero, taking the
preceding shortcut. Both controls also reject all candidates at the cost gate.
Input construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive nonunit ratio | 1,282,928 | 1,238,880 | 3.43% | 34,208 → 33,056 |
| Negative nonunit ratio | 1,284,480 | 1,241,488 | 3.35% | 34,208 → 33,056 |
| Positive unit ratio | 1,198,048 | 1,154,464 | 3.64% | 31,904 → 30,752 |
| Negative unit ratio | 1,212,384 | 1,168,800 | 3.59% | 32,416 → 31,264 |
| Nonzero-constant control | 1,284,984 | 1,284,600 | — | 34,211 → 34,211 |
| Zero-rhs control | 1,106,672 | 1,106,512 | — | 29,344 → 29,344 |

All four targets save **1,152 allocations per call (nine per rejected candidate)**.
Allocated bytes decrease by **3.35–3.64%**.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,472 → 45,088 |
| afiro | sparse | 4,900 → 4,891 | 214,560 → 213,856 |
| afiro | presolve | 16,242 → 16,242 | 729,920 → 728,976 |
| afiro | dual | 17,057 → 17,057 | 865,136 → 864,160 |
| afiro | primal | 16,963 → 16,963 | 843,072 → 842,496 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,778 → 2,751 | 175,224 → 173,992 |
| adlittle | presolve | 82,679 → 82,661 | 3,343,568 → 3,341,648 |
| adlittle | dual | 84,694 → 84,676 | 4,134,336 → 4,131,232 |
| adlittle | primal | 85,492 → 85,474 | 4,410,656 → 4,408,176 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,480 → 461,352 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,504 → 607,664 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,128 → 112,272 |
| kb2 | sparse | 2,836 → 2,836 | 161,808 → 161,712 |
| kb2 | presolve | 229,911 → 229,911 | 10,676,752 → 10,673,376 |
| kb2 | dual | 231,113 → 231,113 | 11,129,568 → 11,128,432 |
| kb2 | primal | 231,280 → 231,280 | 11,144,000 → 11,141,632 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,856 → 878,016 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,864 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,488 → 298,880 |
| sc50a | presolve | 67,503 → 67,503 | 2,848,784 → 2,847,200 |
| sc50a | dual | 68,575 → 68,575 | 3,194,400 → 3,192,864 |
| sc50a | primal | 68,520 → 68,520 | 3,146,880 → 3,145,600 |
| sc50a | dual_no_presolve | 961 → 961 | 306,192 → 306,128 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,232 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 209,976 → 209,512 |
| flugpl | presolve | 31,011 → 31,011 | 1,181,592 → 1,180,312 |
| flugpl | dual | 31,682 → 31,682 | 1,290,400 → 1,290,016 |
| flugpl | primal | 32,031 → 32,031 | 1,334,800 → 1,334,448 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Adlittle saves 18 allocations in full presolve and each presolved solve; direct
sparse aggregation saves 27 for adlittle and nine for afiro. Every other measured
reference-stage count is unchanged, including all solves without presolve.
Direct-pass and full-pipeline savings differ because preceding passes transform
the models and their objective constants.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, full primal vector, and
iteration count (`isequal`).

Machine-readable results:
[`aggregation-zero-objective-constant-allocations-before.toml`](aggregation-zero-objective-constant-allocations-before.toml)
and [`aggregation-zero-objective-constant-allocations-after.toml`](aggregation-zero-objective-constant-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-zero-objective-constant-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_zero_objective_constant_probe(kind; count=128)
    ratio = kind == :unit_positive ? 1.0 : kind == :unit_negative ? -1.0 : kind == :negative ? -3.0 : 3.0
    rhs = kind == :zero_rhs ? 0.0 : 4.0
    constant = kind == :nonzero_constant ? 7.0 : kind in (:negative,:unit_negative) ? -0.0 : 0.0
    odd = collect(1:2:2count); even = odd .+ 1
    # The retained column has degree one, so a rejected x pivot cannot be
    # replaced by a y pivot. Every block fails the retained-cost exactness gate.
    A = sparse(vcat(odd,odd,even),vcat(odd,even,odd),
        vcat(fill(2.0,count),fill(3.0,count),fill(6.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 2ratio : nextfloat(0.0) for i in 1:2count];objective_constant=constant,
        row_lower=Union{Nothing,Float64}[isodd(i) ? rhs : nothing for i in 1:2count],
        row_upper=[isodd(i) ? rhs : 20.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_constant,:zero_rhs)
    problem, pass = aggregation_zero_objective_constant_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,826 assertions** and failed only
the four target allocation guards: 34,253 > 33,600; 34,216 > 33,600;
31,912 > 31,300; and 32,424 > 31,800. Both control budgets
passed. There are **2,830 new assertions**; existing allocation budgets were not relaxed.

Successful aggregations cover Float32, Float64, BigFloat, and Rational{BigInt};
signed unit/nonunit ratios and right-hand sides, positive/negative zero constants,
finite and implied column-bound projections, objective costs, matrix and bound
results, primal restoration, exact objective equivalence, and source immutability.
Three sequential candidates check transitions into and out of zero using committed
constant state. BigFloat checks cover stored 256-bit values under ambient precision
32/64/256, tiny/exact/inexact products, output precision, and representability
rejection. Large rational cases use numerators derived from `2^300+1` and
non-dyadic denominators 5, 7, 15, and 21. Overflow, half-subnormal products, and
tiny nonzero old constants retain rejection without source mutation;
retained-column degree one prevents unrelated alternative pivots.

The combined presolve/basic/doubleton/aggregation targeted suite passed
**63,616 assertions** in **1m31.0s**, exit code zero.

Independent read-only differential review found no blocking issues and passed
**4,464 assertions across 136 models** (107 accepted, 29 identity-rejected; 158
aggregation records), exit code zero. It compared 408 primal restorations,
544 basis restorations, 272 primal-dimension cases, and 272 basis-dimension cases.
Eighteen late cost/matrix/bound rollbacks and 16 rational ownership cases passed.
Committed zero/nonzero transitions, stored BigFloat precision gates, floating
edge rejection, exact objective/CSC structure, and restoration matched baseline.

Ownership note: direct reuse of a `Rational{BigInt}` unit product can newly share
input scalar storage. The 16 ownership cases observed source numerator identity
in eight cases and denominator identity in all 16 (baseline zero and zero).
Canonical values and ordinary arithmetic/result-array mutation preserve source
values. This matches existing shallow scalar ownership in the model constructor
(`src/model.jl:105`); no guarantee of independently mutable internal BigInts is
introduced.

The complete `test/runtests.jl` suite passed **88,501 assertions** in
**5m48.3s**, exit code zero, using:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
