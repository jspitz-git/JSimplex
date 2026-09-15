# MOI/JuMP Adapter Design

**Date:** 2026-09-15

## Purpose

Add a basic, production-quality MathOptInterface (MOI) adapter to JSimplex so
that users can solve supported linear programs through JuMP while preserving
the solver's parametric numeric types and its existing separation between
production and development dependencies.

This first adapter is intentionally one-shot. It translates a complete MOI
model into a fresh `LinearProblem{T}` for every solve. It does not claim that
the simplex core can update a loaded basis or model incrementally. This keeps
the integration honest and leaves a clean boundary for future primal simplex,
scaling, presolve, warm starts, and branch-and-bound.

## Scope

The adapter supports:

- linear minimization, maximization, and feasibility objectives;
- scalar affine objectives, including an objective constant;
- a single variable as the objective;
- scalar affine constraints in `GreaterThan{T}`, `LessThan{T}`,
  `EqualTo{T}`, and `Interval{T}`;
- variable constraints in the same four numeric sets;
- `Integer` and `ZeroOne` variable constraints;
- optional LP relaxation of integer and binary variables;
- model, variable, and scalar-affine constraint names during translation;
- primal variable values, scalar function values, objective value, solve time,
  simplex iterations, and standard MOI result statuses;
- `Float32`, `Float64`, `BigFloat`, and supported rational coefficient types,
  including `Rational{BigInt}`.

The first version does not support:

- dual values or dual certificates;
- basis statuses or warm starts;
- quadratic or nonlinear objectives or constraints;
- SOS, indicator, complementarity, conic, or semi-domain MOI constraints;
- native incremental model modification in the optimizer;
- a MIP algorithm;
- conflict or sensitivity analysis.

Unsupported function-set pairs must remain unsupported at the MOI boundary so
that JuMP/MOI may apply a bridge where one exists or report the standard MOI
error where none exists.

## Package and Dependency Structure

`MathOptInterface` becomes a direct production dependency of JSimplex because
`JSimplex.Optimizer` is production functionality. The package declares
compatibility with the MOI 1.x API used by the adapter. `JuMP` remains a
development-only dependency in `dev/Project.toml`; it is used for integration
tests and examples but is not loaded by or required to install JSimplex.

The package minor version advances from `0.4.0` to `0.5.0` because the adapter
adds a new public integration API.

The implementation is isolated in `src/moi.jl` and included from
`src/JSimplex.jl`. Following MOI wrapper convention, `Optimizer` is public as
`JSimplex.Optimizer` but is not exported. No JuMP symbols appear in production
source code.

## Optimizer Type and Construction

The public optimizer is parametric:

```julia
JSimplex.Optimizer()                         # Float64
JSimplex.Optimizer{Float32}()
JSimplex.Optimizer{BigFloat}()
JSimplex.Optimizer{Rational{BigInt}}()
```

`Optimizer{T} <: MOI.AbstractOptimizer` stores concrete, typed configuration
fields, the optional last `Solution{T}`, and compact typed result mappings. It
does not store an editable copy of the source model. In particular, it does not
use `Dict{String,Any}` as its option store and it does not expose a mutable
`SolverOptions` object through the MOI API.

The default constructor selects `Float64`. A parameterized constructor rejects
numeric types not supported by the JSimplex core using a clear `ArgumentError`.

## One-Shot MOI Interface

`MOI.supports_incremental_interface(::Optimizer)` returns `false`.
The adapter implements the two-argument operation:

```julia
MOI.optimize!(destination::Optimizer{T}, source::MOI.ModelLike)
```

The surrounding MOI/JuMP caching optimizer owns the editable model. On each
solve, JSimplex receives the full current source model, translates it, solves a
new `LinearProblem{T}`, and returns an MOI index map with `copied == false`.
Only attributes set by optimization are subsequently queried from the one-shot
optimizer.

`MOI.empty!` and `MOI.is_empty` describe the optimizer's result state, not a
stored model. `empty!` clears all solution and index-mapping data but preserves
optimizer attributes, as required by MOI.

## Model Translation

Translation is a distinct internal component rather than being interleaved with
result handling. Given a source model, it performs these steps:

1. Enumerate source variables in a deterministic order and create the MOI index
   map to JSimplex columns.
2. Initialize every variable with the JSimplex default lower bound of zero and
   no upper bound. Intersect every supported variable-bound constraint with
   the current bound. Apply `[0, 1]` for `ZeroOne` and mark `Integer` or
   `ZeroOne` domains without discarding their bounds.
3. Enumerate scalar affine constraints, combine repeated terms, and build a
   `SparseMatrixCSC{T,Int}`. Move the affine constant into the set bounds, so
   `a'x + c in S` becomes the appropriate bounds on `a'x`.
4. Translate a scalar affine or single-variable objective, including its
   constant. Map `MIN_SENSE` and `MAX_SENSE` directly. Represent
   `FEASIBILITY_SENSE` as a zero minimization objective.
5. Preserve the model name, variable names, and scalar-affine row names when
   they are available. A missing name is represented by an empty string.
6. Construct `LinearProblem{T}` and invoke `solve` using freshly materialized
   `SolverOptions{T}` and the configured `relax_integrality` value.

All finite coefficients and bounds must already have coefficient type `T` at
the supported MOI boundary. The adapter does not silently downcast a model from
another coefficient type. MOI/JuMP caching and bridge layers are responsible
for presenting the declared typed function-set pairs.

Multiple bound constraints on a variable are legal and are combined by
intersection. An empty intersection is an invalid model. Multiple `Integer`
constraints are harmless. `Integer` and `ZeroOne` combine to a binary domain.

For `BigFloat`, translation preserves the supplied values; arithmetic and the
solve run in Julia's active `BigFloat` precision, consistent with the direct
JSimplex API. Rational data remains exact throughout translation.

## Supported Function-Set Pairs

For `Optimizer{T}`, the adapter declares native support for:

| Function | Set |
| --- | --- |
| `MOI.VariableIndex` | `MOI.GreaterThan{T}` |
| `MOI.VariableIndex` | `MOI.LessThan{T}` |
| `MOI.VariableIndex` | `MOI.EqualTo{T}` |
| `MOI.VariableIndex` | `MOI.Interval{T}` |
| `MOI.VariableIndex` | `MOI.Integer` |
| `MOI.VariableIndex` | `MOI.ZeroOne` |
| `MOI.ScalarAffineFunction{T}` | `MOI.GreaterThan{T}` |
| `MOI.ScalarAffineFunction{T}` | `MOI.LessThan{T}` |
| `MOI.ScalarAffineFunction{T}` | `MOI.EqualTo{T}` |
| `MOI.ScalarAffineFunction{T}` | `MOI.Interval{T}` |

Supported objective function types are `MOI.VariableIndex` and
`MOI.ScalarAffineFunction{T}`. The translator also handles the absence of an
explicit objective under `MOI.FEASIBILITY_SENSE`.

## User-Facing Parameters

JuMP users configure solver-specific options only by stable names:

```julia
model = JuMP.Model(JSimplex.Optimizer)
JuMP.set_optimizer_attribute(model, "iteration_limit", 50_000)
JuMP.set_optimizer_attribute(model, "primal_tolerance", 1e-8)
JuMP.set_optimizer_attribute(model, "relax_integrality", true)
JuMP.set_time_limit_sec(model, 60.0)
JuMP.set_silent(model)
```

The supported `MOI.RawOptimizerAttribute` names are:

- `relax_integrality` (`Bool`);
- `iteration_limit` (nonnegative `Int`);
- `primal_tolerance` (converted to `T` and validated);
- `dual_tolerance` (converted to `T` and validated);
- `zero_tolerance` (converted to `T` and validated);
- `refactorization_interval` (positive `Int`);
- `algorithm` (`Symbol`, currently only `:dual` is implemented by the core).

Unknown names fail at attribute-setting time with a clear error that lists the
supported names. Invalid values also fail when set, before optimization.

The adapter implements the standard `MOI.Silent` and `MOI.TimeLimitSec`
attributes. A `nothing` time limit means no deadline and maps to the core's
positive infinity. Standard attributes take precedence over inventing parallel
raw names. Internally, the typed option fields are materialized into a new
`SolverOptions{T}` for each solve; users never need to interact with that
structure through JuMP.

Changing any optimizer parameter clears the previous result. `MOI.empty!`
preserves the current parameters, including `Silent` and `TimeLimitSec`.

## Result Interface

The optimizer implements:

- `MOI.SolverName` and `MOI.SolverVersion`;
- `MOI.TerminationStatus` and `MOI.RawStatusString`;
- `MOI.ResultCount`, `MOI.PrimalStatus`, and `MOI.DualStatus`;
- `MOI.ObjectiveValue`;
- `MOI.VariablePrimal`;
- `MOI.ConstraintPrimal` for every supported source constraint;
- `MOI.SolveTimeSec`;
- `MOI.SimplexIterations`.

For an optimal solve, `ResultCount` is one, `PrimalStatus` is
`MOI.FEASIBLE_POINT`, and `DualStatus` is `MOI.NO_SOLUTION`. All other current
JSimplex outcomes have zero results because the core does not expose partial
points or certificates. Result-index bounds are checked with the standard MOI
helper.

`ConstraintPrimal` is the value of the original source function at the returned
primal point. For scalar affine functions this includes the original function
constant. This value is computed into a typed result vector during result
materialization, so the one-shot optimizer does not need to retain the source
model.

The termination mapping is:

| JSimplex status | MOI status |
| --- | --- |
| `OPTIMAL` | `MOI.OPTIMAL` |
| `INFEASIBLE` | `MOI.INFEASIBLE` |
| `UNBOUNDED` | `MOI.DUAL_INFEASIBLE` |
| `ITERATION_LIMIT` | `MOI.ITERATION_LIMIT` |
| `TIME_LIMIT` | `MOI.TIME_LIMIT` |
| `NUMERICAL_ERROR` | `MOI.NUMERICAL_ERROR` |
| `INVALID_MODEL` | `MOI.INVALID_MODEL` |
| `MIP_NOT_SUPPORTED` | `MOI.OTHER_ERROR` |
| `ALGORITHM_NOT_SUPPORTED` | `MOI.INVALID_OPTION` |

`RawStatusString` is the exact explanatory message retained by `Solution`.
A MIP model with `relax_integrality == false` therefore reports
`MOI.OTHER_ERROR`, zero results, and a message directing the user to enable the
LP relaxation. With the option enabled, the same model is translated with its
integer domains intact and the existing core relaxation path solves it as an
LP. This preserves the model information for a future MIP implementation.

## Error Handling and State Rules

Unsupported function-set or objective types use standard MOI unsupported
errors. An invalid optimizer attribute never reaches the solver. Invalid model
data that can be represented by MOI, including an empty intersection of bounds,
is reported as `MOI.INVALID_MODEL` with zero results.

Starting a new solve and changing an optimizer attribute invalidate the old
result before any new work begins. A failed translation cannot leave primal
values from the preceding solve accessible.

The adapter does not add a broad exception handler around the numerical core.
Expected numerical failures continue to be converted by the existing solver
into `NUMERICAL_ERROR`; programming errors and unexpected exceptions remain
visible to developers.

## Testing Strategy

The root test suite tests the production MOI interface without depending on
JuMP. It includes:

- the required optimizer lifecycle and result attributes;
- supported function-set and objective declarations;
- affine constants and repeated terms;
- all supported variable and row bound sets;
- multiple-bound intersection and conflicting bounds;
- minimization, maximization, and feasibility sense;
- names and source-to-result index mapping;
- every status mapping that can be triggered deterministically;
- time and iteration limits;
- parameter validation and result invalidation;
- integer rejection and optional LP relaxation;
- constraint primal values;
- direct typed MOI models for `Float32`, `Float64`, `BigFloat`, and
  `Rational{BigInt}`.

Selected `MOI.Test` cases cover the supported LP contract. Unsupported groups,
including dual, basis, warm-start, nonlinear, conic, MIP-solve, and incremental
modification tests, are excluded explicitly with comments tied to this design's
scope. Exclusions must not be used to hide failures in a declared feature.

The development suite adds JuMP smoke and regression tests for:

- ordinary `JuMP.Model(JSimplex.Optimizer)` construction;
- a bounded LP with objective and constraint value queries;
- model modification followed by a fresh one-shot solve through the cache;
- named solver parameters and standard silent/time-limit attributes;
- MIP rejection followed by LP relaxation;
- generic JuMP/MOI numeric models where JuMP supports the selected coefficient
  type.

JET or inference tests target the typed translation helpers and option
materialization, not the necessarily dynamic generic dispatch at the external
MOI boundary.

## Documentation and Acceptance Criteria

README documentation is updated in English with:

- a minimal JuMP example;
- typed optimizer construction examples;
- the complete supported constraint and attribute list;
- MIP relaxation usage;
- a clear statement that duals, warm starts, native incremental modification,
  and a MIP algorithm are not yet available.

All repository documentation, source comments, docstrings, and test descriptions
introduced by this feature are written in English.

The feature is complete when:

1. the clean production environment can instantiate and load JSimplex with MOI
   but without JuMP, GLPK, JET, or BenchmarkTools;
2. the root tests, selected MOI conformance tests, and development JuMP tests
   pass on Julia 1.13;
3. the supported Float32, Float64, BigFloat, and Rational{BigInt} paths preserve
   their coefficient and result types;
4. a modified JuMP model can be solved again through MOI's cache without stale
   results;
5. an integer JuMP model is rejected by default and its LP relaxation solves
   when `relax_integrality` is enabled;
6. unsupported features are reported through MOI rather than silently changed;
7. existing direct and MPS APIs remain compatible and their tests continue to
   pass.

## Future Evolution

The adapter deliberately targets `LinearProblem{T}`, not simplex workspace
internals. A future presolver and scaler therefore remain transparent to MOI.
When the core gains efficient bound changes, basis warm starts, or repeated LP
solves for branch-and-bound, `Optimizer` can add an incremental interface while
reusing the same translation rules and result mapping. Integer and binary
domains are already retained in the translated model, so enabling a future MIP
driver does not require changing the JuMP model contract.
