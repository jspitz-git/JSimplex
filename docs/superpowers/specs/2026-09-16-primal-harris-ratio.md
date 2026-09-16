# Primal Harris ratio test

The primal simplex allows small bound violations within `primal_tolerance`.
Its ratio test should choose a numerically stronger pivot
among rows whose strict breakpoints lie within the first relaxed breakpoint.
The relaxation is `primal_tolerance / abs(movement)` in step units. The entering
variable's opposite bound remains a hard limit.

Before accepting a relaxed pivot, predict all basic bound violations at that
step. If their sum exceeds `primal_tolerance`, use the strict minimum ratio
instead. Exact rational arithmetic has zero default tolerance, so tied strict
breakpoints may still use the larger pivot. Preserve entering bound flips,
unboundedness detection, and the existing status semantics. No public option
or dependency is needed.
