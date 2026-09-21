# Allocation audit: primal phase-I matrix construction

This thirteenth round removes the intermediate artificial-variable matrix from
primal phase-I setup. All preceding allocation changes remain in both
measurements. Measurements use Julia 1.13.0 on aarch64-linux-gnu with one Julia
thread, PFI updates, and native refactorization. Each entry is the minimum of
three warmed calls; no compilation was observed in measured calls. These are
cumulative Julia heap allocations, not peak memory.

## Findings and changes

Phase I previously constructed a sparse matrix of artificial columns from
triplets and then concatenated it with the original constraint matrix. Each
artificial column contains exactly one entry whose row and sign are already
known.

`_primal_phase_one_matrix` now allocates the three final CSC arrays directly.
It copies the original active entries and column pointers, then appends the
singleton columns. The returned matrix owns all its arrays. `nnz(A)` determines
how much input storage is active, so unused trailing capacity is not copied as
matrix entries. Explicitly stored zeros remain intact.

The private helper relies on the valid row/sign pairs selected by its phase-I
caller. It performs no coefficient arithmetic or conversion. Artificial-column
order, model construction, basis selection, and optimization logic are unchanged.

## Results

Isolated Float64 matrix construction with an identity original matrix and
positive unit artificial-column entries:

| Original dimension | Artificial columns | Before (B) | After (B) | Fewer bytes |
|---:|---:|---:|---:|---:|
| 1,024 | 1,024 | 132,632 | 49,528 | 62.7% |
| 1,024 | 3 | 42,616 | 25,080 | 41.1% |
| 0 | 0 | 720 | 224 | 68.9% |

Complete phase-I setup on original fixture models, including initialization and
refactorization:

| Model | Before (B) | After (B) | Fewer bytes |
|---|---:|---:|---:|
| afiro | 90,336 | 88,848 | 1.65% |
| adlittle | 181,088 | 178,464 | 1.45% |
| kb2 | 43,200 | 43,200 | 0.00% |
| sc50a | 48,784 | 48,784 | 0.00% |
| flugpl | 69,104 | 67,296 | 2.62% |

The kb2 and sc50a setups need no artificial columns and return the initial
workspace without calling the new helper.

Whole primal solves without presolve on the fixtures requiring artificial columns:

| Model | Before (B) | After (B) | Measured reduction |
|---|---:|---:|---:|
| afiro | 125,712 | 124,320 | 1.11% |
| adlittle | 615,888 | 613,488 | 0.39% |
| flugpl | 95,728 | 93,920 | 1.89% |

Whole primal solves with presolve ranged from a 0.05% increase to a 0.07%
decrease in bytes. Whole-solve totals include variation outside this small
change; these tiny differences are not a reliable indication of improvement or
regression. The isolated matrix and complete phase-I setup measurements show
the direct effect more clearly. No benefit is attributed to paths that skip
artificial-column construction.

All 20 solve combinations (five models, primal/dual, presolve on/off) remained
`OPTIMAL`. Status, objective, complete primal vector, and iteration count matched
serialized pre-change snapshots exactly using `isequal`.

Machine-readable measurements are in
[`phase-matrix-allocations-before.toml`](phase-matrix-allocations-before.toml) and
[`phase-matrix-allocations-after.toml`](phase-matrix-allocations-after.toml).
Timings overlapped other validation, so no runtime-speedup claim is made.

## Reproduction

The existing audit covers whole solves:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=solve_primal_no_presolve --output=phase-matrix-audit.toml
```

To reproduce isolated matrix and phase-I setup probes, run from the repository
root with `--project=dev`:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

A = JSimplex.SparseArrays.spdiagm(0 => ones(1024))
rows, signs = collect(1:1024), ones(1024)
measure_allocations(_ -> JSimplex._primal_phase_one_matrix(A, rows, signs); samples=3)

problem = read_mps("test/fixtures/solver/afiro.mps")
options = SolverOptions(algorithm=:primal, verbose=false)
progress = JSimplex.SimplexProgressContext(problem)
measure_allocations(_ -> JSimplex._primal_phase_one(problem, options, progress, () -> false);
                    samples=3)
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and inputs for comparisons.

## Regression coverage

The allocation budget failed with the old construction extracted into the shared
helper: 132,536 bytes against a 55,000-byte limit. The final implementation passes.

The 199 new checks cover CSC layout and ordering, explicit zeros, independent
result storage, empty dimensions, unused trailing CSC storage, and retained
512-bit BigFloat coefficients at ambient precision 64 bits. Numeric coverage
includes Float32, Float64, BigFloat, and Rational{BigInt}.

Independent review found no issue. Its 120 differential cases across six numeric
types, including empty dimensions and unused trailing CSC storage, matched the
original construction exactly. BigFloat values and precisions also matched.

The complete mandatory suite passed **15,222/15,222** tests, including the 199
new checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
