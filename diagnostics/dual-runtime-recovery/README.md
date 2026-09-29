# Native dual cleanup on runtime.mps

Base: `339fbdb`. The phase-start logging change remains on its separate branch.
This correction belongs to the numerical core, independently of the strategy.

## Reproduced failure

Input `/home/jspitz/mps/runtime.mps`, SHA-256
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`.
Float64, dual simplex, legacy strategy, steepest-edge, PFI, native factorization,
interval 80, relaxed integrality, default presolve and scaling. The iteration
limit is 1,000,000; the diagnostic solver limit is 660 seconds.

The supplied log stops on the reduced problem at iteration 62,558 with zero
reported primal and dual infeasibility. Our fresh baseline reaches the same
failure mechanism at iteration 61,630. It returns `bounded feasibility recovery
exhausted`; the original-LP retry also fails, at 67,268 cumulative iterations.
The iteration sequences are not identical to the supplied run.

The saved first failure has original working bounds, but shifted working costs.
These shifts come from numerical dual-price repairs, not adaptive stagnation
perturbations. Mandatory cleanup must verify the point and restore the original
objective before returning an optimum. Repeating a native factorization does
not repair the failed verification:

| Basis equation | Absolute residual | Componentwise relative residual |
| --- | ---: | ---: |
| Primal, ordinary recomputation | 7.919607487088303e-10 | 1.0 |
| Dual, ordinary recomputation | 5.186057865064153e-10 | 1.5841580151470558e-13 |
| Primal, native correction and verified zero cleanup | 1.3942453678546228e-10 | 9.241582244092725e-17 |
| Dual, one native correction | 1.6940848039746032e-10 | 9.438915741377121e-17 |

The relative primal error is dominated by homogeneous equations with tiny
nonzero rounding artifacts. An ordinary correction can reduce those artifacts
from roughly 1e-16 to 1e-32 while leaving their relative error at one. This is
consistent with zero reported bound violations: bound feasibility and basis
backward error are different checks. The stored point passes original working
primal feasibility, but the original-objective optimality certificate fails
before cost cleanup. It must not be accepted merely because the progress log
shows zero infeasibility.

## Correction

After ordinary cleanup verification fails, the Float32/Float64 native kernel
tries one compensated-residual correction for each basis solve. Primal values,
dual values, and the corresponding reduced costs remain private until both
solves pass the unchanged componentwise residual test and cancellation has
been checked. Accepted values invalidate the affected pricing and scratch
caches. Costs, bounds, basis, pricing rule, and iteration count are unchanged.

A proposed homogeneous zero cleanup uses the existing numerical solve tolerance
scaled by the correction norm. Scaling by the full solution norm was tested and
rejected: it also removed legitimate small values in this snapshot. Every
proposed cleanup must pass the complete original residual test. A small nonzero
right-hand side is not treated as zero. Unsafe native residual evaluation,
nonfinite candidates, failed correction, disabled correction budget, or
cancellation cannot publish a partial correction.

This path does not change ordinary iterations, enable the checked numerical
profile, widen arithmetic, relax tolerances, or add progress heuristics. The
separately selected checked refinement path retains its behavior. Existing
original-model primal and optimality certification remain mandatory.

## Validation

- Five-row native-LU regression: 24 assertions fail before the correction;
  all 88 pass afterward across both strategies and all four basis managers.
- Targeted numerical/phase recovery regressions: 2,133 checks pass with
  `--compile=min`, including private failed/interrupted corrections and tiny
  nonzero right-hand sides.
- Captured-state continuation: `OPTIMAL` after 7 additional pivots (61,637 total),
  original working costs and bounds active, primal and optimality certificates
  both pass. Objective: `5.14256917621031e7` in the saved working model.
  This continuation alone does not validate original-input postsolve recovery.
- Fresh original-input run: `OPTIMAL`, 62,853 iterations, 196.49 solver seconds,
  objective `5.1425691762103125e7`, and a successful original-input primal
  certificate. No original-LP restart or numerical-error termination occurs.
  The reduced problem finishes after 7 cleanup pivots; postsolve cleanup adds
  1,216 further pivots on the reconstructed original problem. Before the failing
  verification boundary, the baseline and fixed runs follow the same trajectory.
  One bounded feasibility-recovery event remains; it now succeeds.
- Normal compilation: 277 focused/native-residual checks pass, including
  allocation bounds and the added nonzero-dual/publication regressions.
- External corpus: 56 optimal solutions and 172 passing checks. Afiro, adlittle,
  and flugpl cover both algorithms, both strategies, and all four managers;
  fast0507 covers both algorithms and all managers with the fixed strategy.
  All results match reference objectives and pass original-input primal
  certification. The external run takes 243.0 seconds including compilation.
- `reproduce/check-results.py` independently verifies the recorded baseline,
  fixed whole solve, snapshot continuation, and external endpoints. Production
  source is unchanged between these successful runs.

These are targeted checks and bounded original-model runs, not a full
project-suite pass.

## Reproduction and resources

Run each numerical process sequentially through the existing guarded wrapper
in `.worktrees/primal-direction-prices/.superpowers/primal-prices/` of the main
checkout. Julia 1.13.0, aarch64, one Julia thread, one BLAS thread, 8 GiB virtual
memory ceiling, 6 GiB available-RAM floor, 1 GiB swap ceiling. Preserve local
`precompile_workload = false` and untracked environment files.

```sh
julia --project=. diagnostics/dual-runtime-recovery/reproduce/capture.jl /home/jspitz/mps/runtime.mps 660 FRESH_PREFIX
julia --project=. diagnostics/dual-runtime-recovery/reproduce/inspect.jl SNAPSHOT.bin
julia --project=. diagnostics/dual-runtime-recovery/reproduce/replay.jl SNAPSHOT.bin 180 FRESH_OUTPUT.toml
julia --project=. --compile=min diagnostics/dual-runtime-recovery/reproduce/regressions.jl
julia --project=. diagnostics/dual-runtime-recovery/reproduce/normal-and-external.jl FRESH_EXTERNAL.toml
python3 diagnostics/dual-runtime-recovery/reproduce/check-results.py
```

Capture records source hashes and saves limited snapshots at failure/cleanup
boundaries. Binary snapshots stay local under `.superpowers/dual-runtime-recovery/`.
Use a log filename such as `PREFIX-run.log`, not `PREFIX.log`, so it does not
collide with the snapshot prefix freshness check. The guard allowance for a
full run was 840 seconds, including compilation outside the solver budget.

Timing includes diagnostic work and rare-path compilation. It is not a speedup
comparison with the user-provided log. A read-only independent review found no
blocking issue; its recommendation to test corrected nonzero dual values and
all corresponding reduced prices was incorporated into the focused tests.
