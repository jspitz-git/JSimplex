# Reuse missing negative-unit contributions in exact elimination

Round 60 avoids constructing a product and then negating it when
`_subtract_scaled!` encounters a missing target entry and either factor is
negative one. Subtracting that product from zero is exactly the other factor.
The helper reuses that value, inserts it only when nonzero, and continues.

Existing target entries retain their original multiplication, subtraction,
and cancellation handling. Other missing entries also keep the previous path.
Neither source values nor the scale are mutated. Normalization, work limits,
interval calculations, contradictions, and postsolve behavior are unchanged.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times, with setup
outside measurement and garbage collection before each sample. The baseline
includes the preceding 59 allocation rounds. All 33 measurements in each run
recorded zero compilation time. Values below are minimum allocated bytes per
call, not peak or retained memory. Timings overlapped validation; no runtime
speedup is claimed.

Each probe has 64 independent blocks `[1 v 0; s 0 1]`, giving 128 rows and 192
free columns, a zero objective, and upper row bounds of three. Eliminating the
first column introduces a previously absent second-column coefficient. The
targets use `(s, v) = (-1, 2)` and `(2, -1)`; the control uses `(2, 2)`. All
rows are retained and the original model remains unchanged.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Negative-unit scale | 355,248 | 342,512 | 3.59% | 6,618 → 6,234 |
| Negative-unit source value | 355,504 | 347,328 | 2.30% | 6,618 → 6,362 |
| Nonunit control | 374,320 | 372,848 | — | 7,066 → 7,066 |

The targets remove 384 and 256 allocations, respectively. The control retains
its allocation count; its byte difference does not establish a benefit.

| Model | Dependency pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 215,320 → 208,896 | 4,739 → 4,565 | 891,088 → 878,112 |
| adlittle | 727,816 → 725,256 | 16,944 → 16,932 | 3,637,752 → 3,632,776 |
| kb2 | 3,548,152 → 3,499,168 | 82,564 → 80,974 | 11,271,880 → 11,220,264 |
| sc50a | 1,512,432 → 1,418,608 | 36,604 → 33,322 | 3,227,968 → 3,086,432 |
| flugpl | 201,152 → 198,176 | 4,214 → 4,158 | 1,342,240 → 1,339,504 |

All five direct dependency passes allocate less: 0.35–6.20% fewer bytes in these
runs, with consistently lower allocation counts.

| Model | Whole dual solve before → after | Whole primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,025,584 → 1,014,256 | 1,004,400 → 992,752 | 336 |
| adlittle | 4,426,456 → 4,421,608 | 4,702,584 → 4,698,584 | 24 |
| kb2 | 11,724,776 → 11,676,760 | 11,737,992 → 11,688,888 | 1,700 |
| sc50a | 3,573,904 → 3,432,656 | 3,526,704 → 3,384,640 | 4,944 |
| flugpl | 1,451,832 → 1,448,872 | 1,496,424 → 1,493,688 | 0 |

Whole solves on the four affected fixtures allocate 0.09–4.03% fewer bytes.
Sc50a benefits most, at 3.95–4.03%. Full presolve removes the same number of
allocations as each whole solve. Flugpl benefits in the isolated dependency
pass, but its full-pipeline allocation counts are unchanged; the corresponding
byte differences do not establish a benefit.

Exact-arithmetic byte totals fluctuate across processes, so counts provide
clearer evidence for small differences. Unchanged paths without presolve vary
from -448 to +32 bytes with identical allocation counts.

All ten model snapshots (five fixtures × dependency/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`dependent-missing-negation-allocations-before.toml`](dependent-missing-negation-allocations-before.toml)
and [`dependent-missing-negation-allocations-after.toml`](dependent-missing-negation-allocations-after.toml).
Both saved artifacts match the measurement source files byte for byte.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_dependent_rows --output=dependent-missing-negation-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for (scale, value) in ((-1.0, 2.0), (2.0, -1.0), (2.0, 2.0))
    count = 128
    A = kron(spdiagm(0 => ones(count ÷ 2)), sparse([1.0 value 0.0; scale 0.0 1.0]))
    problem = LinearProblem(A, zeros(size(A, 2)); row_upper=fill(3.0, count),
        column_lower=fill(nothing, size(A, 2)))
    println(measure_allocations(_ -> JSimplex.reduce_dependent_rows(problem); samples=3))
end
```

## Regression coverage

Both target allocation guards failed against the original implementation:
6,663 and 6,626 allocations exceeded the 6,450 limit. The other 130 assertions,
including the nonunit control, passed. All 132 new assertions now pass, as do
all 1,605 targeted dependency and presolve assertions together. Allocation-count
budgets avoid unstable exact-arithmetic byte totals.

Direct helper tests cover negative one in either factor and both factors,
zero and fractional controls, absence of stored zero results, existing-entry
subtraction and cancellation, and preservation of source and scale. Full
reduction tests cover all four numeric types, newly introduced coefficients,
dependent-row removal, contradictions, postsolve, and input preservation.

Independent review found no issues and separately passed all 132 new assertions.
Thirty-two saved-baseline comparisons passed 184 additional assertions:
fourteen helper cases, sixteen full reductions across the four numeric types,
and two mixed-precision BigFloat cases. These verify exact arithmetic, omitted
zero results, existing-entry cancellation, contradictions, postsolve, and
preservation of the source, scale, and other inputs.

The full mandatory suite passed all 21,371 assertions in 4m52.6s.
`git diff --check` passed. The two previously documented JET development-suite
failures remain outside this round's scope; the full optional development suite
was not rerun.
