# Zero constant shifts in sparse equality aggregation

Round 130 changes only the shortcut condition for the objective-constant update
in `aggregate_sparse_equalities` in `src/presolve_aggregation.jl`. An exact zero
right-hand side now reuses the currently committed exact constant, skipping
multiplication and addition. A zero objective ratio already used this branch.
Nonzero right-hand sides keep the preceding signed-unit product shortcuts and
ordinary exact arithmetic.

The `_represent_exact` gate still runs even when the constant does not change.
This preserves rejection of stored high-precision BigFloat constants that cannot
be represented at ambient precision. Objective-cost arithmetic and its gates,
pivot choice, private staging, rejection ordering, matrix/bound updates, model
reconstruction, and primal/basis restoration are unchanged. Exact comparisons
distinguish zero from tiny nonzero right-hand sides. No input is mutated and no
GMP internals or noncanonical constructor are used.

## Method and results

The baseline includes the preceding 129 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 probe contains 128 independent two-row blocks: equality
`2*x+3*y=rhs` and inequality `6*x+5*y<=20`. Variable x has bounds `[1,3]`,
y is free, objective costs are `[2*ratio,5]`, and the initial model constant is
seven. Every block eliminates x and retains the equality as a projection of its
bounds. Four targets use ratios +3, -3, +1, and -1 respectively. Positive ratios
use rhs +0.0 and negative ratios use rhs -0.0.

All 128 blocks aggregate successfully, returning a 256-by-128 matrix. In the
zero-rhs targets the constant stays seven and each affected upper bound stays
20. Retained costs become `5-3*ratio`. Measurement includes staging, sparse
reconstruction, model construction, and postsolve metadata. The nonzero-rhs
control uses ratio three and rhs four; the zero-ratio control uses ratio zero
and rhs zero. Both succeed. Input construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive nonunit ratio | 1,773,056 | 1,690,240 | 4.67% | 45,893 → 43,845 |
| Negative nonunit ratio | 1,775,152 | 1,692,448 | 4.66% | 45,893 → 43,845 |
| Positive unit ratio | 1,693,968 | 1,649,120 | 2.65% | 43,845 → 42,693 |
| Negative unit ratio | 1,707,248 | 1,656,624 | 2.97% | 44,357 → 42,949 |
| Nonzero-rhs control | 2,077,392 | 2,076,544 | — | 54,085 → 54,085 |
| Zero-ratio control | 1,507,040 | 1,506,608 | — | 38,469 → 38,469 |

The two nonunit targets save **2,048 allocations per call (16 per candidate)**.
The positive-unit target saves **1,152 (nine per candidate)** and the negative-unit
target **1,408 (11 per candidate)**. Allocated bytes decrease by
**2.65–4.67%**. Both controls retain their allocation counts.
Cross-process byte differences on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,528 → 45,504 |
| afiro | sparse | 4,950 → 4,935 | 217,480 → 215,704 |
| afiro | presolve | 16,293 → 16,277 | 731,720 → 729,880 |
| afiro | dual | 17,108 → 17,092 | 867,064 → 866,216 |
| afiro | primal | 17,014 → 16,998 | 845,656 → 844,424 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,824 → 2,792 | 177,784 → 176,056 |
| adlittle | presolve | 82,757 → 82,693 | 3,348,224 → 3,345,520 |
| adlittle | dual | 84,772 → 84,708 | 4,137,344 → 4,132,848 |
| adlittle | primal | 85,570 → 85,506 | 4,414,336 → 4,409,408 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,288 → 461,384 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,264 → 607,440 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 111,632 → 112,656 |
| kb2 | sparse | 2,836 → 2,836 | 162,560 → 162,032 |
| kb2 | presolve | 229,977 → 229,932 | 10,679,688 → 10,676,168 |
| kb2 | dual | 231,179 → 231,134 | 11,131,128 → 11,129,992 |
| kb2 | primal | 231,346 → 231,301 | 11,145,496 → 11,143,832 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,032 → 878,016 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,864 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,635 → 6,625 | 300,368 → 299,544 |
| sc50a | presolve | 67,608 → 67,538 | 2,854,480 → 2,849,176 |
| sc50a | dual | 68,680 → 68,610 | 3,198,640 → 3,196,024 |
| sc50a | primal | 68,625 → 68,555 | 3,151,504 → 3,149,080 |
| sc50a | dual_no_presolve | 961 → 961 | 306,112 → 306,160 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,763 → 5,598 | 217,928 → 210,296 |
| flugpl | presolve | 31,461 → 31,011 | 1,200,104 → 1,181,224 |
| flugpl | dual | 32,132 → 31,682 | 1,309,808 → 1,290,576 |
| flugpl | primal | 32,481 → 32,031 | 1,354,208 → 1,335,184 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

Full presolve and each presolved solve save 16 allocations for afiro, 64 for
adlittle, 45 for kb2, 70 for sc50a, and 450 for flugpl. Direct sparse aggregation
saves 15, 32, zero, 10, and 165 respectively. All other measured stages retain
their allocation counts, including every solve without presolve. Direct-pass
and full-pipeline savings differ because preceding passes transform the models.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, full primal vector, and
iteration count (`isequal`).

Machine-readable results:
[`aggregation-zero-constant-shift-allocations-before.toml`](aggregation-zero-constant-shift-allocations-before.toml)
and [`aggregation-zero-constant-shift-allocations-after.toml`](aggregation-zero-constant-shift-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-zero-constant-shift-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function aggregation_zero_constant_shift_probe(kind; count=128)
    ratio = kind == :unit_positive ? 1.0 : kind == :unit_negative ? -1.0 : kind == :zero_ratio ? 0.0 : kind == :negative ? -3.0 : 3.0
    rhs = kind == :nonzero_rhs ? 4.0 : kind in (:negative,:unit_negative) ? -0.0 : 0.0
    term = 3.0
    odd = collect(1:2:2count); even = odd .+ 1
    A = sparse(vcat(odd,odd,even,even),vcat(odd,even,odd,even),
        vcat(fill(2.0,count),fill(term,count),fill(6.0,count),fill(5.0,count)),2count,2count)
    problem = LinearProblem(A,[isodd(i) ? 2ratio : 5.0 for i in 1:2count];objective_constant=7.0,
        row_lower=Union{Nothing,Float64}[isodd(i) ? rhs : nothing for i in 1:2count],
        row_upper=[isodd(i) ? rhs : 20.0 for i in 1:2count],
        column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
        column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
    return problem,JSimplex.aggregate_sparse_equalities
end

for kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_rhs,:zero_ratio)
    problem, pass = aggregation_zero_constant_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,254 assertions** and failed only
the four target allocation guards: 45,938 > 45,000; 45,901 > 45,000;
43,853 > 43,400; and 44,365 > 43,900. Both control budgets
passed. There are **2,258 new assertions**; existing allocation budgets were not relaxed.

Accepted aggregations cover Float32, Float64, BigFloat, and Rational{BigInt};
signed unit/nonunit ratios, positive and negative zero right-hand sides and
constants, finite and implied column-bound projections, updated costs, matrix
and bound results, primal restoration, exact objective equivalence, and source
immutability. Sequential candidates check preservation of previously committed
constant shifts. BigFloat checks cover stored 256-bit values under ambient
precision 32/64/256, unit and high-precision nonunit ratios, tiny/exact/inexact
constants, output precision, unchanged affected-bound precision, and
representability rejection. Tiny nonzero right-hand sides retain their exact
contribution. Large rational cases use numerators derived from `2^300+1` and
non-dyadic denominators 5, 7, 15, and 21.

The combined presolve/basic/doubleton/aggregation targeted suite passed
**53,060 assertions** in **1m30.1s**, exit code zero.

Independent read-only differential review found no actionable issues and passed
**4,191 assertions across 128 models** (103 accepted, 25 rejected; 122
aggregation records), exit code zero. It compared 384 primal restorations,
512 basis restorations, 256 primal-dimension cases, 256 basis-dimension cases,
and verified 18 late cost/matrix/bound rollbacks plus eight rational alias cases.
Exact objective/CSC and result snapshots matched the pre-change function,
including stored-precision gates, tiny nonzero rhs, signed zero, and accumulated
constants.

Ownership note: for `Rational{BigInt}`, zero-rhs reductions now retain the source
constant numerator/denominator identity, as the existing zero-ratio shortcut
already does. Ordinary public arithmetic and output-array updates preserve the
source. This matches the shallow scalar ownership of the model constructor
(`src/model.jl:105`); no guarantee of independently mutable internal BigInts is
introduced.

The complete `test/runtests.jl` suite passed **77,945 assertions** in
**5m50.1s**, exit code zero, using:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
