# Use negation for negative-unit products in exact elimination

Round 59 replaces multiplication by negative one with nonmutating negation in
`_subtract_scaled!`. This applies when either the elimination scale or the
source coefficient is negative one. Existing positive-unit shortcuts remain
first; other products retain general exact multiplication.

Cancellation, zero-result deletion, missing target entries, normalization,
interval calculations, work limits, contradictions, and postsolve behavior
are unchanged. The source dictionary and scale are preserved.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 58 allocation rounds. All 33 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

Each probe has 128 proportional rows, free columns, and a zero objective. The
first row is `1 ≤ x + 2y - z ≤ 6`. Remaining rows multiply it by two, negative
one, or one, with bounds reordered when the sign changes. All three reductions
retain the first row. Scale two exercises negative-unit source coefficients;
scale negative one also exercises general source coefficients with that scale.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Scale 2 | 773,216 | 737,976 | 4.56% | 19,787 → 18,898 |
| Scale -1 | 773,408 | 702,192 | 9.21% | 19,787 → 18,009 |
| Scale 1 | 598,688 | 599,776 | — | 15,215 → 15,215 |

The target probes remove 889 and 1,778 allocations, respectively. The positive
unit-scale control retains its allocation count; its small byte difference does
not establish a regression.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 227,520 → 214,984 | 5,051 → 4,739 | 915,088 → 888,496 |
| adlittle | 728,008 → 726,968 | 16,986 → 16,944 | 3,640,072 → 3,634,696 |
| kb2 | 3,751,688 → 3,545,080 | 87,503 → 82,564 | 11,478,072 → 11,271,656 |
| sc50a | 1,774,672 → 1,507,376 | 42,926 → 36,604 | 3,634,808 → 3,228,000 |
| flugpl | 203,472 → 199,424 | 4,312 → 4,214 | 1,341,536 → 1,341,600 |

All five direct dependency passes allocate less: 0.14–15.06% fewer bytes in
these runs, with consistently lower allocation counts.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,051,424 → 1,024,576 | 1,030,704 → 1,003,616 | 658 |
| adlittle | 4,430,200 → 4,426,168 | 4,706,776 → 4,701,400 | 84 |
| kb2 | 11,930,184 → 11,724,520 | 11,944,664 → 11,738,424 | 5,032 |
| sc50a | 3,980,600 → 3,572,912 | 3,933,240 → 3,525,744 | 10,075 |
| flugpl | 1,451,000 → 1,450,888 | 1,495,512 → 1,495,736 | 0 |

Whole solves on the four affected fixtures allocate 0.09–10.36% fewer bytes. Sc50a benefits
most, at 10.24–10.36%. Full presolve removes the same number of allocations as
each whole solve. Flugpl benefits in the isolated dependency pass, but earlier
presolve removes those opportunities; full-pipeline allocation counts are
unchanged. Its byte differences do not establish a benefit or regression.

Exact-arithmetic byte totals fluctuate across processes, so counts provide
clearer evidence for small differences. Unchanged paths without presolve vary
from -208 to zero bytes with identical allocation counts.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-negative-units-allocations-before.toml`](dependent-negative-units-allocations-before.toml)
and [`dependent-negative-units-allocations-after.toml`](dependent-negative-units-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-negative-units-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for scale in (1.0, 2.0, -1.0)
    count = 128
    multipliers = [1.0; fill(scale, count - 1)]
    problem = LinearProblem(sparse(multipliers * [1.0 2.0 -1.0]), zeros(3);
        row_lower=min.(multipliers, 6multipliers), row_upper=max.(multipliers, 6multipliers),
        column_lower=fill(nothing, 3))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

Both new allocation guards failed against the original implementation:
19,832 allocations exceeded the 19,400 limit and 19,795 exceeded 18,800.
The other 132 assertions, including the positive-unit-scale control, passed.
All 134 new assertions now pass, as do all 1,473 targeted dependency and
presolve assertions together. Allocation-count budgets avoid unstable
exact-arithmetic byte totals.

Direct helper tests use literal expected dictionaries for negative one in
either operand and both operands, signed/fractional/zero scale controls,
existing and absent target entries, exact cancellation, and preservation of
the source and scale. Full reduction tests cover Float32, Float64, BigFloat,
and Rational{BigInt}, dependent-row removal, contradictions, postsolve values,
and input preservation.

Independent review found no issues and separately passed all 134 new assertions.
Thirty-four saved-baseline comparisons passed 164 additional assertions:
sixteen direct helper cases, sixteen full reduction cases across all four
numeric types, and two mixed-precision BigFloat cases. These verify both
negative-unit operand positions, both operands equal to negative one,
cancellation, existing and absent entries, zero/fractional controls, retained
rows, failure fields, postsolve, and preservation of source, scale, and input.

The full mandatory suite passed all 21,239 assertions in 4m58.4s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
