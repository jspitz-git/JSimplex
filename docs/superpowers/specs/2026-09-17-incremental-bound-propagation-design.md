# Incremental Row Bound Propagation

## Goal

Avoid repeating exact rational activity calculations for rows untouched since
the preceding bound propagation pass. Preserve the reduced LP, postsolve maps,
and final cleanup on the original LP.

## State and proof of relevance

The first propagation pass checks every row. Afterward the presolve driver
keeps that pass's output model as a reference, plus maps from current row and
column indices to the reference and a set of rows affected by bounds tightened
inside propagation. Each intervening reduction already returns a postsolve map;
the driver composes its retained row and column indices into these maps.

Before another propagation pass, compare the reference and current models in
the mapped coordinate system. A current row is dirty if its row bounds or any
matrix coefficient changed, an old nonzero column term was removed, one of its
current column bounds changed, or it was pending after the preceding pass.
Compare sparse columns exactly, including stored zero handling. The comparison
uses native model values and no rational arithmetic. If a postsolve map cannot
be read, discard the reference and check every row.

Propagation processes dirty rows in ascending order. If it tightens a column
bound, mark later incident rows for this pass. All incident rows become pending
for the next pass so earlier rows can see the new bound. A pass with no dirty
rows is an identity reduction. The direct `propagate_row_bounds(problem)` call
still checks every row.

## Validation

Test row and column mapping, coefficient and bound changes, removed columns,
and chained bound tightening. Compare full and incremental presolve on small
models and verify identical dimensions on `runtime.mps` and `medium.mps`.
Measure presolve time and memory under bounded runs, then run the full suite.
