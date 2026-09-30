# Native recovery during Phase-I export

This integrates the bounded candidate from
[the local row reconstruction experiment](phase-transfer-local-rows.md).
The implementation preserves the mapped primal point before refactorizing the
fresh original-dimension workspace. If its basis reconstruction is unreliable,
it tries one native correction and at most eight local reconstruction sweeps.
The independent, full-system residual checks and original primal-feasibility
checks still decide acceptance. No tolerance is relaxed.

## Scope and ownership

The path is limited to primal Float32/Float64 workspaces satisfying the existing
legacy primal row-validation predicate. Checked/refined/staged policies and dual
exports retain their existing paths. A zero refinement budget forbids recovery.
It changes no adaptive pricing or perturbation policy.

Each local coordinate update is finite and bounded by
`solve_tolerance * maximum(abs, native_correction)`. This is a per-update bound,
not an accumulated movement bound or convergence guarantee. A known portable
cycle remains rejected after eight sweeps. Tiny nonzero right-hand sides are
retained explicitly in the reconstructed equations.

Local iterations use private vectors. The tentative full primal point is checked
under rollback protection; cancellation, a failed certificate or an exception
restores the basic values before returning. Dual values and reduced costs are
published only after acceptance. The outer export owns a fresh workspace and
still runs its original checks before adopting it.

## Verification

The captured production export initially failed its regression assertion before
the implementation. With the implementation it passes 19 assertions, including
unchanged basis residual and point certificates, effective steepest-edge pricing,
and rejection/rollback controls for disabled budgets, incompatible policies,
dual mode, cancellation, exceptions and failed primal certificates.

The portable tests cover both hardware precisions and all four basis managers,
preservation of maintained nonbasic values, tiny right-hand sides, cycle and
zero-cutoff rejection, cancellation after a private update and unavailable
compensated arithmetic. They are included in the standard project test runner.
The combined semantic runner passes **8,163 assertions** with `--compile=min`.

The normal-compilation whole-project suite is incomplete: its 300-second guard
expired in LLVM while compiling `native_cleanup_recovery_tests.jl`. This is not
a passing whole-project result.

## Reproduction

Use the existing memory guard and run numerical processes sequentially, with
one Julia thread and one BLAS thread. Local snapshots require the recorded
Julia environment; they are not portable outer-driver restart points.

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_transfer_recovery_replay.jl .superpowers/adaptive-degeneracy/phase-transfer/runtime-transfer-capture /tmp/phase-transfer-replay
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/phase_transfer_recovery_semantics.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_transfer_recovery_runtime.jl runtime primal both 1800 /tmp/runtime-phase-recovery
```

The fresh runtime harness uses the same isolated policy as the prior capture:
adaptive stalling, temporary pricing and perturbations enabled; other adaptive
features disabled. Weak-pivot preference and the original-LP retry are disabled
by the same diagnostic overrides. Production phase export is not overridden.
A detached final observed workspace is saved only after the solve returns; it
supports local diagnosis, not an exact restart of the outer driver.

The final observation timestamp includes writing the detached snapshot; use the
report's `seconds` field for solver elapsed time. Neither this timestamp nor
wall time including compilation is a controlled speed benchmark.

## Fresh runtime result and requested extension

The fresh solve reproduces all **136 nonfinal records** from the earlier capture.
At iteration **102,446** production export succeeds, phase pricing resets to
`steepest_edge`, and Phase II starts with cost **61,547,897.97008232**.
The solver continues to **124,750 iterations**, **35,006 refactorizations**, and
**1,800.002 seconds**, returning `TIME_LIMIT`. The final observed workspace has
cost **51,479,818.85253397** and zero reported primal infeasibility. That observation
is not a terminal certificate or an original-input optimality claim.

The user requested continuing to completion near this endpoint. A separate
diagnostic continuation loads the detached final workspace, rebuilds presolve
and scaling from the original MPS, and checks every working-model, scaling and
numerical-policy field against the snapshot. It requires the original costs and
bounds, no active perturbations, finite state and a certified stored primal point.
It retains the stored basis matrix, PFI updates, weights and adaptive numerical
history. Julia serializes UMFPACK input arrays and controls rather than its native
numeric/symbolic objects, so the base factorization is reconstructed lazily. The
clock/budget and process-local ownership/context identities are rebound. The standard outer postsolve and original-input certificate remain.
This is an explicitly reconstructed continuation, not an uninterrupted fresh
solve or an exact restoration of the outer driver's history.

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_transfer_recovery_continue.jl runtime primal both 3600 /tmp/runtime-phase-continuation /tmp/runtime-phase-recovery-final.bin
```

The continuation passes its entry checks, advances **4,123 iterations** (4,113
pivots and ten flips), and terminates after **268.789 seconds** at iteration
**128,873**, with **39,055 cumulative refactorizations**. Its status is
`NUMERICAL_ERROR`, reason **`primal pivot is below the zero tolerance`**.
The final observed cost is **51,425,691.78019489**, about **0.018092** above the
previously certified dual objective 51,425,691.762103125. The observed primal
infeasibility is zero, but 47 reduced costs remain infeasible and no original-input
optimum is certified. Near equality of the objective is not a substitute for the
missing terminal certificate.

During this continuation there are 106,542 rejected candidates, 4,049 pivot
refactorizations and one failed certification. The terminal branch rejects a
below-threshold pivot even after the native basis refresh. This localizes the
next investigation to the recorded Phase-II candidate/direction and ratio test;
it does not establish why that pivot was selected. The exact final workspace
is retained for diagnosis. No extra guard, tolerance change or heuristic fallback
is promoted to address this new endpoint.

Two setup-only continuation attempts failed before any pivot: assigning an
observer-bearing context into the detached workspace type, then using an
unregistered diagnostic event. The final wrapper reconstructs only the workspace
container and calls its observer directly. Their error logs are retained locally;
neither attempt contributes iterations or solve measurements above.

Final regression coverage also includes **1,172 normal-compilation structural
and allocation assertions**, and **80 external solves / 245 assertions** across
five permitted inputs, primal/dual algorithms, four basis managers and native/
Markowitz factorization. Every external solve returns the reference optimum and
passes original-model primal feasibility. These focused suites do not turn the
incomplete whole-project run into a full-suite pass.

Text evidence and hashes are in
[results/phase-transfer-recovery](results/phase-transfer-recovery/). Large binary
snapshots and exact as-run scripts remain under
`.superpowers/adaptive-degeneracy/phase-transfer-recovery/`, recorded in the local
artifact manifest. Production SHA-256 throughout both runtime runs is
`4ec571a4c968dca505cee5c193411bc3b55a73ab8dbf82a168887fc8b6dc4957`.
