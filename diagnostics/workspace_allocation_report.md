# Allocation audit: workspace initialization

This seventh round removes temporary copies during simplex workspace
initialization. All preceding allocation changes remain in both measurements.
Measurements use Julia 1.13.0 on aarch64-linux-gnu with one Julia thread, PFI
updates, and native refactorization. Each entry is the minimum of three warmed
calls, with no compilation observed in any measured call. These are cumulative
Julia heap allocations, not peak memory.

## Findings and changes

Initialization copied objective and bound vectors before concatenating them,
even though concatenation already allocates independent result storage. It also
materialized the initial basis indices before passing them to the copying
`Basis` constructor.

- The cost vector is allocated once at its final size. Stored objective values
  are copied into its first part and the slack costs are filled with zero.
- Lower and upper bounds are concatenated directly from the model arrays,
  eliminating four intermediate copies while retaining private workspace arrays.
- The `Basis` constructor receives the slack-index range directly, avoiding a
  temporary collected vector. Its resulting index storage remains `Vector{Int}`.

The objective coefficients and bounds retain their scalar values and precision.
Variable states, basis order, workspace ownership, and initial recomputation are
unchanged. Auxiliary workspace construction is outside this round's changes.

## Results

Complete Float64 workspace initialization on the five solver fixtures:

| Model | Before (B) | After (B) | Fewer bytes | Before allocations | After allocations |
|---|---:|---:|---:|---:|---:|
| afiro | 34,080 | 31,056 | 8.9% | 170 | 156 |
| adlittle | 66,880 | 59,568 | 10.9% | 172 | 158 |
| kb2 | 48,576 | 44,320 | 8.8% | 170 | 156 |
| sc50a | 55,120 | 50,128 | 9.1% | 170 | 156 |
| flugpl | 24,704 | 22,608 | 8.5% | 170 | 156 |

A separate comparison against the original initializer covers four scalar types
on a 32-row, 32-column identity model and the larger `greenbea` input:

| Input / type | Before (B) | After (B) |
|---|---:|---:|
| Identity / Float32 | 16,168 | 14,184 |
| Identity / Float64 | 38,368 | 35,072 |
| Identity / BigFloat | 2,799,384 | 2,796,120 |
| Identity / Rational{BigInt} | 8,384,704 | 8,381,536 |
| greenbea / Float64 | 2,628,744 | 2,297,104 |

`greenbea` has 2,392 rows and 5,405 columns; initialization allocates 12.6% fewer
bytes. This probe does not solve it. The typed identity probes include native
factorization and initial recomputation, whose arbitrary-precision arithmetic
dominates allocations for BigFloat and Rational{BigInt}.

Whole solves without presolve:

| Model | Dual before (B) | Dual after (B) | Fewer bytes | Primal before (B) | Primal after (B) | Fewer bytes |
|---|---:|---:|---:|---:|---:|---:|
| afiro | 98,768 | 95,840 | 3.0% | 139,488 | 133,392 | 4.4% |
| adlittle | 483,368 | 476,344 | 1.5% | 650,656 | 635,312 | 2.4% |
| kb2 | 890,272 | 886,112 | 0.5% | 271,888 | 267,600 | 1.6% |
| sc50a | 320,896 | 315,888 | 1.6% | 244,936 | 239,912 | 2.1% |
| flugpl | 48,768 | 46,672 | 4.3% | 106,256 | 101,664 | 4.3% |

With presolve enabled, whole-solve savings were 0.06–0.47%. All 20 combinations
(five models, primal/dual, presolve on/off) remained `OPTIMAL`. Status, objective,
complete primal vector, and iteration count matched serialized pre-change
snapshots exactly using `isequal`.

Machine-readable measurements are in
[`workspace-allocations-before.toml`](workspace-allocations-before.toml),
[`workspace-allocations-after.toml`](workspace-allocations-after.toml), and
[`workspace-initialization-shapes.toml`](workspace-initialization-shapes.toml).
The shape probe invokes the original and current initializers in the same process
and compares their costs, bounds, basis, primal values, reduced costs, pricing
weights, and Devex references. Timings overlapped other validation, so no
runtime-speedup claim is made.

## Reproduction

The existing audit covers initialization and whole solves:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=initialize --output=workspace-audit.toml
```

To isolate initialization, including `greenbea`, run in Julia with `--project=dev`
from the repository root:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

problem = read_mps("dev/fixtures/greenbea.mps")
options = SolverOptions(verbose=false)
measure_allocations(_ -> JSimplex.initialize_workspace(problem, options); samples=3)
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and inputs for comparisons.

## Regression coverage

The warmed `adlittle` initialization budget failed on the pre-change implementation
at 67,088 bytes against a 63,000-byte limit. Semantic tests cover owned objective
and bound arrays, expected variable states and basis indices, zero rows/columns,
and preservation of stored 512-bit BigFloat objective values at ambient precision
64 bits.

Independent review found no issue. Its 48 workspace comparisons across six
numeric types matched the original initializer exactly, including scratch arrays
and counters as well as costs, bounds, basis, primal values, and reduced costs.

The complete mandatory suite passed **14,513/14,513** tests, including the new
99 allocation, ownership, empty-dimension, and precision checks. The two
previously documented JET development-suite failures remain outside this round's
scope; the full optional development suite was not rerun.
