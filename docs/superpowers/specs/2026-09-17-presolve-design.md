# Reversible LP presolve and original-model cleanup

## Scope

Run presolve after validation and integrality relaxation, before scaling. Remove
fixed columns, structurally empty columns with a finite minimizing bound, and
rows that become empty. Keep the public `solve` result and status contract.
Presolve is automatic. Models without a safe reduction retain the current path.

## Reduction safety

A removed column receives a definite bound value. Subtract its contribution
from finite row bounds and add its objective contribution to the constant. For
floating types, accept a reduction only when every changed value is finite and
exactly representable in the model type; otherwise retain the column. An empty
row is infeasible precisely when zero violates a finite row bound. Rows that
are satisfied at zero are removed. Preserve row and column names and scalar
type. Never mutate the caller's model.

## Restoration and cleanup

Keep row and column index maps and removed column values in one postsolve step.
After an optimal reduced solve, restore both primal values and the simplex
basis. Removed columns are nonbasic at their chosen bounds; removed row activity
variables are basic. Structural and row activity indices of the reduced basis
map to the original model. Scaling does not alter basis indices.

Use the restored basis to initialize a dual-simplex workspace on the original
continuous model. Recompute and, if needed, pivot to optimality under the
remaining iteration and time budgets. Report counters including both solves.
Only return `OPTIMAL` after the original-model feasibility and objective checks.
If the reduced solve is nonoptimal, keep its resource status; for mathematical
infeasibility or unboundedness, verify on the original model before reporting.
If a primal phase-I artificial basis cannot be restored, run the original model
from its standard basis as a conservative fallback.

## Verification

Unit tests cover each reduction, exact and floating arithmetic, all scalar
types, reconstruction, infeasible empty rows, input immutability, and the
original-model cleanup path. Run the full package suite and compare a set of
small models with presolve disabled through the internal identity path.
