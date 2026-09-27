# Forrest–Tomlin failure on a second machine

**The reported failure has not been reproduced locally and is not fixed by this
change.** This work records the evidence and provides a bounded capture of the
missing numerical state. Solver source, tolerances, precision policy and the
adaptive strategy are unchanged.

## Reported failure

The user confirmed commit `e1b15678e86f6d1cf3b2343827bf6d4e25f6e54b`, before the
separate BG stable-row optimization `c7125f7`. The working configuration is
runtime.mps, legacy dual, steepest-edge pricing, native refactorization and
interval 80. The second machine's Julia version and architecture are not yet
confirmed.

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

## Capture on the failing machine

Copy `reproduce/capture-failure.jl` to the checkout at the failing revision. It
uses the same internal diagnostics as the existing runtime-debug tool. From that
checkout in WSL/bash:

```sh
ulimit -v 25165824
export JULIA_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 JULIA_IMAGE_THREADS=1 JULIA_NUM_PRECOMPILE_TASKS=1
export JSIMPLEX_DEBUG_ITERATIONS=46000
export JSIMPLEX_TRACE_PIVOTS=1 JSIMPLEX_TRACE_RELATIVE=1e-7 JSIMPLEX_TRACE_LIMIT=12
julia --startup-file=no --project=. /path/to/capture-failure.jl \
  /home/jspitz/mps/runtime.mps dual forrest_tomlin 900 \
  /home/jspitz/logs/ft-capture.toml > /home/jspitz/logs/ft-capture.log 2>&1
```

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
