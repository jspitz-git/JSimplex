# Separate simplex numerical implementations from progress heuristics

## Scope

The fixed (`:legacy`) strategy no longer defers an otherwise numerically valid
weak primal pivot to search for a stronger candidate. That bounded preference
is controlled by `adaptive_pricing`. Invalid directions and pivots still use the
same numerical rejection, correction, and bounded retry safeguards.

Both public strategies now select the native numerical kernel. Choosing
`:adaptive` only supplies defaults for progress monitoring, pricing preferences,
perturbations, partial pricing, and refactorization scheduling. The internal
`NumericalPolicy(T; numerical_profile=:checked)` preset explicitly selects the
previous combined set of alternative numerical stages. Individual numerical
flags remain overridable. No public option or precision escalation was added;
the policy field layout remains unchanged for stored-state compatibility.

Native residual, pivot, point-preservation, row-value, and working-price guards
are eligible under either strategy. Update preparation is requested by solve
role, rather than by the strategy label. Primal ratio and bound-snap checks use
per-bound feasibility consistently.

Perturbation cleanup remains mandatory after restoring costs or bounds and for
resumed owned journals, even after heuristic flags are disabled. The cleanup
driver verifies the restored state and selects an appropriate simplex phase
without enabling another numerical implementation. Phase options follow the
actual method through its verification; the caller's options are restored on
exit. A focused regression reproduces a lost tolerated row activity when dual
options incorrectly remain active during primal cleanup.

## Verification

Julia 1.13.0, aarch64, one Julia thread and one BLAS thread. Every numerical run
uses the existing wrapper under
`/home/jspitz/JSimplex.jl/.worktrees/primal-direction-prices/.superpowers/primal-prices/`:
`julia.sh` limits virtual memory to 8 GiB and `guard.py` terminates only its owned
process group below 6 GiB available RAM or above 1 GiB used swap. Local
`precompile_workload = false`, manifests, preferences, and old worktrees are
preserved.

- The initial policy regression failed in all 28 strategy/numerical comparisons.
  The weak-pivot regression then distinguished a valid zero pivot in the fixed
  strategy from the deferred candidate in the adaptive strategy.
- The phase-option regression failed for both strategies before the fix and
  passed after it. It verifies the original point and restoration of options.
- `reproduce/semantic.jl`: 19,244 checks passed with `--compile=min` (349.6 s).
  This covers native guards, both strategies, checked numerical stages,
  perturbation/phase cleanup, budgets, callback provenance, postsolve, all basis
  managers, and small NetLib/MIPLib regressions.
- `reproduce/transfer-replay.jl`: 1,838 checks passed with `--compile=min` (12.4 s).
  This includes explicit checkpoint coverage, precision transfer, stored-policy
  replay, disabled-heuristic journal resumption, and the native zero-row shortcut.
  These groups include some repeated separation assertions.

The historical numerical-stage tests now request their checked implementation
explicitly. Public adaptive solves and native safeguards retain separate test
coverage. A read-only independent review covered numerical/heuristic gating,
cleanup ownership, phase options, and migration of test assumptions.

This is targeted and semantic verification, not a complete project-suite run.
Results from bounded real-model runs are recorded separately below. A time limit
without numerical failure does not establish convergence of `runtime.mps`.

## External models

`reproduce/external.jl` completed 56 solves with normal compilation (264.5 s
including first-call compilation; 172 assertions). Every solve reached the
reference objective and passed original-model primal feasibility certification:

- `afiro`, `adlittle`, and `flugpl`: both algorithms, both strategies, all four
  basis managers (48 solves).
- `fast0507`: both algorithms, fixed strategy, all four basis managers (8 solves).

Inputs and reference objectives come from the existing selective-preparation
manifest. Each input hash is checked before use. The report records strategy,
algorithm, manager, endpoint, reference objective, certificate, and source hashes.
No claim is made about adaptive `fast0507` from this matrix.

The broad semantic log precedes six final assertions added to the separation and
phase-transfer tests; the final transfer/replay run covers those additions.
Production source is unchanged between these successful runs and the external
model run. This avoids repeating the entire broad suite solely for test additions.

## Bounded runtime validation

The existing `primal-phase1-stagnation/reproduce/certify-runtime.jl` runner used
PFI, primal simplex, fixed strategy, steepest-edge pricing, native factorization,
interval 80, relaxed integrality, and a 300-second solver limit. The recorded
input SHA-256 matches the user-supplied runtime model.

- `TIME_LIMIT`, 10,479 iterations, 3,652 refactorizations, 45,907 rejected pivots.
- All 59,968 pre-pricing point checks passed, including fresh-factor retries.
  The final stored point also passed the phase-primal and row-consistency checks.
- Only phase I ran. The auxiliary objective stagnated at 605524.5146092784.
  These certificates concern the working phase-I problem, not feasibility of
  the original LP. This run does not solve `runtime.mps`.
- Certification consumed 182.54 of 300.00 solver seconds. This is a correctness
  diagnostic, not a throughput comparison with earlier uninstrumented runs.

The local terminal snapshot is retained at
`.superpowers/strategy-separation/runtime-pfi.terminal.bin`; it is not committed.
The report's source revision is the pre-commit base `3a996c8`; the recorded source
hashes identify the tested implementation. No medium convergence claim follows
from the small dual regressions in this change.

## Reproduction

From the worktree, run each command sequentially through the existing guarded
Julia wrapper. Use `--compile=min` for the first two and normal compilation for
the model runs:

```sh
julia --project=. --compile=min diagnostics/simplex-strategy-separation/reproduce/semantic.jl
julia --project=. --compile=min diagnostics/simplex-strategy-separation/reproduce/transfer-replay.jl
julia --project=. diagnostics/simplex-strategy-separation/reproduce/external.jl FRESH_OUTPUT.toml
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/certify-runtime.jl /home/jspitz/mps/runtime.mps pfi 300 FRESH_PREFIX
```

The observed guard allowances were 480, 420, 600, and 660 wall-clock seconds,
respectively, to include compilation and serialization outside solver budgets.
Keep output paths fresh and local binary snapshots outside version control.
