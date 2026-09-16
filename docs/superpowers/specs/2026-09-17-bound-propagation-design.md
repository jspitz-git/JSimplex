# Exact bound propagation and repeated presolve

## Goal

Derive column bounds from every finite side of a multi-term row using the
current bounds of the other columns. Repeat the existing reductions and this
propagation until a round makes no change, subject to a finite round limit.

## Safety and numerics

Compute row activity intervals from the exact rational values of stored
coefficients and bounds. Tighten a column only when the derived finite bound
is exactly representable in the model's scalar type. A proven bound conflict
or row activity conflict returns `INFEASIBLE`; otherwise undecidable candidates
remain unchanged. A row is removed only when its full activity interval lies
inside its sides. A row that yields a new bound stays in that pass; a later
round may remove it once the stored column bounds imply the row.

## Postsolve

Record the column bounds before each propagation pass and the row mapping for
any redundant rows it removes. A reduced basis can put a column on a newly
finite bound that does not exist in the prior model. During basis restoration,
select an existing opposite bound if finite, otherwise mark the column free
nonbasic. This preserves the basis matrix and gives original-model cleanup a
valid nonbasic state. Cleanup recomputes the original primal and optimizes it;
it need not start at the reduced primal value.
If the reduced numerical solve is inconclusive, retry the original LP within
the remaining time and iteration budget.

## Iteration

Run basic, singleton, proportional, dependent-row, doubleton, and propagation
passes in sequence. Substitution precedes propagation so a free variable in an
equality is not first given a finite implied bound. Repeat when any pass
changes rows, columns, or bounds.
Stop after 12 rounds to avoid nonterminating geometric tightening sequences.
Report the final reduced dimensions through the existing statistics message.

## Verification

Test lower and upper propagation for both coefficient signs, contradiction,
redundant-row removal, exact-value rejection, source-row retention, basis
restoration when a finite bound is newly created, and a chain that needs more
than one round. Run both simplex algorithms and the full repository suite.
