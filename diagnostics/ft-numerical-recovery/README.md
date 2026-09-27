# Forrest–Tomlin failure on a second machine

**The reported failure has not been reproduced in either diagnostic run and is
not fixed by this change.** This work records the evidence and provides a bounded capture of the
missing numerical state. Solver source, tolerances, precision policy and the
adaptive strategy are unchanged.

## Reported failure

The user confirmed commit `e1b15678e86f6d1cf3b2343827bf6d4e25f6e54b`, before the
separate BG stable-row optimization `c7125f7`. The working configuration is
runtime.mps, legacy dual, steepest-edge pricing, native refactorization and
interval 80. The user confirmed that the second machine runs native Windows,
not WSL. The subsequent capture confirms Julia 1.13.0 and x86_64; it did
not reproduce the originally reported termination.

At iteration 45537, reported primal infeasibility is about 5.4e4. At 45617 it
jumps to 1.32e14 and dual infeasibility becomes 3.27. The reduced solve terminates
with `dual feasibility lost`; solving the original LP starts again. The supplied
excerpt shows failure of the reduced solve, not the final outcome of that retry.
It does not identify whether the cause is factor updates, an accepted unstable
exchange, or a recomputation with the fresh factor.

## Local evidence

The unchanged e1b1567 source was loaded from the existing precompile-workloads
worktree to reuse its cache. The capture driver runs outside that source tree.
Julia 1.13.0 / Linux aarch64, one Julia and BLAS thread, 24 GiB virtual-memory
ceiling, one numerical job at a time. No editor processes were signaled.

- The baseline factor tests passed 19,895 assertions.
- The complete FT run reached OPTIMAL in **611.665 seconds**, with **62,939
  iterations**, **790 refactorizations** and objective **51,425,691.76210457**.
  The original primal-feasibility certificate passed. There was no numerical
  termination or restart of the original LP.
- The objective, iteration count, input hash and all diagnostic event counts
  exactly match the prior successful 99ba627 run recorded in
  `diagnostics/triangular-update-kernels/results/prepared-ft-full.toml`.
  Different profiling/host conditions mean their wall times are not a speedup
  measurement.
- There were 4,777 native correction attempts, 4,770 successful corrections and
  one residual-triggered refactorization, at iteration 35375. Ordinary refactor
  intervals remained useful; this was not a refactorization-per-iteration loop.
- Seven snapshots were inspected: the residual-triggered refactorization and
  six accepted relatively small pivots. The small-pivot samples did not show
  a sign disagreement between row and column pivot estimates.

The iteration-35375 snapshot demonstrates sensitivity of a **fresh** native LU:
recomputing its prices gave one nonbasic reduced cost of approximately
-4.935e-4; the existing 256-bit refinement evaluated it at about -5.095e-17.
The local solve recovered and continued. This establishes a concrete cancellation
problem in a local basis, not the cause of the second machine's later failure.
No new safeguard is justified solely by equating the two events.

## Supplied Windows capture

The four files received in `/home/jspitz/logs` have been inspected. The report and
both snapshots share run ID `56310620017900-18816`, the expected e1b1567 source
revision and input SHA-256. The report confirms native Windows x86_64, Julia
1.13.0, one Julia thread and one BLAS thread. Binary snapshot checksums and sizes
are recorded in `results/windows-capture/inputs.toml`; the binaries remain local.
That manifest hashes the received files. The archived text log has CRLF line
endings normalized to LF; its content is otherwise unchanged.

**This run did not reproduce the numerical termination.** It stopped at the
requested 46,000-iteration limit after 451.308 seconds, with 374 refactorizations.
There is no `certification_failed` event, original-LP restart or terminal-failure
snapshot. This limited run is not a certificate that the remaining solve would
succeed.

The trajectory differs materially from the original excerpt. Near iteration
45,000, the original objective was about 4.916e7; the supplied capture was already
about 5.086e7. Logged refactorization gaps grow from 80 to 160 between iterations
13719 and 13879 and remain 160 in the late excerpt. The snapshot at iteration
44115 has 156 accumulated factor updates. This is compatible with the existing
legacy interval-growth mechanism (`_note_stable_dual_refactorization!`); setting
`refactorization_interval=80` does not freeze its effective value at 80.

Two state snapshots are available:

| Iteration | Event | Inspection |
|---|---|---|
| 7011 | Residual-triggered refactorization | Fresh factor, zero updates; explicit Windows L/U entries are finite. Recomputing on Linux gives one reduced cost -1.19074e-7, while existing 256-bit refinement gives -4.02317e-8, within the 1e-7 dual tolerance. |
| 44115 | Accepted relatively small pivot | 156 updates; stored column/row pivots -0.007848745303367143 / -0.007848745303367148 agree, as does a fresh solve to about 3e-15 absolute. No sign disagreement was found. |

As documented below, the 7011 snapshot is taken after rebuilding the factor but
before recomputing the point/prices. The fresh solves in the inspection are
Linux calculations on the saved matrices, not a replay of the exact Windows
native solve. Neither snapshot contains the originally failed basis at 45617.
No solver modification follows from these observations alone.

The user subsequently supplied the original script: `Pkg.activate("./")`,
`using JSimplex`, reading `C:\\tmp\\runtime.mps`, then `solve` with the reported
options, an iteration limit of 1,000,000 and no time limit. JSimplex was installed
with `Pkg.add()`. The user then measured **one Julia thread and eight BLAS
threads** in the original environment, loading
`C:\Users\jiris\.julia\packages\JSimplex\Pz9tN\src\JSimplex.jl`.
The first capture forced one Julia/BLAS thread, disabled `startup.jl`, loaded
JSimplex from `C:\\JSimplex`, and warmed up on AFIRO. These differences are possible
sources of a different trajectory, not established causes of failure. In
particular, eight BLAS threads are now a concrete difference; this does not mean
the simplex iteration loop ran on eight Julia threads. The
same-session entry point below preserves the loaded package and thread settings.

To repeat the snapshot inspection from this worktree (sequential Julia job):

```sh
julia --startup-file=no --project=. diagnostics/ft-numerical-recovery/reproduce/inspect-capture.jl /home/jspitz/logs/ft-capture.toml /home/jspitz/logs/ft-capture.toml.refactor_residual.7011.bin /home/jspitz/logs/ft-capture.toml.accepted_pivot.44115.bin
```

## Capture on the failing machine

### Preferred: use the original Julia session and package environment

Copy the updated `reproduce/capture-failure.jl` to `C:\\tmp\\capture-failure.jl`.
In the same environment used for the original script, after its
`Pkg.activate("./")` and `using JSimplex`, run the following **instead of** its
`solve` call. Keep the normal launch method and Julia/BLAS thread settings.
Do not activate the diagnostic checkout or change the installed package.

```julia
include(raw"C:\tmp\capture-failure.jl")
ENV["JSIMPLEX_TRACE_PIVOTS"] = "1"
ENV["JSIMPLEX_TRACE_RELATIVE"] = "1e-7"
ENV["JSIMPLEX_TRACE_LIMIT"] = "12"
open(raw"C:\tmp\ft-session-01.log", "w") do io
    redirect_stdout(io) do
        redirect_stderr(io) do
            with_logger(ConsoleLogger(io)) do
                Base.invokelatest(main, [raw"C:\tmp\runtime.mps", "dual", "forrest_tomlin", "900",
                      raw"C:\tmp\ft-session-01.toml"];
                     warmup=false, iteration_limit=46000)
            end
        end
    end
end
```

Use a fresh prefix for each run, including the log filename. This entry point
does not modify `ARGS`, the active project, or Julia/BLAS thread counts. It skips
the AFIRO warm-up to match the original script more closely; its timings can
include compilation. The 900-second and 46,000-iteration limits still bound the
diagnostic run around the originally reported failure. Inspect the environment
file before extending those limits if the numerical path differs again.

The `*.toml.environment.toml` file is written before solving. It records the
loaded source path, active project, package version, package tree hash and git
revision when available, BLAS configuration and actual thread counts. A normal
`Pkg.add()` installation may have no `.git` directory: `source_revision` then
reads `unavailable`; the package tree hash provides additional identification.
The same metadata is included in the final report; snapshots retain their
shared run ID, input hash and source revision. Send the log,
both TOML files, and generated `.bin` snapshots. This avoids treating the number
of hardware threads as proof of the number used by Julia or BLAS.

Local validation on Julia 1.13.0 passed 18 checks: AFIRO reaches OPTIMAL with
and without warm-up, environment metadata round-trips, the active project,
`ARGS` and thread counts are preserved, and stale output prefixes are rejected.
See `results/session-smoke.log`. The logging example uses `invokelatest` to
keep the caller from inferring the entire diagnostic solve: a test wrapper
calling it directly was interrupted after more than six minutes in Julia's
type inference. This is not evidence about numerical failure or solve speed.
The updated entry point has not yet been run on native Windows.

### Previous controlled one-thread baseline

Copy `reproduce/capture-failure.jl` into the root of the checkout at the failing
revision, as `capture-failure.jl`. Open PowerShell in that checkout and replace
`C:\data\runtime.mps` below with the actual Windows path to the model:

```powershell
$env:JULIA_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:JULIA_IMAGE_THREADS = '1'
$env:JULIA_NUM_PRECOMPILE_TASKS = '1'
$env:JSIMPLEX_DEBUG_ITERATIONS = '46000'
$env:JSIMPLEX_TRACE_PIVOTS = '1'
$env:JSIMPLEX_TRACE_RELATIVE = '1e-7'
$env:JSIMPLEX_TRACE_LIMIT = '12'
julia --startup-file=no --project=. .\capture-failure.jl 'C:\data\runtime.mps' dual forrest_tomlin 900 .\ft-capture.toml > .\ft-capture.log 2>&1
```

The script runs directly in Julia and does not invoke bash or require WSL.
Reports, snapshots and the log are written to the checkout directory. Use a new
output prefix when repeating the capture. The Linux memory ceiling described
above applies only to local validation; it is not imposed by this Windows command.
The PowerShell instructions have been reviewed but not executed on Windows here.

The 46,000-iteration cap allows the reported failure at 45,617 to be captured,
then bounds the original-LP retry. The 900-second solve budget starts after a
small warm-up. Timing is diagnostic, not a performance comparison. The report
records source revision, source path, input hash, Julia version, architecture,
thread counts, limits, status and event counts. Each run requires a fresh output
prefix: an existing report or snapshot prefix is rejected before solving. Report
and snapshots also share a run identifier, input hash and source revision so a
stale snapshot cannot silently be paired with a newer report.

The key output is `ft-capture.toml.certification_failed.45617.bin` if the same
failure recurs, together with the report/log and any small-pivot snapshots just
before it. The actual iteration is part of the filename; it can differ.
Snapshots contain the problem, basis, costs/bounds, primal vector, reduced costs,
pivot row/direction, pricing weights and factor state. Native numeric L/U,
permutations and row scaling are saved explicitly, because Julia's UMFPACK
serializer otherwise recreates the native numeric factor on deserialization.
The final recorder's snapshot round trips were checked for basis, vectors,
event and explicit U storage.

## Snapshot interpretation

At a `refactor_residual` event, the factor has **already been rebuilt** but the
primal/prices/direction still precede recomputation. It is not a frozen copy of
the discarded updated factor. At `certification_failed`, state is the terminal
workspace. An accepted-pivot snapshot has the prior basis for algebraic pivot
inspection, but costs and bounds are the post-pivot working state; it is not a
complete transaction checkpoint for restarting an identical trajectory.

The local baseline was collected with the first recorder version, which stored
the factor object at residual/failure events but did not yet save explicit native
L/U or environment metadata. Local inspection therefore rebuilt the basis from
its recorded matrix and used the saved vectors. The final recorder adds those
fields without changing solver behavior. Serialized snapshots are kept local
and are not committed; transfer them with the Julia version and matching solver
revision. The matrix/vector data are needed to distinguish inaccurate factor
solves from a genuinely infeasible working basis after an exchange.
