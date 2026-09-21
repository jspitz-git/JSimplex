# Allocation audit: result vectors and postsolve

This eighth round removes duplicate result-vector copies. All preceding
allocation changes remain in both measurements. Measurements use Julia 1.13.0
on aarch64-linux-gnu with one Julia thread, PFI updates, and native refactorization.
Each entry is the minimum of three warmed calls, with no compilation observed
in any measured call. These are cumulative Julia heap allocations, not peak
memory.

## Findings and changes

Three internal paths copied a freshly allocated vector slice: optimal result
construction, recession classification, and primal phase-I certification. The
slice already owns its storage, so the outer `copy` was redundant and is removed.

Postsolve also sliced the final reconstructed vector even when its length already
matched the original column count. Conversion and the built-in postsolve steps
produce fresh dense vectors. The function now returns that vector directly when
its type and length match; it retains the existing slice for truncation and other
vector representations. Feasibility and optimality certification are unchanged.

## Results

Isolated probes with 1,024 structural variables and no constraints:

| Operation | Before (B) | After (B) | Fewer bytes |
|---|---:|---:|---:|
| Identity postsolve | 16,528 | 8,264 | 50.0% |
| Internal optimal result, including certification | 75,832 | 67,600 | 10.9% |

Postsolve on each fixture's prepared presolve result and reduced primal solution:

| Model | Before (B) | After (B) | Fewer bytes |
|---|---:|---:|---:|
| afiro | 2,592 | 2,272 | 12.3% |
| adlittle | 6,784 | 5,936 | 12.5% |
| kb2 | 1,760 | 1,360 | 22.7% |
| sc50a | 3,008 | 2,528 | 16.0% |
| flugpl | 1,216 | 1,008 | 17.1% |

Presolve and solving the reduced model are outside these postsolve measurements.
This stage reconstructs the primal vector; it does not include original-space
cleanup or certification performed later by a complete solve.

Whole solves without presolve:

| Model | Dual before (B) | Dual after (B) | Fewer bytes | Primal before (B) | Primal after (B) | Fewer bytes |
|---|---:|---:|---:|---:|---:|---:|
| afiro | 95,696 | 95,136 | 0.59% | 133,280 | 132,464 | 0.61% |
| adlittle | 476,104 | 474,504 | 0.34% | 635,120 | 632,640 | 0.39% |
| kb2 | 885,888 | 885,184 | 0.08% | 267,584 | 266,848 | 0.28% |
| sc50a | 315,552 | 314,560 | 0.31% | 239,944 | 239,000 | 0.39% |
| flugpl | 46,672 | 46,288 | 0.82% | 101,664 | 100,944 | 0.71% |

With presolve enabled, whole-solve savings were 0.01–0.07%. Result vectors are a
small part of total solve allocations, so their larger relative savings do not
translate into comparable whole-solve reductions.

All 20 combinations (five models, primal/dual, presolve on/off) remained `OPTIMAL`.
Status, objective, complete primal vector, and iteration count matched serialized
pre-change snapshots exactly using `isequal`.

Machine-readable measurements are in
[`result-allocations-before.toml`](result-allocations-before.toml) and
[`result-allocations-after.toml`](result-allocations-after.toml). Timings overlapped
other validation, so no runtime-speedup claim is made.

## Reproduction

The existing audit covers primal reconstruction and whole solves:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=postsolve --output=result-audit.toml
```

To reproduce the isolated probes, run in Julia with `--project=dev` from the
repository root:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, 0, 1024), zeros(1024))
presolved = JSimplex.identity_presolve(problem)
primal = zeros(1024)
workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
measure_allocations(_ -> JSimplex.postsolve_primal(presolved, primal); samples=3)
measure_allocations(_ -> JSimplex._internal_solution(workspace, OPTIMAL, "optimal"); samples=3)
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and inputs for comparisons.

## Regression coverage

Both warmed allocation budgets failed on the pre-change implementation: identity
postsolve allocated 16,528 bytes against a 10,000-byte limit, and internal result
construction allocated 75,752 bytes against a 71,000-byte limit.

Tests cover independent result storage for dense, integer, range, view, and sparse
inputs; truncation and too-short input errors; chained reductions; and independence
between returned primal values and mutable workspace state. These checks run with
Float32, Float64, BigFloat, and Rational{BigInt}.

Independent review found no blocker for supported usage. Its 480 comparisons
matched result types, values, and errors, including empty inputs and truncation.
A separate BigFloat check preserved stored 512-bit values at ambient precision
64 bits. The ownership assumption applies to the built-in reconstruction steps;
a custom private step returning shared cached storage would now expose that
storage. Such internal extensions are outside the supported public API.

The complete mandatory suite passed **14,639/14,639** tests, including the new
126 allocation, ownership, reconstruction, and input-shape checks. The two
previously documented JET development-suite failures remain outside this round's
scope; the full optional development suite was not rerun.
