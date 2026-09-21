# Reuse signed unit operands for free-doubleton row shifts

Round 102 changes only `substitute_free_doubleton` in `src/presolve_substitution.jl`.
The row shift retains its existing zero-alpha shortcut, then checks the exact
row coefficient and exact alpha for signed unit values. Multiplication by +1
reuses the other rational operand; multiplication by -1 negates it. Other
products retain their existing exact multiplication.

The row coefficient is still converted exactly, explicit zero entries still
skip the row, and alpha/beta representability checks precede all row updates.
Both bound shifts use the same exact result. Matrix/objective arithmetic,
candidate staging, rejection, and primal/basis restoration are unchanged.
Unit comparisons use exact rationals; no tolerance or rounded comparison is used.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 101 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Every target eliminates free `x` from `2*x+y=rhs` and 128 rows `c*x+2*y`.
The retained `y` has bounds `[-10,10]`, other rows have bounds `[-100,100]`,
costs are `[2,3]`, and the objective constant is seven. Coefficient-unit probes
use `c=1/-1` and `rhs=4` (alpha two). Alpha-unit probes use `c=3` and
`rhs=2/-2` (alpha one/minus one).

The nonunit control uses `c=3`, `rhs=4`; the zero-alpha control uses `c=3`,
`rhs=0`. Model construction occurs outside all measurements.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Coefficient +1 | 700,416 | 657,296 | 6.16% | 17,954 → 16,802 |
| Coefficient -1 | 701,856 | 666,048 | 5.10% | 17,954 → 17,058 |
| Alpha +1 | 701,760 | 659,216 | 6.06% | 17,954 → 16,802 |
| Alpha -1 | 702,048 | 666,000 | 5.13% | 17,954 → 17,058 |
| Nonunit control | 701,936 | 702,336 | — | 17,954 → 17,954 |
| Zero-alpha control | 311,296 | 312,128 | — | 7,576 → 7,576 |

Positive-unit probes remove 1,152 allocations (nine per affected row), and
negative-unit probes remove 896 allocations (seven per row). Allocated bytes
fall by 5.10–6.16%. Both controls retain their allocation counts; byte differences
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
| afiro | 45,056 → 45,280 | 843 → 843 | 217,912 → 218,536 | 4,987 → 4,987 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 176,960 → 178,160 | 2,843 → 2,843 |
| kb2 | 111,616 → 112,704 | 2,060 → 2,060 | 160,672 → 162,112 | 2,836 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 299,760 → 300,896 | 6,647 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 216,024 → 218,024 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 732,728 → 733,128 | 867,192 → 869,080 | 845,864 → 847,272 | 0 |
| adlittle | 3,351,664 → 3,354,032 | 4,141,936 → 4,143,040 | 4,418,480 → 4,419,600 | 0 |
| kb2 | 10,678,920 → 10,677,992 | 11,131,496 → 11,133,368 | 11,145,464 → 11,147,080 | 0 |
| sc50a | 2,853,328 → 2,853,104 | 3,198,992 → 3,198,080 | 3,151,856 → 3,150,928 | 0 |
| flugpl | 1,201,672 → 1,202,264 | 1,311,232 → 1,312,048 | 1,355,472 → 1,356,496 | 0 |

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
[`doubleton-unit-shift-allocations-before.toml`](doubleton-unit-shift-allocations-before.toml)
and [`doubleton-unit-shift-allocations-after.toml`](doubleton-unit-shift-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=doubleton-unit-shift-basic-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-unit-shift-doubleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=doubleton-unit-shift-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_unit_shift_probe(kind; count=128, T=Float64)
    rhs = T(kind == :positive_alpha ? 2 : kind == :negative_alpha ? -2 : kind == :zero_alpha ? 0 : 4)
    coefficient = T(kind == :positive_coefficient ? 1 : kind == :negative_coefficient ? -1 : 3)
    A = sparse(hcat(vcat(T(2),fill(coefficient,count)),vcat(T(1),fill(T(2),count))))
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),
        row_lower=vcat(rhs,fill(T(-100),count)),row_upper=vcat(rhs,fill(T(100),count)),
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end
for kind in (:positive_coefficient, :negative_coefficient, :positive_alpha, :negative_alpha, :nonunit, :zero_alpha)
    problem, pass = doubleton_unit_shift_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 906 assertions and failed the four
target allocation guards. The positive-coefficient probe measured 17,999 allocations; each of the other
three target probes measured 17,962, against limits of 17,400. Both controls passed.
All 910 new assertions now pass as part of 18,518 targeted assertions
covering presolve, free-doubleton substitution, and related allocation guards.
Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; both signs
of either unit operand; nonunit and zero-alpha controls; finite, one-sided,
and unbounded row endpoints. They compare matrices, bounds, objective/constant,
primal and basis restoration, and source immutability.
Stored-256-bit coefficients near +/-1 preserve their exact tiny
residuals under ambient precision 32/64. Near-unit alpha remains accepted at
precision 256 and rejected at precision 32/64 when it cannot be represented
exactly. Retained variables are bounded so an alternative pivot cannot mask
rejection. Existing tiny-shift and half-subnormal rejection tests also run.

Independent read-only review found no issues. It passed 22,706 assertions:
910 focused assertions plus 21,796 independent checks against the AST-renamed
baseline substitution function. Differential coverage included 912 models and
3,648 basis restorations, all exact signed-unit combinations, neighboring
Float32/Float64 unit values, stored-precision BigFloat operands, rational
fractions, repeated operand reuse, atomic representability rejection followed
by later candidates, input immutability, and matrix/objective/primal equivalence.

The full repository suite passed **43,403 / 43,403** assertions in 5m15.3s
(exit status 0).
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
