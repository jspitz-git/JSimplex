# Allocation audit: primal phase-I costs and bounds

This fourteenth round removes temporary vectors when preparing primal phase-I
costs and column bounds. All preceding allocation changes remain in both
measurements. Measurements use Julia 1.13.0 on aarch64-linux-gnu with one Julia
thread, PFI updates, and native refactorization. Each entry is the minimum of
three warmed calls; no compilation was observed in measured calls. These are
cumulative Julia heap allocations, not peak memory.

## Findings and changes

Phase I previously concatenated zero and unit cost vectors and appended freshly
filled artificial-variable bounds to the original column bounds. The new
`_primal_phase_one_vectors` helper allocates only the three final arrays.

It fills structural costs with zero and artificial costs with one. It copies the
original column bounds into the result prefixes and fills the artificial tails
with lower bound zero and unbounded upper bounds. Copies retain the exact stored
values, including BigFloat precision. New numeric constants use the same current
precision as before.

The result arrays remain independent of each other and the original model.
The existing model constructor still performs its copies and validation.
Artificial-variable selection and optimization logic are unchanged.

## Results

Isolated preparation of the three Float64 vectors:

| Structural columns | Artificial columns | Before (B) | After (B) | Fewer bytes |
|---:|---:|---:|---:|---:|
| 1,024 | 1,024 | 131,768 | 82,328 | 37.5% |
| 1,024 | 3 | 50,112 | 41,544 | 17.1% |
| 0 | 0 | 400 | 272 | 32.0% |

Complete phase-I setup on original fixture models, including initialization and
refactorization:

| Model | Before (B) | After (B) | Fewer bytes |
|---|---:|---:|---:|
| afiro | 88,912 | 88,272 | 0.72% |
| adlittle | 178,416 | 177,152 | 0.71% |
| kb2 | 43,216 | 43,216 | 0.00% |
| sc50a | 48,784 | 48,784 | 0.00% |
| flugpl | 67,296 | 66,464 | 1.24% |

The kb2 and sc50a setups return their initial workspaces without artificial
variables and do not call the helper.

Whole primal solves without presolve on the fixtures requiring artificial columns:

| Model | Before (B) | After (B) | Measured reduction |
|---|---:|---:|---:|
| afiro | 124,272 | 123,728 | 0.44% |
| adlittle | 613,664 | 612,272 | 0.23% |
| flugpl | 93,920 | 93,088 | 0.89% |

Whole primal solves with presolve ranged from a 0.14% increase to a 0.01%
decrease in bytes. Whole-solve totals include variation outside this small
change; these differences are not reliable evidence of a presolve improvement
or regression. Isolated vector construction and phase-I setup provide the
clearest evidence of the removed temporary arrays. No benefit is attributed to
paths that skip this construction.

All 20 solve combinations (five models, primal/dual, presolve on/off) remained
`OPTIMAL`. Status, objective, complete primal vector, and iteration count matched
serialized pre-change snapshots exactly using `isequal`.

Machine-readable measurements are in
[`phase-vectors-allocations-before.toml`](phase-vectors-allocations-before.toml)
and [`phase-vectors-allocations-after.toml`](phase-vectors-allocations-after.toml).
Timings overlapped other validation, so no runtime-speedup claim is made.

## Reproduction

The existing audit covers whole solves:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=solve_primal_no_presolve --output=phase-vectors-audit.toml
```

To reproduce isolated vector and phase-I setup probes, run from the repository
root with `--project=dev`:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, 1024, 1024), ones(1024))
measure_allocations(_ -> JSimplex._primal_phase_one_vectors(problem, 1024); samples=3)

problem = read_mps("test/fixtures/solver/afiro.mps")
options = SolverOptions(algorithm=:primal, verbose=false)
progress = JSimplex.SimplexProgressContext(problem)
measure_allocations(_ -> JSimplex._primal_phase_one(problem, options, progress, () -> false);
                    samples=3)
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and inputs for comparisons.

## Regression coverage

The allocation budget failed with the original concatenation expressions
extracted into the helper: 131,576 bytes against a 90,000-byte limit. The final
implementation passes.

The 209 new checks cover exact costs and bounds, independent arrays, empty
dimensions, unchanged input models, and stored 512-bit BigFloat bounds at
ambient precision 64 bits. Numeric coverage includes Float32, Float64,
BigFloat, and Rational{BigInt}.

Independent review found no issue for inputs supplied by the phase-I caller.
Its 96 differential cases across six numeric types matched values, bound
representations including signed zeros, and independent result storage.

The complete mandatory suite passed **15,431/15,431** tests, including the 209
new checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
