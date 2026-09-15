# MOI/JuMP Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a typed, one-shot MathOptInterface optimizer that lets JuMP solve JSimplex-supported LPs and optionally solve the LP relaxation of integer models.

**Architecture:** `JSimplex.Optimizer{T}` is a non-incremental MOI optimizer. MOI/JuMP owns the editable cache; each two-argument `MOI.optimize!` call translates the complete source model into a fresh `LinearProblem{T}`, calls the existing solver, and stores only typed result mappings. Translation, optimizer attributes, and result access live in focused files behind `src/moi.jl`.

**Tech Stack:** Julia 1.13, JSimplex parametric LP core, MathOptInterface 1.53+, JuMP 1.31+ in the development environment, `Test`, MOI.Test, and JET.

**Spec:** `docs/superpowers/specs/2026-09-15-moi-jump-adapter-design.md`

## Global Constraints

- All repository documentation, comments, docstrings, and test descriptions added by this work must be in English.
- `MathOptInterface` is the only new production dependency; JuMP remains in `dev/Project.toml` and must not appear in production source or the root dependency list.
- The package requires Julia 1.13 and advances from version `0.4.0` to `0.5.0`.
- `JSimplex.Optimizer` is public but not exported; the existing direct and MPS APIs remain compatible.
- The adapter must not claim native incremental modification: `MOI.supports_incremental_interface` returns `false` and optimization uses `MOI.optimize!(dest, src)` with `copied == false`.
- Free MOI variables translate to explicit unbounded lower and upper column bounds, not the direct `LinearProblem` constructor's default lower bound of zero.
- Supported coefficient types remain `Float32`, `Float64`, `BigFloat`, and rational types supported by the core, including `Rational{BigInt}`.
- Named optimizer parameters use concrete typed fields; do not use `Dict{String,Any}` or expose `SolverOptions` through the MOI/JuMP API.
- Integer and binary domains are retained. They are rejected by default and solved only as an LP relaxation when `relax_integrality = true`; no MIP solver is added.
- Do not expose dual values, basis statuses, warm starts, quadratic/nonlinear constraints, SOS, indicators, semi-domain MOI constraints, or native incremental updates in this release.
- Keep the repository root free of a committed `Manifest.toml`; `dev/Manifest.toml` remains ignored.

## File Structure

- `Project.toml`: add the production MOI dependency and compatibility, and set version `0.5.0`.
- `src/JSimplex.jl`: include the MOI adapter entry point without exporting `Optimizer`.
- `src/moi.jl`: import MOI and include the focused adapter components.
- `src/moi/optimizer.jl`: define `Optimizer{T}`, construction, lifecycle, type support declarations, and typed result clearing.
- `src/moi/attributes.jl`: implement standard and named optimizer attributes and typed option materialization.
- `src/moi/translation.jl`: translate variables, bounds, domains, affine rows, objectives, names, and MOI indices into `LinearProblem{T}`.
- `src/moi/results.jl`: run one-shot optimization and implement result/status attributes.
- `test/moi/optimizer_tests.jl`: root tests for construction, lifecycle, declarations, and attributes.
- `test/moi/translation_tests.jl`: root tests for exact model translation and invalid-model detection.
- `test/moi/result_tests.jl`: root tests for solve behavior, result mappings, statuses, numeric types, and relaxation.
- `test/moi/conformance_tests.jl`: selected MOI.Test coverage for the declared LP interface.
- `test/runtests.jl`: include the MOI test files.
- `dev/Project.toml`: add JuMP as a development-only dependency and compatibility bound.
- `dev/tests/jump_tests.jl`: JuMP construction, re-solve, attributes, relaxation, and generic numeric smoke tests.
- `dev/tests/jet_tests.jl`: add inference/JET checks for typed adapter helpers.
- `dev/tests/runtests.jl`: include the JuMP integration tests.
- `README.md`: document JuMP usage, typed construction, supported constraints and attributes, relaxation, and limitations.

---

### Task 1: Production Dependency and Typed Optimizer Lifecycle

**Files:**
- Modify: `Project.toml`
- Modify: `src/JSimplex.jl`
- Create: `src/moi.jl`
- Create: `src/moi/optimizer.jl`
- Create: `test/moi/optimizer_tests.jl`
- Modify: `test/runtests.jl`

**Interfaces:**
- Consumes: `SolverOptions(::Type{T})`, `Solution{T}`, and `_supported_value_type(T)` from the existing core.
- Produces: `Optimizer{T} <: MOI.AbstractOptimizer`, `Optimizer()`, `_clear_result!(::Optimizer)`, MOI lifecycle methods, and native support declarations used by every later task.

- [ ] **Step 1: Add the dependency declaration and write failing lifecycle tests**

Update `Project.toml` to contain:

```toml
version = "0.5.0"

[deps]
LinearAlgebra = "37e2e46d-f89d-539d-b4ee-838fcccc9c8e"
Logging = "56ddb016-857b-54e1-b83d-db4d58db5568"
MathOptInterface = "b8f27783-ece8-5eb3-8dc8-9495eed66fee"
SparseArrays = "2f01184e-e22b-5df5-ae63-d93ebab69eaf"

[compat]
MathOptInterface = "1.53"
julia = "1.13"
```

Create `test/moi/optimizer_tests.jl` with the initial contract:

```julia
import MathOptInterface as MOI

@testset "MOI optimizer construction and lifecycle" begin
    optimizer = JSimplex.Optimizer()
    @test optimizer isa JSimplex.Optimizer{Float64}
    @test JSimplex.Optimizer{Float32}() isa JSimplex.Optimizer{Float32}
    @test JSimplex.Optimizer{BigFloat}() isa JSimplex.Optimizer{BigFloat}
    @test JSimplex.Optimizer{Rational{BigInt}}() isa
          JSimplex.Optimizer{Rational{BigInt}}
    @test_throws ArgumentError JSimplex.Optimizer{Int}()
    @test !MOI.supports_incremental_interface(optimizer)
    @test MOI.is_empty(optimizer)
    @test sprint(summary, optimizer) == "JSimplex optimizer (Float64)"
    MOI.empty!(optimizer)
    @test MOI.is_empty(optimizer)
end
```

Include it inside the top-level test set in `test/runtests.jl`:

```julia
include("moi/optimizer_tests.jl")
```

- [ ] **Step 2: Run the lifecycle test and confirm the missing API failure**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: FAIL because `JSimplex.Optimizer` is not defined.

- [ ] **Step 3: Implement the typed optimizer skeleton**

Create `src/moi.jl`:

```julia
import MathOptInterface as MOI

include("moi/optimizer.jl")
include("moi/attributes.jl")
include("moi/translation.jl")
include("moi/results.jl")
```

Initially create empty `src/moi/attributes.jl`, `src/moi/translation.jl`, and
`src/moi/results.jl` files so that the entry point loads. Add this after
`include("solver.jl")` in `src/JSimplex.jl`:

```julia
include("moi.jl")
```

Create `src/moi/optimizer.jl` around these concrete fields and lifecycle
methods:

```julia
mutable struct Optimizer{T<:Real} <: MOI.AbstractOptimizer
    primal_tolerance::T
    dual_tolerance::T
    zero_tolerance::T
    iteration_limit::Int
    time_limit::Float64
    refactorization_interval::Int
    algorithm::Symbol
    silent::Bool
    relax_integrality::Bool
    solution::Union{Nothing,Solution{T}}
    constraint_primals::Vector{T}
end

function Optimizer{T}() where {T<:Real}
    _supported_value_type(T) ||
        throw(ArgumentError("unsupported optimizer value type $T"))
    options = SolverOptions(T)
    return Optimizer{T}(
        options.primal_tolerance,
        options.dual_tolerance,
        options.zero_tolerance,
        options.iteration_limit,
        options.time_limit,
        options.refactorization_interval,
        options.algorithm,
        false,
        false,
        nothing,
        T[],
    )
end

Optimizer() = Optimizer{Float64}()

function _clear_result!(optimizer::Optimizer{T}) where {T}
    optimizer.solution = nothing
    empty!(optimizer.constraint_primals)
    return
end

MOI.supports_incremental_interface(::Optimizer) = false
MOI.is_empty(optimizer::Optimizer) = isnothing(optimizer.solution) &&
                                     isempty(optimizer.constraint_primals)
MOI.empty!(optimizer::Optimizer) = _clear_result!(optimizer)

function Base.summary(io::IO, ::Optimizer{T}) where {T}
    return print(io, "JSimplex optimizer ($T)")
end
```

Add type-specific `MOI.supports_constraint` methods for the exact pairs in the
specification and `MOI.supports` for objective functions:

```julia
const _MOINumericSet{T} = Union{
    MOI.GreaterThan{T},
    MOI.LessThan{T},
    MOI.EqualTo{T},
    MOI.Interval{T},
}

function MOI.supports_constraint(
    ::Optimizer{T},
    ::Type{MOI.VariableIndex},
    ::Type{<:_MOINumericSet{T}},
) where {T}
    return true
end

function MOI.supports_constraint(
    ::Optimizer,
    ::Type{MOI.VariableIndex},
    ::Type{<:Union{MOI.Integer,MOI.ZeroOne}},
)
    return true
end

function MOI.supports_constraint(
    ::Optimizer{T},
    ::Type{MOI.ScalarAffineFunction{T}},
    ::Type{<:_MOINumericSet{T}},
) where {T}
    return true
end

MOI.supports(
    ::Optimizer{T},
    ::MOI.ObjectiveFunction{MOI.ScalarAffineFunction{T}},
) where {T} = true
MOI.supports(
    ::Optimizer,
    ::MOI.ObjectiveFunction{MOI.VariableIndex},
) = true
```

- [ ] **Step 4: Extend lifecycle tests to cover all declarations and run them**

Add assertions for every supported pair and representative unsupported pairs:

```julia
@test MOI.supports_constraint(
    optimizer,
    MOI.VariableIndex,
    MOI.Interval{Float64},
)
@test MOI.supports_constraint(
    optimizer,
    MOI.ScalarAffineFunction{Float64},
    MOI.EqualTo{Float64},
)
@test MOI.supports_constraint(optimizer, MOI.VariableIndex, MOI.Integer)
@test !MOI.supports_constraint(
    optimizer,
    MOI.ScalarQuadraticFunction{Float64},
    MOI.LessThan{Float64},
)
@test !MOI.supports_constraint(
    optimizer,
    MOI.VectorOfVariables,
    MOI.Nonnegatives,
)
```

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: all existing tests and the new optimizer lifecycle tests PASS.

- [ ] **Step 5: Commit the lifecycle slice**

```bash
git add Project.toml src/JSimplex.jl src/moi.jl src/moi test/runtests.jl test/moi/optimizer_tests.jl
git commit -m "feat: add typed MOI optimizer skeleton"
```

---

### Task 2: Named and Standard Optimizer Attributes

**Files:**
- Modify: `src/moi/attributes.jl`
- Modify: `test/moi/optimizer_tests.jl`

**Interfaces:**
- Consumes: `Optimizer{T}` and `_clear_result!` from Task 1; `SolverOptions(T; ...)` for authoritative validation.
- Produces: `_solver_options(::Optimizer{T})::SolverOptions{T}`, standard MOI attributes, and the seven stable raw parameter names used by optimization and JuMP.

- [ ] **Step 1: Write failing tests for standard and named attributes**

Append test sets that exercise names, types, validation, and preservation across
`empty!`:

```julia
@testset "MOI optimizer attributes" begin
    optimizer = JSimplex.Optimizer{Float32}()
    @test MOI.get(optimizer, MOI.SolverName()) == "JSimplex"
    @test MOI.get(optimizer, MOI.SolverVersion()) == "0.5.0"

    @test MOI.supports(optimizer, MOI.Silent())
    @test !MOI.get(optimizer, MOI.Silent())
    MOI.set(optimizer, MOI.Silent(), true)
    @test MOI.get(optimizer, MOI.Silent())

    @test MOI.supports(optimizer, MOI.TimeLimitSec())
    @test MOI.get(optimizer, MOI.TimeLimitSec()) === nothing
    MOI.set(optimizer, MOI.TimeLimitSec(), 2)
    @test MOI.get(optimizer, MOI.TimeLimitSec()) === 2.0
    MOI.set(optimizer, MOI.TimeLimitSec(), nothing)
    @test MOI.get(optimizer, MOI.TimeLimitSec()) === nothing

    values = Dict(
        "relax_integrality" => true,
        "iteration_limit" => 19,
        "primal_tolerance" => Float32(1e-5),
        "dual_tolerance" => Float32(2e-5),
        "zero_tolerance" => Float32(3e-6),
        "refactorization_interval" => 7,
        "algorithm" => :dual,
    )
    for (name, value) in values
        attr = MOI.RawOptimizerAttribute(name)
        @test MOI.supports(optimizer, attr)
        MOI.set(optimizer, attr, value)
        @test MOI.get(optimizer, attr) == value
    end
    @test JSimplex._solver_options(optimizer) isa SolverOptions{Float32}
    @test_throws MOI.UnsupportedAttribute MOI.set(
        optimizer,
        MOI.RawOptimizerAttribute("unknown_parameter"),
        1,
    )
    @test_throws ArgumentError MOI.set(
        optimizer,
        MOI.RawOptimizerAttribute("iteration_limit"),
        -1,
    )

    MOI.empty!(optimizer)
    @test MOI.get(optimizer, MOI.Silent())
    @test MOI.get(optimizer, MOI.RawOptimizerAttribute("iteration_limit")) == 19
end
```

- [ ] **Step 2: Run the attribute tests and verify missing-method failures**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: FAIL on missing `MOI.get`, `MOI.set`, or `MOI.supports` methods.

- [ ] **Step 3: Implement concrete named attribute dispatch**

In `src/moi/attributes.jl`, define one source of truth for supported names and
materialize core options without exposing the core structure:

```julia
const _RAW_OPTIMIZER_ATTRIBUTES = (
    "relax_integrality",
    "iteration_limit",
    "primal_tolerance",
    "dual_tolerance",
    "zero_tolerance",
    "refactorization_interval",
    "algorithm",
)

function _solver_options(optimizer::Optimizer{T})::SolverOptions{T} where {T}
    return SolverOptions(
        T;
        primal_tolerance=optimizer.primal_tolerance,
        dual_tolerance=optimizer.dual_tolerance,
        zero_tolerance=optimizer.zero_tolerance,
        iteration_limit=optimizer.iteration_limit,
        time_limit=optimizer.time_limit,
        refactorization_interval=optimizer.refactorization_interval,
        log_level=optimizer.silent ? Logging.BelowMinLevel : Logging.Debug,
        algorithm=optimizer.algorithm,
    )
end

MOI.get(::Optimizer, ::MOI.SolverName) = "JSimplex"
MOI.get(::Optimizer, ::MOI.SolverVersion) = string(pkgversion(JSimplex))
MOI.supports(::Optimizer, ::MOI.Silent) = true
MOI.supports(::Optimizer, ::MOI.TimeLimitSec) = true

function MOI.set(optimizer::Optimizer, ::MOI.Silent, value::Bool)
    optimizer.silent = value
    _clear_result!(optimizer)
    return
end

MOI.get(optimizer::Optimizer, ::MOI.Silent) = optimizer.silent
MOI.get(optimizer::Optimizer, ::MOI.TimeLimitSec) =
    isinf(optimizer.time_limit) ? nothing : optimizer.time_limit
```

Implement `TimeLimitSec` and every named setter by constructing a candidate
`SolverOptions{T}` with all current fields plus the proposed new value, then
copying its validated fields back into the optimizer. `relax_integrality` must
accept only `Bool`; `algorithm` must accept only `Symbol`; integer parameters
must reject non-integral and overflowing values. Every successful setter calls
`_clear_result!`.

Unknown raw names must use:

```julia
throw(MOI.UnsupportedAttribute(
    attr,
    "Supported JSimplex optimizer attributes are: " *
    join(_RAW_OPTIMIZER_ATTRIBUTES, ", "),
))
```

- [ ] **Step 4: Run attribute and full root tests**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: all tests PASS, including exact conversion of `Float32` attributes
and parameter preservation across `MOI.empty!`.

- [ ] **Step 5: Commit the attribute slice**

```bash
git add src/moi/attributes.jl test/moi/optimizer_tests.jl
git commit -m "feat: add named MOI solver parameters"
```

---

### Task 3: Variable, Bound, Domain, and Index Translation

**Files:**
- Modify: `src/moi/translation.jl`
- Create: `test/moi/translation_tests.jl`
- Modify: `test/runtests.jl`

**Interfaces:**
- Consumes: the support declarations from Task 1 and MOI source model queries.
- Produces: `MOIScalarEvaluation{T}`, `MOIColumnData{T}`, and `_collect_moi_columns(::Optimizer{T}, source)::MOIColumnData{T}` for full translation in Task 4.

- [ ] **Step 1: Write failing tests for free variables and bound intersection**

Create a `MOI.Utilities.Model{T}` with free and bounded variables,
integer/binary markers, and names. Assert the exact typed column data:

```julia
@testset "MOI column translation" begin
    source = MOI.Utilities.Model{Float64}()
    x = MOI.add_variables(source, 6)
    MOI.set(source, MOI.VariableName(), x[1], "free")
    MOI.add_constraint(source, x[2], MOI.GreaterThan(-1.0))
    MOI.add_constraint(source, x[2], MOI.LessThan(3.0))
    MOI.add_constraint(source, x[3], MOI.Integer())
    MOI.add_constraint(source, x[4], MOI.ZeroOne())
    MOI.add_constraint(source, x[5], MOI.EqualTo(2.0))
    MOI.add_constraint(source, x[6], MOI.Interval(-4.0, 5.0))

    columns = JSimplex._collect_moi_columns(JSimplex.Optimizer(), source)
    @test !isfinite(columns.lower[1])
    @test !isfinite(columns.upper[1])
    @test bound_value(columns.lower[2]) == -1.0
    @test bound_value(columns.upper[2]) == 3.0
    @test columns.domains == [
        CONTINUOUS,
        CONTINUOUS,
        INTEGER,
        BINARY,
        CONTINUOUS,
        CONTINUOUS,
    ]
    @test bound_value(columns.lower[4]) == 0.0
    @test bound_value(columns.upper[4]) == 1.0
    @test bound_value(columns.lower[5]) == 2.0
    @test bound_value(columns.upper[5]) == 2.0
    @test bound_value(columns.lower[6]) == -4.0
    @test bound_value(columns.upper[6]) == 5.0
    @test columns.names == ["free", "", "", "", "", ""]
    @test columns.index_map[x[1]] == MOI.VariableIndex(1)
end
```

Add a conflicting-bound case and assert
`columns.error == "column lower bound exceeds column upper bound for variable 1"`.

- [ ] **Step 2: Run the translation test and confirm the helper is missing**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: FAIL because `_collect_moi_columns` is not defined.

- [ ] **Step 3: Implement typed column data and intersection helpers**

Use these data types in `src/moi/translation.jl`:

```julia
struct MOIScalarEvaluation{T<:Real}
    columns::Vector{Int}
    coefficients::Vector{T}
    constant::T
end

struct MOIColumnData{T<:Real}
    index_map::MOI.Utilities.IndexMap
    lower::Vector{Bound{T}}
    upper::Vector{Bound{T}}
    domains::Vector{VariableDomain}
    names::Vector{String}
    evaluations::Vector{MOIScalarEvaluation{T}}
    error::Union{Nothing,String}
end
```

Implement `_collect_moi_columns` by enumerating
`MOI.get(source, MOI.ListOfVariableIndices())`, assigning destination
`MOI.VariableIndex(column)`, and explicitly filling both bound vectors with
`_unbounded_bound(T)`. For every supported `VariableIndex` constraint, assign
a destination `ConstraintIndex{F,S}` whose value is
`length(evaluations) + 1`, add `MOIScalarEvaluation(T[column], T[one(T)],
zero(T))`, and intersect the corresponding bound or domain.

Use typed set dispatch:

```julia
_moi_set_bounds(set::MOI.GreaterThan{T}) where {T} =
    (Bound(set.lower), _unbounded_bound(T))
_moi_set_bounds(set::MOI.LessThan{T}) where {T} =
    (_unbounded_bound(T), Bound(set.upper))
_moi_set_bounds(set::MOI.EqualTo{T}) where {T} =
    (Bound(set.value), Bound(set.value))
_moi_set_bounds(set::MOI.Interval{T}) where {T} =
    (Bound(set.lower), Bound(set.upper))
```

Intersections take `max` of finite lower values and `min` of finite upper
values while preserving unbounded tags. `ZeroOne` intersects with `[0, 1]` and
sets `BINARY`; `Integer` changes `CONTINUOUS` to `INTEGER` but leaves `BINARY`
unchanged. Record the first conflict in the typed `error` field.

- [ ] **Step 4: Run translation and regression tests**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: all tests PASS; the free variable has two unbounded tags and is not
silently constrained to be nonnegative.

- [ ] **Step 5: Commit the column translation slice**

```bash
git add src/moi/translation.jl test/moi/translation_tests.jl test/runtests.jl
git commit -m "feat: translate MOI variable domains and bounds"
```

---

### Task 4: Affine Rows, Objectives, Names, and Complete LinearProblem Translation

**Files:**
- Modify: `src/moi/translation.jl`
- Modify: `test/moi/translation_tests.jl`

**Interfaces:**
- Consumes: `MOIColumnData{T}` and `MOIScalarEvaluation{T}` from Task 3.
- Produces: `MOITranslation{T}` and `_translate_moi_model(::Optimizer{T}, source)::MOITranslation{T}` consumed by one-shot optimization.

- [ ] **Step 1: Write a failing exact translation test**

Build a rational MOI model whose repeated terms, affine constants, interval,
objective constant, sense, and names all have observable translations:

```julia
@testset "MOI affine model translation" begin
    T = Rational{BigInt}
    source = MOI.Utilities.Model{T}()
    x = MOI.add_variables(source, 2)
    MOI.set(source, MOI.Name(), "typed model")
    MOI.set(source, MOI.VariableName(), x[1], "x")
    f = MOI.ScalarAffineFunction(
        MOI.ScalarAffineTerm{T}[
            MOI.ScalarAffineTerm(T(2), x[1]),
            MOI.ScalarAffineTerm(T(3), x[2]),
            MOI.ScalarAffineTerm(T(-1), x[1]),
        ],
        T(5),
    )
    ci = MOI.add_constraint(source, f, MOI.Interval(T(7), T(11)))
    MOI.set(source, MOI.ConstraintName(), ci, "range")
    objective = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(T(4), x[2])],
        T(3),
    )
    MOI.set(source, MOI.ObjectiveSense(), MOI.MAX_SENSE)
    MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)

    translated = JSimplex._translate_moi_model(
        JSimplex.Optimizer{T}(),
        source,
    )
    @test translated.error === nothing
    problem = something(translated.problem)
    @test problem isa LinearProblem{T}
    @test Matrix(problem.A) == T[1 3]
    @test bound_value(problem.row_lower[1]) == T(2)
    @test bound_value(problem.row_upper[1]) == T(6)
    @test problem.objective == T[0, 4]
    @test problem.objective_constant == T(3)
    @test problem.objective_sense == MAX_SENSE
    @test problem.name == "typed model"
    @test problem.column_names == ["x", ""]
    @test problem.row_names == ["range"]
    @test translated.index_map[ci].value == 1
end
```

Add a feasibility-sense case and assert a zero minimization objective. Add all
four scalar affine set types and assert that the function constant is
subtracted from the correct lower and upper sides. Add a separate
`MOI.VariableIndex` objective and assert that it produces a unit coefficient in
the selected objective column.

- [ ] **Step 2: Run the model translation tests and verify failure**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: FAIL because `_translate_moi_model` and `MOITranslation` are missing.

- [ ] **Step 3: Implement the complete typed translation**

Define:

```julia
struct MOITranslation{T<:Real}
    problem::Union{Nothing,LinearProblem{T}}
    index_map::MOI.Utilities.IndexMap
    evaluations::Vector{MOIScalarEvaluation{T}}
    error::Union{Nothing,String}
end
```

Before reading data, iterate
`MOI.get(source, MOI.ListOfConstraintTypesPresent())` and throw
`MOI.UnsupportedConstraint{F,S}` for any pair not declared by the destination.
Validate the objective type against the two declared objective types when the
sense is not `MOI.FEASIBILITY_SENSE`.

For scalar affine rows:

- assign a destination constraint index using the next global evaluation id;
- combine repeated columns by summing into typed triplets;
- store the original function as `MOIScalarEvaluation{T}`;
- subtract `function.constant` from every finite side returned by
  `_moi_set_bounds(set)`;
- append the adjusted bounds and optional constraint name.

Construct the sparse matrix with:

```julia
A = sparse(row_indices, column_indices, coefficients, row_count, column_count)
```

Translate `MOI.VariableIndex` and `MOI.ScalarAffineFunction{T}` objectives.
Use zero coefficients, zero constant, and `MIN_SENSE` for feasibility sense.
Then call `LinearProblem` with explicit `row_lower`, `row_upper`,
`column_lower`, and `column_upper` values from the translator.

If column intersection already failed, or `LinearProblem` throws its expected
model-validation `ArgumentError`, return `MOITranslation{T}(nothing, index_map,
evaluations, message)` without hiding unrelated exception types.

- [ ] **Step 4: Add tests for unsupported types and non-finite model data**

Add:

```julia
quadratic = MOI.Utilities.Model{Float64}()
x = MOI.add_variable(quadratic)
q = MOI.ScalarQuadraticFunction(
    MOI.ScalarQuadraticTerm{Float64}[],
    [MOI.ScalarAffineTerm(1.0, x)],
    0.0,
)
MOI.add_constraint(quadratic, q, MOI.LessThan(1.0))
@test_throws MOI.UnsupportedConstraint JSimplex._translate_moi_model(
    JSimplex.Optimizer(),
    quadratic,
)
```

Also test an affine NaN coefficient and assert a non-`nothing` translation
error whose text names the non-finite coefficient.

- [ ] **Step 5: Run full root tests and commit**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: all tests PASS, including exact rational equality of every translated
coefficient and bound.

Commit:

```bash
git add src/moi/translation.jl test/moi/translation_tests.jl
git commit -m "feat: translate affine MOI models"
```

---

### Task 5: One-Shot Solve and MOI Result Interface

**Files:**
- Modify: `src/moi/results.jl`
- Create: `test/moi/result_tests.jl`
- Modify: `test/runtests.jl`

**Interfaces:**
- Consumes: `_translate_moi_model`, `_solver_options`, `_clear_result!`, and the existing `solve` API.
- Produces: two-argument `MOI.optimize!` and all result attributes promised by the specification.

- [ ] **Step 1: Write a failing optimal-result test**

Create a source model directly in MOI, call the one-shot method, and query the
returned destination indices:

```julia
@testset "MOI optimal result" begin
    source = MOI.Utilities.Model{Float64}()
    x = MOI.add_variables(source, 2)
    x_bound = MOI.add_constraint(source, x[1], MOI.GreaterThan(0.0))
    MOI.add_constraint(source, x[2], MOI.GreaterThan(0.0))
    row = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(1.0, x[1]),
         MOI.ScalarAffineTerm(1.0, x[2])],
        2.0,
    )
    ci = MOI.add_constraint(source, row, MOI.GreaterThan(3.0))
    objective = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(1.0, x[1]),
         MOI.ScalarAffineTerm(2.0, x[2])],
        4.0,
    )
    MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
    MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)

    optimizer = JSimplex.Optimizer()
    index_map, copied = MOI.optimize!(optimizer, source)
    @test !copied
    @test !MOI.is_empty(optimizer)
    @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.OPTIMAL
    @test MOI.get(optimizer, MOI.ResultCount()) == 1
    @test MOI.get(optimizer, MOI.PrimalStatus()) == MOI.FEASIBLE_POINT
    @test MOI.get(optimizer, MOI.DualStatus()) == MOI.NO_SOLUTION
    @test MOI.get(optimizer, MOI.ObjectiveValue()) == 5.0
    @test MOI.get(optimizer, MOI.VariablePrimal(), index_map[x[1]]) == 1.0
    @test MOI.get(optimizer, MOI.VariablePrimal(), index_map[x[2]]) == 0.0
    @test MOI.get(optimizer, MOI.ConstraintPrimal(), index_map[x_bound]) == 1.0
    @test MOI.get(optimizer, MOI.ConstraintPrimal(), index_map[ci]) == 3.0
    @test MOI.get(optimizer, MOI.SolveTimeSec()) >= 0.0
    @test MOI.get(optimizer, MOI.SimplexIterations()) >= 0
end
```

- [ ] **Step 2: Run the result test and verify missing optimize/result methods**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: FAIL because the two-argument optimizer method is not implemented.

- [ ] **Step 3: Implement optimization, evaluations, and result access**

At the start of `MOI.optimize!`, clear the previous result. Translate the
source, retain its evaluation vector, and either create an invalid-model
`Solution{T}` or call the core:

```julia
function MOI.optimize!(optimizer::Optimizer{T}, source::MOI.ModelLike) where {T}
    _clear_result!(optimizer)
    translation = _translate_moi_model(optimizer, source)
    if translation.error !== nothing
        optimizer.solution = Solution{T}(
            INVALID_MODEL,
            nothing,
            nothing,
            SolveStatistics(),
            translation.error,
        )
    else
        problem = something(translation.problem)
        optimizer.solution = solve(
            problem;
            relax_integrality=optimizer.relax_integrality,
            options=_solver_options(optimizer),
        )
    end
    solution = optimizer.solution::Solution{T}
    if solution.status == OPTIMAL
        primal = something(solution.primal)
        append!(
            optimizer.constraint_primals,
            (_evaluate_moi_function(evaluation, primal)
             for evaluation in translation.evaluations),
        )
    end
    return translation.index_map, false
end
```

Implement `_evaluate_moi_function(::MOIScalarEvaluation{T}, ::Vector{T})::T`
as a typed loop starting from the stored constant.

Implement the full status table in the specification. Before optimization,
`TerminationStatus` is `MOI.OPTIMIZE_NOT_CALLED`, both result statuses are
`MOI.NO_SOLUTION`, `ResultCount` is zero, and `RawStatusString` is
`"optimize not called"`. For an optimal result, check result indices with
`MOI.check_result_index_bounds` before returning objective, variable, or
constraint primal values.

Implement statistics using the retained core solution:

```julia
MOI.get(optimizer::Optimizer, ::MOI.SolveTimeSec) =
    isnothing(optimizer.solution) ? 0.0 : optimizer.solution.statistics.elapsed_seconds
MOI.get(optimizer::Optimizer, ::MOI.SimplexIterations) =
    isnothing(optimizer.solution) ? 0 : optimizer.solution.statistics.iterations
```

- [ ] **Step 4: Add deterministic status and stale-result tests**

Add cases that trigger and assert:

```julia
INFEASIBLE          => MOI.INFEASIBLE
UNBOUNDED           => MOI.DUAL_INFEASIBLE
ITERATION_LIMIT     => MOI.ITERATION_LIMIT
TIME_LIMIT          => MOI.TIME_LIMIT
NUMERICAL_ERROR     => MOI.NUMERICAL_ERROR
INVALID_MODEL       => MOI.INVALID_MODEL
MIP_NOT_SUPPORTED   => MOI.OTHER_ERROR
ALGORITHM_NOT_SUPPORTED => MOI.INVALID_OPTION
```

After an optimal solve, set `MOI.TimeLimitSec()` and assert `ResultCount() == 0`,
`TerminationStatus() == MOI.OPTIMIZE_NOT_CALLED`, and that querying
`ObjectiveValue()` throws the standard result-index error.

- [ ] **Step 5: Run all root tests and commit**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: all tests PASS and every non-optimal status exposes zero results.

Commit:

```bash
git add src/moi/results.jl test/moi/result_tests.jl test/runtests.jl
git commit -m "feat: solve MOI models and expose primal results"
```

---

### Task 6: Parametric Numeric Paths and Optional Integrality Relaxation

**Files:**
- Modify: `test/moi/result_tests.jl`
- Modify: `src/moi/translation.jl`
- Modify: `src/moi/results.jl`

**Interfaces:**
- Consumes: the completed translation and result API from Tasks 3-5.
- Produces: verified typed solve behavior for all required numeric types and the approved MIP-relaxation contract.

- [ ] **Step 1: Write failing cross-type and relaxation tests**

Use the direct MOI API so JuMP is not a root-test dependency:

```julia
@testset "MOI numeric types" begin
    for T in (Float32, Float64, Rational{BigInt})
        source = MOI.Utilities.Model{T}()
        x = MOI.add_variable(source)
        MOI.add_constraint(source, x, MOI.GreaterThan(T(2)))
        objective = MOI.ScalarAffineFunction(
            [MOI.ScalarAffineTerm(one(T), x)],
            T(1),
        )
        MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
        MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)
        optimizer = JSimplex.Optimizer{T}()
        index_map, _ = MOI.optimize!(optimizer, source)
        @test MOI.get(optimizer, MOI.ObjectiveValue()) isa T
        @test MOI.get(optimizer, MOI.VariablePrimal(), index_map[x]) isa T
        @test MOI.get(optimizer, MOI.ObjectiveValue()) == T(3)
    end
end

@testset "MOI integrality relaxation" begin
    source = MOI.Utilities.Model{Float64}()
    x = MOI.add_variable(source)
    MOI.add_constraint(source, x, MOI.ZeroOne())
    MOI.add_constraint(source, x, MOI.GreaterThan(0.5))
    objective = MOI.ScalarAffineFunction(
        [MOI.ScalarAffineTerm(1.0, x)],
        0.0,
    )
    MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
    MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)
    optimizer = JSimplex.Optimizer()
    MOI.optimize!(optimizer, source)
    @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.OTHER_ERROR
    @test occursin("relax_integrality", MOI.get(optimizer, MOI.RawStatusString()))
    MOI.set(optimizer, MOI.RawOptimizerAttribute("relax_integrality"), true)
    map, _ = MOI.optimize!(optimizer, source)
    @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.OPTIMAL
    @test MOI.get(optimizer, MOI.VariablePrimal(), map[x]) == 0.5
end
```

Add a `setprecision(BigFloat, 256) do` case using non-`Float64`-representable
decimal input and assert `BigFloat` result types and retained precision.

- [ ] **Step 2: Run the typed tests and inspect every failure**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: new tests may initially FAIL where translation accidentally creates
`Float64` literals, downcasts values, or reports the core MIP message without
the public attribute name.

- [ ] **Step 3: Remove numeric widening and finalize the relaxation message**

Replace every numeric literal in typed translation paths with `zero(T)`,
`one(T)`, or explicit `convert(T, value)`. Ensure sparse triplets are
`Vector{T}` and every evaluation returns `T`. When mapping
`MIP_NOT_SUPPORTED`, keep `MOI.OTHER_ERROR` and expose this adapter-level raw
message:

```julia
"integer variables require a MIP solver; set relax_integrality=true to solve the LP relaxation"
```

Do not mutate or erase `problem.variable_domains`; pass the Boolean relaxation
choice only to the existing `solve` call.

- [ ] **Step 4: Run root tests under all numeric contexts**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: all tests PASS with exact equality for rational tests and typed values
for Float32, Float64, BigFloat, and Rational{BigInt}.

- [ ] **Step 5: Commit the typed and relaxation slice**

```bash
git add src/moi/translation.jl src/moi/results.jl test/moi/result_tests.jl
git commit -m "test: cover typed MOI solves and LP relaxation"
```

---

### Task 7: Selected MOI Conformance Coverage

**Files:**
- Create: `test/moi/conformance_tests.jl`
- Modify: `test/runtests.jl`
- Modify: adapter files only when a conformance test exposes a violation of the declared interface

**Interfaces:**
- Consumes: the complete root MOI optimizer from Tasks 1-6.
- Produces: a reproducible selected MOI.Test gate for supported LP behavior without claiming excluded features.

- [ ] **Step 1: Add the selected MOI.Test harness**

Create `test/moi/conformance_tests.jl`:

```julia
@testset "MOI conformance" begin
    optimizer = MOI.instantiate(
        MOI.OptimizerWithAttributes(
            JSimplex.Optimizer,
            MOI.Silent() => true,
        );
        with_bridge_type=Float64,
    )
    config = MOI.Test.Config(
        atol=1e-6,
        rtol=1e-6,
        optimal_status=MOI.OPTIMAL,
        exclude=Any[
            MOI.ConstraintDual,
            MOI.ConstraintBasisStatus,
            MOI.ConstraintPrimalStart,
            MOI.ObjectiveBound,
            MOI.VariableBasisStatus,
            MOI.VariablePrimalStart,
        ],
    )
    tests = (
        MOI.Test.test_attribute_RawStatusString,
        MOI.Test.test_attribute_Silent,
        MOI.Test.test_attribute_SolverName,
        MOI.Test.test_attribute_SolveTimeSec,
        MOI.Test.test_attribute_TimeLimitSec,
        MOI.Test.test_linear_DUAL_INFEASIBLE,
        MOI.Test.test_linear_FEASIBILITY_SENSE,
        MOI.Test.test_linear_INFEASIBLE,
        MOI.Test.test_linear_Interval_inactive,
        MOI.Test.test_linear_LessThan_and_GreaterThan,
        MOI.Test.test_linear_inactive_bounds,
        MOI.Test.test_linear_integration,
        MOI.Test.test_linear_integration_2,
        MOI.Test.test_linear_integration_Interval,
        MOI.Test.test_linear_integration_modification,
    )
    for test in tests
        @testset "$(nameof(test))" begin
            MOI.empty!(optimizer)
            test(optimizer, config)
        end
    end
end
```

Include the file after the focused MOI result tests.

- [ ] **Step 2: Run only the conformance file and record exact contract failures**

Run:

```bash
julia --startup-file=no --project=. -e 'using JSimplex, Test; import MathOptInterface as MOI; include("test/moi/conformance_tests.jl")'
```

Expected: the harness runs only the named MOI 1.53 test functions. Any failure identifies
a declared behavior that must be fixed, not excluded.

- [ ] **Step 3: Fix contract violations with focused regression assertions**

For each failing named test, first add the smallest reproducer to
`optimizer_tests.jl`, `translation_tests.jl`, or `result_tests.jl`, then change
the corresponding adapter method. Keep the `include` list unchanged unless the
test's own `@requires` documents that it exclusively requires a feature listed
outside this specification, such as constraint duals.

Examples of allowed corrections are returning an exact MOI attribute value
type, clearing solution state before a second solve, or preserving a free
variable bound. Adding a dual or incremental solver interface is outside this
task.

- [ ] **Step 4: Run selected conformance and all root tests**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Expected: selected MOI conformance and the complete existing JSimplex suite
PASS.

- [ ] **Step 5: Commit the conformance gate**

```bash
git add test/moi/conformance_tests.jl test/moi test/runtests.jl src/moi
git commit -m "test: add selected MOI conformance coverage"
```

---

### Task 8: Development-Only JuMP Integration and JET Checks

**Files:**
- Modify: `dev/Project.toml`
- Create: `dev/tests/jump_tests.jl`
- Modify: `dev/tests/runtests.jl`
- Modify: `dev/tests/jet_tests.jl`
- Update ignored file: `dev/Manifest.toml`

**Interfaces:**
- Consumes: `JSimplex.Optimizer`, named attributes, one-shot caching behavior, and generic numeric constructors.
- Produces: JuMP end-to-end validation without making JuMP a production dependency.

- [ ] **Step 1: Add JuMP to the development project and write failing smoke tests**

Add to `dev/Project.toml`:

```toml
JuMP = "4076af6c-e467-56ae-b986-b466b2749572"
```

and add:

```toml
[compat]
JuMP = "1.31"
julia = "1.13"
```

Preserve the existing development dependencies. Create
`dev/tests/jump_tests.jl`:

```julia
using JSimplex
using JuMP
import MathOptInterface as MOI

@testset "JuMP Float64 integration" begin
    model = JuMP.Model(JSimplex.Optimizer)
    JuMP.set_silent(model)
    JuMP.set_optimizer_attribute(model, "iteration_limit", 10_000)
    @variable(model, x >= 0)
    @variable(model, -2 <= y <= 4)
    @objective(model, Min, x + 2y + 7)
    row = @constraint(model, x + y >= 1)
    JuMP.optimize!(model)
    @test JuMP.termination_status(model) == MOI.OPTIMAL
    @test JuMP.objective_value(model) ≈ 6.0
    @test JuMP.value(x) ≈ 3.0
    @test JuMP.value(y) ≈ -2.0
    @test JuMP.value(row) ≈ 1.0

    JuMP.set_lower_bound(y, 0.0)
    JuMP.optimize!(model)
    @test JuMP.objective_value(model) ≈ 8.0
    @test JuMP.value(x) ≈ 1.0
    @test JuMP.value(y) ≈ 0.0
end

@testset "JuMP relaxation" begin
    model = JuMP.Model(JSimplex.Optimizer)
    JuMP.set_silent(model)
    @variable(model, 0 <= x <= 1, Int)
    @constraint(model, x >= 0.5)
    @objective(model, Min, x)
    JuMP.optimize!(model)
    @test JuMP.termination_status(model) == MOI.OTHER_ERROR
    JuMP.set_optimizer_attribute(model, "relax_integrality", true)
    JuMP.optimize!(model)
    @test JuMP.termination_status(model) == MOI.OPTIMAL
    @test JuMP.value(x) ≈ 0.5
end
```

Add generic `JuMP.GenericModel{T}(() -> JSimplex.Optimizer{T}())` smoke tests for
`Float32`, `BigFloat`, and `Rational{BigInt}` using typed coefficients and exact
assertions where appropriate. Include `jump_tests.jl` from
`dev/tests/runtests.jl`.

- [ ] **Step 2: Resolve the development environment and run JuMP tests**

Run:

```bash
julia --startup-file=no --project=dev -e 'using Pkg; Pkg.resolve(); Pkg.instantiate()'
julia --startup-file=no --project=dev dev/tests/runtests.jl
```

Expected: JuMP installs only in the development environment. New tests may
expose cache/index-map integration issues and must FAIL before those issues are
fixed.

- [ ] **Step 3: Correct JuMP cache integration without adding incremental methods**

Fix only one-shot behavior: returned variable and constraint indices, result
attribute types, result invalidation, and `copied == false`. Confirm
`MOI.supports_incremental_interface(JSimplex.Optimizer())` remains `false` and
that no `MOI.add_variable`, `MOI.add_constraint`, `MOI.modify`, or `MOI.delete`
method is added for `JSimplex.Optimizer`.

- [ ] **Step 4: Add typed inference and JET assertions**

In `dev/tests/jet_tests.jl`, create typed source models and add:

```julia
float_optimizer = JSimplex.Optimizer{Float32}()
float_source = MOI.Utilities.Model{Float32}()
float_x = MOI.add_variable(float_source)
MOI.add_constraint(float_source, float_x, MOI.GreaterThan(Float32(1)))
@test @inferred(JSimplex._solver_options(float_optimizer)) isa SolverOptions{Float32}
@test @inferred(JSimplex._evaluate_moi_function(
    JSimplex.MOIScalarEvaluation(Int[1], Float32[2], Float32(3)),
    Float32[4],
)) === Float32(11)
JET.@test_opt target_modules=(JSimplex,) JSimplex._solver_options(float_optimizer)
```

Add an inferred rational evaluation as well. Do not require inference through
the fully generic `MOI.ModelLike` query boundary.

- [ ] **Step 5: Run development tests and JET, then commit tracked files**

Run:

```bash
julia --startup-file=no --project=dev dev/tests/runtests.jl
julia --startup-file=no --project=dev dev/tests/jet_tests.jl
```

Expected: JuMP smoke tests and all existing development tests PASS; JET reports
no issue in the typed adapter helpers under test.

Commit only tracked environment declarations and tests; do not add the ignored
development manifest:

```bash
git add dev/Project.toml dev/tests/runtests.jl dev/tests/jump_tests.jl dev/tests/jet_tests.jl src/moi
git commit -m "test: add development-only JuMP integration"
```

---

### Task 9: User Documentation and Final Verification

**Files:**
- Modify: `README.md`
- Modify: adapter docstrings or tests only if documentation verification exposes an error

**Interfaces:**
- Consumes: the finished public adapter and its passing root/development tests.
- Produces: English end-user documentation and final evidence for every acceptance criterion.

- [ ] **Step 1: Add an executable JuMP quick-start section**

Add this example near the direct API quick start in `README.md`:

```julia
using JSimplex
using JuMP
import MathOptInterface as MOI

model = Model(JSimplex.Optimizer)
set_silent(model)
@variable(model, x >= 0)
@variable(model, y >= 0)
@constraint(model, x + y >= 1)
@objective(model, Min, x + 2y)
optimize!(model)

@assert termination_status(model) == MOI.OPTIMAL
@assert objective_value(model) ≈ 1.0
```

State immediately before the example that JuMP is a user-selected integration
dependency and is not installed as a dependency of JSimplex.

- [ ] **Step 2: Document types, parameters, relaxation, and limitations**

Document:

```julia
JSimplex.Optimizer()
JSimplex.Optimizer{Float32}()
JSimplex.Optimizer{BigFloat}()
JSimplex.Optimizer{Rational{BigInt}}()
```

List all supported function-set pairs and the seven exact raw parameter names.
Show:

```julia
set_optimizer_attribute(model, "relax_integrality", true)
set_optimizer_attribute(model, "iteration_limit", 50_000)
set_time_limit_sec(model, 60.0)
```

Update the limitations section to say that the basic one-shot adapter is now
available but duals, warm starts, native incremental modification, and a MIP
algorithm are not. Explain that editing a JuMP model is supported through its
MOI cache and causes a fresh `LinearProblem` translation on the next solve.

- [ ] **Step 3: Run documentation examples as code**

Run the Float64 JuMP example and a relaxation example in the development
environment:

```bash
julia --startup-file=no --project=dev -e 'using JSimplex, JuMP; model = Model(JSimplex.Optimizer); set_silent(model); @variable(model, x >= 0); @variable(model, y >= 0); @constraint(model, x + y >= 1); @objective(model, Min, x + 2y); optimize!(model); @assert termination_status(model) == MOI.OPTIMAL; @assert objective_value(model) ≈ 1.0'
```

Expected: command exits successfully with no output.

- [ ] **Step 4: Run the complete verification matrix**

Run:

```bash
julia --startup-file=no --project=. test/runtests.jl
julia --startup-file=no --project=dev dev/tests/runtests.jl
julia --startup-file=no --project=dev dev/tests/jet_tests.jl
julia --startup-file=no --project=dev -e 'using JSimplex, JuMP; import MathOptInterface as MOI; model = Model(JSimplex.Optimizer); set_silent(model); @variable(model, x >= 0); @objective(model, Min, x); optimize!(model); @assert termination_status(model) == MOI.OPTIMAL'
git diff --check
git status --short
```

Then validate dependency isolation from temporary project and depot directories:

```bash
jsimplex_prod_project="$(mktemp -d)"
jsimplex_prod_depot="$(mktemp -d)"
JULIA_DEPOT_PATH="$jsimplex_prod_depot" julia --startup-file=no --project="$jsimplex_prod_project" -e 'using Pkg; Pkg.develop(path=pwd()); Pkg.instantiate(); using JSimplex; names = Set(info.name for info in values(Pkg.dependencies())); @assert "MathOptInterface" in names; @assert isdisjoint(names, Set(["JuMP", "GLPK", "JET", "BenchmarkTools"])); @assert JSimplex.Optimizer() isa JSimplex.Optimizer{Float64}'
```

Expected:

- all root tests, selected MOI.Test cases, development tests, and JET checks PASS;
- the JuMP smoke command exits successfully;
- the isolated production installation loads JSimplex and MOI without JuMP,
  GLPK, JET, or BenchmarkTools;
- `git diff --check` has no output;
- `git status --short` lists only the intended README change before the final
  documentation commit;
- no root `Manifest.toml` is tracked or left in the working tree;
- `dev/Manifest.toml` remains ignored.

- [ ] **Step 5: Commit documentation**

```bash
git add README.md
git commit -m "docs: document MOI and JuMP integration"
```

- [ ] **Step 6: Perform the completion review**

Compare the final diff against every acceptance criterion in the specification.
Run `git log --oneline` and `git status --short --branch`; record the final test
counts, MOI and JuMP versions, package commit, and any intentionally unsupported
MOI.Test groups for the handoff. Do not merge or push until the user explicitly
requests repository integration.
