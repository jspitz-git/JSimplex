# Cancelled retained costs in singleton aggregation

Round 150 changes only retained objective coefficient subtraction in
`aggregate_singleton_equalities` in `src/presolve_aggregation.jl`. When the
current staged cost equals the exact ratio/matrix-term product, the result is
canonical rational zero. Other nonzero costs retain general subtraction. The
preceding zero-ratio, signed-unit product, and zero-old-cost shortcuts are
unchanged, as are the representability gates and Float32/64 singleton rounding.

Comparison uses exact rational values at full stored precision. Adjacent floats
and tiny BigFloat residuals must not be treated as cancellation. The check uses
the current committed cost, including after earlier eliminations. Constant
updates, projection, candidate selection, staging, rollback and primal/basis
restoration remain unchanged. No operands are mutated.

## Method and results

The baseline includes the preceding 149 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 singleton columns and one shared retained column, with
`2*x_i+3*y=4`, x_i bounds `[1,3]`, and free y. Objective ratios alternate signs,
starting at 3, -3, 1, or -1. Each x_i price is twice its ratio. The retained
price starts at three times the first ratio, and the constant starts at seven.
All eliminations succeed. The first update cancels the retained price, the
second restores its initial value, and this repeats for 64 exact cancellations.
The other 64 updates use the preceding zero-old-cost shortcut. After all 128
eliminations the retained cost equals its initial value, the constant is seven,
and projected rows have coefficient three and bounds `[-2,2]`. Measurement
includes projection, staging, objective updates and reconstruction.

The noncancelling control (`nonzero_cost`) starts at five with alternating ratios
3 and -3, so the retained cost alternates between five and minus four without
cancellation. The zero-ratio control retains the preceding direct cost reuse
path. Both controls accept all pivots. Input construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| First ratio 3 | 992,104 | 978,472 | 1.37% | 26,240 → 25,920 |
| First ratio -3 | 992,328 | 979,592 | 1.28% | 26,240 → 25,920 |
| First ratio 1 | 912,760 | 899,384 | 1.47% | 24,192 → 23,872 |
| First ratio -1 | 912,904 | 899,576 | 1.46% | 24,192 → 23,872 |
| Noncancelling control | 1,015,432 | 1,016,744 | — | 26,880 → 26,880 |
| Zero-ratio control | 766,856 | 768,216 | — | 19,578 → 19,578 |

Allocated bytes decrease by **1.28–1.47%** across the four targets.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

- `positive` saves **320 allocations per call**, or 5 per exact cancellation.
- `negative` saves **320 allocations per call**, or 5 per exact cancellation.
- `unit_positive` saves **320 allocations per call**, or 5 per exact cancellation.
- `unit_negative` saves **320 allocations per call**, or 5 per exact cancellation.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 40,640 → 40,896 |
| afiro | sparse | 4,891 → 4,891 | 213,504 → 214,080 |
| afiro | propagation | 2,437 → 2,437 | 92,536 → 92,664 |
| afiro | presolve | 16,121 → 16,121 | 724,616 → 725,992 |
| afiro | dual | 16,936 → 16,936 | 860,056 → 860,936 |
| afiro | primal | 16,842 → 16,842 | 838,424 → 839,960 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,936 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,747 → 2,747 | 174,616 → 174,488 |
| adlittle | propagation | 18,182 → 18,182 | 641,784 → 643,544 |
| adlittle | presolve | 82,433 → 82,433 | 3,326,664 → 3,328,840 |
| adlittle | dual | 84,448 → 84,448 | 4,115,544 → 4,116,792 |
| adlittle | primal | 85,246 → 85,246 | 4,391,272 → 4,393,656 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,496 → 461,384 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,680 → 607,472 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,192 → 105,704 |
| kb2 | sparse | 2,836 → 2,836 | 161,920 → 162,064 |
| kb2 | propagation | 12,948 → 12,948 | 454,400 → 455,296 |
| kb2 | presolve | 229,049 → 229,049 | 10,632,712 → 10,634,504 |
| kb2 | dual | 230,251 → 230,251 | 11,085,864 → 11,087,096 |
| kb2 | primal | 230,418 → 230,418 | 11,100,728 → 11,101,720 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,256 → 877,920 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,896 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 298,992 → 299,824 |
| sc50a | propagation | 6,020 → 6,020 | 221,648 → 222,448 |
| sc50a | presolve | 67,457 → 67,457 | 2,845,800 → 2,848,184 |
| sc50a | dual | 68,529 → 68,529 | 3,191,800 → 3,194,344 |
| sc50a | primal | 68,474 → 68,474 | 3,144,664 → 3,147,128 |
| sc50a | dual_no_presolve | 961 → 961 | 306,176 → 306,096 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,184 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 209,432 → 210,984 |
| flugpl | propagation | 3,253 → 3,253 | 122,976 → 123,232 |
| flugpl | presolve | 30,791 → 30,791 | 1,169,920 → 1,172,368 |
| flugpl | dual | 31,462 → 31,462 | 1,279,400 → 1,281,016 |
| flugpl | primal | 31,811 → 31,811 | 1,323,848 → 1,326,056 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All 50 reference measurements retain their allocation counts. These fixtures
do not show a measurable benefit from this particular cancellation shortcut.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`singleton-cancelled-retained-cost-allocations-before.toml`](singleton-cancelled-retained-cost-allocations-before.toml)
and [`singleton-cancelled-retained-cost-allocations-after.toml`](singleton-cancelled-retained-cost-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=singleton-cancelled-retained-cost-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function singleton_cancelled_retained_cost_probe(kind; count=128, T=Float64)
    ratio=kind==:unit_positive ? 1 : kind==:unit_negative ? -1 : kind==:negative ? -3 : kind==:zero_ratio ? 0 : 3
    old=kind==:nonzero_cost ? T(5) : T(3ratio)
    prices=T[isodd(i) ? 2ratio : -2ratio for i in 1:count]
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(fill(T(3),count,1)))
    problem=LinearProblem(A,[prices;old];objective_constant=T(7),
        row_lower=fill(T(4),count),row_upper=fill(T(4),count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end

for kind in (:positive,:negative,:unit_positive,:unit_negative,:nonzero_cost,:zero_ratio)
    problem, pass = singleton_cancelled_retained_cost_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **3,098 assertions** and failed only
the four target allocation guards: 26,285 and 26,248 against 26,100, and two
cases of 24,200 against 24,052. Both control budgets passed. There are
**3,102 new assertions**; existing budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; signed
integer/fractional products; exact cancellation and unequal-cost controls;
committed costs reaching zero and then leaving zero; odd/even elimination
counts; finite/free bounds; projected matrix/bounds/objective; primal and basis
restoration; objective equivalence; canonical rational zero; and source
preservation under ordinary arithmetic and output mutation.

BigFloat tests use stored 256-bit operands at ambient precision 32/64/256.
Products `±(3+2^-200)` cancel exactly or leave representable tiny residuals;
inexact residuals such as `2+2^-200` reject at lower precision. Adjacent Float32/64
costs retain their nonzero differences. The retained column has degree two to
prevent unrelated alternate singleton candidates. Large non-dyadic rational
cases cover both factor positions and signs with denominators 5, 7, 15, 21,
and explicitly check the canonical zero numerator and denominator.

The targeted presolve/allocation suite passed **101,002 / 101,002 assertions**
in 2m03.2s, including every new allocation guard.

Independent read-only review found no issues in the source change or focused
tests. An AST-renamed baseline passed **2,901 assertions across 156 differential
models**, covering all numeric types and ambient BigFloat precisions, signed/
fractional/non-dyadic cancellation, canonical zero, adjacent costs and tiny
residuals, sequential committed updates, late rejection and rollback, candidate
selection, constant gates, projected/free/fixed bounds, primal/basis restoration,
and source preservation after ordinary rational arithmetic and output mutation.

The full test suite passed **120,499 / 120,499 assertions** in **6m12.9s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
