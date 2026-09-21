# Zero retained costs in singleton aggregation

Round 149 changes only retained objective coefficient subtraction in
`aggregate_singleton_equalities` in `src/presolve_aggregation.jl`. When the
current staged retained cost is exactly zero, the already computed product is
negated directly instead of subtracted from zero. Nonzero costs retain general
subtraction. The preceding zero-ratio and signed-unit product shortcuts remain
unchanged, as do all representability checks and the Float32/64 singleton
objective-rounding policy.

The test uses the current committed cost, so it works after earlier eliminations
leave or return to zero. Tiny nonzero values are not classified as zero.
BigFloat and Rational{BigInt} costs still require exact representation. Constant
updates, projection, candidate ordering, staging, rollback, and primal/basis
restoration are unchanged. Public rational negation is nonmutating; it can share
a denominator with its operand, consistent with existing scalar reuse paths.
Deep ownership against mutation through internal GMP APIs is not a model contract.

## Method and results

The baseline includes the preceding 148 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 singleton columns and one shared retained column, with
`2*x_i+3*y=4`, x_i bounds `[1,3]`, and free y. Objective ratios alternate signs,
starting at 3, -3, 1, or -1. Each x_i price is twice its ratio; the retained
price starts at zero (negative zero for negative first ratios), and the objective
constant starts at seven. All eliminations succeed. The retained cost alternates
between zero and the negated first product, so 64 updates use the new shortcut.
After 128 eliminations, the retained cost is canonical zero, the constant is
seven, and all projected rows have coefficient three and bounds `[-2,2]`.
Measurement includes projection, staging, objective updates and reconstruction.

The nonzero-cost control starts at five with alternating ratios 3 and -3,
so the retained cost alternates between five and minus four and never takes
the new branch. The zero-ratio control retains the earlier direct cost reuse
path. Both controls accept all pivots. Input construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| First ratio 3 | 1,011,256 | 992,792 | 1.83% | 26,682 → 26,234 |
| First ratio -3 | 1,011,816 | 994,296 | 1.73% | 26,682 → 26,234 |
| First ratio 1 | 931,928 | 914,296 | 1.89% | 24,634 → 24,186 |
| First ratio -1 | 931,976 | 914,376 | 1.89% | 24,634 → 24,186 |
| Nonzero-cost control | 1,016,488 | 1,017,272 | — | 26,880 → 26,880 |
| Zero-ratio control | 767,880 | 768,696 | — | 19,578 → 19,578 |

Allocated bytes decrease by **1.73–1.89%** across the four targets.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

- `positive` saves **448 allocations per call**, or 7 per zero-cost update.
- `negative` saves **448 allocations per call**, or 7 per zero-cost update.
- `unit_positive` saves **448 allocations per call**, or 7 per zero-cost update.
- `unit_negative` saves **448 allocations per call**, or 7 per zero-cost update.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 782 → 747 | 42,248 → 41,008 |
| afiro | sparse | 4,891 → 4,891 | 214,768 → 214,240 |
| afiro | propagation | 2,437 → 2,437 | 93,192 → 92,888 |
| afiro | presolve | 16,156 → 16,121 | 727,264 → 724,824 |
| afiro | dual | 16,971 → 16,936 | 862,656 → 861,032 |
| afiro | primal | 16,877 → 16,842 | 841,728 → 839,096 |
| afiro | dual_no_presolve | 555 → 555 | 89,936 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,776 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,747 → 2,747 | 174,104 → 175,000 |
| adlittle | propagation | 18,182 → 18,182 | 642,984 → 642,264 |
| adlittle | presolve | 82,433 → 82,433 | 3,327,640 → 3,328,424 |
| adlittle | dual | 84,448 → 84,448 | 4,117,160 → 4,116,808 |
| adlittle | primal | 85,246 → 85,246 | 4,394,040 → 4,394,568 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,576 → 461,224 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,424 → 607,792 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,964 → 1,915 | 107,072 → 105,544 |
| kb2 | sparse | 2,836 → 2,836 | 162,400 → 162,448 |
| kb2 | propagation | 12,948 → 12,948 | 455,600 → 455,520 |
| kb2 | presolve | 229,098 → 229,049 | 10,637,728 → 10,635,784 |
| kb2 | dual | 230,300 → 230,251 | 11,091,696 → 11,087,752 |
| kb2 | primal | 230,467 → 230,418 | 11,105,680 → 11,100,568 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,984 → 878,240 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 300,256 → 300,016 |
| sc50a | propagation | 6,020 → 6,020 | 223,456 → 222,720 |
| sc50a | presolve | 67,457 → 67,457 | 2,847,512 → 2,846,936 |
| sc50a | dual | 68,529 → 68,529 | 3,193,768 → 3,191,848 |
| sc50a | primal | 68,474 → 68,474 | 3,146,184 → 3,144,952 |
| sc50a | dual_no_presolve | 961 → 961 | 306,176 → 306,288 |
| sc50a | primal_no_presolve | 964 → 964 | 232,184 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 210,904 → 210,792 |
| flugpl | propagation | 3,253 → 3,253 | 123,792 → 123,024 |
| flugpl | presolve | 30,791 → 30,791 | 1,172,096 → 1,170,352 |
| flugpl | dual | 31,462 → 31,462 | 1,280,840 → 1,279,784 |
| flugpl | primal | 31,811 → 31,811 | 1,325,800 → 1,324,232 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

The standalone singleton pass, full presolve, and both solves with presolve
each save **35 allocations on afiro** and **49 on kb2**. The other 42 reference
measurements retain their allocation counts, including all solves without
presolve.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`singleton-zero-retained-cost-allocations-before.toml`](singleton-zero-retained-cost-allocations-before.toml)
and [`singleton-zero-retained-cost-allocations-after.toml`](singleton-zero-retained-cost-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=singleton-zero-retained-cost-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function singleton_zero_retained_cost_probe(kind; count=128, T=Float64)
    ratio=kind==:unit_positive ? 1 : kind==:unit_negative ? -1 : kind==:negative ? -3 : kind==:zero_ratio ? 0 : 3
    old=kind==:nonzero_cost ? T(5) : ratio<0 ? -zero(T) : zero(T)
    prices=T[isodd(i) ? 2ratio : -2ratio for i in 1:count]
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(fill(T(3),count,1)))
    problem=LinearProblem(A,[prices;old];objective_constant=T(7),
        row_lower=fill(T(4),count),row_upper=fill(T(4),count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end

for kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_cost,:zero_ratio)
    problem, pass = singleton_zero_retained_cost_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **4,048 assertions** and failed only
the four target allocation guards: 26,727 and 26,690 against 26,482, and two
cases of 24,642 against 24,434. Both control budgets passed. There are
**4,052 new assertions**; existing budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; signed zero
costs; signed unit/nonunit factors; zero-ratio control; sequential updates leaving
and returning to zero; odd/even elimination counts; finite/free bounds; projected
matrix/bounds/objective; restored primal and basis; objective equivalence;
canonical rational values; and source preservation under ordinary arithmetic
and output mutation.

BigFloat tests use stored 256-bit inputs at ambient precision 32/64/256. Direct
products `±(3+2^-200)` reject at lower precision, while three and `2^-200` are
exactly representable. Tiny nonzero retained costs `±2^-200` minus one also reject
at low precision; they must not be treated as zero. Float32/64 tests preserve
permitted rounding of tiny-nonzero-cost and one-third updates, and retain
rejection for overflow and half-subnormal products. The retained column has
degree two to prevent unrelated alternate singleton candidates. Large rational
cases cover both factor positions, signs, and denominators 5, 7, 15, and 21.

The targeted presolve/allocation suite passed **97,900 / 97,900 assertions**
in 2m01.9s, including every new allocation guard.

Independent read-only review found no issues. An AST-renamed baseline passed
**2,795 assertions across 156 differential models**, covering all numeric types
and ambient BigFloat precisions, signed-zero/tiny nonzero costs, unit/nonunit
products, sequential zero transitions, precision and rejection gates, rollback,
projected/free/fixed bounds, exact-candidate preference and permitted rounding,
primal/basis restoration, and source preservation after public rational
arithmetic and output mutation. An informational alias check confirmed that
rational negation shares its denominator while subtraction from zero copies it;
public value semantics are preserved.

The full test suite passed **117,397 / 117,397 assertions** in **6m18.7s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
