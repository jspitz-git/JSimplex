# MA private product scratch for native BigFloat DenseLU

## Intent and evidence

The user requests a concrete plan and independent review, following current-master
profiling. This document specifies a new bounded native DenseLU route; no code or
numerics is authorized by this documentation step. Master is6f68e24, profiling
commit78aeff2. BigFloat256 sc50a has68.150ms ordinary median/120.21MB allocation
traffic; diagnosed FTRAN25.81ms/79calls and BTRAN12.13ms/44calls against69.405ms
whole solve. Sampling is perturbed3.99–8.93x and small sparse LPs do not establish
large-HH benefit. See CURRENT-MASTER-TIME-BREAKDOWN.md for unchanged evidence.

## Chosen design

Reuse **one call-local BigFloat product only**, at current ambient result precision.
Replace an evaluated `a*b` feeding a subtraction by
`MutableArithmetics.operate_to!(product, *, a, b)`, then retain the original ordinary
subtraction, scalar division, array assignment and permutation. No fma/muladd,
MA subtraction/division, in-place mutation of a published result, scalar output
pool, persistent scratch, matrix conversion or numerical scan is introduced.
Ordinary subtraction still creates the new result owner. Never publish product.
This narrower design removes temporary products, not all O(n²) scalar allocations.

Alternatives considered: mutating destination entries would need scalar ownership
proof despite container ownership and risks retained aliases; rejected for this
plan. A product+accumulator optimization could save more allocations but changes
publication/exception concerns; deferred. Global LinearAlgebra or MPFR method
replacement is prohibited. Direct MPFR calls are outside this MA proposal.

`_copy_backend(::DenseLUBackend)=backend`: copied PFI factors share LU data.
All factor/RHS numeric leaves are read-only; destination entries may be replaced
exactly as before but old leaves must stay unchanged. Copied factors, previous
outputs and shared leaves across distinct containers are mandatory tests.

## Boundary and arithmetic

Eligible only: exact Vector{BigFloat} destination and RHS, native
DenseLUBackend{BigFloat,LU{BigFloat,Matrix{BigFloat},Vector{Int}}}, square dimensions
and matching lengths, n>=16, and Base.MPFR.rounding_raw(BigFloat) equal to
Base.MPFR.ROUNDING_MODE[]. All other cases use the original whole `ldiv!` call
BEFORE copying/permuting/writing. n16 is a prospective conservative amortization
boundary (240products across two generic triangular solves), not a measured optimum.
It is frozen before cost qualification; no post-result tuning or case deletion.
No finite, coefficient-support or stored-precision scan. Mixed stored precisions
are allowed only after exact reference tests: both Base multiplication and scratch
output use ambient precision, rather than max operand precision.

Installed Julia1.13 Base binary multiplication allocates BigFloat() and calls
mpfr_mul with rounding_raw(BigFloat). Installed MA1.8.1 SaQfc writes to its output
with ROUNDING_MODE[]. The O(1) equality gate is essential for scoped/nested rounding.
Do not change rounding or ambient precision to qualify a call. Ordinary single-task
numeric execution is assumed; concurrent unsynchronized mutation of global MPFR
state is not newly supported. No new task/thread or persistent rounding cache.

Mirror the current entire native LU solve sequence, including initial copyto!,
forward pivots before L/U, inverse pivots after U'/L', dimension checks, unit
operations, zero-pivot checks and partial writes. Preserve each triangular wrapper's
**actual `istriu` selection**, upper/lower wrapper normalization and indexing.
A UnitLowerTriangular can select the upper path for a diagonal matrix; hardcoding
four mathematical triangular loops is insufficient. The clone must cover all eight
branches of the installed generic_trimatdiv! reached by normalized wrappers,
including nested wrappers. MA-R must enumerate all reachable normalized wrapper
types for the exact eligible LU storage and cover them. If it cannot, reject the
candidate admission; do not introduce a leaf fallback after the whole-call gate. All products including
zero coefficients remain; NaN/Inf/signedzero behavior must match.

Keep dimension/unsupported-type failures on the original path. For eligible manual
LU objects with zero pivots or invalid pivot entries, compare thrown type/message
and visible destination prefix to the original; do not add an earlier pivot scan.
No catch-and-recompute after writes. OOM/resource-exhaustion equivalence is not
claimed: allocation elimination necessarily changes resource-failure timing.

## Work and memory contract

Per eligible complete FTRAN or BTRAN: O(1) metadata/rounding gate, one private
BigFloat allocation at ambient precision, no retained scratch after return.
Existing copy/permutation and `istriu` work remain; do not duplicate these scans.
For conventional n-dimensional nondegenerate branches, n(n-1) products total
(two triangles), and n(n-1)-1 temporary product constructions can be avoided.
This is a source-derived opportunity, not observed allocation events/bytes or
native memory freed. Wrapper normalization, division/subtraction and output
allocation remain. n16/32/64 opportunities239/991/4031; bit complexity scales with
precision. Update-chain work outside the backend is unchanged. Unsupported paths
allocate no MA scratch. Construction/import and future direct dependency costs
are separately measured, not hidden in kernel savings.

## Acceptance and delivery

Plan only now; next deliverable is an isolated unexecuted candidate/reference/tests,
then its own reviewed short numerical admission. Correctness precedes cost.
Do not weaken numerical tolerances, skip coefficients or precision controls.
Promotion requires both whole forward and whole transpose improvement including
scratch initialization, no control regression beyond the predeclared noise budget,
and fresh public-solver integration evidence. Component gains alone do not promote.
No historical probe/driver reruns; CIoff, HHreuse disabled, automation paused.
MA-O/P and rejected Markowitz routes remain unchanged. BigFloat only; Rational
and Float32/64 backend changes are outside this plan.
