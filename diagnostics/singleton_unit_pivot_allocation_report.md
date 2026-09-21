# Skip division by one when normalizing singleton bounds

Round 37 avoids exact rational division by one in `_singleton_bound`. A finite
bound still converts to an exact rational, and `_represent_exact` still checks
its conversion to the model's numeric type. Only the division is skipped for a
unit coefficient. Other coefficients and the unbounded early return retain
their previous behavior.

Returning the original bound directly would change signed-zero normalization
and could accept a stored BigFloat value that is not representable at the
working precision. The implementation retains both existing behaviors.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 32 measurements per run recorded zero compilation
time. The baseline includes the preceding 36 allocation rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The unit-pivot probe has 128 rows `2 ≤ xᵢ ≤ 6`, free column bounds, and objective
coefficients of one. The nonunit control scales the matrix and row bounds by
two. Both passes remove all rows and produce column bounds `[2,6]`.

| Probe | Before | After | Reduction | Allocations before → after |
| --- | ---: | ---: | ---: | ---: |
| Unit pivots | 481,928 | 394,408 | 18.16% | 12,852 → 10,548 |
| Nonunit pivots | 483,176 | 483,752 | — | 12,852 → 12,852 |

The unit probe removes 2,304 allocations. The nonunit control keeps identical
allocation counts; its 576-byte increase is not attributed to this change.

| Model | Singleton pass before → after | Allocations before → after | Full presolve before → after |
| --- | ---: | ---: | ---: |
| afiro | 16,224 → 15,552 | 185 → 167 | 1,126,920 → 1,126,248 |
| adlittle | 41,528 → 40,248 | 273 → 241 | 4,727,896 → 4,726,184 |
| kb2 | 1,408 → 1,408 | 8 → 8 | 13,121,824 → 13,118,976 |
| sc50a | 1,648 → 1,648 | 8 → 8 | 4,111,456 → 4,111,296 |
| flugpl | 11,864 → 11,192 | 159 → 141 | 1,487,640 → 1,487,176 |

The affected standalone passes save 3.08–5.66% of allocated bytes. Kb2 has no
standalone benefit but saves allocations in later singleton passes within full
presolve. Sc50a retains identical counts throughout; its small whole-solve byte
changes do not establish a benefit.

| Model | Dual solve before → after | Primal solve before → after | Allocations removed per solve |
| --- | ---: | ---: | ---: |
| afiro | 1,263,096 → 1,262,152 | 1,241,912 → 1,240,536 | 18 |
| adlittle | 5,518,024 → 5,514,728 | 5,794,344 → 5,792,008 | 32 |
| kb2 | 13,574,400 → 13,572,480 | 13,587,344 → 13,586,288 | 16 |
| sc50a | 4,458,928 → 4,457,392 | 4,411,632 → 4,409,904 | 0 |
| flugpl | 1,598,000 → 1,597,104 | 1,642,352 → 1,641,760 | 18 |

Full presolve removes the same number of allocations as each whole solve.
Cross-process byte variability prevents attributing the entire byte difference
to this change: unchanged paths without presolve vary from -224 to +240 bytes
with identical allocation counts, and exact arithmetic in presolve introduces
further variation. The unit-pivot probe gives the clearest measurement.

All ten model snapshots (five fixtures × singleton/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`singleton-unit-pivot-allocations-before.toml`](singleton-unit-pivot-allocations-before.toml)
and [`singleton-unit-pivot-allocations-after.toml`](singleton-unit-pivot-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=reduce_singleton_rows --output=singleton-unit-pivot-audit.toml
```

For the probes, run from the repository root with the same flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays
for pivot in (1.0, 2.0)
    count = 128
    A = sparse(1:count, 1:count, fill(pivot, count), count, count)
    problem = LinearProblem(A, ones(count); row_lower=fill(2pivot, count),
        row_upper=fill(6pivot, count), column_lower=fill(nothing, count))
    println(measure_allocations(_ -> JSimplex.reduce_singleton_rows(problem); samples=3))
end
```

## Regression coverage

The final 11,000-allocation limit fails against the original helper at 12,897
and passes after the change at 10,593. Direct test instrumentation records 45
more allocations than the warmed benchmark. The initial 10,000 estimate was
replaced with the final limit after measuring the actual saving; the original
helper was rerun to verify that the final guard still detects the regression.

All 121 new assertions pass. They cover the allocation guard and produced
column bounds; pivots of 1, -1, 2, and 1/2; finite and unbounded endpoints;
inexact nonunit rejection; input preservation; negative-zero normalization;
and a 256-bit BigFloat bound rejected at a 64-bit working precision despite
its unit coefficient. Numeric coverage includes Float32, Float64, BigFloat,
and Rational{BigInt}.

Together with existing singleton scan, bound-copy, and source-map tests, all
385 targeted assertions pass.

Independent review found no issue and passed 2,320 assertions: 121 focused,
1,827 helper equivalence/input-preservation, 120 row-pass equivalence, and 252
BigFloat precision checks. Helper checks covered ten numeric types, including
Float16 and fixed-width rationals. Twenty warmed allocation comparisons across
Float32, Float64, BigFloat, and Rational{BigInt} confirmed 2,304 fewer allocations
for every unit case; all sixteen negative/nonunit controls retained baseline
counts without a boxing regression.

Review excluded absolute BigFloat exponent extrema after reproducing failures
in the shared exact-conversion path on the baseline, including an
`OutOfMemoryError`. Bounded values through ±2¹⁰⁰⁰ and working-precision changes
were covered. Internal BigInt object identity is outside the value-preservation
contract; actual input preservation was checked.

The complete mandatory suite passed **18,306/18,306** tests, including the 121
new assertions. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
