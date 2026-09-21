# Skip unit-pivot normalization in dependent-row elimination

Round 27 skips normalization in `reduce_dependent_rows` when the selected exact
pivot is one. The row coefficients and its proof combination are already
normalized, so dividing either dictionary's values by one only creates temporary
`Rational{BigInt}` objects. Other pivots follow the original normalization path.
Elimination, interval proofs, work limits, row selection, and postsolve maps are
unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 26 rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The unit-pivot probe has 128 independent rows `xᵢ + xᵢ₊₁ ≤ 3`, free variables,
and a zero objective. No rows are removed. It fell from **420,960 to 287,424 bytes
(31.72%)**, and from 8,342 to 4,886 allocations. The 3,456 removed allocations
come from avoiding normalization of two coefficients and one proof entry per
row. A control with rows `2xᵢ + xᵢ₊₁ ≤ 3` retained all 8,342 allocations; its
byte total varied from 422,016 to 421,056.

| Model | Dependency pass before | After | Allocations before → after | Full presolve before | After |
| --- | ---: | ---: | ---: | ---: | ---: |
| afiro | 267,728 | 258,944 | 6,070 → 5,854 | 1,169,784 | 1,143,576 |
| adlittle | 853,784 | 809,960 | 20,246 → 19,175 | 4,869,240 | 4,766,136 |
| kb2 | 4,150,152 | 4,135,272 | 97,463 → 97,229 | 13,164,496 | 13,163,552 |
| sc50a | 1,971,328 | 1,967,088 | 48,123 → 48,069 | 4,283,712 | 4,142,064 |
| flugpl | 244,304 | 219,312 | 5,316 → 4,731 | 1,506,720 | 1,503,952 |

Direct dependency-pass byte reductions range from 0.22% to 10.23%. Presolve
changes the matrices seen by later passes, so direct-pass savings do not predict
whole-solver savings on the same original fixture.

| Model | Whole dual before | After | Whole primal before | After | Allocations removed per solve |
| --- | ---: | ---: | ---: | ---: | ---: |
| afiro | 1,305,576 | 1,278,440 | 1,283,544 | 1,257,720 | 648 |
| adlittle | 5,658,536 | 5,555,416 | 5,935,656 | 5,832,328 | 2,628 |
| kb2 | 13,615,488 | 13,615,232 | 13,629,664 | 13,630,496 | 0 |
| sc50a | 4,629,360 | 4,487,488 | 4,581,872 | 4,440,496 | 3,699 |
| flugpl | 1,616,168 | 1,614,696 | 1,660,552 | 1,659,016 | 0 |

These solves enable presolve. Afiro, adlittle, and sc50a show 1.74–3.09% fewer
allocated bytes with reduced allocation counts. The unchanged counts on kb2 and
flugpl do not establish an optimization benefit for their whole solves. Paths
without presolve also retain identical counts and vary from -240 to +80 bytes.
Small byte differences, including the 832-byte increase on primal kb2, should
not be attributed to this change.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependency-unit-pivot-allocations-before.toml`](dependency-unit-pivot-allocations-before.toml)
and [`dependency-unit-pivot-allocations-after.toml`](dependency-unit-pivot-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependency-unit-pivot-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for pivot in (1.0, 2.0)
    count = 128
    A = sparse([collect(1:count); collect(1:count)],
        [collect(1:count); collect(2:count+1)],
        [fill(pivot, count); ones(count)], count, count + 1)
    problem = LinearProblem(A, zeros(count + 1); row_upper=fill(3.0, count),
        column_lower=fill(nothing, count + 1))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

The direct-call allocation test failed before the change at 411,680 bytes against
a 350,000-byte limit and now passes. Its call context and equivalent model
construction differ from the warmed benchmark, so its byte count is not the
table's benchmark result.

The 226 new checks include the budget and identity result on independent rows,
plus redundant and contradictory dependent rows after pivots of 1, -1, 2, and
1/2. The second pivot becomes one through elimination and has a proof combining
two original rows. Checks cover retained coefficients and bounds, row maps,
postsolve reconstruction, and input preservation. Numeric coverage includes
Float32, Float64, BigFloat, and Rational{BigInt}.

Independent review found no issue, including in shared `Rational{BigInt}` values:
later arithmetic replaces dictionary entries without mutating their BigInts.
Its 216 differential cases across six numeric types matched baseline outputs,
maps, failure metadata, and deep-copied source inputs. It independently passed
all 226 targeted assertions.

The complete mandatory suite passed **16,990/16,990** tests, including the 226 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
