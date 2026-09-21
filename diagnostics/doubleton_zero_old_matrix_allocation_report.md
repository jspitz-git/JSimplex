# Skip exact addition to zero matrix entries in free-doubleton substitution

Round 103 changes only `substitute_free_doubleton` in `src/presolve_substitution.jl`.
For each affected matrix entry, the exact product is computed as before. When
the original retained-column entry is zero, the product is passed directly to
`_represent_exact`. A nonzero old entry retains exact conversion and addition.
This avoids converting a stored/implicit zero to a rational and adding it.

The CSC lookup still uses the original problem matrix, and explicit zero
eliminated-column coefficients still skip the row. Every matrix candidate
retains its exact representability check; row-bound shifts, objective arithmetic,
candidate staging/rejection, and primal/basis restoration remain unchanged.
Both absent entries and explicitly stored signed zeros follow the same shortcut.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 102 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Every target eliminates free `x` from `2*x+y=4` and 128 rows `c*x`, with
`c=3/-3`. The retained `y` has bounds `[-10,10]`, other rows have bounds
`[-100,100]`, costs are `[2,3]`, and the objective constant is seven.
Two probes have absent retained-column entries; two store explicit +0/-0
entries in CSC storage. Their reduced entries are `-c/2`.

The nonzero-old-entry control stores a retained-column coefficient of two.
The zero-eliminated-coefficient control additionally stores zero in the
eliminated column of affected rows, which skips their updates.
Model construction occurs outside all measurements.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Absent old entry, c=3 | 700,144 | 617,152 | 11.85% | 17,572 → 15,268 |
| Absent old entry, c=-3 | 701,824 | 618,560 | 11.86% | 17,572 → 15,268 |
| Stored +0, c=3 | 695,744 | 611,856 | 12.06% | 17,570 → 15,266 |
| Stored -0, c=-3 | 695,168 | 611,984 | 11.97% | 17,570 → 15,266 |
| Nonzero old entry control | 704,800 | 701,952 | — | 17,954 → 17,954 |
| Zero eliminated coefficient control | 80,272 | 79,808 | — | 1,442 → 1,442 |

Each target removes 2,304 allocations (18 per affected matrix entry), reducing
allocated bytes by 11.85–12.06%. Both controls retain their allocation counts; byte differences
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
| afiro | 44,816 → 45,200 | 843 → 843 | 219,064 → 218,136 | 4,987 → 4,987 |
| adlittle | 60,816 → 60,816 | 608 → 608 | 179,072 → 177,200 | 2,843 → 2,843 |
| kb2 | 112,288 → 112,176 | 2,060 → 2,060 | 162,320 → 160,912 | 2,836 → 2,836 |
| sc50a | 12,608 → 12,608 | 298 → 298 | 301,600 → 299,776 | 6,647 → 6,647 |
| flugpl | 4,384 → 4,384 | 100 → 100 | 218,120 → 216,376 | 5,772 → 5,772 |

| Model | Full presolve before → after | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per stage |
| --- | ---: | ---: | ---: | ---: |
| afiro | 734,888 → 732,024 | 870,056 → 867,912 | 848,456 → 845,608 | 0 |
| adlittle | 3,354,864 → 3,352,048 | 4,143,488 → 4,140,848 | 4,420,192 → 4,416,960 | 0 |
| kb2 | 10,680,008 → 10,678,392 | 11,132,472 → 11,132,152 | 11,146,872 → 11,145,656 | 0 |
| sc50a | 2,853,984 → 2,852,096 | 3,200,416 → 3,197,168 | 3,153,216 → 3,150,288 | 0 |
| flugpl | 1,203,672 → 1,201,640 | 1,312,896 → 1,310,960 | 1,357,456 → 1,355,504 | 0 |

All reference fixtures retain their allocation counts at every measured stage.
The benefit in this round is demonstrated by the targeted zero-old-entry probes.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`doubleton-zero-old-matrix-allocations-before.toml`](doubleton-zero-old-matrix-allocations-before.toml)
and [`doubleton-zero-old-matrix-allocations-after.toml`](doubleton-zero-old-matrix-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=doubleton-zero-old-matrix-basic-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-zero-old-matrix-doubleton-audit.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=doubleton-zero-old-matrix-sparse-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_zero_old_matrix_probe(kind; count=128, T=Float64)
    coefficient = T(kind in (:absent_negative,:stored_negative) ? -3 : kind == :zero_coefficient ? 0 : 3)
    stored = kind in (:stored_positive,:stored_negative,:nonzero,:zero_coefficient)
    second_rows = stored ? collect(1:count+1) : [1]
    old_value = kind in (:nonzero,:zero_coefficient) ? T(2) : kind == :stored_negative ? -zero(T) : zero(T)
    A = sparse(vcat(collect(1:count+1),second_rows),vcat(fill(1,count+1),fill(2,length(second_rows))),
        vcat(T[2;fill(coefficient,count)],stored ? T[1;fill(old_value,count)] : T[1]),count+1,2)
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),
        row_lower=vcat(T(4),fill(T(-100),count)),row_upper=vcat(T(4),fill(T(100),count)),
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end
for kind in (:absent_positive, :absent_negative, :stored_positive, :stored_negative, :nonzero, :zero_coefficient)
    problem, pass = doubleton_zero_old_matrix_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 528 assertions and failed the four
target allocation guards. Absent-entry probes measured 17,617 / 17,580 allocations; stored-zero probes
each measured 17,578, against limits of 17,000. Both controls passed.
All 532 new assertions now pass as part of 19,050 targeted assertions
covering presolve, free-doubleton substitution, and related allocation guards.
Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; absent and
explicitly stored old zeros; both coefficient signs; zero/nonzero right-hand
sides; and unchanged controls. They verify CSC storage, reduced matrices and
bounds, objective/constant, primal and basis restoration, and source immutability.
Tiny nonzero old entries still contribute to exact results, including under
reduced ambient BigFloat precision. Half-subnormal products reject updates
for both absent and stored zeros. Tiny old entries that make the matrix update
unrepresentable still reject candidates; retained variables are bounded so an
alternative pivot cannot mask rejection.

Independent read-only review found no issues. It passed 30,968 assertions:
532 focused assertions plus 30,436 independent checks against the AST-renamed
baseline substitution function. Differential coverage included 1,212 models
and 4,848 basis restorations. Additional zero-old-entry cases covered mixed
zero/nonzero/cancelling rows, absent and stored signed zeros, staged insertion
followed by rejection and a later valid candidate, stored BigFloat precision,
and repeated large rational operands. Exact representability, source
immutability, objectives, and postsolve primals matched the baseline.

The full repository suite passed **43,935 / 43,935** assertions in 5m22.2s
(exit status 0).
`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
