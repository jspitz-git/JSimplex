# Equal-denominator constant sums in singleton aggregation

Round 147 changes only objective constant addition in
`aggregate_singleton_equalities` in `src/presolve_aggregation.jl`. When the
current exact constant and the ratio/RHS product share a denominator, their
numerators are added directly. A zero numerator yields canonical zero; other
sums use the public `Rational{BigInt}` constructor, preserving reduction and
positive denominators. Unequal denominators retain general rational addition.

The preceding zero-ratio/RHS, signed-unit product, and zero-constant shortcuts
remain unchanged. The test uses the current committed constant, so denominator
changes after reduction or earlier eliminations are respected. Every candidate
constant still passes through `_represent_exact`. Projection, exact-versus-rounded
singleton objective selection, staging, rollback, and primal/basis restoration
are unchanged. No operands are mutated or GMP internals used.

## Method and results

The baseline includes the preceding 146 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe has 256 singleton columns and a shared retained column, with
`2*x_i+y=rhs`, x_i bounds `[1,3]`, and free y. Prices on x_i alternate -6 and 6,
giving ratios -3 and 3; the retained price starts at two. All eliminations
succeed. The final constant equals the initial one, the retained cost is two,
and all projected rows have coefficient one and bounds `[rhs-6,rhs-2]`.
Measurement includes projection, staging, objective updates and reconstruction.

The integer cancellation case starts at three with RHS one: 128 sums cancel
and 128 updates reuse the product because the constant is zero. The fractional
cancellation case starts at 3/2 with RHS 1/2 and has the same branch pattern.
The integer sum case starts at five with RHS one, alternating between five and
two; all 256 updates use shared denominators. The fractional sum case starts
at 1/2 with RHS 1/2, alternating between 1/2 and -1; 128 updates use shared
denominators and 128 use general addition after denominator reduction.

The unequal-denominator control starts at 1/8 with RHS 1/2, alternating between
1/8 and -11/8; every product has denominator two while every constant has
denominator eight. The zero-RHS control retains the preceding zero-shift path.
Both controls accept all pivots. Input construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Integer cancellation | 1,913,096 | 1,893,032 | 1.05% | 50,315 → 49,931 |
| Fractional cancellation | 2,054,056 | 2,036,248 | 0.87% | 53,515 → 53,259 |
| Integer sum | 1,968,008 | 1,942,696 | 1.29% | 51,851 → 51,339 |
| Fractional sum | 2,106,744 | 2,097,048 | 0.46% | 55,051 → 54,923 |
| Unequal-denominator control | 2,104,360 | 2,106,200 | — | 54,923 → 54,923 |
| Zero-RHS control | 1,772,248 | 1,774,072 | — | 46,219 → 46,219 |

Allocated bytes decrease by **0.46–1.29%** across the four targets.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

- `cancel_integer` saves **384 allocations per call**, or 3 per shared-denominator update.
- `cancel_fraction` saves **256 allocations per call**, or 2 per shared-denominator update.
- `sum_integer` saves **512 allocations per call**, or 2 per shared-denominator update.
- `sum_fraction` saves **128 allocations per call**, or 1 per shared-denominator update.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 834 → 834 | 44,592 → 44,448 |
| afiro | sparse | 4,891 → 4,891 | 213,456 → 214,880 |
| afiro | propagation | 2,437 → 2,437 | 92,664 → 93,160 |
| afiro | presolve | 16,208 → 16,208 | 727,224 → 729,016 |
| afiro | dual | 17,023 → 17,023 | 863,416 → 865,000 |
| afiro | primal | 16,929 → 16,929 | 841,240 → 843,080 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,747 → 2,747 | 174,040 → 174,296 |
| adlittle | propagation | 18,182 → 18,182 | 641,400 → 642,664 |
| adlittle | presolve | 82,433 → 82,433 | 3,328,296 → 3,329,784 |
| adlittle | dual | 84,448 → 84,448 | 4,116,760 → 4,118,552 |
| adlittle | primal | 85,246 → 85,246 | 4,394,536 → 4,395,368 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,368 → 461,464 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,456 → 607,328 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,015 → 2,015 | 109,520 → 109,760 |
| kb2 | sparse | 2,836 → 2,836 | 161,504 → 162,288 |
| kb2 | propagation | 12,948 → 12,948 | 454,288 → 455,744 |
| kb2 | presolve | 229,149 → 229,149 | 10,639,536 → 10,640,288 |
| kb2 | dual | 230,351 → 230,351 | 11,091,888 → 11,092,272 |
| kb2 | primal | 230,518 → 230,518 | 11,104,912 → 11,106,464 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 877,920 → 878,256 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,832 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,168 → 300,528 |
| sc50a | propagation | 6,020 → 6,020 | 221,888 → 223,504 |
| sc50a | presolve | 67,457 → 67,457 | 2,846,696 → 2,848,024 |
| sc50a | dual | 68,529 → 68,529 | 3,191,976 → 3,193,976 |
| sc50a | primal | 68,474 → 68,474 | 3,144,760 → 3,146,616 |
| sc50a | dual_no_presolve | 961 → 961 | 306,112 → 306,576 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,216 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 209,720 → 210,824 |
| flugpl | propagation | 3,253 → 3,253 | 122,608 → 123,296 |
| flugpl | presolve | 30,791 → 30,791 | 1,170,384 → 1,171,696 |
| flugpl | dual | 31,462 → 31,462 | 1,279,400 → 1,280,856 |
| flugpl | primal | 31,811 → 31,811 | 1,324,296 → 1,325,768 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

All 50 reference measurements retain their allocation counts. These fixtures
do not show a measurable benefit from this particular constant-sum shortcut.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`singleton-equal-constant-denominator-allocations-before.toml`](singleton-equal-constant-denominator-allocations-before.toml)
and [`singleton-equal-constant-denominator-allocations-after.toml`](singleton-equal-constant-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=singleton-equal-constant-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function singleton_equal_constant_denominator_probe(kind; count=256, T=Float64)
    rhs=kind in (:cancel_integer,:sum_integer) ? one(T) : kind==:zero_rhs ? zero(T) : T(1)/2
    initial=kind==:cancel_integer ? T(3) : kind==:cancel_fraction ? T(3)/2 :
        kind in (:sum_integer,:zero_rhs) ? T(5) : kind==:sum_fraction ? T(1)/2 : T(1)/8
    prices=T[isodd(i) ? -6 : 6 for i in 1:count]
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(ones(T,count,1)))
    problem=LinearProblem(A,[prices;T(2)];objective_constant=initial,
        row_lower=fill(rhs,count),row_upper=fill(rhs,count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end

for kind in (:cancel_integer,:cancel_fraction,:sum_integer,:sum_fraction,:unequal_denominator,:zero_rhs)
    problem, pass = singleton_equal_constant_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **4,490 assertions** and failed only
the four target allocation guards: 50,360 > 50,123; 53,523 > 53,387;
51,859 > 51,595; and 55,059 > 54,987. Both control budgets passed. There are
**4,494 new assertions**; existing budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; signed
integer/fractional sums and cancellation; shared/unequal denominators; zero
constants; finite/free pivot bounds; committed constants changing denominator
or reaching zero; odd/even numbers of eliminations; projected matrix/bounds/
objective; restored primal and basis; objective equivalence; canonical signs
and reduction; and source preservation under ordinary output mutation.

BigFloat tests use stored 256-bit inputs at ambient precision 32/64/256. Exact
sums, complete cancellation and tiny residuals remain accepted; inexact residuals
such as `8+2^-199` reject at lower precision. Float32/64 checks retain rejection
for overflow and half-subnormal sums. The retained column has degree two to
prevent unrelated alternate singleton candidates. Large non-dyadic rational
cases exercise signs, reduction, and cancellation with denominators 5, 7, 15, 21.

The targeted presolve/allocation suite passed **91,498 / 91,498 assertions**
in 2m02.3s, including every new allocation guard.

Independent read-only review found no issues in the source delta or new tests.
An AST-renamed baseline passed **2,321 assertions across 144 differential models**,
covering all four numeric types and ambient BigFloat precisions, shared and
unequal denominators, canonical cancellation and reduction, committed constants,
late rejection and rollback, candidate preference, projected/free/fixed bounds,
primal/basis restoration, and source preservation.

The full test suite passed **110,995 / 110,995 assertions** in **6m01.0s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
