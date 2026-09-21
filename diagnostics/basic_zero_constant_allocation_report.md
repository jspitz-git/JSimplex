# Reuse exact contributions when the basic-presolve constant is zero

Round 112 changes only `_presolve_basic` in `src/presolve.jl`.
For nonzero objective contributions, an exactly zero accumulated constant now
reuses the exact contribution instead of converting zero to an exact rational
and adding it. Nonzero constants retain their existing exact conversion and sum.
The zero-contribution and signed-unit-product shortcuts remain unchanged.

`_represent_exact` still checks the resulting constant before row staging,
including when the initial constant is zero. The stored constant is compared
exactly with zero; no tolerance or rounded arithmetic is introduced. Row-bound
checks, rejection, staged updates, removed values/states, empty-row checks,
and primal/basis restoration are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 111 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each probe has 128 rows `x_i+2*y`, fixed `x_i` alternating between +2 and -2,
and retained `y` with bounds `[-10,10]` and cost three. Target costs for all `x_i`
are three, and the initial constant is zero. This returns the constant to zero
after every pair of eliminations, exercising the shortcut 64 times per call.
The positive target starts with +2; the negative target starts with -2.
The negative-zero target starts with +2 and an initial constant of -0.
These three have unbounded row endpoints. The finite-row target instead uses
row bounds `[-100,100]` and starts with +2 and constant +0.

The nonzero-constant control uses constant seven, cost three, and unbounded
rows; its constant alternates between seven and thirteen. The zero-contribution
control uses cost zero, initial constant -0, and unbounded rows. Model construction
occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Positive first contribution | 331,872 | 291,488 | 12.17% | 8,516 → 7,364 |
| Negative first contribution | 332,944 | 292,624 | 12.11% | 8,516 → 7,364 |
| Initial negative-zero constant | 332,960 | 292,384 | 12.19% | 8,516 → 7,364 |
| Finite row endpoints | 681,216 | 640,576 | 5.97% | 17,732 → 16,580 |
| Nonzero-constant control | 342,672 | 342,864 | — | 8,900 → 8,900 |
| Zero-contribution control | 75,632 | 75,296 | — | 1,604 → 1,604 |

All four targets save 1,152 allocations per call, or 18 for each of the 64
nonzero contributions applied to a zero constant. Allocated bytes drop by
5.97–12.19% across the targets. Both controls retain their allocation counts; byte differences
on unchanged paths alone establish no benefit.

The following table gives all nine measured stages for each reference fixture.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 44,928 → 45,520 |
| afiro | sparse | 4,987 → 4,987 | 218,696 → 218,776 |
| afiro | presolve | 16,330 → 16,330 | 732,712 → 732,456 |
| afiro | dual | 17,145 → 17,145 | 868,248 → 868,616 |
| afiro | primal | 17,051 → 17,051 | 846,824 → 845,736 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,920 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,728 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 178,592 → 177,360 |
| adlittle | presolve | 82,776 → 82,776 | 3,347,160 → 3,345,352 |
| adlittle | dual | 84,791 → 84,791 | 4,135,512 → 4,136,152 |
| adlittle | primal | 85,589 → 85,589 | 4,413,192 → 4,412,968 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,688 → 461,544 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,280 → 607,248 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,000 → 112,736 |
| kb2 | sparse | 2,836 → 2,836 | 162,176 → 161,088 |
| kb2 | presolve | 230,004 → 230,004 | 10,681,336 → 10,676,456 |
| kb2 | dual | 231,206 → 231,206 | 11,132,376 → 11,131,320 |
| kb2 | primal | 231,373 → 231,373 | 11,146,456 → 11,145,528 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,240 → 877,984 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,816 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 301,152 → 300,496 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,200 → 2,853,056 |
| sc50a | dual | 68,706 → 68,706 | 3,198,288 → 3,198,368 |
| sc50a | primal | 68,651 → 68,651 | 3,151,136 → 3,150,912 |
| sc50a | dual_no_presolve | 961 → 961 | 306,592 → 306,144 |
| sc50a | primal_no_presolve | 964 → 964 | 232,280 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 218,008 → 217,144 |
| flugpl | presolve | 31,497 → 31,461 | 1,200,840 → 1,199,752 |
| flugpl | dual | 32,168 → 32,132 | 1,310,672 → 1,309,600 |
| flugpl | primal | 32,517 → 32,481 | 1,355,392 → 1,353,680 |
| flugpl | dual_no_presolve | 376 → 376 | 42,752 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,728 → 91,680 |

Full presolve and each whole primal/dual solve save 36 allocations on `flugpl`.
The other four fixtures retain their counts. Direct basic/doubleton/singleton/
sparse passes retain their counts on all five fixtures; the affected
eliminations occur later in the full presolve pipeline.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, complete primal vector,
and iteration count (`isequal`).

Machine-readable results:
[`basic-zero-constant-allocations-before.toml`](basic-zero-constant-allocations-before.toml)
and [`basic-zero-constant-allocations-after.toml`](basic-zero-constant-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=basic-zero-constant-basic-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function basic_zero_constant_probe(kind; count=128, T=Float64)
    direction = kind == :negative ? -1 : 1
    values = T[direction*(isodd(i) ? 2 : -2) for i in 1:count]
    cost = kind == :zero_contribution ? zero(T) : T(3)
    constant = kind == :nonzero_constant ? T(7) : kind in (:negative_zero,:zero_contribution) ? -zero(T) : zero(T)
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),fill(count+1,count)),vcat(ones(T,count),fill(T(2),count)),count,count+1)
    problem = LinearProblem(A,vcat(fill(cost,count),T[3]);objective_constant=constant,
        row_lower=fill(kind == :finite_rows ? T(-100) : nothing,count),
        row_upper=fill(kind == :finite_rows ? T(100) : nothing,count),
        column_lower=vcat(values,T[-10]),column_upper=vcat(values,T[10]))
    return problem,JSimplex._presolve_basic
end
for kind in (:positive,:negative,:negative_zero,:finite_rows,:nonzero_constant,:zero_contribution)
    problem, pass = basic_zero_constant_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 676 assertions and failed only the
four target allocation guards: 8,561 > 8,000; 8,524 > 8,000 (two cases);
and 17,740 > 17,250. Both controls passed. All 680 new assertions now pass as
part of 26,774 targeted assertions covering basic elimination and
related presolve allocation guards. Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; positive/
negative first contributions; initial negative zero; finite/unbounded rows;
nonzero-constant and zero-contribution controls; computed/cached selections;
retained matrices, bounds, objective values, primal/basis restoration,
removed-variable states, and source/selection immutability. Tiny nonzero
constants still participate in exact cancellation and cannot be rounded away.
Stored-256-bit BigFloat inputs under ambient precision 32/64/256 still enforce
contribution representability. Overflowing contributions and half-subnormal
finite row shifts still reject elimination, including from an initial zero
constant. Earlier objective-contribution tests remain in the targeted suite.

Independent read-only review found no issues. It passed 12,864 additional
assertions, separate from the focused 680, against an AST-renamed copy of
the preceding basic-presolve implementation: 560 independently constructed
model comparisons, 1,984 basis restorations, and 64 matching failure records.
Coverage included stored BigFloat precision, tiny constants, cancellation,
overflow/underflow rejection, repeated zero transitions, row staging, cached
selections, empty/free columns, signed zero, source aliases, and primal
restoration. Outputs matched the saved implementation; source values, identities,
and cached selections remained unchanged.

The mandatory full package suite passed **51,659/51,659** assertions in
5m36.4s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
