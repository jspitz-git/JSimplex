# LP Presolve Reductions Design

## Goal

Reduce continuous LPs further using equality aggregation, bounds implied by
rows, and objective-aware dual fixings. Keep the original model available for
postsolve and cleanup from a restored basis.

## Safety rules

- A new finite coefficient, bound, or objective value is stored only when it is
  exactly representable in the model scalar type. Otherwise skip that candidate.
- Every removal records enough information to restore a primal solution and a
  nonsingular candidate basis in the original row and column space.
- A candidate that needs unbounded work or raises matrix nonzeros beyond its
  fill-in budget is skipped. Presolve retains its round and time limits.
- A reduction never declares an LP optimal from presolve alone. The original LP
  remains the authority for final objective and feasibility checks.

## Equality aggregation

For an equality `a*x + s = b` where `x` occurs in only this row, eliminate `x`
in one sparse batch. Its bounds become bounds on `s`, and its objective
coefficient changes the costs of the variables in `s` and the objective
constant. This introduces no new matrix nonzeros. Restore `x = (b-s)/a` and
translate the reduced row slack basis state to the original `x` state.

For a non-singleton pivot, substitute `x` only when the equality and the bounds
of the other variables prove that the old bounds of `x` are redundant. Limit
the row and column degrees and the estimated matrix fill-in. Select independent
pivots so substitutions can be applied together and reversed independently.
Restore each eliminated `x` as basic in its removed equality row.

## Bound inference

Use exact row activity intervals to prove that an equality pivot's column
bounds are implied by the other column bounds. Feed that proof to aggregation;
the bounds may then be omitted from the reduced model. Preserve existing row
bound propagation and repeat all structural passes to a fixed point.

## Dual reductions

For minimization, fix a column to a finite lower or upper bound when moving to
that bound cannot violate any incident row and cannot worsen the objective.
Reverse the sign test for maximization. Store fixed values through the existing
column elimination map. Skip columns with an ambiguous row direction or an
infinite chosen bound.

## Validation

Test each transformation with positive and negative coefficients, finite and
infinite bounds, both objective senses, all supported scalar types, and basis
restoration. Compare presolve enabled solutions with original LP solutions on
small models. Measure rows, columns, NNZ, presolve time, and the original-model
cleanup on `runtime.mps` and `medium.mps` within explicit resource limits.
