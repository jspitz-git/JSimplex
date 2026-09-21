# Equal-denominator objective sums in basic presolve

Round 113 changes only `_presolve_basic` in `src/presolve.jl`.
When the exact accumulated constant and exact nonzero contribution have the
same denominator, their numerators are added directly. A zero numerator becomes
canonical exact zero; other sums use the canonical `Rational{BigInt}` constructor
with their shared denominator. Unequal denominators retain the existing rational
addition. Prior zero-contribution, signed-unit, and zero-constant shortcuts remain.

The canonical constructor still reduces fractions, including when the new
numerator shares factors with the denominator. No mutable input is modified and
no GMP internals are used. `_represent_exact` still checks the resulting constant
before row staging. Rejection, row-bound checks, staged updates, removed values/
states, empty-row checks, and primal/basis restoration are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 112 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each probe has 128 rows `x_i+2*y`, fixed `x_i`, unbounded row endpoints, and
retained `y` with bounds `[-10,10]` and cost three. Cancellation targets use
cost three, initial constant zero, and `x_i` alternating +2/-2 (or -2/+2).
They exercise 64 equal-denominator cancellations per call. Noncancelling targets
fix every `x_i=2`, use cost +3/-3 and initial constant +7/-7, and exercise 128
equal-denominator nonzero sums per call. All these exact denominators are one.

The unequal-denominator control uses initial constant 1/2, cost three, and
`x_i=2`: its constant keeps denominator two while contributions have denominator
one. The zero-contribution control uses cost zero, initial constant -0, and
`x_i=2`. Model construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Cancellation, positive first | 292,496 | 280,128 | 4.23% | 7,364 → 7,172 |
| Cancellation, negative first | 293,504 | 281,680 | 4.03% | 7,364 → 7,172 |
| Positive nonzero sums | 343,552 | 329,168 | 4.19% | 8,900 → 8,644 |
| Negative nonzero sums | 343,504 | 328,880 | 4.26% | 8,900 → 8,644 |
| Unequal-denominator control | 343,536 | 343,824 | — | 8,900 → 8,900 |
| Zero-contribution control | 75,664 | 75,072 | — | 1,604 → 1,604 |

Cancellation probes save 192 allocations per call (three per each of 64
cancellations). Nonzero-sum probes save 256 per call (two per each of 128 sums).
Allocated bytes drop by 4.03–4.26% across the four targets. Both controls retain their allocation counts; byte differences
on unchanged paths alone establish no benefit.

The following table gives all nine measured stages for each reference fixture.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,864 → 45,088 |
| afiro | sparse | 4,987 → 4,987 | 219,272 → 218,840 |
| afiro | presolve | 16,330 → 16,330 | 733,384 → 732,776 |
| afiro | dual | 17,145 → 17,145 | 869,496 → 868,712 |
| afiro | primal | 17,051 → 17,051 | 846,968 → 847,048 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 178,608 → 177,920 |
| adlittle | presolve | 82,776 → 82,776 | 3,349,080 → 3,347,048 |
| adlittle | dual | 84,791 → 84,791 | 4,138,040 → 4,137,096 |
| adlittle | primal | 85,589 → 85,589 | 4,414,760 → 4,414,168 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,720 → 461,512 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,312 → 607,168 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,576 → 112,816 |
| kb2 | sparse | 2,836 → 2,836 | 162,432 → 161,632 |
| kb2 | presolve | 230,004 → 230,004 | 10,680,248 → 10,678,632 |
| kb2 | dual | 231,206 → 231,206 | 11,134,008 → 11,131,176 |
| kb2 | primal | 231,373 → 231,373 | 11,146,856 → 11,145,032 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,176 → 878,080 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 301,408 → 300,896 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,872 → 2,853,904 |
| sc50a | dual | 68,706 → 68,706 | 3,199,472 → 3,199,408 |
| sc50a | primal | 68,651 → 68,651 | 3,152,160 → 3,151,824 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,288 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 218,056 → 217,256 |
| flugpl | presolve | 31,461 → 31,461 | 1,200,648 → 1,200,808 |
| flugpl | dual | 32,132 → 32,132 | 1,310,544 → 1,310,800 |
| flugpl | primal | 32,481 → 32,481 | 1,355,088 → 1,355,520 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All five reference fixtures retain their allocation counts in every measured
stage. They establish unchanged behavior; they show no allocation-count benefit
from this particular shortcut.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, complete primal vector,
and iteration count (`isequal`).

Machine-readable results:
[`basic-equal-denominator-allocations-before.toml`](basic-equal-denominator-allocations-before.toml)
and [`basic-equal-denominator-allocations-after.toml`](basic-equal-denominator-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=basic-equal-denominator-basic-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function basic_equal_denominator_probe(kind; count=128, T=Float64)
    values = T[kind in (:cancel_positive,:cancel_negative) ? (kind == :cancel_negative ? -1 : 1)*(isodd(i) ? 2 : -2) : 2 for i in 1:count]
    cost = T(kind == :zero_contribution ? 0 : kind == :negative_sum ? -3 : 3)
    constant = kind in (:cancel_positive,:cancel_negative) ? zero(T) : kind == :zero_contribution ? -zero(T) : kind == :unequal_denominator ? T(1)/T(2) : T(kind == :negative_sum ? -7 : 7)
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),fill(count+1,count)),vcat(ones(T,count),fill(T(2),count)),count,count+1)
    problem = LinearProblem(A,vcat(fill(cost,count),T[3]);objective_constant=constant,
        row_lower=fill(nothing,count),row_upper=fill(nothing,count),
        column_lower=vcat(values,T[-10]),column_upper=vcat(values,T[10]))
    return problem,JSimplex._presolve_basic
end
for kind in (:cancel_positive,:cancel_negative,:positive_sum,:negative_sum,:unequal_denominator,:zero_contribution)
    problem, pass = basic_equal_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 1,358 assertions and failed only the
four target allocation guards: 7,409 > 7,300; 7,372 > 7,300;
and 8,908 > 8,800 (two cases). Both controls passed. All 1,362 new assertions
now pass as part of 28,136 targeted assertions covering basic elimination
and related presolve allocation guards. Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; cancellation
and nonzero sums of both signs; unequal-denominator and zero-contribution
controls; computed/cached selections; retained matrices, bounds, objective
values, primal/basis restoration, removed states, and source/selection
immutability. Fractional sums with shared denominators 1/2/4/8/16 retain their
canonical reduction, including denominator changes between eliminations.
Stored-256-bit BigFloat operands under ambient precision 32/64/256 preserve
tiny nonzero residuals and reject nonrepresentable sums. Overflowing sums still
reject elimination. Earlier row-bound and objective-precision checks remain
in the targeted suite.

Independent read-only review found no correctness issues. It passed 11,892
additional assertions, separate from the focused 1,362, against an AST-renamed
copy of the preceding basic-presolve implementation: 484 model comparisons,
1,744 basis comparisons, and 48 matching failure records. Coverage included
non-dyadic fractions, 300-bit rational numerators, denominator transitions,
cancellation, stored-256-bit BigFloat values under ambient precision 32/64/256,
overflow and staged rejection, cached selections, empty/free columns, signed
zero, source aliases, and primal restoration. Constructor inspection confirmed
canonical reduction and sign normalization; exact cancellation yields 0//1.

The mandatory full package suite passed **53,021/53,021** assertions in
5m32.9s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
