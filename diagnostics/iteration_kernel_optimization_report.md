# Remove temporary allocations from repeated iteration kernels

This change implements three priorities from the [iteration audit](iteration_allocation_report.md).
It changes PFI update construction, the primal ratio test, and bound-flipping ratio
scratch. Presolve and factorization algorithms are unchanged.

## Changes

- PFI allocates its two packed arrays at their final capacity, then fills them
  with the existing pivot-first ordering. Previously each array was allocated as
  a singleton and immediately grown. The arrays remain owned by the update;
  mixed-type columns retain their single conversion pass.
- The primal ratio test tracks whether a step/relaxed limit exists with Boolean
  flags. Numeric accumulators stay concrete instead of alternating between a
  number and `nothing`. The function still returns `nothing` for an unbounded
  or inconclusive step, and retains Harris selection, strict fallback, bounds,
  tie handling and feasibility checks.
- Bound-flipping ratio tests borrow a workspace-owned flips vector. Each test
  clears it, including fallback after accumulating a partial proposal. Capacity
  grows on demand and remains reusable. The returned vector is valid until the
  next bound-flipping test on that workspace. Existing callers consume it before
  another test or abandon it when retrying/terminating. Refinement success replaces
  the pending proposal; refinement failure terminates without applying it.

The scratch change adds one empty vector per workspace; larger flip lists grow
only when needed. This trades a small initialization/retained-storage cost for
removing repeated temporary vectors. It is not shared between workspaces.

## Measured results

The same deterministic-replay audit was rerun with three samples, two warmups,
Float64, native factorization, presolve off and scaling off, on Julia 1.13.0,
aarch64-linux-gnu, one Julia thread. All compared metadata, preparation statuses,
completed-step counts and iteration statuses agree with the baseline.
Compilation time is zero in every measured row. Timing overlapped validation;
no runtime speedup is claimed.

Whole PFI iterations after five requested steps, with steepest-edge pricing:

| Fixture | Algorithm | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| afiro | dual | 7 → 4 | 416 → 320 |
| afiro | primal | 11 → 4 | 448 → 288 |
| adlittle | dual | 7 → 4 | 288 → 192 |
| adlittle | primal | 11 → 4 | 768 → 608 |
| kb2 | dual | 7 → 4 | 416 → 320 |
| kb2 | primal | 11 → 4 | 576 → 416 |
| sc50a | dual | 7 → 4 | 288 → 160 |
| sc50a | primal | 11 → 4 | 480 → 320 |
| flugpl | dual | 8 → 4 | 336 → 192 |

Primal flugpl has already reached optimality before that snapshot and is omitted.
All nine remaining five-step PFI states now allocate only the four allocations
for the two owned packed-update arrays. Dual iteration counts decrease by
42.9–50%; primal counts decrease by 63.6%. This is a per-iteration result on these
states, not a claim about every iteration or total solver memory.

Across all 20 PFI snapshots, the standalone primal ratio test decreases from
3 allocations / 64 bytes to **zero** wherever applicable. Bound-flipping ratio
tests decrease from 1 / 32 (flugpl after five steps: 2 / 80) to **zero**.
Same-type multi-entry PFI updates save two allocations; singleton updates already
needed no buffer growth. Initial iterations may still grow the update history or
initialize pricing. Existing zero-allocation solve/recompute/pricing kernels
remain at zero.

The all-method survey covers 48 adlittle snapshots (four basis methods × three
pricing choices × two algorithms × two preparation depths). Every whole-iteration
row improves; all ratio-test rows become allocation-free. The triangular methods
retain their own update allocations, while benefiting from the shared ratio fixes.

Steepest-edge whole iterations after five steps:

| Method | Algorithm | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| pfi | dual | 7 → 4 | 288 → 192 |
| pfi | primal | 11 → 4 | 768 → 608 |
| forrest_tomlin | dual | 11 → 10 | 736 → 704 |
| forrest_tomlin | primal | 13 → 8 | 640 → 544 |
| suhl_suhl | dual | 11 → 10 | 736 → 704 |
| suhl_suhl | primal | 13 → 8 | 608 → 512 |
| bartels_golub | dual | 8 → 7 | 480 → 448 |
| bartels_golub | primal | 14 → 9 | 1,136 → 1,040 |

Across the two surveys, **67 whole-iteration measurements improve** and no kernel
allocation count regresses among 711 compared rows. Preparation/iteration statuses
and step counts are unchanged. Refactorization and basis-assembly allocation counts
are unchanged; small byte variation on these unchanged native-library paths is
not included in the claimed savings.

## Remaining allocations

Refactorization is unchanged: it still allocates the CSC basis and new factors.
Reusing native LU storage safely requires investigating sparsity changes,
failure handling and actual refactorization frequency. This change makes no
claim that the remaining factor storage is avoidable. Triangular update storage
and initial steepest-edge cache setup also remain separate follow-up work.

The four allocations in an ordinary PFI pivot store the two arrays owned by the
new eta update. Eliminating those would require a different storage/lifetime
scheme; they cannot simply borrow the next iteration's scratch arrays.

## Validation and reproduction

The initial allocation regression run failed seven checks as intended: PFI used
6 allocations instead of at most 4, and the ratio probes allocated 96, 80 and
32 bytes instead of zero. All checks passed after the changes. Additional tests
cover Float32/Float64/BigFloat/fixed- and arbitrary-width rationals, mixed-type
PFI inputs, update ownership and solve residuals, unbounded/boxed/tied primal
steps, exhausted flip lists and overflow fallback after a partial flip proposal.
The tests are registered in `test/runtests.jl`.

Validation completed:

- 78 new regression assertions pass; the targeted factorization/primal/dual run
  passes 2,323 assertions including those new checks.
- All 194,992 production-suite assertions pass across two runs. The original
  full invocation passed 194,331 assertions, then stopped at the first MOI import
  because `MathOptInterface` is not a direct dependency of the dev environment.
  Adding the repository project to `LOAD_PATH` made the installed dependency
  visible; all five remaining MOI test files then passed 661 assertions. No
  production assertion failed, and no dependencies or project files were changed.
- The audit-tool regression suite passes 282 assertions.
- Independent code review found no blocking numerical, ownership or lifetime
  issues. Refinement-specific flips lifetime was checked by control-flow review;
  direct tests cover retries, exhaustion and partial-list fallback.
- `git diff --check` passes.

The full-suite reproduction below includes the corrected import path.

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'push!(LOAD_PATH, pwd()); include("test/runtests.jl")'
julia --startup-file=no --compiled-modules=existing --project=dev dev/tests/iteration_allocation_tests.jl
julia --startup-file=no --compiled-modules=existing --project=dev dev/iteration_allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile --output=diagnostics/iteration-kernels-optimized-pfi.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/iteration_allocations.jl adlittle --basis-update=all --pricing=all --samples=3 --profile --output=diagnostics/iteration-kernels-optimized-backends.toml
```

Raw before/after results: [PFI before](iteration-kernels-pfi.toml),
[PFI after](iteration-kernels-optimized-pfi.toml),
[basis methods before](iteration-kernels-backends.toml),
[basis methods after](iteration-kernels-optimized-backends.toml).
As in the audit, runtime allocation counters and separate profiler samples need
not match; byte variation in unchanged library paths is not counted as a saving.
