# Integrality relaxation allocation audit

Round 20 removes temporary bound copies from `relax_integrality` when no domain
requires a bound adjustment. This transformation is called by every accepted
solve, including continuous LPs, to create an independent working model.

The helper initially reads the original lower and upper bound vectors. Continuous
and ordinary integer variables keep their bounds. On the first binary,
semi-continuous, or semi-integer variable, it copies both vectors before running
the existing bound adjustments. Subsequent special domains reuse those working
copies. The final `LinearProblem{T}` constructor still copies and validates every
input array, so the result never shares mutable bound storage with its source.

This changes allocation timing only: binary clamping, semi-domain relaxation,
stored coefficient precision, model metadata, and final ownership are preserved.

## Method

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native
basis factorization with PFI updates. Each case was warmed twice and sampled
three times, with setup outside measurement and garbage collection before each
sample. Tables report minimum allocated bytes. All 28 measurements per run
recorded zero compilation time. The baseline includes the preceding 19 rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped verification, so no runtime-speedup claim is made. Values represent
bytes allocated per call, not peak or retained memory.

## Measurements

Synthetic models have no rows, 4,096 columns, unit lower bounds, unbounded upper
bounds, and zero objective coefficients.

| Domain of every variable | Before | After | Reduction |
| --- | ---: | ---: | ---: |
| Continuous | 336,704 | 205,488 | 38.97% |
| Integer | 336,704 | 205,488 | 38.97% |
| Semi-integer | 336,704 | 336,704 | unchanged |

The continuous and integer probes drop from 30 to 24 allocations. The
semi-integer probe retains both the previous byte total and allocation count,
because it still needs the temporary bounds.

| Model | Relaxation before | Relaxation after | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| afiro | 6,320 | 5,168 | 18.23% | 28 → 24 |
| adlittle | 18,416 | 15,088 | 18.07% | 30 → 26 |
| kb2 | 11,184 | 9,648 | 13.73% | 30 → 26 |
| sc50a | 9,632 | 7,936 | 17.61% | 28 → 24 |
| flugpl | 4,064 | 3,328 | 18.11% | 28 → 24 |

Whole solves without presolve allocated 0.19–1.69% fewer bytes. Allocation counts
fell by four in all 20 whole-solve configurations, including those with presolve.
For runs with presolve, small byte-total differences ranged from a 2,160-byte
decrease to a 576-byte increase. These small differences do not establish a
uniform byte reduction for entire presolved solves. The isolated relaxation
results are the clearest evidence of
the removed copies.

All five relaxed model snapshots matched their baseline exactly: CSC arrays,
objective and constant, objective sense, bounds, domains, and model/row/column
names. All 20 whole-solve combinations (five fixtures, primal/dual, presolve on/off)
remained `OPTIMAL`; status, objective, complete primal vector, and iteration count
matched baseline snapshots exactly with `isequal`.

Machine-readable results are in
[`relaxation-allocations-before.toml`](relaxation-allocations-before.toml) and
[`relaxation-allocations-after.toml`](relaxation-allocations-after.toml).

## Reproduction

Run from the repository root with
`julia --startup-file=no --compiled-modules=existing --project=dev`:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays

problem = read_mps("test/fixtures/solver/netlib/adlittle.mps")
println(measure_allocations(_ -> JSimplex.relax_integrality(problem); samples=3))

for domain in (CONTINUOUS, INTEGER, SEMI_INTEGER)
    wide = LinearProblem(spzeros(0, 4096), zeros(4096);
        column_lower=ones(4096), variable_domains=fill(domain, 4096))
    println(measure_allocations(_ -> JSimplex.relax_integrality(wide); samples=3))
end
```

The existing `dev/allocations.jl` CLI measures the whole-solve combinations.

## Regression coverage

Both continuous and integer allocation budgets failed before the change at
336,704 bytes against a 220,000-byte limit and now pass at 205,488 bytes.

The 165 new checks cover unchanged continuous/integer bounds, mixed domains,
copying before the first special domain after an unchanged prefix, binary and
semi-domain values, unbounded semi-continuous variables, source preservation,
independent result arrays, empty models, and type inference. Numeric coverage
includes Float32, Float64, BigFloat, and Rational{BigInt}. A separate check
preserves stored BigFloat bound values under lower ambient precision.

Independent review found no issue. Its 150 randomized domain-sequence cases
across six numeric types matched every baseline model field and bound
representation without modifying source bounds. A mixed-domain BigFloat case
also preserved baseline values and precisions with 512-bit inputs under an
ambient precision of 64 bits.

The complete mandatory suite passed **16,141/16,141** tests, including the 165
new checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
