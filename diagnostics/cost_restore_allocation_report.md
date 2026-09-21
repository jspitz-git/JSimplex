# Allocation audit: restoring original costs

This eleventh round removes temporary vectors when restoring original costs
after dual optimization and after primal phase I. All preceding allocation
changes remain in both measurements. Measurements use Julia 1.13.0 on
aarch64-linux-gnu with one Julia thread, PFI updates, and native refactorization.
Each entry is the minimum of three warmed calls; no compilation was observed in
measured calls. These are cumulative Julia heap allocations, not peak memory.

## Findings and changes

Both cleanup paths previously concatenated the original objective and a fresh
zero vector, then copied that temporary vector into `workspace.costs`. They now
call `_restore_original_costs!`, which copies the objective directly into the
existing workspace array and fills its row-activity tail with zeros.

After primal phase I, the workspace problem includes artificial columns. The
helper uses that problem's column count and objective, including the artificial
costs that the caller has already reset to zero. It preserves the existing cost
array, original coefficients, and unrelated workspace state. It introduces no
coefficient arithmetic or conversion.

## Results

Isolated cost restoration on prepared Float64 workspaces, with workspace
construction and resetting shifted costs outside measurement:

| Rows | Structural columns | Before (B) | After (B) |
|---:|---:|---:|---:|
| 1 | 1,024 | 8,392 | 0 |
| 1,024 | 1 | 16,592 | 0 |
| 0 | 0 | 64 | 0 |

These zero-allocation results apply to the measured Float64 helper. Other
numeric types can still allocate when constructing their zero value.

Paired whole dual solves without presolve:

| Model | Before (B) | After (B) | Measured reduction |
|---|---:|---:|---:|
| afiro | 92,592 | 91,792 | 0.86% |
| adlittle | 468,504 | 465,896 | 0.56% |
| kb2 | 881,984 | 880,752 | 0.14% |
| sc50a | 310,240 | 308,912 | 0.43% |
| flugpl | 44,560 | 43,984 | 1.29% |

The measured allocation count fell by four in every listed solve. For primal
solves without presolve, it fell by four on afiro, adlittle, and flugpl; it was
unchanged on kb2 and sc50a. The latter paths skip the phase-I cost restoration,
so small byte differences there are not evidence of improvement from this change.

Whole-solve byte totals include variation outside the changed helper. Separate
processes initially showed differences larger than this small cleanup's savings,
so the saved measurements use paired before/after runs on the same problem
objects in one process. The shared helper was replaced in memory with the old
concatenation expression or final in-place body before warming each measurement.
Both versions used the same call sites; method replacement and warmup were
outside measurement.

Even in paired measurements, whole solves with presolve ranged from a 0.017%
increase to a 0.066% decrease in bytes, although allocation counts fell by four
or eight. These small total-byte differences should not be interpreted as a
reliable presolve improvement or regression. The isolated helper measurements
provide the clearest evidence of the removed temporary vectors.

All 20 combinations (five models, primal/dual, presolve on/off) remained
`OPTIMAL`. Status, objective, complete primal vector, and iteration count matched
exactly using `isequal`, both in separate-process comparisons against serialized
pre-change snapshots and in paired comparisons.

Machine-readable paired measurements are in
[`cost-restore-allocations-before.toml`](cost-restore-allocations-before.toml)
and [`cost-restore-allocations-after.toml`](cost-restore-allocations-after.toml).
Timings overlapped other validation, so no runtime-speedup claim is made.

## Reproduction

The existing audit covers the affected whole-solve paths:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=solve_dual_no_presolve --output=cost-restore-audit.toml
```

To compare the isolated old expression and current helper in one process, run
from the repository root with `--project=dev`:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

function old_restore!(workspace)
    workspace.costs .= vcat(workspace.problem.objective,
                            zeros(eltype(workspace.costs), size(workspace.problem.A, 1)))
    return nothing
end

problem = LinearProblem(JSimplex.SparseArrays.spzeros(Float64, 1, 1024), ones(1024))
workspace = JSimplex.initialize_workspace(problem, SolverOptions(verbose=false))
prepare = () -> (fill!(workspace.costs, 99.0); workspace)
measure_allocations(old_restore!; setup=prepare, samples=3)
measure_allocations(JSimplex._restore_original_costs!; setup=prepare, samples=3)
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and inputs for comparisons.

## Regression coverage

The allocation regression test failed with the old expression extracted into
the shared helper: 8,392 bytes against a zero-allocation requirement. It passes
with the in-place implementation.

The 130 new checks cover reuse of the cost array, unchanged objective and
unrelated workspace arrays, restoration after objective changes, empty
dimensions, artificial columns, signed zeros, and stored 512-bit BigFloat
coefficients at ambient precision 64 bits. Numeric coverage includes Float32,
Float64, BigFloat, and Rational{BigInt}.

Independent review found no issue. Its 30 differential workspace comparisons
across six numeric types and empty dimensions matched the old expression while
retaining the destination array and source objective.

The complete mandatory suite passed **14,932/14,932** tests, including the 130
new checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
