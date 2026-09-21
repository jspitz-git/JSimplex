# Allocation audit: original-basis restoration

This fifteenth round removes temporary copies when restoring a basis after
primal phase I. All preceding allocation changes remain in both measurements.
Measurements use Julia 1.13.0 on aarch64-linux-gnu with one Julia thread, PFI
updates, and native refactorization. Each entry is the minimum of three warmed
calls; no compilation was observed in measured calls. These are cumulative
Julia heap allocations, not peak memory.

## Findings and changes

`_primal_original_basis` previously copied two slices of variable states,
concatenated them, and passed the combined states and freshly computed indices
to the copying `Basis` constructor.

The helper now copies structural and row-activity states directly into one
final vector. It transfers that vector and its freshly allocated index vector
to an internal `Basis(..., Val(:owned))` constructor without another copy.
This constructor has one call site, which supplies two private local arrays.
The normal two-argument constructor retains its input-copying behavior, as does
the restoration branch with no artificial variables.

Index mapping and the collision check are unchanged. Returned bases remain
independent of the workspace and of results from other calls. A collision still
returns `nothing` without modifying the input basis.

## Results

Isolated restoration from prepared Float64 phase-I workspaces:

| Original columns | Rows / artificial columns | Before (B) | After (B) | Fewer bytes |
|---:|---:|---:|---:|---:|
| 1,024 | 1,024 | 23,040 | 10,416 | 54.8% |
| 1,024 | 1 | 3,584 | 1,216 | 66.1% |
| 0 | 0 | 96 | 96 | 0.0% |

Restoration from each fixture's prepared initial phase-I workspace, with setup
outside measurement:

| Model | Before (B) | After (B) | Fewer bytes |
|---|---:|---:|---:|
| afiro | 1,024 | 432 | 57.81% |
| adlittle | 1,808 | 784 | 56.64% |
| kb2 | 576 | 576 | 0.00% |
| sc50a | 672 | 672 | 0.00% |
| flugpl | 800 | 336 | 58.00% |

The kb2 and sc50a preparations have no artificial variables and use the
unchanged copying branch. These isolated measurements cover structural basis
remapping; they do not include solving phase I.

Whole primal solves without presolve on fixtures requiring artificial variables:

| Model | Before (B) | After (B) | Measured reduction |
|---|---:|---:|---:|
| afiro | 123,728 | 123,184 | 0.44% |
| adlittle | 611,808 | 611,008 | 0.13% |
| flugpl | 93,088 | 92,624 | 0.50% |

With presolve enabled, measured whole-primal-solve savings were 0.01–0.10%.
Whole-solve totals include variation outside this small change; the isolated
restoration measurements show its direct effect most clearly. No benefit is
attributed to paths that skip restoration after artificial variables.

All 20 solve combinations (five models, primal/dual, presolve on/off) remained
`OPTIMAL`. Status, objective, complete primal vector, and iteration count matched
serialized pre-change snapshots exactly using `isequal`.

Machine-readable measurements are in
[`basis-restore-allocations-before.toml`](basis-restore-allocations-before.toml)
and [`basis-restore-allocations-after.toml`](basis-restore-allocations-after.toml).
Timings overlapped other validation, so no runtime-speedup claim is made.

## Reproduction

The existing audit covers whole solves:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=solve_primal_no_presolve --output=basis-restore-audit.toml
```

To reproduce isolated restoration, run from the repository root with
`--project=dev`:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

problem = read_mps("test/fixtures/solver/afiro.mps")
options = SolverOptions(algorithm=:primal, verbose=false)
workspace, count, _ = JSimplex._primal_phase_one(
    problem, options, JSimplex.SimplexProgressContext(problem), () -> false)
measure_allocations(_ -> JSimplex._primal_original_basis(workspace, size(problem.A, 2), count);
                    samples=3)
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and inputs for comparisons.

## Regression coverage

The allocation budget failed before the change: 23,040 bytes against a
12,000-byte limit. It passes after the change.

The 71 new checks cover structural/artificial/slack index mapping, collision
rejection without mutation, independent result storage, the ordinary
constructor's copying behavior, and empty original columns and rows. Numeric
coverage includes Float32, Float64, BigFloat, and Rational{BigInt}.

Independent review found no issue. Its differential checks matched results and
ownership for 120 random bases, including 26 collision returns and empty
dimensions. It confirmed that the sole ownership-transfer call site supplies
freshly allocated arrays.

The complete mandatory suite passed **15,502/15,502** tests, including the 71
new checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
