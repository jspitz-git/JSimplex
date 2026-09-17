# Rounded Objective Updates for Singleton Equalities

## Goal

Eliminate singleton columns in equality rows when only the transformed
objective coefficients fail the current exact-representability check. Preserve
the exact checks for row bounds, objective constants, matrix coefficients, and
all other presolve passes. Verify final LP solutions on the original model.

## Scope and numerical rule

For `Float32` and `Float64` only, convert an exact rational objective update to
the nearest finite value of the model type. Accept it only when its relative
error is at most eight machine epsilons; reject underflow of a nonzero update.
Accumulate a batch of updates in exact rational form and round only the stored
coefficient. Keep `BigFloat` and rational models on the existing exact rule.
The objective constant and projected column bounds must remain exactly
representable for every accepted elimination. When an equality has several
eligible singleton columns, prefer one whose objective update is exact.

## Recovery

Keep the existing singleton equality postsolve map and basis restoration. The
solver recomputes and optimizes the original LP from the restored basis after
every reduced optimum, and checks original primal feasibility and objective
optimality. If cleanup reports a numerical error, retry the original LP from
scratch with the remaining solve budget, as already done when the reduced solve
reports a numerical error. Final objective values always come from the
original model.

## Validation

Use a small equality whose transformed cost is inexact in `Float64` to prove
the old pass skips and the new pass eliminates it. Test accepted Float32 and
Float64 updates, rejected overflow/underflow, unchanged exact-type behavior,
postsolve and basis restoration, and public solve. Compare presolved dimensions,
statuses, objectives, and original feasibility on the checked-in NetLib and
MIPLib cases in both simplex algorithms. Do not solve `runtime.mps` or
`medium.mps` in this change.
