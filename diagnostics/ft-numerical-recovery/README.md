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

One controlled-environment difference needs clarification: the capture command
forced one Julia/BLAS thread and disabled `startup.jl`. The launch method and
thread settings of the original failing session are not yet known. Those changes
are possible sources of a different numerical trajectory, not established causes
of the failure. Check the original session before prescribing another long run.

To repeat the snapshot inspection from this worktree (sequential Julia job):

```sh
julia --startup-file=no --project=. diagnostics/ft-numerical-recovery/reproduce/inspect-capture.jl /home/jspitz/logs/ft-capture.toml /home/jspitz/logs/ft-capture.toml.refactor_residual.7011.bin /home/jspitz/logs/ft-capture.toml.accepted_pivot.44115.bin
```

## Capture on the failing machine

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
