# Equal-denominator matrix sums in doubleton substitution

Round 126 changes only the affected-row matrix addition in
`substitute_free_doubleton` in `src/presolve_substitution.jl`. When a nonzero
existing coefficient and its exact substitution product have the same denominator,
their BigInt numerators are added directly. Zero sums become canonical exact zero;
other sums use the canonical `Rational{BigInt}` constructor to reduce the fraction.
Unequal denominators retain the existing rational addition. Zero old coefficients
still reuse the product through the preceding shortcut.

The matrix `_represent_exact` gate remains before the existing bound checks.
Product shortcuts, objective updates, rejection ordering, private-copy staging,
model construction, `dropzeros!`, and primal/basis restoration are unchanged.
No input is mutated and no GMP internals or noncanonical constructor are used.

## Method and results

The baseline includes the preceding 125 allocation rounds. Measurements used
Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI factorization.
Each case was warmed twice and sampled three times, with setup outside measurement
and garbage collection before every sample. All 51 measurements in each run had
zero compilation time. Bytes are minimum allocated bytes per call, not peak or
retained memory. Timings overlapped validation; no runtime speedup is claimed.

Each Float64 target has one equality `2*x+retained_coefficient*y=4` and 128
affected rows `3*x+old_value*y`. Variable x is free, y is bounded by `[-10,10]`,
and all affected rows are unbounded. Objective costs are `[2,3]` with constant
seven. Integer probes use retained coefficient two, giving beta=-1 and product
-3; fractional probes use retained coefficient one, giving beta=-1/2 and product
-3/2. Existing matrix entries and updates are:

- Integer cancellation: `3 + (-3) = 0`, common denominator one.
- Fractional cancellation: `3/2 + (-3/2) = 0`, common denominator two.
- Nonzero integer sum: `5 + (-3) = 2`, common denominator one.
- Reduced fractional sum: `1/2 + (-3/2) = -1`, common denominator two.

Every probe successfully substitutes the first candidate and returns a 128-by-1
reduced matrix. Cancellation targets have zero stored entries after `dropzeros!`;
nonzero sums retain 128 entries. Measurement includes working copies, sparse
reduction, model construction, and postsolve metadata. The objective becomes
`[1]` for integer probes and `[2]` for fractional probes; the constant is eleven.

The unequal-denominator control computes `1 + (-3/2)`. The zero-old control starts
with explicitly stored zero entries and reuses -3/2 through the prior shortcut.
Both also succeed. Model construction for each input occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Integer cancellation | 261,320 | 237,816 | 8.99% | 6,269 → 5,885 |
| Fractional cancellation | 297,168 | 275,920 | 7.15% | 7,044 → 6,788 |
| Nonzero integer sum | 274,920 | 258,920 | 5.82% | 6,655 → 6,399 |
| Reduced fractional sum | 309,648 | 295,856 | 4.45% | 7,430 → 7,302 |
| Unequal-denominator control | 312,240 | 310,176 | — | 7,558 → 7,558 |
| Zero-old control | 220,528 | 218,720 | — | 4,870 → 4,870 |

The four targets save **384, 256, 256, and 128 allocations per call**, respectively:
**3, 2, 2, and 1 per affected row**. Allocated bytes decrease by **4.45–8.99%**.
Both controls retain their allocation counts. Cross-process byte differences
on unchanged paths alone establish no benefit.

All nine measured stages for each reference fixture follow.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,232 → 44,896 |
| afiro | sparse | 4,987 → 4,987 | 219,160 → 218,136 |
| afiro | presolve | 16,330 → 16,330 | 733,928 → 732,440 |
| afiro | dual | 17,145 → 17,145 | 869,464 → 867,992 |
| afiro | primal | 17,051 → 17,051 | 848,040 → 846,392 |
| afiro | dual_no_presolve | 555 → 555 | 89,936 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 178,832 → 177,232 |
| adlittle | presolve | 82,776 → 82,776 | 3,347,896 → 3,346,120 |
| adlittle | dual | 84,791 → 84,791 | 4,136,856 → 4,137,176 |
| adlittle | primal | 85,589 → 85,589 | 4,413,560 → 4,413,416 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,512 → 461,624 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,056 → 607,408 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,688 → 112,736 |
| kb2 | sparse | 2,836 → 2,836 | 162,352 → 161,104 |
| kb2 | presolve | 230,004 → 230,004 | 10,680,840 → 10,677,064 |
| kb2 | dual | 231,206 → 231,206 | 11,133,656 → 11,132,232 |
| kb2 | primal | 231,373 → 231,373 | 11,148,712 → 11,146,856 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,288 → 878,288 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,848 → 260,976 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 301,440 → 299,952 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,088 → 2,852,592 |
| sc50a | dual | 68,706 → 68,706 | 3,198,848 → 3,197,584 |
| sc50a | primal | 68,651 → 68,651 | 3,151,472 → 3,150,400 |
| sc50a | dual_no_presolve | 961 → 961 | 306,384 → 306,208 |
| sc50a | primal_no_presolve | 964 → 964 | 232,216 → 232,184 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 217,672 → 216,728 |
| flugpl | presolve | 31,461 → 31,461 | 1,199,848 → 1,198,680 |
| flugpl | dual | 32,132 → 32,132 | 1,310,720 → 1,309,040 |
| flugpl | primal | 32,481 → 32,481 | 1,355,296 → 1,353,696 |
| flugpl | dual_no_presolve | 376 → 376 | 42,752 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,728 → 91,680 |

All five fixtures retain their allocation counts in every measured stage,
including solves without presolve. They establish unchanged behavior and show
no allocation-count benefit from this particular shortcut.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, full primal vector, and
iteration count (`isequal`).

Machine-readable results:
[`doubleton-equal-matrix-denominator-allocations-before.toml`](doubleton-equal-matrix-denominator-allocations-before.toml)
and [`doubleton-equal-matrix-denominator-allocations-after.toml`](doubleton-equal-matrix-denominator-allocations-after.toml).
The saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=substitute_free_doubleton --output=doubleton-equal-matrix-denominator-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function doubleton_equal_matrix_denominator_probe(kind; count=128, T=Float64)
    retained_coefficient = T(kind in (:cancel_integer,:sum_integer) ? 2 : 1)
    old_value = kind == :cancel_fraction ? T(3)/2 : kind == :sum_fraction ? T(1)/2 : T(kind == :cancel_integer ? 3 : kind == :sum_integer ? 5 : kind == :zero_old ? 0 : 1)
    A = sparse(vcat(collect(1:count+1),collect(1:count+1)),vcat(fill(1,count+1),fill(2,count+1)),
        vcat(T[2;fill(T(3),count)],T[retained_coefficient;fill(old_value,count)]),count+1,2)
    problem = LinearProblem(A,T[2,3];objective_constant=T(7),
        row_lower=vcat(T(4),fill(nothing,count)),row_upper=vcat(T(4),fill(nothing,count)),
        column_lower=[nothing,T(-10)],column_upper=[nothing,T(10)])
    return problem,JSimplex.substitute_free_doubleton
end

for kind in (:cancel_integer,:cancel_fraction,:sum_integer,:sum_fraction,:unequal_denominator,:zero_old)
    problem, pass = doubleton_equal_matrix_denominator_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed **1,578** assertions and failed only
the four target allocation guards: 6,314 > 6,100; 7,052 > 6,950;
6,663 > 6,500; and 7,438 > 7,380. Both control budgets passed. There are
**1,582 new assertions**; existing allocation budgets were not relaxed.

Accepted substitutions cover Float32, Float64, BigFloat, and Rational{BigInt};
cancellation, nonzero sums, fraction reduction, unequal denominators, signed
coefficients and beta, finite/unbounded affected rows, reduced CSC storage,
objective results, row bounds, primal/basis restoration, and source immutability.
BigFloat checks cover stored-256-bit coefficients under ambient precision
32/64/256, exact tiny cancellation tails, zero removal, output precision, and
nonrepresentable matrix sums. Large rational cases use numerators derived from
`2^300+1` and non-dyadic denominators 5, 7, 15, and 21, including further reduction.
Explicit overflow and half-subnormal matrix cases check rejection without source
storage changes.

All **44,286/44,286** targeted assertions passed in 1m30.5s (exit 0), including
the 1,582 new checks and the existing basic, doubleton, aggregation, and related
presolve allocation guards.

Independent read-only review found no issues. An AST-renamed round-125 baseline
comparison passed **5,456 additional assertions** across 152 selected differential
models (124 accepted and 28 rejected), excluding the focused tests. This included
608 basis restoration cases, 304 primal-dimension cases, and 304 basis-dimension
cases. Coverage included explicit CSC zeros and global `dropzeros!` cleanup,
canonical cancellation/reduction, large non-dyadic rationals and ownership,
stored-256-bit BigFloat inputs under ambient precision 32/64/256, early objective
gates, late matrix/bound rejection, staged rollback, later candidates, restoration,
and source immutability.

The mandatory full package suite passed **69,171/69,171** assertions in
5m48.3s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
