# Rejection surge: finite residuals and a rejected fix

The results and decisions below describe the recorded historical revision. See
[the native pivot-probe follow-up](NATIVE-PIVOT-PROBE.md) for the later core fix,
its certified runtime runs, and the remaining bound-snap obstruction.

Base: `46f9708248a315181a512165885b85e32bb3d6f0` on top of `b29e10e`.
This follows the [bound-snap investigation](README.md). That investigation left production source and
the project test entry point unchanged; see the subsequent
[equation-loss investigation](EQUATION-LOSS.md) for the later point-preservation fix. Removing the weak-pivot probe's
`quality.reliable` gate explains and removes the captured local rejection surge,
but the unrestricted change regresses on a fresh runtime solve. It is retained
only as a diagnostic intervention, not as a solver fix.

## Live rejection evidence

The instrumented 1,200-step `preserve_structural` continuation reproduces the
previous endpoint exactly: objective 605142.6843376105, 73 refactorizations,
1,757 counted candidate rejections, and passing endpoint certificates.
Hooks preserve live factor updates, reduced costs, DSE weights and validity flags.
They do not solve systems or modify candidates. The logged transpose-pivot field
is meaningful for `pivot_row` failures; weak deferrals precede BTRAN and can log
a stale tableau entry. Trace collection starts at step
1,110; therefore the classified counts below describe that suffix.

There are 1,330 failed pivot-row checks, all at row 522, and 485 weak-pivot
preferences. No direction-price, ratio, unresolved-pivot, or zero-cutoff failure
is observed in this suffix. The 1,815 hook observations are not the same counter
as 1,757 exclusions: 58 observations trigger a fresh-factor retry instead of
immediate exclusion. There were no earlier counted exclusions in this run.
Across the failed row checks, maximum forward/transpose relative disagreement
is 1.142e-12, maximum stored/actual weight ratio is 1.000000140, and maximum
relative price disagreement is 3.189e-13. This evidence does not support stale
prices or DSE weights as the cause of this captured surge.

The first saved failure is continuation step 1,143, entering column 22,991:

- Pivot: 8.159513556265789e-7; direction infinity norm: 342.86589951215313.
- Cached reduced cost: -2930.929145196363; direction price: -2930.929145196359.
- Stored DSE weight: 1210.6476339507922; computed weight: 1210.6476339505944.
- The live factor has 22 updates; the workspace has had 15 refactorizations.
- The transpose row passes its residual check, and its pivot agrees to 3.78e-14.

The compensated direction residual is finite, with absolute error 1.385e-13,
but componentwise relative error one. Tiny homogeneous rows dominate that
relative metric: row 2,219 has residual and scale about 1.009e-19; row 6,860
about 2.835e-20. The production gate rejects before attempting the correction.
One Float64 correction changes the selected pivot by only -6.6231e-20
(relative 8.117e-14), while changing the whole direction by at most 2.627e-11.
The corrected direction still has componentwise relative error one.

A separate 256-bit residual-refinement diagnostic confirms the corrected pivot
near 8.1595135562651267e-7 and reduces the absolute residual to about 2.67e-75.
It uses the saved Float64 factor to solve correction equations; it is **not**
an independent high-precision factorization. Neither that diagnostic nor the
native correction is used to raise solver arithmetic precision.

## Minimal experiment and counterexample

The experiment removes only `!quality.reliable` from the early residual gate.
Unavailable and nonfinite residuals still reject; the native correction,
finite/cancellation checks and relative pivot-sensitivity threshold remain.
The proposed direction is not modified. The exact original source delta is
saved in [finite-residual.patch](reproduce/finite-residual.patch).

| Controlled 1,200-step continuation | Refactorizations | Rejections | Auxiliary objective |
| --- | ---: | ---: | ---: |
| Structural-value intervention alone | 73 | 1,757 | 605142.6843376105 |
| Plus finite-residual experiment | 16 | 29 | 605025.4237371949 |

Both endpoints pass all-bound, phase-model and stored-row certificates. These
continuations are refreshed references, not exact cache replays of the initial
PFI endpoint. This comparison establishes the local rejection mechanism; it does
not establish safe behavior from the initial model or completion of phase I.

The mandatory fresh 300-second PFI runtime test uses only the finite-residual
experiment, without the structural-value intervention. It restarts on the original
LP after `NUMERICAL_ERROR: primal feasibility lost` at iteration 3,683, about
44.7 solver seconds into the run. Final status is `TIME_LIMIT`, 21,622 total
iterations, 1,527 refactorizations, and auxiliary objective 908708.1942097376
on the restarted, larger phase model. That objective is not comparable with the
reduced-model continuation objective. Phase I does not finish.

A targeted rerun captures the point before iteration 3,683:

- Before the step, every bound violation is below 1e-7 (maximum 9.924e-8), but
  both the independent phase-primal and stored-row consistency checks fail.
- The last pivot is strong: 1.0 in a direction of infinity norm 59.87, with zero
  step. This pivot bypasses the weak-direction probe. The leaving variable is
  59,131, whose before/after values are both zero: no bound snap occurs there.
- After the scheduled refactorization, maximum individual bound violation is
  3.969e-6, while stored-row consistency passes. Variable 6,558 moves from
  1.773e-7 to -3.969e-6. The aggregate primal infeasibility in the solver log is
  4.445e-5; this is distinct from the maximum individual violation.
- The predicted zero-step point also fails the two equation certificates. The
  existing point-preservation fallback is therefore right to reject it.

The immediate failing step is not evidence of another false tiny pivot. The
trajectory has already lost equation feasibility before this strong pivot and
refactorization. The diagnostic does not yet locate the **first** such loss or
attribute it to a particular preceding update. Small pivot corrections alone
do not certify the full direction or a feasible reconstructed point.

## Verification and decision

The experimental change passes 1,570 focused assertions with `--compile=min`,
including 72 new assertions over Float32/Float64 and all four basis managers.
The new fixture has a tiny irrelevant homogeneous-row error and an accurate
weak pivot. Existing correlated false-pivot rejection tests also pass.
The initial test ran red (40 passes, 32 failures) before removing the gate.
Passing those tests did not predict the fresh runtime regression.

After withdrawing the source edit, the isolated override passes the 72-assertion
fixture again. Normal-compilation snapshot checks add 32 passing assertions
for the old false pivot and 20 for the newly captured accurate pivot, across
all four managers. These check the local diagnostic behavior, not convergence.
The isolated runner also reproduces all nine selected trajectory/certificate
fields of the 1,200-step experiment exactly. Its shared capture entry point
solves AFIRO optimally with original-model feasibility verified.

Read-only review caught an observer-order bug in the restart snapshot capture.
The final script saves the old workspace at the first identity change and checks
iteration 3,683. Its guarded targeted rerun reproduces both the acceptance trace
and the before/after inspection byte-for-byte; the pair is saved successfully.

The experimental production edit was withdrawn after that regression. The new
fixture lives under diagnostics and is not included in `test/runtests.jl`.
Broader external solves and three other runtime managers were not run for this
rejected candidate. No full-suite or convergence claim is made.

The next bounded experiment should locate the first loss of phase-primal or
stored-row feasibility along the newly admitted trajectory, then inspect the
responsible direction, basis update and recomputed point. Simply accepting all
finite residuals is not an acceptable production remedy, and adding rejections
without addressing that point/direction inconsistency would not resolve runtime.

## Reproduction

Use the same guarded Julia 1.13.0 aarch64 environment as the parent report: one
numerical process, one Julia/BLAS thread, 8 GiB virtual memory limit, 6 GiB free-RAM
floor, 1 GiB swap ceiling, and local `precompile_workload = false`.
Input and initial snapshot hashes are in the parent report. All generated binary
snapshots remain local in `.superpowers/phase1-rejections/`; selected hashes and
text evidence are in [results/rejection-surge](results/rejection-surge).

Use a fresh output prefix; do not redirect the log to a filename starting with
that prefix plus a dot, because the capture preflight correctly treats that as
an existing output. From the worktree, through the memory/time guard:

```sh
# Unchanged production behavior plus the original structural diagnostic mode.
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/rejections.jl INITIAL_SNAPSHOT 1200 180 OUTPUT_PREFIX
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/inspect-rejection.jl OUTPUT_PREFIX.rejected.bin

# Isolated finite-residual override; each invocation ends with the process.
julia --compile=min --project=. diagnostics/primal-phase1-stagnation/reproduce/run-residual-experiment.jl diagnostics/primal-phase1-stagnation/reproduce/residual-probe-tests.jl
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/run-residual-experiment.jl diagnostics/primal-phase1-stagnation/reproduce/continuation.jl INITIAL_SNAPSHOT preserve_structural 300 1200 OUTPUT.toml
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/run-residual-experiment.jl diagnostics/primal-runtime-stability/reproduce/capture.jl /home/jspitz/mps/runtime.mps pfi 300 OUTPUT.toml

# Targeted regression capture: hard-coded to the recorded pre-step iteration 3682.
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/capture-residual-regression.jl /home/jspitz/mps/runtime.mps 120 OUTPUT_PREFIX
julia --project=. diagnostics/primal-phase1-stagnation/reproduce/inspect-residual-regression.jl OUTPUT_PREFIX.before.bin OUTPUT_PREFIX.after.bin
```

The original full run and test reports record the temporary modified source hash.
The committed process-only intervention performs the same single gate change on
unmodified source; it does not make those historical reports describe a run of
the final checkout. Keep provenance and experiment mode when comparing results.
