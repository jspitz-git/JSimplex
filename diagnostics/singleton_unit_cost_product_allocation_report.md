# Signed-unit cost products in singleton aggregation

Round 148 changes only the retained objective coefficient product in
`aggregate_singleton_equalities` in `src/presolve_aggregation.jl`. After the
existing zero-objective-ratio shortcut, the stored matrix term is converted
exactly. If the ratio or term is one, the other factor is reused; minus one
negates it. Other factors retain general rational multiplication. The product
is still subtracted from the current staged cost normally.

All representability checks and the singleton Float32/64 objective-rounding
policy remain intact. BigFloat and Rational{BigInt} costs still require exact
representation. The checks use full exact input values, so stored BigFloat
neighbors of units are not mistaken for units at lower ambient precision.
Constant updates, projection, candidate ordering, staging, rollback and
primal/basis restoration remain unchanged. No operands are mutated.

## Method and results

The baseline includes the preceding 147 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 56 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each probe contains 128 singleton columns and one shared retained column, with
`2*x_i+term*y=4`, x_i bounds `[1,3]`, and free y. Prices on x_i equal twice the
objective ratio; the price on y starts at two and the constant at seven.
The four targets use ratio 1 or -1 with term three, or ratio three with term
1 or -1. All 128 eliminations succeed. The projected rows retain their term
and bounds `[-2,2]`, the retained cost is `2-128*ratio*term`, and the constant
is `7+512*ratio`. Each candidate updates the retained cost committed by earlier
eliminations. Measurement includes projection, staging and reconstruction.

The nonunit control uses ratio three and term three. The zero-ratio control
retains the previous direct old-cost reuse path, with term three. Both controls
accept all pivots. Input construction is outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Ratio 1 | 971,080 | 928,184 | 4.42% | 25,728 → 24,576 |
| Ratio -1 | 979,448 | 943,896 | 3.63% | 25,984 → 25,088 |
| Term 1 | 1,015,768 | 972,936 | 4.22% | 26,880 → 25,728 |
| Term -1 | 1,015,912 | 980,312 | 3.50% | 26,880 → 25,984 |
| Nonunit control | 1,015,848 | 1,016,584 | — | 26,880 → 26,880 |
| Zero-ratio control | 776,888 | 777,480 | — | 19,968 → 19,968 |

Allocated bytes decrease by **3.50–4.42%** across the four targets.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

- `ratio_positive` saves **1,152 allocations per call**, or 9 per retained-cost update.
- `ratio_negative` saves **896 allocations per call**, or 7 per retained-cost update.
- `term_positive` saves **1,152 allocations per call**, or 9 per retained-cost update.
- `term_negative` saves **896 allocations per call**, or 7 per retained-cost update.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 834 → 782 | 44,976 → 42,024 |
| afiro | sparse | 4,891 → 4,891 | 213,888 → 213,424 |
| afiro | propagation | 2,437 → 2,437 | 92,648 → 92,504 |
| afiro | presolve | 16,208 → 16,156 | 728,008 → 725,104 |
| afiro | dual | 17,023 → 16,971 | 864,056 → 861,088 |
| afiro | primal | 16,929 → 16,877 | 841,496 → 839,120 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,747 → 2,747 | 174,472 → 174,008 |
| adlittle | propagation | 18,182 → 18,182 | 641,848 → 641,384 |
| adlittle | presolve | 82,433 → 82,433 | 3,326,760 → 3,327,096 |
| adlittle | dual | 84,448 → 84,448 | 4,118,120 → 4,115,512 |
| adlittle | primal | 85,246 → 85,246 | 4,394,680 → 4,392,280 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,432 → 461,400 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,536 → 607,296 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,015 → 1,964 | 109,824 → 107,616 |
| kb2 | sparse | 2,836 → 2,836 | 162,064 → 161,504 |
| kb2 | propagation | 12,948 → 12,948 | 455,632 → 454,400 |
| kb2 | presolve | 229,149 → 229,098 | 10,638,624 → 10,635,824 |
| kb2 | dual | 230,351 → 230,300 | 11,091,536 → 11,087,392 |
| kb2 | primal | 230,518 → 230,467 | 11,106,256 → 11,101,792 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,288 → 878,240 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,848 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,618 → 6,618 | 299,424 → 299,168 |
| sc50a | propagation | 6,020 → 6,020 | 222,128 → 221,888 |
| sc50a | presolve | 67,457 → 67,457 | 2,846,408 → 2,845,912 |
| sc50a | dual | 68,529 → 68,529 | 3,192,008 → 3,191,928 |
| sc50a | primal | 68,474 → 68,474 | 3,144,712 → 3,145,128 |
| sc50a | dual_no_presolve | 961 → 961 | 306,496 → 306,208 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,598 → 5,598 | 210,568 → 209,784 |
| flugpl | propagation | 3,253 → 3,253 | 123,408 → 122,272 |
| flugpl | presolve | 30,791 → 30,791 | 1,170,064 → 1,170,416 |
| flugpl | dual | 31,462 → 31,462 | 1,279,784 → 1,279,624 |
| flugpl | primal | 31,811 → 31,811 | 1,323,832 → 1,324,328 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,680 |

The standalone singleton pass, full presolve, and both solves with presolve
each save **52 allocations on afiro** and **51 on kb2**. The other 42 reference
measurements retain their allocation counts, including all solves without
presolve.

All 30 model snapshots (five fixtures × basic/doubleton/singleton/sparse/
propagation/full presolve) matched exactly: CSC arrays, objective and constant,
sense, bounds, domains, names, and original column count. All 20 whole-solve
combinations remained `OPTIMAL`, with identical status, objective, full primal
vector, and iteration count (`isequal`).

Machine-readable results:
[`singleton-unit-cost-product-allocations-before.toml`](singleton-unit-cost-product-allocations-before.toml)
and [`singleton-unit-cost-product-allocations-after.toml`](singleton-unit-cost-product-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_singleton_equalities --output=singleton-unit-cost-product-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function singleton_unit_cost_product_probe(kind; count=128, T=Float64)
    ratio=kind==:ratio_positive ? one(T) : kind==:ratio_negative ? -one(T) : kind==:zero_ratio ? zero(T) : T(3)
    term=kind==:term_positive ? one(T) : kind==:term_negative ? -one(T) : T(3)
    A=hcat(sparse(1:count,1:count,fill(T(2),count),count,count),sparse(fill(term,count,1)))
    problem=LinearProblem(A,[fill(2ratio,count);T(2)];objective_constant=T(7),
        row_lower=fill(T(4),count),row_upper=fill(T(4),count),
        column_lower=[ones(T,count);nothing],column_upper=[fill(T(3),count);nothing])
    return problem,JSimplex.aggregate_singleton_equalities
end

for kind in (:ratio_positive,:ratio_negative,:term_positive,:term_negative,:nonunit,:zero_ratio)
    problem, pass = singleton_unit_cost_product_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **2,346 assertions** and failed only
the four target allocation guards: 25,773 > 25,278; 25,992 > 25,534; and two
cases of 26,888 > 26,430. Both control budgets passed. There are
**2,350 new assertions**; existing budgets were not relaxed.

Coverage includes Float32, Float64, BigFloat, and Rational{BigInt}; signed units
on either side of the product; zero/nonunit controls; sequential updates to a
shared retained cost; finite/free bounds; projected matrix/bounds/objective;
restored primal and basis; objective equivalence; canonical rational reduction;
and source preservation under ordinary output mutation.

BigFloat tests use stored 256-bit inputs at ambient precision 32/64/256.
Values `±(1+2^-200)` in either factor stay nonunit. Inexact retained costs reject
at lower precision, while exact tiny tails and complete cancellations succeed.
Float32/64 tests retain rejection for overflow and half-subnormal products, and
explicitly preserve permitted rounding of unit-term objective updates involving
one third. The retained column has degree two to prevent unrelated alternate
singleton candidates. Large non-dyadic rational cases cover both factor positions,
signs, and denominators 5, 7, 15, and 21.

The targeted presolve/allocation suite passed **93,848 / 93,848 assertions**
in 2m00.2s, including every new allocation guard.

Independent read-only review found no issues in the source delta or focused
tests. An AST-renamed baseline passed **2,650 assertions across 156 differential
models**, covering all four numeric types and ambient BigFloat precisions,
signed units and near-units, exact tails/cancellation, committed retained costs,
late rejection and rollback, candidate selection, overflow and half-subnormals,
projected/free/fixed bounds, primal/basis restoration, and source preservation
after public rational arithmetic and output mutation.

The full test suite passed **113,345 / 113,345 assertions** in **6m17.6s**.

Full-suite command:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
