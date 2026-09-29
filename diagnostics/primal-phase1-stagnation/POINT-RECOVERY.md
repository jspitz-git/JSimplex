# Terminate or repair a failed primal-point reconstruction

Base revision: `33922c7cda384a3b970942a855913c2ac7103d5e`.

## Defect and bounded recovery

The legacy primal path already detected a reconstructed point that violated
bounds or stored equations, and tried to preserve the predicted pivot point.
When that prediction also failed certification, `_restore_legacy_primal_point!`
restored the bad reconstruction and returned `false`. All three production
callers ignored the return value. A bound-feasible but equation-inconsistent
point could therefore reach another pricing call.

The new completion helper distinguishes a usable point from a terminal failure.
After the existing predicted-point fallback fails, it tries exactly one native
correction. It computes the compensated residual of the complete stored point,
`row_activity - A * structural_primal`, including nonbasic contributions. An
ordinary basis FTRAN solves for a correction to basic values. Reusing the rounded
reconstruction RHS would miss the equation error being repaired.

The trial must pass finiteness, every variable bound, original-model feasibility,
and consistency between structural values and stored row activities. Only then
are the basic values and `row_solution` retained. A failed trial, cancellation,
or exception during trial validation restores the reconstructed values.
Correction arithmetic remains Float32 or Float64; the existing equation
certificate can use its exact-input fallback when its native enclosure is
inconclusive. There is no iterative precision increase or repeated correction.

If neither preservation nor correction succeeds, the iteration returns
`NUMERICAL_ERROR`; cancellation returns `TIME_LIMIT`. The failure clears the
candidate-retry marker so a fresh-factor retry cannot send the invalid point
back to pricing. This applies after a completed step, a rejected-candidate
refactorization, and the small-pivot refactorization branch.

The existing fast reconstruction check and its handling of an unavailable native
probe are unchanged. This patch closes the ignored-failure path after that check
has detected a bad point; it does not strengthen every equation probe into an
exact certificate. The existing policy/type exclusions are unchanged, including
adaptive and staged paths.

## Small reproductions

`test/legacy_primal_point_recovery_tests.jl` exercises Float32 and Float64 with
PFI, Forrest–Tomlin, Suhl–Suhl and Bartels–Golub. A two-row fixture introduces a
small factor error in an unchanged basis column. Its BTRAN check still passes,
but the large row activity amplifies the error enough that both reconstruction
and prediction violate the equations. Before the fix, the initial 80-assertion
regression has 56 passes and 24 failures. The repaired iteration needs one
correction and no refactorization.

A separate `3x = 1` fixture uses a primal tolerance of `eps(T)^2`. No binary
floating value of `x` can satisfy that equation within the configured tolerance.
It must terminate instead of pricing again. The same failure is exercised through
both refactorization branches. Additional tests cancel before FTRAN and cancel
or throw after a certified trial has been applied, checking rollback of primal
values and preservation of `row_solution`.

The complete new test file has 360 assertions. The successful correction has a
separate `primal_point_corrected` diagnostic event, alongside the existing
`correction_attempt` and `correction` events.

## Certified runtime verification

The four runs use the original Float64 legacy-primal configuration with native
factorization, steepest-edge pricing, refactorization interval 80, relaxed
integrality, and a 300-second solver limit. Julia 1.13.0 runs on aarch64 with one
Julia and BLAS thread. The existing guard limits virtual memory to 8 GiB and
stops only its own process group below 6 GiB available RAM or above 1 GiB swap.
Processes run sequentially. The input SHA-256 is
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`.

| Manager | Iterations | Refactorizations | Rejections | Certified pricing points | Auxiliary objective |
| --- | ---: | ---: | ---: | ---: | ---: |
| PFI | 12,154 | 1,266 | 32,815 | 46,112 | 605519.5025306537 |
| Forrest–Tomlin | 6,505 | 1,664 | 40,808 | 48,922 | 605524.4037304183 |
| Suhl–Suhl | 6,544 | 901 | 34,137 | 41,524 | 605524.4037491891 |
| Bartels–Golub | 5,286 | 1,600 | 48,125 | 54,970 | 605524.4037554335 |

All 191,528 points presented to pricing, including retries, pass the independent
certificate. All four terminal points also pass. Every run ends in `TIME_LIMIT`
with one phase-I workspace, no reported numerical failure, and no original-model
restart. None finishes phase I. Certificate time is included in the solver
deadline, so these iteration counts are not a throughput comparison.

The new `primal_point_corrected` count is zero in all four runs. They check for
regressions on runtime; they do not exercise the new correction branch or show
that it resolves the existing plateau. The small reproductions above establish
the repair and termination behavior when both earlier point choices fail.

Text reports and test logs are in [results/point-recovery](results/point-recovery/).
Reports were produced before committing the fix: `source_revision` records the
base HEAD, while `source_sha256` identifies the tested modified source. The
validation metadata also records hashes of the local terminal snapshots under
`.superpowers/point-recovery/`. The existing bound-snap obstruction remains
separate from this error-path fix.

## Regression verification

The focused runner passes 2,122 assertions, including the new 360-assertion file;
the broader semantic runner passes 2,698, both with `--compile=min`. Normal
compilation passes 125 native-residual checks (including allocations) and repeats
all 360 new assertions successfully. All 80 external LP relaxations pass the
reference-optimum and original-feasibility checks (245 assertions). This is 5,190
assertions without counting the repeated new tests, not a full project-suite run.

An initial combined command mistakenly ran allocation assertions with
`--compile=min`, producing four allocation failures. The separate normal build
passes those checks; the corrected semantic invocation also exits successfully.
No production change was made in response to those four mode-dependent failures.

Read-only code review found no blocking issue. Its requested tests for late
cancellation/exception rollback and both fresh-factor failure paths were added
before final validation. The correction buffers and residual sign were also
reviewed.

## Reproduction

Use the existing time/memory guard and Julia wrapper, one numerical process at
a time. Preserve local `precompile_workload = false`.

```sh
julia --compile=min --project=. diagnostics/primal-phase1-stagnation/reproduce/focused-core.jl
julia --compile=min --project=. diagnostics/primal-runtime-stability/reproduce/regressions.jl
julia --project=. -e 'using JSimplex, Test; include("test/native_residual_tests.jl"); include("test/legacy_primal_point_recovery_tests.jl")'
julia --project=. diagnostics/basis-selective-preparation/reproduce/external.jl diagnostics/basis-selective-preparation/reproduce/external-inputs.toml OUTPUT.toml
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/certify-runtime.jl /home/jspitz/mps/runtime.mps pfi 300 OUTPUT_PREFIX
```

Repeat the last command sequentially for the other three managers with fresh
output prefixes. Binary snapshots remain local. Text reports record source and
input hashes; the external runner's original hash list covers factorization
sources, so the accompanying validation metadata also records the primal sources.
