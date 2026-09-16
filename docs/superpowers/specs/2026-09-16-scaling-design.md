# LP scaling design

## Goal and scope

Add reversible row and column scaling to the existing LP solve pipeline. Enable it
by default for floating point models, preserve exact rational behavior by default,
and keep public primal values, objective values, and progress objective values in
the original model's units. Do not scale the objective as a whole or add presolve.

## User interface

Add `scaling::Symbol = :auto` to `SolverOptions`, with `:auto`, `:on`, and `:off`.
`:auto` enables scaling for supported `AbstractFloat` types and uses the identity
transform for rational types. `:off` always uses the identity transform. `:on`
enables scaling for floating point types; reject `:on` for rational types with an
`ArgumentError`. Preserve the mode when converting options to a model's type.
Expose the same mode through the MOI raw optimizer attribute `"scaling"`.

## Transformation

After integrality relaxation and identity presolve, produce a scaled working
`LinearProblem{T}` and a `Scaling{T}` containing positive row factors `r_i` and
column factors `c_j`. The transformed problem uses

```
A'_{ij} = A_{ij} / (r_i * c_j)
row bounds'_i = row bounds_i / r_i
column bounds'_j = c_j * column bounds_j
objective'_j = objective_j / c_j
objective constant' = objective constant
x_j = x'_j / c_j
y_i = y'_i / r_i
```

Preserve unbounded bound tags, objective sense, variable domains, names, and sparse
matrix structure. Never modify the caller's model. Apply minimization conversion
to the scaled model before simplex. Both primal and dual simplex use the same
working problem. Existing original-model primal and objective certification runs
after unscaling. Progress reporting evaluates the original objective on the
unscaled structural variables, including during phase I.

The solve pipeline scales only after integrality relaxation. If the transform is
called directly on a model with discrete domains, leave those columns at factor
1 so their integer or binary domain meaning is preserved.

## Factor selection and numerical safety

Make one pass over rows, then one pass over columns of the row-scaled sparse
matrix. For a maximum absolute nonzero coefficient `m`, choose the largest
representable power of two no greater than `m`. The largest magnitude after
that pass is in `[1, 2)` when the factor is accepted. Use factor 1 for an empty
row or column. A candidate
factor is applied only if every affected nonzero coefficient stays nonzero and
finite and every affected finite bound stays nonzero when originally nonzero and
finite after transformation. Column checks also include nonzero objective
coefficients. If a candidate fails, retain factor 1 for that row or column.
This avoids introducing zeros or infinities into a valid floating model. For
`BigFloat`, perform each exponent shift at the larger of the stored value's
precision and the active solve precision. Preserve stored values and precision
in the caller's model. Solving may return `NUMERICAL_ERROR` if the original-model
certificate is inconclusive.

The simplex tolerances remain expressed in working-problem units. Because a
single global absolute tolerance cannot represent every original row and column
after scaling, the final original-model feasibility check remains mandatory.
Users can select `:off` to compare behavior on numerically sensitive cases.

## Verification

- Unit tests for factor selection, reversible primal and dual mappings, both
  finite and unbounded row/column bounds, zero rows/columns, objective sense and
  constant, and no mutation of input data.
- Tests for unsafe factors near floating point underflow and overflow, including
  `Float32`, `Float64`, and `BigFloat` precision preservation.
- Solver tests for both simplex algorithms and all scaling modes, plus exact
  rational default behavior and rejection of rational `:on`.
- Progress and MOI raw attribute tests, including original-unit results.
- Run the package test suite and representative local MPS fixtures in the
  isolated worktree.
