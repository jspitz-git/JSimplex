# Allocation audit: owned basis arrays

This sixteenth round extends internal ownership transfer to initial workspace
bases and basis restoration through presolve maps. All preceding allocation
changes remain in both measurements. Measurements use Julia 1.13.0 on
aarch64-linux-gnu with one Julia thread, PFI updates, and native refactorization.
Each entry is the minimum of three warmed calls; no compilation was observed in
measured calls. These are cumulative Julia heap allocations, not peak memory.

## Findings and changes

Workspace initialization already creates its variable-state vector locally.
It now constructs the slack-index vector explicitly and transfers both arrays
to `Basis(..., Val(:owned))`, removing the redundant state-vector copy.

`restore_basis(::PresolveMap, ::Basis)` also creates its result arrays locally.
It now builds slack indices directly from the shifted range, eliminating the
temporary unshifted index vector, and transfers the final indices and states
without copying them again.

Both call sites supply newly allocated private arrays. Input bases and presolve
maps remain unchanged, and subsequent restoration steps may still mutate their
independent result. Ordinary `Basis` construction and identity restoration retain
their copying behavior. Index mapping and numerical calculations are unchanged.

## Results

Isolated Float64 probes:

| Operation | Before (B) | After (B) | Fewer bytes |
|---|---:|---:|---:|
| Initialize 8,192 columns with no rows | 873,896 | 865,632 | 0.95% |
| Restore one identity map with 1,024 columns and 1,024 rows | 29,064 | 10,416 | 64.16% |

Fixture measurements:

| Model | Initialize before (B) | Initialize after (B) | Fewer bytes | Restore before (B) | Restore after (B) | Fewer bytes |
|---|---:|---:|---:|---:|---:|---:|
| afiro | 31,008 | 30,864 | 0.46% | 8,736 | 4,432 | 49.27% |
| adlittle | 59,568 | 59,344 | 0.38% | 14,560 | 7,440 | 48.90% |
| kb2 | 44,304 | 44,160 | 0.33% | 5,776 | 2,944 | 49.03% |
| sc50a | 50,128 | 49,968 | 0.32% | 11,616 | 5,536 | 52.34% |
| flugpl | 22,608 | 22,512 | 0.42% | 3,408 | 1,456 | 57.28% |

Initialization uses the original fixture model. Restoration applies the complete
presolve stack to an initial basis prepared on the reduced model; presolve and
workspace initialization are outside that measurement. It measures basis
reconstruction, without solving or original-space cleanup.

Whole-solve byte reductions ranged from 0.005–0.225% without presolve and
0.011–0.303% with presolve. Whole-solve totals include variation outside these
small changes; isolated measurements provide the clearest evidence of the
removed copies.

All five reconstructed fixture bases matched serialized pre-change indices and
states exactly. All 20 solve combinations (five models, primal/dual, presolve
on/off) remained `OPTIMAL`; status, objective, complete primal vector, and
iteration count matched pre-change snapshots exactly with `isequal`.

Machine-readable measurements are in
[`owned-bases-allocations-before.toml`](owned-bases-allocations-before.toml) and
[`owned-bases-allocations-after.toml`](owned-bases-allocations-after.toml).
Timings overlapped other validation, so no runtime-speedup claim is made.

## Reproduction

The existing audit covers initialization and whole solves:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=initialize --output=owned-bases-audit.toml
```

To reproduce isolated fixture-stage measurements, run from the repository root
with `--project=dev`:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

problem = read_mps("test/fixtures/solver/afiro.mps")
options = SolverOptions(verbose=false)
measure_allocations(_ -> JSimplex.initialize_workspace(problem, options); samples=3)

presolved = JSimplex.presolve_problem(problem)
reduced = JSimplex.initialize_workspace(presolved.problem, options)
measure_allocations(_ -> JSimplex.restore_basis(presolved, reduced.basis); samples=3)
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and inputs for comparisons.

## Regression coverage

Both budgets failed before the change: initialization allocated 873,896 bytes
against an 869,000-byte limit, and single-map restoration allocated 29,032 bytes
against a 12,000-byte limit. Both pass after the change.

The 102 new checks cover independent initial workspaces, structural and slack
index mapping, removed rows and columns, chained presolve maps, unchanged input
bases and maps, identity copying, and empty dimensions. Numeric coverage includes
Float32, Float64, BigFloat, and Rational{BigInt}.

Independent review found no issue. Its 120 random-map comparisons matched the
original mapping and confirmed isolation of later mutations. Review also
verified that singleton, propagation, equality, and doubleton restoration steps
continue to mutate only their independent results.

The complete mandatory suite passed **15,604/15,604** tests, including the 102
new checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
