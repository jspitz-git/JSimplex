# Native terminal certificate and postsolve projection recovery

This repair starts from master `b190658` and uses the saved terminal states of
both HH/native-160 `medium.mps` runs. The experimental basis-manager branch is
not part of this change.

## Terminal certificate

Both main runs reached phase II and failed the original-objective certificate
at iterations 212280 (dual) and 335046 (primal), before postsolve. Their cached
basic reduced costs were zero, but independently solving for the original-cost
dual witness left stationarity errors above the absolute certificate tolerance.
Fresh LU alone did not resolve the diagnostic failure.

After a failed certificate, native Float32/Float64 now tries one compensated
residual correction of the private dual witness, in the same precision. The full
original witness checker, including nonbasic complementarity, still decides
acceptance. The basis, primal point, working prices and costs are unchanged.
Successful certificates take the old fast path; checked solves do not receive
another correction budget. Deadlines and a zero correction budget are respected.

## Postsolve projection

Continuing the dual terminal state exposed a separate handoff problem. The
postsolved point is feasible, but the restored original basis is far from it.
Projection finds a useful basis whose fresh native solve has a small rounding
error. The driver rejected the projection and restored the very infeasible old
basis, causing prolonged auxiliary optimization.

In the uncorrected handoff probe, the projected point differed from the target
by at most 1.8440187e-7 and failed original-model feasibility. Existing native
cleanup reconstruction reduced the difference to 9.3132257e-9 and passed that
same check. This is a reconstruction defect, not evidence of an infeasible
postsolved target.

Projection now invokes that existing bounded reconstruction before discarding
its exchanges. It repeats both workspace-bound and original-model feasibility
checks. A genuinely infeasible reconstructed basis remains rejected. No
simplex candidate, tolerance, precision, pricing heuristic or adaptive option
is changed.

## Reproduction and limits

`reproduce/medium_snapshot.jl` rebuilds the explicit saved HH factors and checks
the production terminal certificate. It verifies that rereading, presolving and
scaling the original input produces the saved working model. It then applies
the production primal basis mapping (where needed), unscaling, postsolve and
basis restoration. `handoff` mode saves this boundary for independent cleanup
runs; `reproduce/handoff_cleanup.jl` calls the production cleanup entry point.
These are terminal-state continuations, not fresh multi-hour solves or generic
mid-iteration checkpoints.

The input SHA-256 is
`79c374a584b1463305cf4b0faee8920d0364df2dd5d0468a44ab58d9e9d49dc0`.
Saved snapshots remain in the older worktree's local
`.superpowers/medium-hh-main/{dual,primal}/attempt-1/reports/` directories.
Their hashes and source hashes are recorded by the reproduction scripts.

Run every numerical command sequentially under the existing memory guard:
8 GiB virtual memory, at least 6 GiB available RAM, at most 1 GiB swap, one
Julia thread and one BLAS thread. Local preferences disable the precompile
workload. Semantic interpreter tests and compiled allocation tests are reported
separately. Never treat a missing report, interrupted diagnostic, resource
failure or time limit as a completed optimal solve.

Local exploratory attempts are retained in `.superpowers/certificate-repair`.
The first handoff probe accidentally produced a cyclic report dictionary;
that invalid TOML is retained compressed and is not used as evidence. Its
corrected rerun is `medium-dual-probe-2.toml`. A 600-second cleanup attempt with
only the certificate fix ended at TIME_LIMIT, after 14639 additional iterations;
profiling showed real auxiliary simplex work rather than compilation.

## Verification commands

Use the active checkout as the Julia project. The local shell wrapper in the
older experimental checkout supplies the existing Julia depot and 8 GiB VM
limit; the Python guard supplies the independent RAM/swap watchdog. A
`--heap-size-hint=2G` runtime setting requests earlier garbage collection without
altering solver arithmetic or increasing the memory cap.

The committed scripts support:

- `reproduce/semantic.jl` with `--compile=min`: related primal, dual, phase,
  cleanup, reconstruction, deadline, precision and driver regressions.
- `test/certification_allocation_tests.jl` and `test/solver_tests.jl` with normal
  compilation: certificate fast-path and existing allocation expectations.
- `reproduce/external.jl` with the existing
  `diagnostics/basis-selective-preparation/reproduce/external-inputs.toml`:
  100 solves, five inputs, both algorithms, all five public managers and both
  native and Markowitz refactorization; checks optimum and original feasibility.
- `reproduce/runtime.jl`: a fresh full dual runtime solve with HH/native-160,
  legacy steepest-edge, presolve/scaling defaults and relaxed integrality.
- `reproduce/medium_snapshot.jl SNAPSHOT HANDOFF handoff`, followed by
  `reproduce/handoff_cleanup.jl HANDOFF REPORT SECONDS`: independent terminal
  certificate and original-model cleanup validation.

A complete project-wide suite is not implied by these targeted checks.

## Completed regression evidence

- 13,905 semantic assertions passed (`--compile=min`).
- 61 certificate and allocation assertions passed with normal compilation
  (`-g0 -O1`), including the unchanged certificate fast-path allocation limits.
- All 100 external solves passed: 305 assertions, correct reference optima and
  original-input primal feasibility. `results/external-audit.json` verifies the
  complete set of unique combinations, not merely the number of output rows.
- The separate compiled `solver_tests.jl` attempt reached its 300-second guard
  inside LLVM debug-info cloning. It is not reported as a passing full suite.

The complete original-model cleanup continuations did not produce a final
solver result. Both repaired handoffs enter primal cleanup with zero primal
infeasibility. The dual continuation progressed from iteration 212280 through
213200; the primal continuation progressed from 335046 through 336000. Neither
an accepted terminal certificate nor those intermediate points are a
successful full medium solve. These two local numerical repairs are independently
validated; complete medium convergence remains unvalidated. All recorded
incomplete attempts are distinguished in `results/incomplete-attempts.json`.

The fresh runtime solve passed with HH/native-160 and the requested dual legacy
configuration: OPTIMAL after 55,469 iterations, objective
`5.142569176210457e7`, and original-model primal feasibility. The timed solve
block took 178.72 seconds under `-g0 -O1`; this is functional evidence, not a
benchmark against other compiler settings.

The primal terminal snapshot also passes production certification. Its expanded
phase-I workspace retains a zero objective constant in phase II; the public
solver evaluates the original objective from the recovered point. The snapshot
comparison therefore checks this existing convention instead of incorrectly
requiring equality to the unaugmented working constant. The failed diagnostic
assertion is retained separately from solver failures.

## Remaining process-memory limitation

Repeated complete cleanup attempts hit process resource failures under the
unchanged 8 GiB virtual-memory cap. In the last primal diagnostic, explicit full
GC every 100 pivots did not prevent a native SIGSEGV: the stack enters GC and
finalizers from `__gmpz_init2`. The process exited 139 after 617.30 seconds, with
peak RSS 7,410,120 KiB and over 5.27 billion pool allocations. This is a native
process crash, not a returned simplex NUMERICAL_ERROR and not proof that the
virtual-memory cap alone caused the crash. No Julia process remains from this
attempt, and its queued dual repeat was not started.

The observer measured about 473 MB of Julia-visible workspace and 149 MB of
factor data at iteration 336000. Factor nonzero counts and update storage
remained bounded during the probe. `Base.summarysize` does not account for all
external factor/GMP storage, JIT memory or allocator retention. Repeated exact
feasibility fallback is a plausible allocation contributor, but root causality
has not been established. Julia's installed GMP hooks use counted allocation;
GMP must not be described as categorically invisible to Julia GC.

`reproduce/handoff_cleanup_gc.jl` is diagnostic instrumentation only. Its full
collections and structure-size measurements are not production solver changes
and invalidate elapsed times as performance benchmarks. A prior dual `-O1`
attempt was additionally interrupted by a failed SIGUSR1 profile request at the
VM cap; that failure is preserved separately.

Independent code and evidence review found no substantive issue in either
functional repair. Integration includes those bounded repairs and their tests,
not an unverified memory workaround or a claim of fully solved medium.mps.

## Original target versus reconstructed basis

The independent handoff export also checks the postsolved target itself against
the original model. The dual target passes, whereas the primal target does not.
Their evaluated target objectives are respectively `2.2389455643711373e7` and
`2.2389401116820432e7`; neither value is presented as a certified original-model
optimum. An OPTIMAL certificate in the reduced working problem does not certify
the postsolved original target. Production cleanup retains its independent
original-model feasibility checks, including after projection/reconstruction.
Zero logged `pinf` is a workspace metric and by itself does not replace that
original-model certificate. The exported handoff reports preserve this
additional limitation explicitly.
