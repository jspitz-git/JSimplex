# Skip zero objective contributions in basic presolve

Round 110 changes only `_presolve_basic` in `src/presolve.jl`.
When an eliminated column has exactly zero objective cost or exactly zero
eliminated value, the original objective constant is reused immediately.
This avoids converting its cost to an exact rational and multiplying it by the
already exact eliminated value just to discover that its contribution is zero.

Nonzero contributions retain exact multiplication, addition, and the existing
representability check before any staged row changes. The eliminated value is
still converted exactly for row shifts. Row-bound checks, rejection, staged
updates, removed values/states, empty-row checks, and primal/basis restoration
are unchanged. Zero comparisons introduce no tolerance or rounded arithmetic.
The unchanged constant retains its identity, signed zero, and stored precision.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 109 allocation rounds. All 51 measurements in each run
recorded zero compilation time. Bytes are minimum allocated bytes per call,
not peak or retained memory. Timings overlapped validation; no runtime speedup
is claimed.

Each probe has 128 rows `x_i+2*y`, both row endpoints unbounded, and a retained
variable `y` with bounds `[-10,10]` and cost three. The objective constant is
seven. The four targets fix all `x_i`: zero cost and value 2; negative-zero cost
and value -2; cost 3 and zero value; and cost -3 and negative-zero value.
The nonzero control fixes `x_i=2` with cost 3. The no-elimination control gives
`x_i` bounds `[-2,2]` with cost 3. Model construction occurs outside measurement.

| Probe | Bytes before | Bytes after | Byte reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Zero cost | 151,632 | 75,504 | 50.21% | 3,652 → 1,604 |
| Negative-zero cost | 153,264 | 75,168 | 50.96% | 3,652 → 1,604 |
| Zero value | 153,232 | 64,448 | 57.94% | 3,652 → 1,220 |
| Negative-zero value | 153,232 | 64,432 | 57.95% | 3,652 → 1,220 |
| Nonzero contribution control | 342,928 | 342,816 | — | 8,900 → 8,900 |
| No-elimination control | 4,080 | 4,080 | — | 15 → 15 |

Zero-cost probes save 2,048 allocations (16 per eliminated variable);
zero-value probes save 2,432 (19 per eliminated variable). Allocated bytes
drop by 50.21–57.95% across the four targets. Both controls retain their allocation counts; byte differences
on unchanged paths alone establish no benefit.

The following table gives all nine measured stages for each reference fixture.

| Model | Stage | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | basic | 15 → 15 | 1,392 → 1,392 |
| afiro | doubleton | 3 → 3 | 1,072 → 1,072 |
| afiro | singleton | 843 → 843 | 45,824 → 45,616 |
| afiro | sparse | 4,987 → 4,987 | 218,392 → 218,968 |
| afiro | presolve | 16,330 → 16,330 | 732,392 → 733,032 |
| afiro | dual | 17,145 → 17,145 | 868,232 → 868,184 |
| afiro | primal | 17,051 → 17,051 | 846,456 → 846,040 |
| afiro | dual_no_presolve | 555 → 555 | 89,920 → 89,936 |
| afiro | primal_no_presolve | 759 → 759 | 121,728 → 121,776 |
| adlittle | basic | 15 → 15 | 2,928 → 2,928 |
| adlittle | doubleton | 3 → 3 | 2,208 → 2,208 |
| adlittle | singleton | 608 → 608 | 60,816 → 60,816 |
| adlittle | sparse | 2,843 → 2,843 | 177,616 → 177,536 |
| adlittle | presolve | 82,814 → 82,776 | 3,348,872 → 3,345,352 |
| adlittle | dual | 84,829 → 84,791 | 4,137,400 → 4,136,360 |
| adlittle | primal | 85,627 → 85,589 | 4,414,472 → 4,412,904 |
| adlittle | dual_no_presolve | 1,326 → 1,326 | 461,496 → 461,432 |
| adlittle | primal_no_presolve | 1,899 → 1,899 | 607,344 → 607,616 |
| kb2 | basic | 15 → 15 | 1,680 → 1,680 |
| kb2 | doubleton | 3 → 3 | 1,664 → 1,664 |
| kb2 | singleton | 2,060 → 2,060 | 112,640 → 113,200 |
| kb2 | sparse | 2,836 → 2,836 | 161,424 → 161,472 |
| kb2 | presolve | 230,004 → 230,004 | 10,679,736 → 10,678,600 |
| kb2 | dual | 231,206 → 231,206 | 11,132,296 → 11,131,640 |
| kb2 | primal | 231,373 → 231,373 | 11,145,832 → 11,146,584 |
| kb2 | dual_no_presolve | 1,508 → 1,508 | 878,016 → 877,984 |
| kb2 | primal_no_presolve | 1,054 → 1,054 | 260,832 → 260,864 |
| sc50a | basic | 60 → 60 | 17,760 → 17,760 |
| sc50a | doubleton | 3 → 3 | 1,808 → 1,808 |
| sc50a | singleton | 298 → 298 | 12,608 → 12,608 |
| sc50a | sparse | 6,647 → 6,647 | 300,656 → 300,448 |
| sc50a | presolve | 67,634 → 67,634 | 2,853,312 → 2,853,680 |
| sc50a | dual | 68,706 → 68,706 | 3,198,720 → 3,197,840 |
| sc50a | primal | 68,651 → 68,651 | 3,151,696 → 3,150,880 |
| sc50a | dual_no_presolve | 961 → 961 | 306,128 → 306,448 |
| sc50a | primal_no_presolve | 964 → 964 | 232,200 → 232,200 |
| flugpl | basic | 15 → 15 | 1,056 → 1,056 |
| flugpl | doubleton | 3 → 3 | 800 → 800 |
| flugpl | singleton | 100 → 100 | 4,384 → 4,384 |
| flugpl | sparse | 5,772 → 5,772 | 217,240 → 216,808 |
| flugpl | presolve | 31,516 → 31,497 | 1,202,624 → 1,200,696 |
| flugpl | dual | 32,187 → 32,168 | 1,311,624 → 1,310,768 |
| flugpl | primal | 32,536 → 32,517 | 1,356,568 → 1,355,392 |
| flugpl | dual_no_presolve | 376 → 376 | 42,736 → 42,736 |
| flugpl | primal_no_presolve | 739 → 739 | 91,680 → 91,728 |

Full presolve and each whole primal/dual solve save 38 allocations on
`adlittle` and 19 on `flugpl`. The other three fixtures retain their counts.
Direct basic/doubleton/singleton/sparse passes retain their counts on all five
fixtures; the affected eliminations occur later in the full presolve pipeline.
All no-presolve solves retain their allocation counts. Cross-process byte
variations alone establish no benefit on unchanged paths.

All 25 model snapshots (five fixtures × basic/doubleton/singleton/sparse/full
presolve) matched exactly: CSC arrays, objective and constant, sense, bounds,
domains, names, and original column count. All 20 whole-solve combinations
remained `OPTIMAL`, with identical status, objective, complete primal vector,
and iteration count (`isequal`).

Machine-readable results:
[`basic-zero-objective-allocations-before.toml`](basic-zero-objective-allocations-before.toml)
and [`basic-zero-objective-allocations-after.toml`](basic-zero-objective-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=_presolve_basic --output=basic-zero-objective-basic-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
function basic_zero_objective_probe(kind; count=128, T=Float64)
    cost = T(kind in (:zero_cost,:negative_zero_cost) ? 0 : kind == :negative_zero_value ? -3 : 3)
    kind == :negative_zero_cost && (cost = -zero(T))
    value = kind == :negative_zero_value ? -zero(T) : T(kind == :zero_value ? 0 : kind == :negative_zero_cost ? -2 : 2)
    A = sparse(vcat(collect(1:count),collect(1:count)),vcat(collect(1:count),fill(count+1,count)),vcat(ones(T,count),fill(T(2),count)),count,count+1)
    problem = LinearProblem(A,vcat(fill(cost,count),T[3]);objective_constant=T(7),
        row_lower=fill(nothing,count),row_upper=fill(nothing,count),
        column_lower=vcat(fill(kind == :no_elimination ? T(-2) : value,count),T[-10]),
        column_upper=vcat(fill(value,count),T[10]))
    return problem,JSimplex._presolve_basic
end
for kind in (:zero_cost,:negative_zero_cost,:zero_value,:negative_zero_value,:nonzero,:no_elimination)
    problem, pass = basic_zero_objective_probe(kind)
    println(measure_allocations(_ -> pass(problem); samples=3))
end
```

## Regression coverage

Before the change, the focused file passed 682 assertions and failed only the
four target allocation guards: 3,697 and 3,660 (three cases) exceeded 3,000.
Both controls passed. All 686 new assertions now pass as part of
24,576 targeted assertions covering basic elimination and related
presolve allocation guards. Existing allocation budgets were not relaxed.

New checks cover Float32, Float64, BigFloat, and Rational{BigInt}; zero costs
and zero values of both signs; computed/cached selections; retained matrices,
bounds and constant identity, objective values, primal/basis restoration,
removed-variable states, and source/selection immutability. Stored-256-bit
BigFloat costs, eliminated values, and unchanged constants retain their exact
values under ambient precision 32/64/256. Tiny nonzero contributions remain
nonzero; half-subnormal objective contributions still reject elimination;
and zero cost does not bypass rejection of a nonrepresentable row shift.

Independent read-only review found no issues. It passed 9,040 additional
assertions, separate from the focused 686, against an AST-renamed copy of
the preceding basic-presolve implementation: 400 model comparisons, 1,344
basis-restoration comparisons, and 64 matching expected failures. Checks
covered full result metadata, exact primal objective equality, source/container/
element identity and immutability, stored-256-bit BigFloat constants under
ambient precision 32/64/256, tiny nonzero and underflow rejection, shared-row
staged rejection followed by zero-value/zero-cost/empty candidates, cached
free/lower/upper states, signed zero, and empty-row failures.

The mandatory full package suite passed **49,461/49,461** assertions in
5m36.3s (exit 0):

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'using JSimplex; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex.MOI)))); include("test/runtests.jl")'
```

`git diff --check` passed. The previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
