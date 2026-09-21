# Bound-only presolve result allocation audit

Round 19 removes intermediate row slices from `_row_result` when all rows are
retained in their original order. This occurs when propagation changes column
bounds without removing rows. Previously, the helper sliced the complete sparse
matrix, row bounds, and row names before the model constructor copied them again.

The helper now supplies those original arrays directly to `LinearProblem{T}`,
which still copies and validates its inputs. The resulting model therefore keeps
independent mutable arrays. Missing row names are also passed directly for the
constructor to copy, avoiding a temporary empty vector.

The optimization checks the row indices, not just their count: reordered or
reduced row selections still use slicing. Sparse matrices with spare backing
storage also retain the matrix-slicing path to discard inactive entries. Without
this guard, Julia 1.13's `copy` rejects the padded buffers, which the old row slice
accepted. The existing no-change identity return is untouched.

## Method

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native
basis factorization with PFI updates. Each case was warmed twice and sampled
three times with input preparation outside measurement and garbage collection
before each sample. Tables report minimum allocated bytes. All 36 measurements
per run recorded zero compilation time. The baseline includes the preceding 18
allocation rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timing
overlapped validation, so no runtime-speedup claim is made. The measurements are
bytes allocated per call, not peak or retained memory.

## Measurements

For a dense 128 × 128 CSC matrix, changing one column lower bound without
removing rows reduced allocation from **544,816 to 276,048 bytes (49.33%)**.
Allocation count fell from 49 to 33.

The `bounds_only` cases below exercise `_row_result` directly with all rows and
one changed lower bound, prepared outside measurement. They measure result
construction without executing propagation. The propagation cases run the real
`propagate_row_bounds` pass on the original fixtures.

| Model | Bounds-only before | Bounds-only after | Reduction | Propagation before | Propagation after | Reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| afiro | 9,472 | 6,048 | 36.15% | 202,688 | 198,416 | 2.11% |
| adlittle | 27,408 | 17,168 | 37.36% | 1,157,912 | 1,148,712 | 0.79% |
| kb2 | 18,128 | 10,672 | 41.13% | 944,280 | 938,008 | 0.66% |
| sc50a | 14,640 | 9,136 | 37.60% | 506,304 | 500,880 | 1.07% |
| flugpl | 6,144 | 3,952 | 35.68% | 229,608 | 228,328 | 0.56% |

| Model | Full presolve before | Full presolve after | Reduction |
| --- | ---: | ---: | ---: |
| afiro | 1,189,592 | 1,186,840 | 0.23% |
| adlittle | 4,907,096 | 4,897,704 | 0.19% |
| kb2 | 13,200,064 | 13,194,432 | 0.04% |
| sc50a | 4,328,912 | 4,325,344 | 0.08% |
| flugpl | 1,515,264 | 1,514,208 | 0.07% |

Whole solves with presolve enabled allocated 0.04–0.23% fewer bytes. The unchanged
paths with presolve disabled varied by -112 to +32 bytes with identical
allocation counts. Those small fluctuations are not attributed to this change;
isolated result construction gives the clearest evidence of eliminated copies.

All 15 result snapshots (five fixtures × bounds-only/propagation/full presolve)
matched exactly: CSC arrays, objective and constant, objective sense, bounds,
domains, model/row/column names, and original column count. All 20 whole-solve
combinations (five fixtures, primal/dual, presolve on/off) remained `OPTIMAL`;
status, objective, complete primal vector, and iteration count matched baseline
snapshots exactly with `isequal`.

Machine-readable results are in
[`row-result-allocations-before.toml`](row-result-allocations-before.toml) and
[`row-result-allocations-after.toml`](row-result-allocations-after.toml).

## Reproduction

The existing audit covers propagation, full presolve, and whole solves:

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=propagate_row_bounds --output=row-result-audit.toml
```

For isolated result construction, run from the repository root with the same
Julia flags:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex
using JSimplex.SparseArrays

problem = LinearProblem(sparse(ones(128, 128)), ones(128))
rows = collect(axes(problem.A, 1))
lower = copy(problem.column_lower)
lower[1] = Bound(1.0)
println(measure_allocations(
    _ -> JSimplex._row_result(problem, rows; column_lower=lower); samples=3))
```

## Regression coverage

The allocation budget failed before the change at 544,816 bytes against a
350,000-byte limit and now passes at 276,048 bytes. The padded-CSC test also
caught the initial optimization's constructor error before the fallback guard
was added.

The 193 new checks cover independent model and bound arrays, source preservation
after result mutation, stored zeros, reordered and reduced row selections,
postsolve mapping, named and unnamed rows, empty dimensions, identity returns,
and inactive CSC storage. Numeric coverage includes Float32, Float64, BigFloat,
and Rational{BigInt}; stored BigFloat precision is preserved under a lower ambient
precision.

Independent review found no remaining issue. Its 480 differential cases across
six numeric types matched the baseline exactly, covering full, permuted, reduced,
and empty row selections, names, padded CSC storage, postsolve maps, and output
ownership.

The complete mandatory suite passed **15,976/15,976** tests, including the 193
new checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
