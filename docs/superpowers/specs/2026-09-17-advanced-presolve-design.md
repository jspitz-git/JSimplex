# Advanced reversible LP presolve

## Goal and scope

Extend the current automatic presolver with four safe rules: singleton-row
bound tightening, dominance of proportional rows, general linear-dependence
proofs for redundant rows, and substitution of a free variable from a
two-term equality. Keep the public `solve` API and cleanup on the original LP.

## Numeric policy

Interpret every stored coefficient and finite bound as an exact rational
number for deciding whether a reduction is valid. Convert transformed model
data back to `T` only when exactly representable and finite; otherwise leave
that reduction unapplied. Do not classify near-dependence as dependence. A
dependent row with stricter bounds stays unless its redundancy or infeasibility
is proved from retained row bounds. Cap general elimination work to protect
large or dense models; reaching the cap leaves remaining rows unchanged.

## Reduction pipeline

Run existing fixed/empty reductions, then singleton rows, proportional rows,
general dependent rows, and eligible doubleton equalities. Repeat cheap passes
after a substitution, with a finite pass limit. Each pass yields a reduced
problem plus one reversible step, or a proved infeasibility. Keep source names
and original model arrays unchanged. Report the final reduced size in the
existing presolve statistics message.

Singleton rows produce exact column bound intersections. The removed row is
stored as the source of a newly active bound. When restoring a basis, move a
column nonbasic at such a bound into the removed row's basis slot and set that
row activity variable to its original active bound. A nonactive removed row
activity remains basic.

Proportional rows use exact coefficient ratios and interval containment. A
looser row is removed when a kept row implies it; disjoint intervals prove
infeasibility. Crossing intervals remain. General dependent rows use sparse
rational row elimination to express a row as a combination of independent
retained rows. The combination gives an outer interval for its activity. A row
is removed only if this interval lies inside its bounds; a disjoint interval
proves infeasibility.

For substitution, require an equality with exactly two nonzero coefficients
and an eliminated variable free on both sides. Store `x_eliminated = alpha +
beta*x_kept`. Substitute into the objective and all other rows only when all
new coefficients, constants, and finite bounds are exactly representable in
`T`. Restore the eliminated variable as basic in the removed equality row.

## Postsolve and status handling

Apply postsolve steps in reverse reduction order to restore primal values and
basis states. The existing original-model cleanup resolves from that basis.
Reduced infeasible/unbounded statuses retain the existing original-model
verification path. A presolve infeasibility is returned only with an exact
bound contradiction. Time and iteration budgets remain shared.

## Verification

Test each rule in Float32, Float64, BigFloat, and Rational{BigInt} where
applicable. Include nonredundant dependent inequalities, inconsistent
dependent equalities, a nonparallel linear combination, negative row scaling,
inexact floating transformations, basis restoration, and original-model
cleanup for both simplex algorithms. Run the full repository suite and check
runtime on the existing regression fixtures.
