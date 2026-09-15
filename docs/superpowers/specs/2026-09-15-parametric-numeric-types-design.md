# Parametric Numeric Types and Type-Stable Solver Core

Date: 2026-09-15

## Goal

Make JSimplex type-stable and parameterize its numerical model, transformations,
factorization, simplex workspace, internal results, and public solution over a
scalar type `T`. The same dual-simplex implementation must support floating-point
arithmetic and exact rational arithmetic without silently converting numerical
data through `Float64`.

The supported scalar families are `AbstractFloat` and `Rational`. Integer-only
input remains convenient, but integers are not a valid simplex working field
because division is not closed over `Integer`.

## Non-goals

This change does not add a primal simplex method, a MIP solver, effective scaling
or presolve, an MOI/JuMP adapter, or a new sparse factorization package. It does
not promise that dense `BigFloat` or rational solves are suitable for large
models. It does not support complex coefficients or integer arithmetic as the
solver's working scalar type.

## Scalar selection

`LinearProblem` infers one common scalar type from the constraint matrix,
objective, objective constant, and finite bound values:

- an inferred `AbstractFloat` or `Rational` type is retained;
- an integer-only common type becomes `Float64`;
- ordinary Julia promotion rules apply to mixed floating and rational input;
- `value_type=T` overrides inference and converts all finite numerical data to
  `T` with validation;
- unsupported requested or inferred working types raise an English
  `ArgumentError`.

Omitted numerical arguments do not participate in inference. In particular,
an omitted objective constant and all constructor defaults are created as
`zero(T)`, `one(T)`, or tagged unbounded values only after `T` has been
selected, so they cannot accidentally force a `Float64` model.

Examples:

```julia
LinearProblem(A32, c32)                              # LinearProblem{Float32}
LinearProblem(Abig, cbig)                            # LinearProblem{BigFloat}
LinearProblem(Arational, crational)                  # rational T is retained
LinearProblem(Ainteger, cinteger)                    # LinearProblem{Float64}
LinearProblem(Ainteger, cinteger;
              value_type=Rational{BigInt})           # exact rational model
```

MPS text has no native Julia scalar type. `read_mps(path)` therefore continues
to return `LinearProblem{Float64}`, while
`read_mps(path; value_type=Rational{BigInt})` requests exact parsing. The public
documentation recommends `Rational{BigInt}` for exact MPS work; fixed-width
rational numerator types retain Julia's normal overflow limitations.

## Bounds without floating-point infinity

Rational numbers cannot represent `Inf`. Bounds therefore use a concrete tagged
value rather than mixing scalar types or storing `Union{T,Float64}`:

```julia
struct Bound{T<:Real}
    value::T
    bounded::Bool
end
```

An unbounded value stores `zero(T)` as inert payload and has `bounded == false`.
Its direction is determined by whether it appears in a lower- or upper-bound
array. The validated constructors prevent a bound marked finite from containing
a non-finite floating value.

The public API includes `Bound`, `isfinite(::Bound)`, and
`bound_value(::Bound)`. `bound_value` returns `T` for a finite bound and throws
an English `ArgumentError` for an unbounded value.

`LinearProblem{T}` stores each bound collection as `Vector{Bound{T}}`. Public
constructors accept:

- a finite real value;
- `Bound` values convertible to `T`;
- `nothing` for an unbounded side;
- correctly signed `-Inf` lower bounds and `Inf` upper bounds for compatibility
  with floating-point callers.

Incorrectly signed infinities remain invalid. Floating infinities are normalized
to unbounded `Bound{T}` values even when `T` is rational. Type inference ignores
`nothing` and correctly signed infinite sentinels and includes all finite bound
values.

Defaults remain mathematically unchanged: row lower and upper bounds are
unbounded, column lower bounds are `zero(T)`, and column upper bounds are
unbounded. Binary bounds are intersected with `[zero(T), one(T)]`. Public
examples will show both the new `nothing` representation and the accepted
floating-point compatibility syntax.

## Parametric public contracts

The primary public structures become:

```julia
LinearProblem{T}
SolverOptions{T}
Solution{T}
```

`LinearProblem{T}` owns a `SparseMatrixCSC{T,Int}`, `Vector{T}` objective data,
`Vector{Bound{T}}` bounds, and existing non-numerical metadata. Sparse index
storage remains `Int`; this change parameterizes numerical values, not index
width.

`Solution{T}` contains `Union{Nothing,T}` objective data and
`Union{Nothing,Vector{T}}` primal data. Every termination path from a solve of a
`LinearProblem{T}` returns the same concrete `Solution{T}` type. As before, only
`OPTIMAL` exposes a primal vector and objective value.

`SolveStatistics` remains non-parametric because counters are `Int` and elapsed
wall-clock time is `Float64` rather than model arithmetic.

`SolverOptions(T; ...)` constructs numerical tolerances in `T`.
`SolverOptions()` remains shorthand for `SolverOptions(Float64; ...)`. The
floating defaults retain the existing absolute values: primal and dual
tolerances are `1 / 10^7`, and zero tolerance is `1 / 10^12`, evaluated in `T`.
If converting one of these positive defaults to a low-precision floating type
would produce zero, it is clamped to `nextfloat(zero(T))`. The rational defaults
are exactly zero. Iteration and refactorization limits remain `Int`; the time
limit remains `Float64` seconds.

`solve(problem; options=nothing)` creates defaults for the problem's `T`.
Supplying `SolverOptions{S}` explicitly converts its numerical tolerances to
`T`, validates the result, and leaves non-numerical options unchanged. This
preserves the familiar `SolverOptions()` call while preventing the omitted
default from injecting floating tolerances into an exact solve.

## Internal type structure

All numerical containers in the solve path carry `T`:

- `Scaling{T}`;
- `PackedEta{T}`;
- `PFIFactorization{T,F}`;
- `SimplexWorkspace{T,P,O,F}` or an equivalent fully concrete parameterization;
- `DualRunResult{T}`;
- typed MPS records and accumulators;
- typed presolve and postsolve results.

The current `PFIFactorization.base::Any` is removed. Hot-path structures must
not contain `Any`, abstractly typed numerical fields, or containers whose
element type erases `T`.

`PresolveResult` parameterizes both its problem and postsolve-stack
representation. The identity implementation uses a concrete empty tuple rather
than `Vector{AbstractPostsolveStep}`. Future presolvers may provide a concrete
tuple or a concrete tagged-union vector without changing the public solve
contract.

Functions allocate through `zeros(T, ...)`, `ones(T, ...)`, `zero(T)`, and
`one(T)`. Decimal algorithm constants are constructed in `T` from integer
ratios, never by first materializing a `Float64` value.

## Arithmetic policy

An internal compile-time trait distinguishes exact rational arithmetic from
inexact floating arithmetic. It changes numerical policy, not algorithm flow.

For `Rational`:

- default primal, dual, and zero tolerances are zero;
- the Harris safety pivot cutoff is zero;
- recession-ray roundoff allowance is zero;
- feasibility, optimality, and ray checks use exact comparisons;
- every pivot, eta update, price, reduced cost, objective, and returned primal
  remains rational.

Callers may explicitly supply nonzero rational tolerances, but the exact
defaults never originate from a floating literal.

For `AbstractFloat`:

- the current absolute tolerance semantics are retained in `T`;
- the Harris safety cutoff is the current `1 / 10^7` expressed in `T`;
- recession certification uses `eps(T)` and the existing per-row dot-product
  error-envelope design;
- all non-finite iterate and result checks remain active.

The phase-I artificial bound magnitude, DSE weight floor, signs, zeros, and all
other constants are constructed in `T`. Time measurement remains independent
of this policy.

MPS rational parsing and builder arithmetic use `Rational{BigInt}`
intermediates, followed by checked conversion to the requested rational type.
Overflow while constructing a fixed-width rational model therefore becomes a
source-aware `MPSParseError`. Subsequent arithmetic on a caller-selected
fixed-width `Rational{I}` retains Julia's ordinary fixed-width overflow
behavior; arbitrary-size exact intermediates are guaranteed only for
`Rational{BigInt}`, which is the documented and tested exact type.

## Factorization boundary

The product-form update layer is parameterized independently of its initial
basis backend:

```text
SimplexWorkspace{T,F}
        |
PFIFactorization{T,F}
        |
        +-- T == Float64  -> sparse UMFPACK LU
        +-- other T       -> generic dense LinearAlgebra LU
        +-- zero rows     -> concrete empty backend
```

`forward_solve`, `transpose_solve`, `replace_column!`, and `refactorize!` form
the backend boundary. They return vectors in `T`, never the backend library's
implicit promotion type. Refactorization preserves the concrete backend type.

UMFPACK remains an implementation detail selected only for `Float64`. The
generic dense path preserves `Float32`, `BigFloat`, and rational arithmetic and
provides correctness coverage until a future generic sparse backend replaces
it. Backend choice is not exposed as a public option in this change.

Zero-row models use a concrete no-op factorization rather than `Any` or a dense
floating placeholder. The zero-row fast solve remains valid for every supported
`T`.

## Typed MPS parsing

`BoundRecord{T}` and the completed `MPSAccumulator{T}` retain values in the
requested scalar type. Fixed/free detection, source locations, named sets,
objective selection, range semantics, bounds, markers, and domain composition
remain unchanged.

For floating `T`, normalized `D` exponents are parsed directly with `tryparse(T,
token)` and must be finite.

For rational `T`, the parser accepts the existing MPS decimal grammar, including
optional sign, decimal point, and `E`/`D` exponent. It constructs an integer
significand and a power-of-ten numerator or denominator. Parsing, duplicate
aggregation, and derived range arithmetic use `Rational{BigInt}` scratch values;
each completed value is range-checked when converted to `T`. This keeps the
stored model typed while making construction overflow detectable for
fixed-width rational types. It never parses through `Float64` or `BigFloat`.
Examples:

```text
1.25   -> 5//4
-2e-3  -> -1//500
3D+2   -> 300//1
```

Malformed values, non-finite floating tokens, conversion overflow, duplicate
aggregation overflow, and derived RANGES overflow retain source-aware English
`MPSParseError` diagnostics.

## Transformations and future integrations

Identity presolve, identity scaling, integrality relaxation, objective-sense
normalization, unscale, and postsolve preserve `T` and the tagged bounds. The LP
relaxation continues to include zero for semi domains and clip binary domains to
zero and one.

The tagged bound representation maps directly to future MOI bound sets without
requiring artificial floating infinities. Future primal simplex, scaling,
presolve, and MIP nodes will share the same `LinearProblem{T}` and workspace
contracts. Algorithms that require inexact arithmetic must declare that
restriction rather than silently converting exact models.

## Type-stability verification

Mandatory package tests use `@inferred` on representative calls to:

- model and option construction;
- bound access;
- fixed/free MPS loading for `Float64` and `Rational{BigInt}`;
- relaxation, presolve, scaling, and postsolve;
- basis factorization and eta solves;
- nonempty workspace initialization and recomputation;
- bounded, infeasible, unbounded, and resource-limited public solves.

Tests also inspect hot structure field types to reject `Any` and abstract
numerical containers. `Test.detect_ambiguities` checks the public module after
the new conversion constructors are added.

JET is added only to `dev/Project.toml`. Focused `JET.@test_opt` checks cover
representative nonempty `Float64` and `Rational{BigInt}` solve kernels. JET is
part of development/extended validation and never becomes a production or
mandatory package-test dependency.

Functional tests solve equivalent small models with `Float32`, `Float64`,
`BigFloat`, and `Rational{BigInt}`. They verify result element types, exact
rational optima, multiple pivots, refactorization, MIP relaxation, objective
constants and senses, infeasible/unbounded statuses, and iteration/time limits.
Rational MPS fixtures cover exact decimals and exponents. Existing Float64
parser, solver, AFIRO, and development GLPK regressions remain green.

`BigFloat` examples use `setprecision` around model construction and solve;
documentation states that BigFloat precision is controlled by Julia's ambient
precision context.

## Error handling and diagnostics

Direct model conversion failures throw `ArgumentError`. MPS conversion failures
remain `MPSParseError` with source, line, and section. Unsupported scalar types
are rejected before solver state is constructed. Expected backend singularity,
zero-pivot, and non-finite floating arithmetic map to `NUMERICAL_ERROR`.
Programming errors, caller logger/callback exceptions, and Julia's ordinary
fixed-width integer overflow behavior are not hidden by broad catches.

All diagnostics, comments, tests, docstrings, and documentation remain English.
The production package gains no dependency.

## Compatibility and release

The default MPS and integer-only direct-construction behavior remains
`Float64`. Existing callers may continue passing floating `Inf` sentinels to
constructors. The intentional breaking change is that stored bound fields now
contain `Bound{T}` values instead of floating numbers. README migration guidance
will show `nothing`, `isfinite(bound)`, and `bound_value(bound)`.

The package version increases from `0.3.0` to `0.4.0`. Development tooling gains
JET, while GLPK and BenchmarkTools remain isolated from the root project.

## Acceptance criteria

The change is complete when:

1. the supported public and hot internal structures are concretely parameterized
   and contain no `Any` numerical storage;
2. representative public and internal calls pass `@inferred` checks;
3. `Float32`, `Float64`, `BigFloat`, and `Rational{BigInt}` small LPs solve with
   their input scalar type preserved through the result;
4. rational MPS decimals and exponents are represented exactly;
5. unbounded bounds work without floating infinity in rational models;
6. rational default solves use exact zero tolerances and no roundoff allowance;
7. Float64 retains sparse UMFPACK behavior and existing AFIRO results;
8. JET development checks have no actionable runtime-dispatch finding in the
   selected hot paths;
9. all package and development tests pass on Julia 1.13;
10. production dependencies remain limited to the current standard libraries;
11. README, docstrings, and examples describe the new bound and scalar APIs in
    English; and
12. the committed worktree is clean and contains no generated manifests.
