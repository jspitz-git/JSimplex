# Equal-denominator retained costs in singleton aggregation

Round 151 changes only retained objective coefficient subtraction in
`aggregate_singleton_equalities` in `src/presolve_aggregation.jl`. After the
existing zero-old-cost and exact-cancellation guards, matching denominators
allow direct subtraction of numerators. The public `Rational{BigInt}` constructor
normalizes and reduces the result. Unequal denominators retain general subtraction.

The comparison uses the current staged cost and exact product, including the
full stored precision of BigFloat inputs. Earlier zero-ratio and signed-unit
product shortcuts, representability gates, Float32/64 singleton objective-rounding
policy, constant updates, projection, candidate selection, staging, rollback,
and primal/basis restoration remain unchanged. No operands are mutated and no
GMP internals or noncanonical constructors are used.

## Method and results

The baseline includes the preceding 150 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe has 256 singleton columns and a shared retained column, with
`2*x_i+term*y=4`, x_i bounds `[1,3]`, and free y. Ratios alternate signs, starting
at three or minus three; each x_i price is twice its ratio. The objective
constant starts at seven. All eliminations succeed. After the even number of
eliminations the retained cost equals its initial value, the constant is seven,
and projected rows retain their term with bounds `[-2,2]`. Measurement includes
projection, staging, objective updates and reconstruction.

Integer targets use term three and initial retained cost five. Costs alternate
between five and minus four or fourteen; all 256 updates use shared denominator
one. Fractional targets use term 1/2 and initial cost 1/2. Costs alternate between
1/2 and minus one or two: 128 updates have shared denominator two, and 128 retain
general subtraction after denominator reduction.

The unequal-denominator control uses term 1/2 and initial cost 1/8, alternating
between 1/8 and -11/8. Its cost denominator stays eight while the product
denominator is two. The zero-ratio control retains the preceding direct cost
reuse path with initial cost five. Both controls accept all pivots. Input
construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Integer positive first ratio | 2,025,176 | 1,997,192 | 1.38% | 53,643 → 53,131 |
| Integer negative first ratio | 2,027,384 | 2,000,264 | 1.34% | 53,643 → 53,131 |
| Fractional positive first ratio | 2,025,224 | 2,013,800 | 0.56% | 53,515 → 53,387 |
| Fractional negative first ratio | 2,025,144 | 2,013,736 | 0.56% | 53,515 → 53,387 |
| Unequal-denominator control | 2,022,952 | 2,022,856 | — | 53,387 → 53,387 |
| Zero-ratio control | 1,551,624 | 1,551,304 | — | 39,819 → 39,819 |

Allocated bytes decrease by **0.56–1.38%** across the four targets.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

- `integer_positive` saves **512 allocations per call**, or 2 per shared-denominator update.
- `integer_negative` saves **512 allocations per call**, or 2 per shared-denominator update.
- `fraction_positive` saves **128 allocations per call**, or 1 per shared-denominator update.
- `fraction_negative` saves **128 allocations per call**, or 1 per shared-denominator update.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 747 → 747 | 41,264 → 40,688 |
| afiro | sparse | 4,891 → 4,891 | 213,776 → 213,600 |
| afiro | propagation | 2,437 → 2,437 | 92,792 → 92,376 |
| afiro | presolve | 16,121 → 16,121 | 724,216 → 724,104 |
| afiro | dual | 16,936 → 16,936 | 860,120 → 859,432 |
| afiro | primal | 16,842 → 16,842 | 838,584 → 838,328 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,747 → 2,747 | 174,696 → 174,104 |
| adlittle | propagation | 18,182 → 18,182 | 641,656 → 641,368 |
| adlittle | presolve | 82,433 → 82,433 | 3,328,280 → 3,327,432 |
| adlittle | dual | 84,448 → 84,448 | 4,117,912 → 4,116,696 |
| adlittle | primal | 85,246 → 85,246 | 4,394,808 → 4,393,624 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,352 → 461,064 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,472 → 607,328 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 1,915 → 1,915 | 105,192 → 104,792 |
| kb2 | sparse | 2,836 → 2,836 | 162,080 → 162,368 |
| kb2 | propagation | 12,948 → 12,948 | 454,784 → 454,320 |
| kb2 | presolve | 229,049 → 229,049 | 10,634,920 → 10,634,216 |
| kb2 | dual | 230,251 → 230,251 | 11,087,704 → 11,087,432 |
| kb2 | primal | 230,418 → 230,418 | 11,101,832 → 11,100,456 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,096 → 878,064 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,856 → 299,264 |
| sc50a | propagation | 6,020 → 6,020 | 222,912 → 222,368 |
| sc50a | presolve | 67,457 → 67,457 | 2,847,144 → 2,846,584 |
| sc50a | dual | 68,529 → 68,529 | 3,193,656 → 3,192,760 |
| sc50a | primal | 68,474 → 68,474 | 3,146,184 → 3,145,448 |
| sc50a | dual_no_presolve | 961 → 961 | 306,144 → 306,528 |
| sc50a | primal_no_presolve | 964 → 964 | 232,184 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 210,824 → 210,024 |
| flugpl | propagation | 3,253 → 3,253 | 123,376 → 123,520 |
| flugpl | presolve | 30,791 → 30,791 | 1,170,816 → 1,170,368 |
| flugpl | dual | 31,462 → 31,462 | 1,280,296 → 1,279,864 |
| flugpl | primal | 31,811 → 31,811 | 1,324,856 → 1,324,568 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All 50 reference measurements retain their allocation counts. These fixtures
do not show a measurable benefit from this particular cost-denominator shortcut.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`singleton-equal-cost-denominator-allocations-before.toml`](singleton-equal-cost-denominator-allocations-before.toml)
and [`singleton-equal-cost-denominator-allocations-after.toml`](singleton-equal-cost-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=singleton-equal-cost-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function singleton_equal_cost_denominator_probe(kind; count=256, T=Float64)
    fractional=kind in (:fraction_positive,:fraction_negative,:unequal_denominator)
    ratio=kind==:zero_ratio ? 0 : kind in (:integer_negative,:fraction_negative) ? -3 : 3
    term=fractional ? T(1)/2 : T(3)
    old=kind==:unequal_denominator ? T(1)/8 : fractional ? T(1)/2 : T(5)
    prices=T[isodd(i) ? 2ratio : -2ratio for i in 1:count]
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(fill(term,count,1)))
    problem=LinearProblem(A,[prices;old];objective_constant=T(7),
        row_lower=fill(T(4),count),row_upper=fill(T(4),count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end

for kind in (:integer_positive,:integer_negative,:fraction_positive,:fraction_negative,:unequal_denominator,:zero_ratio)
    problem, pass = singleton_equal_cost_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,994 assertions** and failed only
the four target allocation guards: 53,688 and 53,651 against 53,387, and two
cases of 53,523 against 53,451. Both control budgets passed. There are
**2,998 new assertions**; existing budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; shared and
unequal integer/fractional denominators; signed differences and canonical
reduction; zero and cancellation paths; committed updates changing denominators;
odd/even elimination counts; finite/free bounds; projected matrix/bounds/
objective; primal and basis restoration; objective equivalence; and source
preservation under ordinary arithmetic and output mutation.

BigFloat tests use stored 256-bit inputs at ambient precision 32/64/256. Exact
integer differences, complete cancellation and tiny residuals stay accepted;
inexact residuals such as `2-2^-199` reject at lower precision. Float32/64 tests
retain rejection for overflow and half-subnormal residuals. The retained column
has degree two to prevent unrelated alternate singleton candidates. Large
non-dyadic rational cases cover signs, canonical reduction, and denominators
5, 7, 15, and 21.

The targeted presolve/allocation suite passed **104,000 / 104,000 assertions**
in 2m06.4s, including every new allocation guard.

Independent read-only review found no issues in the source delta or focused
tests. An AST-renamed baseline passed **2,940 assertions across 160 differential
models**, covering all numeric types and ambient BigFloat precisions, shared
and unequal denominators, canonical reduction, committed denominator changes,
zero/unit/cancellation paths, precision and rejection gates, rollback, candidate
preference, constant gates, projected/free/fixed bounds, primal/basis restoration,
and source preservation under public rational arithmetic and output mutation.

The full test suite passed **123,497 / 123,497 assertions** in **6m06.2s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
