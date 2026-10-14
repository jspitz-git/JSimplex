# MA-K: selective rational equality-bound activity design

Date: 2026-10-14. Planning only; no candidate or numerical acceptance.

## Problem and evidence

MA-J's whole `_equality_implies_column_bounds` component experiment includes
scratch construction. Its eight-term general Rational{BigInt} case has paired
median time ratio 0.8849, about22.3% lower bytes and23.2% fewer events. Rational
four-term unit/cancellation cases regress by about23.2%/50.7%, with368 extra
bytes per call. BigFloat does not establish a time benefit. See
[MA-J report](../../../diagnostics/simplex-core-architecture/MA-PRESOLVE-EQUALITY-QUALIFICATION.md).
These are small synthetic single-process observations, not a threshold fit or
presolver speedup. MA-J's unconditional replacement remains rejected.

The current aggregation caller permits only2–8 nonzero terms and retains its
fill/work caps. Thus “longer rows” in this proposal means exactly8 terms, not a
new permission to aggregate larger rows. Only exact Rational{BigInt} models
and their ordinary Vector{Tuple{Int,Rational{BigInt}}} row containers qualify.
All other types/containers and other lengths keep the original arithmetic.

## Proposed selection, to be qualified rather than assumed profitable

Use the existing ordered accumulation to recognize general arithmetic. Do not
pre-scan rows, allocate classification metadata, change _row_entries, or cache
eligibility across calls. Before activation use the original addition branches.
Count qualifying *endpoint additions*, in min-then-max order, only at original
row positions1–3. Both pivot bounds, both live activity endpoints and both
bounds of the current term must be finite; current term bounds must be unequal.
The original branch must require adding a nonzero activity and nonzero product
with unequal denominators. Zero initial assignments and shared fixed-activity
reuse do not count. Two endpoint additions in the same row position may count.

At the second such addition, inspect the two numerator signs and at most two
`ndigits(numerator(value); base=2)` values. Activate only when the signs agree
and both bit lengths are at least129. A failed check, or reaching position4
without activation, permanently declines activation for that invocation.
The128-bit boundary and second-addition rule are one fixed hypothesis, not
empirically established optimal thresholds; do not tune them after measurement.
By position3 at least4 nonpivot terms remain, but no claim is made that those
terms will require expensive additions. Adversarial tails are acceptance tests.

On activation create the MA-J-style three private rational destinations and
three BigInt addition buffers (nine distinct mutable leaves). Include the
triggering addition in MA. Keep the computed prefix; no rescan/reconstruction.
After activation every subsequent nonzero addition uses the private-add helper,
including same-denominator additions. Preserve zero assignment and shared fixed
activity shortcuts. Mixing ordinary same-denominator constructors back into
this phase can share a mutable scratch denominator and is forbidden.
Destinations must not alias either live endpoint or any input numerator or
denominator. The pool stops mutating before unchanged final bound predicates.
The only result is Bool; no persistent scratch or input mutation is allowed.

## Constraints and acceptance intent

- Keep arithmetic order, products, exact conversion, final comparisons, caller
  row/fill caps, tolerances, precision, exception propagation and safeguards.
- No extra row/matrix traversal, basis solve, factorization, persistent cache,
  global method overwrite or changes to rejected MA-I/MA-J artifacts.
- Noneligible calls allocate no MA scratch. A dispatch/length branch is still
  work; it is not a proof of zero runtime cost or compiler elimination.
- Qualify complete calls including routing, scalar checks and fresh scratch.
  Short/simple controls must meet the explicit nonregression gates in the plan.
  Failure or uncertainty means no promotion; correct values alone are not enough.
- Source bit-length reads use the public base2 API; installed gmp.jl routes this
  to MPZ.sizeinbase, avoiding abs/shift/string BigInt temporaries. Native cost and
  allocation behavior still require measurement; no direct limb-field access.
- Acceptance is bounded to tested component cases. A separate actual presolver
  integration/performance review is required before production deployment.

This request authorizes a plan and independent review only. The next bounded
step is offline candidate/test preparation. Standing short-run authorization
persists, with a separate concrete technical admission before future numerics.
