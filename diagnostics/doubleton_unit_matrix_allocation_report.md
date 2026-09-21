# Reuse signed unit operands for free-doubleton matrix products

Round 104 changes only `substitute_free_doubleton` in `src/presolve_substitution.jl`.
The matrix-update product checks the exact row coefficient and exact beta for
signed unit values. Multiplication by +1 reuses the other rational operand;
multiplication by -1 negates it. Other products retain exact multiplication.

Both operands are exact rationals and nonzero on this path. Explicit zero
eliminated-column entries still skip the row. The zero-old-entry shortcut from
round 103 and `_represent_exact` still process the resulting product; row shifts,
objective arithmetic, candidate staging/rejection, and primal/basis restoration
remain unchanged. No tolerance or rounded comparison is used.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 103 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Every target eliminates free `x` from `2*x+e*y=4` and 128 rows `c*x+2*y`.
The retained `y` has bounds `[-10,10]`, other rows have bounds `[-100,100]`,
costs are `[2,3]`, and the objective constant is seven. Coefficient-unit probes
use `c=1/-1` and `e=1` (beta minus one half). Beta-unit probes use `c=3` and
`e=-2/2` (beta one/minus one).

The nonunit control uses `c=3`, `e=1`; the zero-coefficient control uses `c=0`,
`e=1`, so the eliminated column is absent outside the equality. Model construction
occurs outside all measurements.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Coefficient +1 | 657,312 | 614,480 | 6.52% | 16,802 → 15,650 |
| Coefficient -1 | 665,968 | 630,496 | 5.33% | 17,058 → 16,162 |
| Beta +1 | 702,624 | 659,760 | 6.10% | 17,954 → 16,802 |
| Beta -1 | 702,688 | 666,928 | 5.09% | 17,954 → 17,058 |
| Nonunit control | 702,672 | 703,072 | — | 17,954 → 17,954 |
| Zero-coefficient control | 35,616 | 35,616 | — | 288 → 288 |

Positive-unit probes remove 1,152 allocations (nine per affected matrix entry);
negative-unit probes remove 896 allocations (seven per entry). Allocated bytes
fall by 5.09–6.52%. Both controls retain their allocation counts; byte differences
on unchanged paths alone establish no benefit.

| Model | Basic before → after | Basic allocations before → after | Doubleton before → after | Doubleton allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 1,392 → 1,392 | 15 → 15 | 1,072 → 1,072 | 3 → 3 |
| adlittle | 2,928 → 2,928 | 15 → 15 | 2,208 → 2,208 | 3 → 3 |
| kb2 | 1,680 → 1,680 | 15 → 15 | 1,664 → 1,664 | 3 → 3 |
| sc50a | 17,760 → 17,760 | 60 → 60 | 1,808 → 1,808 | 3 → 3 |
| flugpl | 1,056 → 1,056 | 15 → 15 | 800 → 800 | 3 → 3 |

| Model | Singleton before → after | Singleton allocations before → after | Sparse before → after | Sparse allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 45,248 → 45,472 | 843 → 843 | 217,640 → 218,984 | 4,987 → 4,987 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 177,328 → 177,312 | 2,843 → 2,843 |
| kb2 | 112,576 → 112,624 | 2,060 → 2,060 | 161,248 → 161,088 | 2,836 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 299,760 → 299,904 | 6,647 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 217,192 → 216,856 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 731,576 → 732,392 | 867,704 → 868,568 | 845,464 → 845,944 | 0 |
| adlittle | 3,352,992 → 3,352,176 | 4,142,112 → 4,142,656 | 4,419,264 → 4,419,360 | 0 |
| kb2 | 10,679,624 → 10,678,936 | 11,133,464 → 11,132,712 | 11,147,368 → 11,146,696 | 0 |
| sc50a | 2,853,200 → 2,853,392 | 3,198,192 → 3,198,992 | 3,151,216 → 3,151,408 | 0 |
| flugpl | 1,201,656 → 1,202,376 | 1,311,312 → 1,312,048 | 1,356,336 → 1,356,592 | 0 |

All reference fixtures retain their allocation counts at every measured stage.
The benefit in this round is demonstrated by the targeted signed-unit probes.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`doubleton-unit-matrix-allocations-before.toml`](doubleton-unit-matrix-allocations-before.toml)
and [`doubleton-unit-matrix-allocations-after.toml`](doubleton-unit-matrix-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=doubleton-unit-matrix-basic-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-unit-matrix-doubleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=doubleton-unit-matrix-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_unit_matrix_probe(kind; count=128, T=Float64)
    coefficient = T(kind == :positive_coefficient ? 1 : kind == :negative_coefficient ? -1 : kind == :zero_coefficient ? 0 : 3)
    retained_coefficient = T(kind == :positive_beta ? -2 : kind == :negative_beta ? 2 : 1)
    A = sparse(hcat(vcat(T(2),fill(coefficient,count)),vcat(retained_coefficient,fill(T(2),count))))
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),
        row_lower=vcat(T(4),fill(T(-100),count)),row_upper=vcat(T(4),fill(T(100),count)),
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end
for kind in (:positive_coefficient, :negative_coefficient, :positive_beta, :negative_beta, :nonunit, :zero_coefficient)
    problem, pass = doubleton_unit_matrix_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 890 assertions and failed the four
target allocation guards. Coefficient probes measured 16,847 / 17,066 allocations against 16,200 /
16,500; both beta probes measured 17,962 against 17,400. Both controls passed.
All 894 new assertions now pass as part of 19,944 targeted assertions
covering presolve, free-doubleton substitution, and related allocation guards.
Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; both signs
of either unit operand; nonunit and zero-coefficient controls; zero/nonzero
right-hand sides; and zero/nonzero old matrix entries. They compare matrices,
bounds, objective/constant, primal and basis restoration, zero removal, and
source immutability.
Stored-256-bit coefficients near +/-1 preserve tiny exact matrix residuals
under ambient precision 32/64. Near-unit beta is accepted at precision 256 and
rejected at precision 32/64 when it cannot be represented exactly. The retained
variable is bounded so an alternative pivot cannot mask rejection. Existing
zero-old-entry, tiny-product, and half-subnormal rejection guards also run.

Independent read-only review found no issues. It passed 58,882 assertions:
894 focused assertions plus 57,988 independent checks against the AST-renamed
baseline substitution function. Differential coverage included 2,412 models
and 9,648 basis restorations, both unit signs, zero-old products, cancellation,
near-unit controls, stored BigFloat precision, rational operand reuse and source
immutability, exact representability rejection, staged updates, and later
candidates. Reused rational operands encounter no mutating arithmetic.

The full repository suite passed **44,829 / 44,829** assertions in 5m16.8s
(exit status 0).
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
