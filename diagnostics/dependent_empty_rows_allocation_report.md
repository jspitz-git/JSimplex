# Skip coefficient dictionaries for empty dependent rows

Round 56 checks the row's nonzero entries before constructing its exact
coefficient dictionary in `reduce_dependent_rows`. Previously the pass built
an empty dictionary and then discarded it. `_row_entries` already excludes
stored zeros, so rows containing only explicit zeros take the same shortcut.

Empty rows remain retained and are not checked for feasibility by this pass;
the dedicated empty-row reduction handles that separately. Nonempty rows keep
their original proof construction, normalization, elimination, and interval
checks. Work limits and postsolve behavior are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 55 allocation rounds. All 35 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

Both target probes contain 128 zero rows, zero row bounds, free columns, and a
zero objective. One stores no matrix entries; the other stores one explicit
zero per row. Both retain the original model. The nonempty controls use 128
identical rows with coefficients `[1, 2, -1]` and bounds `[1, 6]` or `[0, 0]`.
The nonunit control scales all but the first row, including bounds, by two.
Each nonempty control retains the first row.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Empty rows | 80,400 | 6,672 | 91.70% | 649 → 137 |
| Stored zero rows | 80,400 | 6,672 | 91.70% | 649 → 137 |
| Unit weight | 598,144 | 599,488 | — | 15,215 → 15,215 |
| Nonunit weight | 859,296 | 860,768 | — | 22,073 → 22,073 |
| Nonempty rows, zero bounds | 472,984 | 474,104 | — | 10,897 → 10,897 |

Each target removes 512 allocations and 73,728 bytes. Nonempty controls retain
identical counts; their small byte differences reflect cross-process
exact-arithmetic allocation variation.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 255,040 → 255,312 | 5,708 → 5,708 | 969,376 → 968,992 |
| adlittle | 806,392 → 805,816 | 19,011 → 19,011 | 3,806,152 → 3,805,384 |
| kb2 | 4,109,928 → 4,111,288 | 96,494 → 96,494 | 12,146,472 → 12,144,312 |
| sc50a | 1,958,928 → 1,961,952 | 47,835 → 47,831 | 3,838,936 → 3,840,264 |
| flugpl | 217,536 → 218,544 | 4,681 → 4,681 | 1,372,560 → 1,373,984 |

Sc50a's isolated dependency pass removes four allocations for one empty row.
Its byte total rises slightly despite that count reduction. Other direct
fixture passes retain identical counts. Earlier presolve removes empty rows,
so these fixtures show no allocation-count benefit in the complete pipeline.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,105,056 → 1,105,920 | 1,083,408 → 1,083,920 | 0 |
| adlittle | 4,595,112 → 4,594,824 | 4,871,416 → 4,871,688 | 0 |
| kb2 | 12,596,408 → 12,595,272 | 12,610,632 → 12,608,344 | 0 |
| sc50a | 4,184,936 → 4,185,272 | 4,138,152 → 4,138,088 | 0 |
| flugpl | 1,482,696 → 1,483,384 | 1,526,936 → 1,527,912 | 0 |

All whole solves retain identical allocation counts; their byte differences
do not establish a benefit or regression. Unchanged paths without presolve
vary from -512 to +32 bytes with identical counts. This round's measured benefit
applies to empty rows when the dependency pass is invoked directly.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-empty-rows-allocations-before.toml`](dependent-empty-rows-allocations-before.toml)
and [`dependent-empty-rows-allocations-after.toml`](dependent-empty-rows-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-empty-rows-audit.toml
```

For the target probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
count = 128
for A in (spzeros(count, 3), sparse(collect(1:count), ones(Int, count), zeros(count), count, 3))
    problem = LinearProblem(A, zeros(3); row_lower=zeros(count), row_upper=zeros(count),
        column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

Both allocation guards failed against the original implementation: 694 and 657
allocations exceeded the 200 limit, while the other 110 assertions passed.
All 112 new assertions now pass, as do all 1,054 targeted dependency and presolve
assertions together. Allocation-count budgets avoid unstable exact-arithmetic
byte totals.

The tests cover empty matrices, stored zeros, zero-row models, the existing
large-row-count bypass, and interspersed empty/nonempty rows across Float32,
Float64, BigFloat, and Rational{BigInt}. They check preservation of matrix storage
and bounds, the existing handling of infeasible empty rows, correct row maps,
dependent-row removal, contradictions in nonempty rows, and postsolve values.

Independent review found no issues and separately passed all 112 new assertions.
Forty-one saved-baseline comparisons passed 238 additional assertions across
the four numeric types. These cover empty dimensions, explicit signed zeros,
varied bounds, interspersed dependencies, infeasibility, both size caps, and
mixed BigFloat precision. Complete results, identity behavior, postsolve maps
and primal output, and preservation of all input fields were compared.

The full mandatory suite passed all 20,820 assertions in 4m55.6s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
