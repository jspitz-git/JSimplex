# Capture the restored-basis verification failure

Run this in a **fresh Julia process**, from the supplied source directory (the directory containing `Project.toml`). No Git checkout is needed. Install dependencies once with `julia --project=. -e 'using Pkg; Pkg.instantiate()'` if needed. Use the Julia version and environment of the failing solve; the Intel report used Julia 1.13.3.

PowerShell example:

```powershell
julia --startup-file=no --compiled-modules=existing --project=. diagnostics/runtime-primal-regression/capture_basis_failure.jl C:/disk_d_dmp/runtime-capture.handoff.bin C:/disk_d_dmp/basis-failure 600
```

The examples retain Julia’s default optimization/debug settings to match the original Intel run. Local ARM validation used `-O1 -g0` and one Julia/BLAS thread, recorded in its environment report.

The last argument is the replay budget in seconds (default 600). Compilation counts against it. Choose a fresh output prefix for each run. The script does not change BLAS or Julia thread settings, solver tolerances, arithmetic precision, or algorithm settings. It intentionally invokes original-model cleanup **without** `target_primal` to exercise the historical restored-basis fallback, even when the source includes the postsolve projection repair.

The diagnostic clones the installed `_verify_driver_basis!` body after checking its complete parsed source shape, then wraps its result. It stops after the first false verification, before subsequent recovery retries. It also captures an exception from verification and rethrows that original exception. Outside this fresh process, nothing is patched.

Outputs:

- `.environment.toml`: Julia/CPU/BLAS/thread configuration, dependency versions, source hashes, and input hash. Git revision is optional; hashes work in an extracted ZIP.
- `.basis-failure.bin`: the exact published state after failed verification, including problem, basis, primal, working costs/bounds, dual prices (`rho`), reduced costs, active Huangfu–Hall factorization/update chain, numerical policy, and recovery/refactorization metadata. Written and closed before residual analysis, via a `.partial` file renamed on completion.
- `.basis-failure.toml`: separate primal and transpose solve quality, unchanged reliability decisions, residual/scale information for the ten largest componentwise errors, iteration and factorization counts, and failure reason.
- `.run.toml`: whether a failure was captured, the solver result if none was captured, exceptions, and elapsed time including compilation and diagnostic work.
- `.analysis-error.toml` only if residual reporting fails after the binary snapshot was saved.

A `.bin.partial` file is incomplete; it is never announced as a completed snapshot. Retain and send all completed outputs together. Exit code 0 means a failed verification was captured, **not** that optimization succeeded. Exit code 2 means no verification failure was captured; exit code 3 means verification stopped at the time budget, which is not evidence of a numerical failure. Unexpected exceptions retain a nonzero Julia exit and original stack trace.

For a residual-only comparison on another compatible Julia/JSimplex installation:

```powershell
julia --startup-file=no --compiled-modules=existing --project=. diagnostics/runtime-primal-regression/replay_basis_failure.jl C:/disk_d_dmp/basis-failure.basis-failure.bin C:/disk_d_dmp/basis-replay
```

This writes `.replay.toml` and `.replay-environment.toml`. It checks the saved equations without refactorizing or advancing the solver. Compare source hashes and environments: a different architecture may make different floating-point decisions. Julia Serialization is not a universal interchange format; use matching source/type definitions and compatible Julia versions on 64-bit systems. This script requires `basis_update=:huangfu_hall` and `basis_refactorization=:native`, matching the Intel handoff. Exact active extracted L/U arrays and the update chain are retained. Disposable backend refactorization scratch is omitted (its type is recorded), because it can contain UMFPACK pointers even under `:native`; no backend pointers need to travel between processes.

The captured state is **after** verification. Native cleanup computes candidate corrections privately; a rejected private candidate is not published and is not the saved primal/dual vector. The diagnostic reports the published vectors' quality; it does not claim to identify which private correction stage rejected a trial. For an exception, the saved state can be partially recomputed. Descriptive residual/scale ratios do not replace the solver's roundoff-aware acceptance test.

All extra matrix assembly, residual scans, sorting, serialization, and retained snapshot memory are diagnostic work performed after failure. Before failure, the wrapper adds a function call and a Boolean branch per driver verification; it adds no basis solves, full-vector copies, or per-pivot work. Do not use instrumented timings as production performance measurements.

Standalone diagnostic tests (not part of `test/runtests.jl`):

```text
julia --startup-file=no --compiled-modules=existing --project=. diagnostics/runtime-primal-regression/test_basis_failure.jl
```
