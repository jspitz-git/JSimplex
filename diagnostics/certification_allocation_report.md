# Allocation audit: optimality certification

This ninth round removes temporary concatenated vectors from original-objective
optimality certification. All preceding allocation changes remain in both
measurements. Measurements use Julia 1.13.0 on aarch64-linux-gnu with one Julia
thread, PFI updates, and native refactorization. Each entry is the minimum of
three warmed calls; no compilation was observed in the measured calls. These
are cumulative Julia heap allocations, not peak memory.

## Findings and changes

The candidate dual witness previously required concatenating the complete
original cost vector with zero slack costs, then gathering its basic entries.
The implementation now prepares only the basic cost vector. Structural costs
still come from the original problem, independently of shifted workspace costs.
Invalid basic indices retain bounds checking.

Reduced-cost interval arrays are now allocated at their final size. The existing
interval loop fills every structural entry, and the dual vector is copied into
the slack entries directly. This removes two temporary zero vectors while
retaining independent output arrays and stored BigFloat precision.

Complementarity checks now read structural values and computed row-activity
intervals directly, removing two more concatenated vectors. Arithmetic order,
interval operations, tolerances, and certification conditions are unchanged.

## Results

Isolated probes with 1,024 structural variables, unit costs, and no constraints:

| Operation | Before (B) | After (B) | Fewer bytes |
|---|---:|---:|---:|
| Original optimality certification | 58,008 | 16,656 | 71.3% |
| Original reduced-cost intervals | 33,088 | 16,560 | 50.0% |

Whole solves without presolve:

| Model | Dual before (B) | Dual after (B) | Fewer bytes | Primal before (B) | Primal after (B) | Fewer bytes |
|---|---:|---:|---:|---:|---:|---:|
| afiro | 95,088 | 92,592 | 2.62% | 132,384 | 127,104 | 3.99% |
| adlittle | 474,104 | 468,072 | 1.27% | 632,624 | 619,824 | 2.02% |
| kb2 | 885,488 | 881,568 | 0.44% | 266,848 | 263,296 | 1.33% |
| sc50a | 314,624 | 310,672 | 1.26% | 239,016 | 235,048 | 1.66% |
| flugpl | 46,288 | 44,560 | 3.73% | 100,944 | 96,784 | 4.12% |

With presolve enabled, whole-solve savings were 0.03–0.27%. Certification is a
small part of total solve allocations, so the isolated probe's larger reduction
does not describe the improvement of a complete solve.

All 20 combinations (five models, primal/dual, presolve on/off) remained
`OPTIMAL`. Status, objective, complete primal vector, and iteration count matched
serialized pre-change snapshots exactly using `isequal`.

Machine-readable measurements are in
[`certification-allocations-before.toml`](certification-allocations-before.toml)
and [`certification-allocations-after.toml`](certification-allocations-after.toml).
Timings overlapped other validation, so no runtime-speedup claim is made.

## Reproduction

The existing audit covers whole solves:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=solve_dual_no_presolve --output=certification-audit.toml
```

To reproduce the isolated probes, run in Julia with `--project=dev` from the
repository root:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, 0, 1024), ones(1024))
workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
primal = zeros(1024)
measure_allocations(_ -> JSimplex._original_optimality_certified(workspace, primal); samples=3)
measure_allocations(_ -> JSimplex._original_reduced_cost_bounds(problem, Float64[]); samples=3)
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and inputs for comparisons.

## Regression coverage

Both warmed allocation budgets failed before the change: certification allocated
58,008 bytes against a 25,000-byte limit, and reduced-cost bounds allocated
33,056 bytes against a 20,000-byte limit. Both budgets pass after the change.

The 61 new checks cover independent interval arrays, empty dimensions, mixed
structural/slack bases, original costs despite workspace shifts, invalid basic
indices, lower/upper row-bound complementarity, and retention of stored 512-bit
BigFloat slack values at ambient precision 64 bits. Numerical cases run with
Float32, Float64, BigFloat, and Rational{BigInt}. Existing cancellation and tight
tolerance certification regressions remain part of the mandatory suite.

Independent review found no issue for valid internal inputs. Its 72 differential
certification decisions matched across six numeric types, structural bases, and
shifted workspace costs. Reduced-cost intervals and a BigFloat cancellation
case also matched, including stored precision at ambient precision 64 bits.

The complete mandatory suite passed **14,700/14,700** tests, including the 61 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
