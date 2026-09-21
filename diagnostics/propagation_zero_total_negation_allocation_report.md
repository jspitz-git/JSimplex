# Negate a column contribution when the total activity is zero

Round 81 replaces general subtraction `0 - term` with exact negation in
`_other_activity`. A single branch follows the existing checks for remaining
unbounded terms and absent/zero contributions. Those checks retain precedence;
nonzero totals continue through exact cancellation or general subtraction.
The negation creates a value without mutating the shared contribution.

Only an exact rational zero qualifies. Tiny nonzero activity totals remain
nonzero even when their original BigFloat bounds were stored at a higher
precision than the working precision. Candidate calculation, acceptance,
cache updates, worklist activation, and postsolve are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 80 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each probe has 128 independent rows `c*x[i] - c*y[i]`, with all objective
coefficients equal to one. The minimum-activity probe uses `c=2`, `x` in `[2,3]`,
`y` in `[1,2]`, and row upper bound one. The zero minimum activity yields
`x <= 2.5` and `y >= 1.5`. The maximum-activity probe uses `c=2`, `x` in `[1,2]`,
`y` in `[2,3]`, and row lower bound minus one. Its zero maximum activity yields
`x >= 1.5` and `y <= 2.5`. The unit probe uses the minimum case with `c=1` and
row upper bound 0.5.

The nonzero-total control uses `c=2`, `x` in `[3,4]`, `y` in `[1,2]`, and row
upper bound three. Its minimum activity is two, giving `x <= 3.5` and
`y >= 1.5`. The unbounded control uses the minimum case with no lower bound on
`x`; it tightens `x <= 2.5` while leaving the lower bounds unchanged.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero minimum, coefficient 2 | 1,289,856 | 1,218,160 | 5.56% | 36,303 → 34,511 |
| Zero maximum, coefficient 2 | 1,287,792 | 1,215,664 | 5.60% | 36,175 → 34,383 |
| Zero minimum, coefficient 1 | 1,079,136 | 1,007,600 | 6.63% | 31,311 → 29,519 |
| Nonzero-total control | 1,291,568 | 1,292,480 | — | 36,303 → 36,303 |
| Unbounded-activity control | 816,040 | 816,328 | — | 22,860 → 22,860 |

Each target removes 1,792 allocations. Both controls retain their allocation
counts. Small byte differences on unchanged paths reflect cross-process
exact-arithmetic variation; no benefit is claimed for those cases.

| Model | Propagation before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 90,504 → 90,792 | 2,437 → 2,437 | 781,600 → 781,088 |
| adlittle | 645,704 → 644,648 | 18,243 → 18,243 | 3,382,392 → 3,380,504 |
| kb2 | 470,024 → 468,696 | 13,262 → 13,262 | 10,758,024 → 10,756,632 |
| sc50a | 224,232 → 223,336 | 6,064 → 6,064 | 3,028,952 → 3,028,200 |
| flugpl | 125,224 → 124,136 | 3,297 → 3,297 | 1,263,928 → 1,263,240 |

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 918,160 → 917,168 | 896,192 → 896,288 | 0 |
| adlittle | 4,171,464 → 4,168,968 | 4,448,872 → 4,445,544 | 0 |
| kb2 | 11,214,248 → 11,211,080 | 11,227,176 → 11,223,560 | 0 |
| sc50a | 3,374,360 → 3,374,456 | 3,327,640 → 3,326,616 | 0 |
| flugpl | 1,374,160 → 1,373,360 | 1,418,576 → 1,417,792 | 0 |

All five fixtures retain their allocation counts in direct propagation, full
presolve, and whole dual/primal solves, including paths without presolve.
The byte variations alone do not establish a benefit on these fixtures.
The measured reduction is confined to the targeted zero-total probes.

All ten model snapshots (five fixtures × propagation/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`propagation-zero-total-negation-allocations-before.toml`](propagation-zero-total-negation-allocations-before.toml)
and [`propagation-zero-total-negation-allocations-after.toml`](propagation-zero-total-negation-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=propagation-zero-total-negation-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function propagation_zero_total_negation_probe(kind; count=128)
    coefficient = kind == :unit ? 1.0 : 2.0
    lower_side = kind == :maximum
    first_low, first_high = lower_side ? (1.0,2.0) : (2.0,3.0)
    second_low, second_high = lower_side ? (2.0,3.0) : (1.0,2.0)
    kind == :nonzero && ((first_low, first_high) = (3.0,4.0))
    A = sparse(vcat(collect(1:count),collect(1:count)),
        vcat(collect(1:count),collect(count+1:2count)),
        vcat(fill(coefficient,count),fill(-coefficient,count)),count,2count)
    endpoint = (lower_side ? -0.5 : kind == :nonzero ? 1.5 : 0.5)*coefficient
    return LinearProblem(A,ones(2count);
        row_lower=fill(lower_side ? endpoint : nothing,count),
        row_upper=fill(lower_side ? nothing : endpoint,count),
        column_lower=vcat(fill(kind == :unbounded ? nothing : first_low,count),fill(second_low,count)),
        column_upper=vcat(fill(first_high,count),fill(second_high,count)))
end
for kind in (:minimum, :maximum, :unit, :nonzero, :unbounded)
    problem = propagation_zero_total_negation_probe(kind)
    println(measure_allocations(_ -> JSimplex.propagate_row_bounds(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused test file passed 544 assertions and failed five
allocation guards. Both helper probes allocated 336 bytes, exceeding 176.
The three whole-pass probes allocated 36,348, 36,183, and 31,319 objects,
exceeding their budgets of 35,000, 34,900, and 30,000. Both controls passed.
All 549 new assertions now pass as part of 5,674 targeted propagation and
presolve assertions. Existing allocation budgets were not relaxed.

The helper cases check both signs, zero/absent contributions, remaining
unbounded terms, exact cancellation, unequal nonzero totals, optional shared
zero seeds, and input preservation. Whole-model coverage includes Float32,
Float64, BigFloat, and Rational{BigInt}; positive/negative unit and general
coefficients; zero minimum and maximum activities; lower and upper row bounds;
source preservation; changed flags; postsolve; and full/incremental activation
of a later row.

Stored 256-bit BigFloat bounds `2 ± 2^-200` produce tiny nonzero activity totals
and candidates `1.5 ± 2^-200`. At ambient precision 32/64 those candidates must
be rejected as unrepresentable, while an exact upper candidate of 2.5 is
accepted. The tests ensure that neither tiny total is incorrectly treated as
zero and that stored bound precision remains intact.

Independent review found no issues. All 549 focused assertions passed again.
A bounded saved-baseline comparison passed 1,076 assertions covering 28 helper
cases and 80 model cases, including full/incremental worklists, tiny residuals,
infeasible/unbounded cases, input preservation, and primal/basis restoration.

The full mandatory test suite passed **26,375/26,375 assertions** in 5m01.7s
with exit code zero.
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
