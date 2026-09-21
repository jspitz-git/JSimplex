# Allocation audit: MOI translation

This third round targets translation from MathOptInterface models. The preceding
presolve and MPS changes remain in both measurements; the baseline MOI code is
unchanged from `4fb2026`. Measurements use Julia 1.13.0 on aarch64-linux-gnu with
one Julia thread. Each entry is the minimum of three warmed calls, with no
compilation observed in any measured call. These are cumulative Julia heap
allocations, not peak memory.

## Findings and changes

The `adlittle` allocation profile identified per-row coefficient dictionaries
and growing affine-evaluation vectors as avoidable translation costs.

- Evaluation vectors now allocate their known final length directly. Each
  constraint retains independent vectors, including its original term order.
- A lazily allocated integer vector records the last triplet position for each
  column. The current row's starting position distinguishes an existing entry
  from an entry belonging to an earlier row. Duplicate coefficients are added
  in input order using the existing `_moi_add` operation.
- This replaces a fresh dictionary for every affine row. Scratch requires
  O(columns) memory once, with O(terms) aggregation work and no per-row clearing.
  Empty rows and models without affine terms do not initialize this scratch.

A stress case with one 10,000-term row followed by 2,000 singleton rows also
checked that wide rows do not impose repeated clearing work on later rows.
Constraint mappings, shifted bounds, constant terms, and retained evaluations
keep their existing semantics.

## Results

| Input | Before (B) | After (B) | Fewer bytes | Before allocations | After allocations |
|---|---:|---:|---:|---:|---:|
| afiro | 75,608 | 62,616 | 17.2% | 1,373 | 1,251 |
| adlittle | 238,728 | 187,224 | 21.6% | 3,533 | 3,179 |
| kb2 | 161,952 | 132,400 | 18.2% | 2,494 | 2,232 |
| sc50a | 129,416 | 106,584 | 17.6% | 2,236 | 2,025 |
| flugpl | 58,360 | 50,472 | 13.5% | 1,036 | 966 |
| greenbea | 16,594,000 | 12,318,008 | 25.8% | 237,372 | 192,150 |

Sources are prepared `MOI.Utilities.Model{Float64}` models of the fixtures'
continuous relaxations. File loading and source construction are outside the
translation measurement. Every `LinearProblem` field, retained evaluation,
mapped index, and translation error was compared with a serialized pre-change
snapshot using `isequal`. All six cases matched exactly.

Complete `MOI.optimize!` calls on the five smaller models allocated 0.2–0.8%
fewer bytes. All five remained `OPTIMAL`, with exactly matching objective values
and iteration counts. Most solve allocations occur after translation, so the
larger translation savings do not represent equivalent whole-solve savings.
The `greenbea` measurement covers translation only.

Machine-readable measurements are in
[`moi-allocations-before.toml`](moi-allocations-before.toml) and
[`moi-allocations-after.toml`](moi-allocations-after.toml). Timings were collected
while other validation ran, so no runtime-speedup claim is made.

## Reproduction

Use the existing full-pipeline audit on the smaller registered datasets:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=moi_translation --output=moi-audit.toml
```

To isolate translation, including `greenbea`, run the following in Julia with
`--project=dev` from the repository root:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

problem = read_mps("dev/fixtures/greenbea.mps")
source = JSimplexAllocations.moi_source(JSimplex.relax_integrality(problem))
optimizer = JSimplex.Optimizer()
measure_allocations(_ -> JSimplex._translate_moi_model(optimizer, source); samples=3)
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and input files for comparisons.

## Regression coverage

The allocation budget test rejects the original translator's 453,784-byte
measurement on 256 short rows with repeated terms. Its 380,000-byte limit allows
headroom for result storage and source getters. Additional checks cover
duplicate cancellation, disjoint and empty rows, constant shifts, and retained
evaluations after a subsequent translation for Float32, Float64, BigFloat, and
Rational{BigInt}.

Independent review found no actionable issue. Its 40 randomized translations
matched the original translator across five numeric types, all four affine set
types, variable bounds, empty rows, and duplicate terms, comparing every model
field, mapped affine constraint index, and retained evaluation.

The JuMP integration suite passed all 23 tests, including generic numeric types.
The complete mandatory suite passed **14,212/14,212** tests, including the new
25 MOI allocation and evaluation checks. The two previously documented JET
development-suite failures remain outside this round's scope; this is not a
claim that the full optional development suite passes.
