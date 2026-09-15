# Parametric Numeric Types Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make JSimplex's public model and dual-simplex kernel type-stable over `Float32`, `Float64`, `BigFloat`, and `Rational{BigInt}`, including exact typed MPS input and explicit unbounded bounds.

**Architecture:** Introduce a shared numeric-policy and tagged-bound layer, then parameterize public data, MPS records, transformations, factorization, workspace state, and the dual-simplex kernel over one scalar `T`. Keep sparse UMFPACK behind a concrete wrapper for `Float64`; use generic dense LU for all other supported scalars and a typed empty representation for zero-row Float64 bases.

**Tech Stack:** Julia 1.13, `SparseArrays`, `LinearAlgebra`, `Logging`, `Test`, JET in the isolated development environment, GLPK only for development reference checks.

**Spec:** `docs/superpowers/specs/2026-09-15-parametric-numeric-types-design.md`

## Global Constraints

- Julia compatibility remains exactly `julia = "1.13"`.
- Supported working scalar families are `AbstractFloat` and `Rational`; integer-only inferred input becomes `Float64`.
- `read_mps(path)` defaults to `Float64`; `value_type=T` requests typed parsing and model construction.
- Omitted numeric constructor arguments are created only after `T` is selected.
- `Rational{BigInt}` is the documented and tested arbitrary-size exact type; fixed-width rationals retain Julia's ordinary solve-time overflow behavior.
- Rational default primal, dual, zero, Harris, and roundoff tolerances are exactly zero.
- Elapsed time and `time_limit` remain `Float64`; counters and indices remain `Int`.
- `Float64` bases use sparse UMFPACK; every other supported `T` uses generic dense `LinearAlgebra.lu`.
- Production dependencies remain the current standard libraries only; JET, GLPK, and BenchmarkTools stay in `dev/Project.toml`.
- Repository documentation, diagnostics, docstrings, comments, and test descriptions are English.
- The release version changes from `0.3.0` to `0.4.0`.
- Do not commit a generated `Manifest.toml`, local Julia depot, or downloaded benchmark collection.

## File Structure

- Create `src/numeric.jl`: supported-scalar validation, exact/inexact policy, typed constants, tagged `Bound{T}`, and bound conversion helpers.
- Modify `src/JSimplex.jl`: include numeric foundations before options/model and export the public bound API.
- Modify `src/options.jl`: `SolverOptions{T}`, typed option conversion, and `Solution{T}`.
- Modify `src/model.jl`: `LinearProblem{T}`, scalar inference/override, bound normalization, and typed validation.
- Modify `src/transformations.jl`: typed presolve/scaling/postsolve containers and bound-preserving relaxation.
- Modify `src/mps/records.jl`: typed records, exact decimal/exponent parsing, and checked rational arithmetic helpers.
- Modify `src/mps/parser.jl`: propagate `T` through fixed/free parsing and typed record accumulation.
- Modify `src/mps/build.jl`: typed coefficient aggregation, ranges, bounds, and final model construction.
- Modify `src/mps.jl`: expose `value_type=T` while retaining `Float64` by default.
- Modify `src/factorization.jl`: typed eta data and replaceable concrete factorization backend boundary.
- Modify `src/simplex.jl`: `SimplexWorkspace{T,F}`, tagged working bounds, and typed recomputation.
- Modify `src/dual_simplex.jl`: type-stable dual kernel, exact arithmetic policy, and `DualRunResult{T}`.
- Modify `src/solver.jl`: problem-typed options and stable `Solution{T}` on every status path.
- Create `test/numeric_tests.jl`: scalar policy and public `Bound` behavior.
- Create `test/numeric_type_tests.jl`: multi-scalar solver, exact MPS, field-type, ambiguity, and `@inferred` acceptance checks.
- Create `test/fixtures/parser/exact-rational.mps`: checked-in exact decimal and exponent fixture.
- Modify existing focused test files where numeric bounds become `Bound{T}` and result/options types become parametric.
- Modify `test/runtests.jl`: include the two new package-test files.
- Create `dev/tests/jet_tests.jl`: development-only inference checks for representative Float64 and rational kernels.
- Modify `dev/tests/runtests.jl` and `dev/Project.toml`: run JET checks only in the development environment.
- Modify `README.md` and public docstrings: scalar selection, `nothing` bounds, exact MPS, BigFloat precision, backend behavior, and migration notes.
- Modify `Project.toml`: release version only; do not add runtime dependencies.

---

### Task 1: Numeric Policy and Tagged Bounds

**Files:**
- Create: `src/numeric.jl`
- Create: `test/numeric_tests.jl`
- Modify: `src/JSimplex.jl`
- Modify: `test/runtests.jl`

**Interfaces:**
- Consumes: Julia `Real`, `AbstractFloat`, `Rational`, `zero`, `one`, `isfinite`, and `nextfloat`.
- Produces: `Bound{T}`, `Bound(value)`, `isfinite(::Bound)`, `bound_value`, `_finite_bound`, `_unbounded_bound`, `_normalize_bound`, `_is_exact`, `_typed_ratio`, and `_supported_value_type`.

- [ ] **Step 1: Write failing public-bound and numeric-policy tests**

Add `include("numeric_tests.jl")` before `options_tests.jl` in `test/runtests.jl`, then create `test/numeric_tests.jl` with these cases:

```julia
@testset "Numeric policy and tagged bounds" begin
    finite = @inferred Bound(3.0f0)
    @test finite isa Bound{Float32}
    @test isfinite(finite)
    @test @inferred(bound_value(finite)) === 3.0f0

    missing = @inferred JSimplex._unbounded_bound(Rational{BigInt})
    constructed_missing = @inferred Bound{Rational{BigInt}}(nothing)
    @test missing isa Bound{Rational{BigInt}}
    @test constructed_missing == missing
    @test !isfinite(missing)
    @test_throws ArgumentError bound_value(missing)

    @test JSimplex._is_exact(Rational{BigInt}) === Val(true)
    @test JSimplex._is_exact(Float64) === Val(false)
    @test JSimplex._typed_ratio(Float32, 1, 10^7) isa Float32
    @test JSimplex._typed_ratio(Rational{BigInt}, 1, 10^7) == 1 // big(10)^7
    @test JSimplex._supported_value_type(Float64)
    @test JSimplex._supported_value_type(Rational{Int})
    @test !JSimplex._supported_value_type(Int)

    exact_lower = @inferred JSimplex._normalize_bound(
        Rational{BigInt}, -Inf, :lower, "column lower bound",
    )
    exact_upper = @inferred JSimplex._normalize_bound(
        Rational{BigInt}, nothing, :upper, "column upper bound",
    )
    @test !isfinite(exact_lower)
    @test !isfinite(exact_upper)
    @test_throws ArgumentError JSimplex._normalize_bound(
        Float64, Inf, :lower, "column lower bound",
    )
end
```

- [ ] **Step 2: Run the focused test and verify the missing API failure**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/numeric_tests.jl")'
```

Expected: FAIL because `Bound` and the internal numeric-policy functions do not exist.

- [ ] **Step 3: Implement the numeric foundation**

Create `src/numeric.jl` with the following public representation and policy. The inner constructor must reject non-finite bounded floats, while an unbounded value always carries inert `zero(T)`:

```julia
_supported_value_type(::Type{T}) where {T} =
    isconcretetype(T) && (T <: AbstractFloat || T <: Rational)
_is_exact(::Type{<:Rational}) = Val(true)
_is_exact(::Type{<:AbstractFloat}) = Val(false)
_typed_ratio(::Type{T}, numerator::Integer, denominator::Integer) where {T<:Real} =
    T(numerator // denominator)

struct Bound{T<:Real}
    value::T
    bounded::Bool

    function Bound{T}(value::T, bounded::Bool) where {T<:Real}
        bounded && !isfinite(value) &&
            throw(ArgumentError("a finite bound must contain a finite value"))
        return new{T}(bounded ? value : zero(T), bounded)
    end
end

Bound(value::T) where {T<:Real} = Bound{T}(value, true)
Bound{T}(value::Real) where {T<:Real} = Bound{T}(T(value), true)
Bound{T}(::Nothing) where {T<:Real} = Bound{T}(zero(T), false)
_finite_bound(::Type{T}, value) where {T<:Real} = Bound{T}(T(value), true)
_unbounded_bound(::Type{T}) where {T<:Real} = Bound{T}(zero(T), false)
Base.isfinite(bound::Bound) = bound.bounded

function bound_value(bound::Bound)
    isfinite(bound) || throw(ArgumentError("an unbounded bound has no finite value"))
    return bound.value
end
```

Implement `_normalize_bound(T, input, side, label)` with these exact branches: `nothing` becomes unbounded; a `Bound` is converted without reading an unbounded payload; finite `Real` values become bounded; `-Inf` is accepted only for `side == :lower`; `Inf` is accepted only for `side == :upper`; NaN and incorrectly signed infinity raise `ArgumentError` naming `label`. Reject unsupported `T` before conversion.

- [ ] **Step 4: Include and export the new API**

In `src/JSimplex.jl`, insert `include("numeric.jl")` before `include("options.jl")`, then add `Bound` and `bound_value` to the export list. Extend `Base.isfinite`; do not define a second exported `isfinite` function.

- [ ] **Step 5: Run focused and complete package tests**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/numeric_tests.jl")'
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
```

Expected: both commands PASS and existing Float64 behavior is unchanged.

- [ ] **Step 6: Commit the numeric foundation**

```sh
git add src/numeric.jl src/JSimplex.jl test/numeric_tests.jl test/runtests.jl
git commit -m "feat: add typed bounds and numeric policy"
```

---

### Task 2: Parametric Options and Results

**Files:**
- Modify: `src/options.jl`
- Modify: `src/solver.jl`
- Modify: `test/options_tests.jl`

**Interfaces:**
- Consumes: `_is_exact`, `_typed_ratio`, `_supported_value_type` from Task 1.
- Produces: `SolverOptions{T}`, `SolverOptions(::Type{T}; ...)`, `SolverOptions(::Type{T}, ::SolverOptions)`, default `SolverOptions()` as `SolverOptions{Float64}`, and `Solution{T}`.

- [ ] **Step 1: Add failing typed option and solution tests**

Append these assertions to `test/options_tests.jl`:

```julia
@testset "Parametric solver options and results" begin
    @test @inferred(SolverOptions()) isa SolverOptions{Float64}
    options32 = @inferred SolverOptions(Float32)
    @test options32.primal_tolerance isa Float32
    @test options32.primal_tolerance > 0.0f0
    @test SolverOptions(Float16).zero_tolerance == nextfloat(zero(Float16))

    exact = @inferred SolverOptions(Rational{BigInt})
    @test exact.primal_tolerance == 0
    @test exact.dual_tolerance == 0
    @test exact.zero_tolerance == 0

    converted = @inferred SolverOptions(Rational{BigInt}, SolverOptions(time_limit=2.5))
    @test converted isa SolverOptions{Rational{BigInt}}
    @test converted.time_limit === 2.5
    @test_throws ArgumentError SolverOptions(Int)

    stats = SolveStatistics()
    optimal = @inferred Solution(OPTIMAL, 3.0f0, Float32[1], stats, "optimal")
    stopped = @inferred Solution{Float32}(TIME_LIMIT, nothing, nothing, stats, "stopped")
    @test optimal isa Solution{Float32}
    @test stopped isa Solution{Float32}
end
```

- [ ] **Step 2: Run the option tests and verify the parametric-type failure**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/options_tests.jl")'
```

Expected: FAIL because `SolverOptions` and `Solution` are not parametric.

- [ ] **Step 3: Replace `SolverOptions` with the typed contract**

Use this field layout and public constructor family:

```julia
struct SolverOptions{T<:Real}
    primal_tolerance::T
    dual_tolerance::T
    zero_tolerance::T
    iteration_limit::Int
    time_limit::Float64
    refactorization_interval::Int
    log_level::LogLevel
    algorithm::Symbol
end

SolverOptions(; kwargs...) = SolverOptions(Float64; kwargs...)

function SolverOptions(::Type{T};
    primal_tolerance=nothing, dual_tolerance=nothing, zero_tolerance=nothing,
    iteration_limit::Integer=100_000, time_limit::Real=Inf,
    refactorization_interval::Integer=20,
    log_level::LogLevel=Logging.Debug, algorithm::Symbol=:dual,
) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported solver value type $T"))
    defaults = _is_exact(T) === Val(true) ? (zero(T), zero(T), zero(T)) :
        (_positive_tolerance(T, 1 // 10^7), _positive_tolerance(T, 1 // 10^7),
         _positive_tolerance(T, 1 // 10^12))
    tolerances = map(T, (
        something(primal_tolerance, defaults[1]),
        something(dual_tolerance, defaults[2]),
        something(zero_tolerance, defaults[3]),
    ))
    all(isfinite, tolerances) || throw(ArgumentError("tolerances must be finite"))
    if _is_exact(T) === Val(true)
        all(>=(zero(T)), tolerances) ||
            throw(ArgumentError("rational tolerances must be nonnegative"))
    else
        all(>(zero(T)), tolerances) ||
            throw(ArgumentError("floating tolerances must be positive"))
    end
    iteration_limit >= 0 || throw(ArgumentError("iteration_limit must be nonnegative"))
    time_limit >= 0 || throw(ArgumentError("time_limit must be nonnegative"))
    refactorization_interval > 0 ||
        throw(ArgumentError("refactorization_interval must be positive"))
    return SolverOptions{T}(tolerances..., Int(iteration_limit), Float64(time_limit),
                            Int(refactorization_interval), log_level, algorithm)
end
```

Define `_positive_tolerance(T, ratio)` as `T(ratio)` clamped to `nextfloat(zero(T))` when conversion produces zero. Reject non-finite converted tolerances and time limits other than nonnegative finite values or positive `Inf`. Add `SolverOptions(T, options)` by forwarding every field through the typed constructor, preserving the explicitly supplied tolerance values.

- [ ] **Step 4: Parameterize `Solution` without parameterizing statistics**

Replace the result field types and add an inference constructor:

```julia
struct Solution{T<:Real}
    status::TerminationStatus
    objective_value::Union{Nothing,T}
    primal::Union{Nothing,Vector{T}}
    statistics::SolveStatistics
    message::String
end

function Solution(status::TerminationStatus, objective::T,
                  primal::Vector{T}, statistics::SolveStatistics,
                  message::AbstractString) where {T<:Real}
    return Solution{T}(status, objective, primal, statistics, String(message))
end
```

Non-optimal internal callers must use `Solution{T}(..., nothing, nothing, ...)` so the status never changes the concrete result type.

At this intermediate stage `LinearProblem` is still Float64-only. Update
`_finish_solve` in `src/solver.jl` to construct `Solution{Float64}` explicitly
for every status; Task 7 replaces that temporary Float64 relationship with the
problem's `T`. This keeps the complete existing package suite executable after
the public result type becomes parametric.

- [ ] **Step 5: Run option tests and the Float64 regression suite**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/options_tests.jl")'
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
```

Expected: PASS. Default constructors still produce Float64 options/results and zero floating tolerances remain invalid.

- [ ] **Step 6: Commit typed options and results**

```sh
git add src/options.jl src/solver.jl test/options_tests.jl
git commit -m "feat: parameterize options and solutions"
```

---

### Task 3: Replaceable Typed Factorization Boundary

**Files:**
- Modify: `src/factorization.jl`
- Modify: `src/simplex.jl`
- Modify: `test/factorization_tests.jl`

**Interfaces:**
- Consumes: scalar `T`, `SparseArrays.UMFPACK.UmfpackLU{Float64,Int}`, and generic dense `LU`.
- Produces: `PackedEta{T}`, `UMFPACKBackend`, `DenseLUBackend{T,F}`, `PFIFactorization{T,F}`, typed `forward_solve`, `transpose_solve`, `replace_column!`, and `refactorize!`.

- [ ] **Step 1: Add failing backend and multi-scalar factorization tests**

Add a test loop to `test/factorization_tests.jl`:

```julia
function test_factorization_type(::Type{T}) where {T}
    B = JSimplex.SparseArrays.sparse(T[2 1; 1 3])
    rhs = T[5, 7]
    factor = @inferred JSimplex.PFIFactorization(B)
    x = @inferred JSimplex.forward_solve(factor, rhs)
    xt = @inferred JSimplex.transpose_solve(factor, rhs)
    @test eltype(x) === T
    @test eltype(xt) === T
    if T <: Rational
        @test B * x == rhs
        @test transpose(B) * xt == rhs
    else
        @test B * x ≈ rhs
        @test transpose(B) * xt ≈ rhs
    end
    @test fieldtype(typeof(factor), :base) !== Any
    if T === Float64
        @test factor.base isa JSimplex.UMFPACKBackend
    else
        @test factor.base isa JSimplex.DenseLUBackend
    end
end

@testset "Parametric factorization backends" begin
    foreach(test_factorization_type, (Float32, Float64, BigFloat, Rational{BigInt}))

    empty_factor = @inferred JSimplex.PFIFactorization(
        JSimplex.SparseArrays.spzeros(Float64, 0, 0),
    )
    @test isempty(@inferred JSimplex.forward_solve(empty_factor, Float64[]))
end
```

- [ ] **Step 2: Run factorization tests and verify the Float32/inference failure**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/factorization_tests.jl")'
```

Expected: FAIL because all bases and eta values currently convert to Float64 and `base` is `Any`.

- [ ] **Step 3: Introduce concrete backend wrappers**

Use concrete wrappers so zero-row Float64 and nonempty Float64 factorization have the same outer backend type:

```julia
const Float64UMFPACK = SparseArrays.UMFPACK.UmfpackLU{Float64,Int}

struct UMFPACKBackend
    factorization::Union{Nothing,Float64UMFPACK}
    dimension::Int
end

struct DenseLUBackend{T,F}
    factorization::F
end

struct PackedEta{T<:Real}
    indices::Vector{Int}
    values::Vector{T}
    pivot_row::Int
end

mutable struct PFIFactorization{T<:Real,F}
    base::F
    updates::Vector{PackedEta{T}}
end
```

For `SparseMatrixCSC{Float64,Int}`, construct `UMFPACKBackend(nothing, 0)` for a zero-size square matrix and `UMFPACKBackend(lu(B), size(B, 1))` otherwise. For every other supported `T`, convert once to `Matrix{T}` and store `DenseLUBackend{T,typeof(lu_result)}`; dense zero-by-zero LU is valid. Matrix squareness validation stays at the boundary.

- [ ] **Step 4: Parameterize solve/update/refactor operations**

Make RHS and tableau conversion explicit and type preserving:

```julia
function forward_solve(factor::PFIFactorization{T}, rhs::AbstractVector) where {T}
    _check_rhs_dimension(factor, rhs)
    x = _backend_forward_solve(factor.base, T.(rhs))
    for eta in factor.updates
        pivot = x[eta.pivot_row]
        x[eta.pivot_row] = zero(T)
        for index in eachindex(eta.indices)
            x[eta.indices[index]] += pivot * eta.values[index]
        end
    end
    return x
end

function transpose_solve(factor::PFIFactorization{T}, rhs::AbstractVector) where {T}
    _check_rhs_dimension(factor, rhs)
    x = T.(rhs)
    for eta in Iterators.reverse(factor.updates)
        value = zero(T)
        for index in eachindex(eta.indices)
            value += eta.values[index] * x[eta.indices[index]]
        end
        x[eta.pivot_row] = value
    end
    return _backend_transpose_solve(factor.base, x)
end
```

Implement empty UMFPACK backend solves as `copy(rhs)`. `replace_column!` converts pivot/tableau values to `T`, stores `PackedEta{T}`, and validates `zero_tolerance` in `T`. `refactorize!` calls the backend-specific rebuild method and mutates the wrapper without changing `typeof(factor.base)`.

In `recompute!`, remove the direct assignment of a dense zero-row LU to
`workspace.factorization.base`; call `refactorize!(workspace.factorization, B)`
for empty and nonempty bases alike so the backend wrapper owns that decision.

- [ ] **Step 5: Run factorization and package regressions**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/factorization_tests.jl")'
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
```

Expected: PASS for all four types, including exact equality for rational solves; existing Float64 eta tests remain green.

- [ ] **Step 6: Commit the backend boundary**

```sh
git add src/factorization.jl src/simplex.jl test/factorization_tests.jl
git commit -m "refactor: parameterize basis factorization"
```

---

### Task 4: Typed MPS Records and Exact Number Parsing

**Files:**
- Modify: `src/mps/records.jl`
- Modify: `src/mps/parser.jl`
- Modify: `src/mps.jl`
- Modify: `test/mps_parser_tests.jl`

**Interfaces:**
- Consumes: requested scalar `T` and existing source/line/section diagnostics.
- Produces: `BoundRecord{T}`, `MPSAccumulator{T}`, `_parse_mps(io, source, T; format)`, `_parse_mps_file(path, T; format)`, `_mps_number(::MPSAccumulator{T}, ...)::T`, and `_mps_checked_convert`.

- [ ] **Step 1: Add failing typed parser tests**

Add to `test/mps_parser_tests.jl`:

```julia
@testset "Typed MPS numeric records" begin
    text = "NAME EXACT\nROWS\n N OBJ\n E EQ\nCOLUMNS\n X OBJ 1.25 EQ -2e-3\nRHS\n R EQ 3D+2\nENDATA\n"
    records = @inferred JSimplex._parse_mps(
        IOBuffer(text), "memory.mps", Rational{BigInt}; format=:free,
    )
    @test records isa JSimplex.MPSAccumulator{Rational{BigInt}}
    @test records.coefficients[1][3] == 5 // big(4)
    @test records.coefficients[2][3] == -1 // big(500)
    @test records.rhs_sets["R"][1][2] == 300 // big(1)

    float32_records = @inferred JSimplex._parse_mps(
        IOBuffer(text), "memory.mps", Float32; format=:free,
    )
    @test float32_records isa JSimplex.MPSAccumulator{Float32}
    @test float32_records.coefficients[1][3] === 1.25f0

    @test_throws MPSParseError JSimplex._parse_mps(
        IOBuffer(replace(text, "1.25" => "1e999999999999999999999")),
        "memory.mps", Rational{Int}; format=:free,
    )
    fixed_overflow = replace(text, "1.25" => string(big(typemax(Int)) + 1))
    error = try
        JSimplex._parse_mps(IOBuffer(fixed_overflow), "memory.mps",
                            Rational{Int}; format=:free)
    catch exception
        exception
    end
    @test error isa MPSParseError
    @test error.line == 6
    @test error.section == :COLUMNS
end
```

- [ ] **Step 2: Run parser tests and verify the missing typed method**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/mps_parser_tests.jl")'
```

Expected: FAIL because parser records and numeric conversion are fixed to Float64.

- [ ] **Step 3: Parameterize record storage**

Use these field types throughout `src/mps/records.jl`:

```julia
struct BoundRecord{T<:Real}
    kind::Symbol
    column::String
    value::Union{Nothing,T}
    line::Int
end

mutable struct MPSAccumulator{T<:Real}
    source::String
    name::String
    objective_sense::ObjectiveSense
    objective_name::Union{Nothing,String}
    objective_name_line::Int
    row_order::Vector{String}
    row_types::Dict{String,Char}
    column_order::Vector{String}
    coefficients::Vector{Tuple{String,String,T,Int}}
    rhs_sets::Dict{String,Vector{Tuple{String,T,Int}}}
    rhs_order::Vector{String}
    ranges_sets::Dict{String,Vector{Tuple{String,T,Int}}}
    ranges_order::Vector{String}
    bounds_sets::Dict{String,Vector{BoundRecord{T}}}
    bounds_order::Vector{String}
    marker_domains::Dict{String,VariableDomain}
end
```

`MPSAccumulator(source, T)` constructs all dictionaries and vectors with concrete `T` element types.

- [ ] **Step 4: Implement exact MPS decimal parsing**

Normalize `D`/`d` to `E`, and use the anchored grammar below for rational values:

```julia
const _MPS_DECIMAL = r"^([+-]?)(?:(\d+)(?:\.(\d*))?|\.(\d+))(?:[Ee]([+-]?\d+))?$"

function _mps_big_rational(token::AbstractString)
    normalized = replace(token, 'D' => 'E', 'd' => 'e')
    match_result = match(_MPS_DECIMAL, normalized)
    isnothing(match_result) && return nothing
    sign = match_result.captures[1] == "-" ? -1 : 1
    whole = something(match_result.captures[2], "0")
    fraction = something(match_result.captures[3], match_result.captures[4], "")
    significand = parse(BigInt, whole * fraction)
    exponent = parse(BigInt, something(match_result.captures[5], "0")) - length(fraction)
    abs(exponent) <= typemax(Int) || return nothing
    power = big(10)^Int(abs(exponent))
    return exponent >= 0 ? (sign * significand * power) // big(1) :
                           (sign * significand) // power
end
```

For `T<:AbstractFloat`, call `tryparse(T, normalized)` and require a finite result. For `T == Rational{BigInt}`, return the exact value. For `T == Rational{I}` with fixed-width `I`, convert numerator and denominator separately with `I(...)` inside a narrow `try/catch`; conversion failure calls `_mps_error` with the original source context. Do not catch unrelated parser errors.

Expose the checked conversion under this signature so Task 6 can reuse it for
duplicate and range arithmetic:

```julia
function _mps_checked_convert(::Type{Rational{I}}, value::Rational{BigInt},
                              records, line::Int, section::Symbol,
                              message::String) where {I<:Integer}
    try
        return Rational{I}(I(numerator(value)), I(denominator(value)))
    catch exception
        exception isa InexactError || exception isa OverflowError || rethrow()
        _mps_error(records, line, section, message)
    end
end
```

- [ ] **Step 5: Thread `T` through parser functions without exposing partial model construction**

Define:

```julia
_parse_mps(io::IO, source::AbstractString; format::Symbol=:auto) =
    _parse_mps(io, source, Float64; format)

function _parse_mps(io::IO, source::AbstractString, ::Type{T};
                    format::Symbol=:auto) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported MPS value type $T"))
    records = MPSAccumulator(source, T)
    # Run the existing section-order and fixed/free state machine. Every numeric
    # field is obtained with _mps_number(records, token, line, section), and every
    # inserted tuple or BoundRecord uses T.
    return records
end
```

Add the corresponding `_parse_mps_file(path, T; format)` overload. Keep the existing no-type overload and public `read_mps` on Float64 until Task 6 connects typed building.

- [ ] **Step 6: Run parser and complete package tests**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/mps_parser_tests.jl")'
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
```

Expected: PASS for fixed/free Float64 records and the new exact/Float32 record cases.

- [ ] **Step 7: Commit typed record parsing**

```sh
git add src/mps/records.jl src/mps/parser.jl src/mps.jl test/mps_parser_tests.jl
git commit -m "feat: parse typed MPS numbers exactly"
```

---

### Task 5: Parametric Model, Transformations, and Workspace Bounds

**Files:**
- Modify: `src/model.jl`
- Modify: `src/transformations.jl`
- Modify: `src/simplex.jl`
- Modify: `src/dual_simplex.jl`
- Modify: `src/solver.jl`
- Modify: `test/model_tests.jl`
- Modify: `test/transformations_tests.jl`
- Modify: `test/mps_parser_tests.jl`
- Modify: `test/mps_build_tests.jl`
- Modify: `test/simplex_workspace_tests.jl`
- Modify: `test/dual_simplex_tests.jl`
- Modify: `test/solver_tests.jl`

**Interfaces:**
- Consumes: `Bound{T}`, `SolverOptions{T}`, and `PFIFactorization{T,F}` from Tasks 1–3.
- Produces: `LinearProblem{T}`, `_working_value_type`, `PresolveResult{T,S}`, `Scaling{T}`, `SimplexWorkspace{T,F}`, and bound-aware Float64-compatible solver behavior.

- [ ] **Step 1: Add failing model inference and bound-normalization tests**

Add these focused cases to `test/model_tests.jl`:

```julia
@testset "Parametric LinearProblem inference" begin
    sparse = JSimplex.SparseArrays.sparse
    p32 = @inferred LinearProblem(sparse(Float32[1 2]), Float32[3, 4])
    pbig = @inferred LinearProblem(sparse(BigFloat[1 2]), BigFloat[3, 4])
    pexact = @inferred LinearProblem(
        sparse(Rational{BigInt}[1 2]), Rational{BigInt}[3, 4];
        row_lower=Union{Nothing,Rational{BigInt}}[nothing],
        row_upper=Rational{BigInt}[5],
    )
    pinteger = @inferred LinearProblem(sparse([1 2]), [3, 4])
    poverride = @inferred LinearProblem(sparse([1 2]), [3, 4];
                                        value_type=Rational{BigInt})
    pmixed = @inferred LinearProblem(sparse(Float32[1 2]), [3, 4])

    @test p32 isa LinearProblem{Float32}
    @test pbig isa LinearProblem{BigFloat}
    @test pexact isa LinearProblem{Rational{BigInt}}
    @test pinteger isa LinearProblem{Float64}
    @test poverride isa LinearProblem{Rational{BigInt}}
    @test pmixed isa LinearProblem{Float32}
    @test !isfinite(only(pexact.row_lower))
    @test bound_value(only(pexact.row_upper)) == 5
    @test_throws ArgumentError LinearProblem(sparse([1;;]), [1]; value_type=Int)
end
```

Update old field assertions across `model_tests.jl`, `transformations_tests.jl`,
`mps_parser_tests.jl`, `mps_build_tests.jl`, `simplex_workspace_tests.jl`,
`dual_simplex_tests.jl`, and `solver_tests.jl` to compare finite values through
`bound_value`, and unbounded values through `!isfinite`. Replace
`fieldnames(LinearProblem)` with `fieldnames(typeof(problem))`. Tests that
previously assigned `NaN` directly into a numeric bound vector must instead
exercise constructor rejection, because an invalid bounded `Bound{T}` cannot be
constructed or inserted. Do not add equality between `Bound` and `Real`, because
the stored-bound API is intentionally breaking.

- [ ] **Step 2: Run model tests and verify the non-parametric failure**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/model_tests.jl")'
```

Expected: FAIL because `LinearProblem` is fixed to Float64 and stores numeric infinities.

- [ ] **Step 3: Parameterize `LinearProblem` and implement scalar selection**

Replace its numeric fields with this layout:

```julia
struct LinearProblem{T<:Real}
    A::SparseMatrixCSC{T,Int}
    objective::Vector{T}
    objective_constant::T
    objective_sense::ObjectiveSense
    row_lower::Vector{Bound{T}}
    row_upper::Vector{Bound{T}}
    column_lower::Vector{Bound{T}}
    column_upper::Vector{Bound{T}}
    variable_domains::Vector{VariableDomain}
    name::String
    row_names::Vector{String}
    column_names::Vector{String}
end
```

Change numeric keyword defaults to `nothing`. `_working_value_type` collects types from `eltype(A)`, `eltype(objective)`, an explicitly supplied objective constant, and each finite bound input. It ignores omitted vectors, `nothing` elements, unbounded `Bound` values, and correctly signed float infinities. Apply `promote_type`; map any integer-only result to `Float64`; retain an `AbstractFloat` or `Rational`; reject every other result. If `value_type=T` is supplied, validate and use `T` before converting data.

After selecting `T`, create omitted values as follows:

```julia
objective_constant === nothing && (objective_constant = zero(T))
row_lower === nothing && (row_lower = fill(nothing, size(A, 1)))
row_upper === nothing && (row_upper = fill(nothing, size(A, 1)))
column_lower === nothing && (column_lower = fill(zero(T), size(A, 2)))
column_upper === nothing && (column_upper = fill(nothing, size(A, 2)))
```

Normalize all bounds with `_normalize_bound`; intersect binary finite endpoints with `zero(T)` and `one(T)`; preserve copy ownership. Validation uses `isfinite(bound)` before `bound_value(bound)` and keeps the current English dimension/domain diagnostics.

- [ ] **Step 4: Parameterize identity transformations and relaxation**

Use concrete transformation containers:

```julia
struct PresolveResult{T<:Real,S<:Tuple}
    problem::LinearProblem{T}
    postsolve_stack::S
    original_column_count::Int
end

struct Scaling{T<:Real}
    row_factors::Vector{T}
    column_factors::Vector{T}
end

identity_presolve(problem::LinearProblem{T}) where {T} =
    PresolveResult(problem, (), size(problem.A, 2))
identity_scaling(problem::LinearProblem{T}) where {T} =
    Scaling(ones(T, size(problem.A, 1)), ones(T, size(problem.A, 2)))
```

`unscale_primal`, `unscale_dual`, and identity postsolve return `Vector{T}`. Implement postsolve tuple traversal recursively so no `Vector{AbstractPostsolveStep}` remains. In `relax_integrality`, replace binary/semi endpoints only when finite and use `Bound(zero(T))`/`Bound(one(T))`; unbounded endpoints remain unbounded.

- [ ] **Step 5: Add and run typed transformation tests**

Add to `test/transformations_tests.jl`:

```julia
function test_typed_transformations(::Type{T}) where {T}
    problem = LinearProblem(JSimplex.SparseArrays.sparse(T[1 1]), T[1, 2];
        column_lower=T[2, 3], column_upper=T[7, 9],
        variable_domains=[SEMI_CONTINUOUS, SEMI_INTEGER])
    relaxed = @inferred JSimplex.relax_integrality(problem)
    presolved = @inferred JSimplex.identity_presolve(relaxed)
    scaling = @inferred JSimplex.identity_scaling(presolved.problem)
    @test relaxed isa LinearProblem{T}
    @test presolved.postsolve_stack === ()
    @test @inferred(JSimplex.unscale_primal(scaling, T[1, 2])) isa Vector{T}
end

foreach(test_typed_transformations, (Float32, BigFloat, Rational{BigInt}))
```

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/transformations_tests.jl")'
```

Expected: PASS.

- [ ] **Step 6: Parameterize workspace storage and bound operations**

Use this concrete workspace layout:

```julia
mutable struct SimplexWorkspace{T<:Real,F}
    problem::LinearProblem{T}
    options::SolverOptions{T}
    costs::Vector{T}
    lower::Vector{Bound{T}}
    upper::Vector{Bound{T}}
    basis::Basis
    primal::Vector{T}
    reduced_costs::Vector{T}
    pricing_weights::Vector{T}
    factorization::PFIFactorization{T,F}
    iterations::Int
    refactorizations::Int
    perturbed::Bool
end
```

Replace every workspace allocation with `zeros(T, ...)`, `ones(T, ...)`, `zero(T)`, or `one(T)`. Build the slack basis with `-one(T)`. `_nonbasic_value` calls `bound_value` for `AT_LOWER`/`AT_UPPER` and returns `zero(T)` for free variables. Introduce exact helpers and use them in both `simplex.jl` and the still-Float64 dual path:

```julia
_is_fixed(lower::Bound, upper::Bound) =
    isfinite(lower) && isfinite(upper) && bound_value(lower) == bound_value(upper)
_lower_violation(bound::Bound{T}, value::T) where {T} =
    isfinite(bound) ? bound_value(bound) - value : zero(T)
_upper_violation(bound::Bound{T}, value::T) where {T} =
    isfinite(bound) ? value - bound_value(bound) : zero(T)
```

Convert supplied options once with `SolverOptions(T, options)` in `initialize_workspace`. Keep the default Float64 solver passing by replacing every direct arithmetic/comparison on bounds in `dual_simplex.jl` and `solver.jl` with `_is_fixed`, `_lower_violation`, `_upper_violation`, `isfinite`, and `bound_value`; full scalar generalization follows in Task 7.

- [ ] **Step 7: Update workspace tests and verify typed recomputation**

Add a loop to `test/simplex_workspace_tests.jl`:

```julia
function test_workspace_type(::Type{T}) where {T}
    problem = LinearProblem(JSimplex.SparseArrays.sparse(reshape(T[2], 1, 1)), T[5];
                            row_lower=T[1], column_lower=T[1], column_upper=T[4])
    workspace = @inferred JSimplex.initialize_workspace(problem, SolverOptions(T))
    @test workspace isa JSimplex.SimplexWorkspace{T}
    @test eltype(workspace.primal) === T
    @test workspace.primal == T[1, 2]
    @test @inferred(JSimplex.primal_infeasibility(workspace)) isa T
    @test @inferred(JSimplex.dual_infeasibility(workspace)) isa T
end


foreach(test_workspace_type, (Float32, Float64, BigFloat, Rational{BigInt}))
```

Update existing bound assertions to use `isfinite`/`bound_value`, then run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/model_tests.jl"); include("test/transformations_tests.jl"); include("test/simplex_workspace_tests.jl")'
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
```

Expected: PASS, including all existing Float64 dual-simplex and solver regressions.

- [ ] **Step 8: Commit the model and workspace migration**

```sh
git add src/model.jl src/transformations.jl src/simplex.jl src/dual_simplex.jl src/solver.jl test/model_tests.jl test/transformations_tests.jl test/mps_parser_tests.jl test/mps_build_tests.jl test/simplex_workspace_tests.jl test/dual_simplex_tests.jl test/solver_tests.jl
git commit -m "refactor: parameterize model and workspace"
```

---

### Task 6: Typed MPS Model Construction

**Files:**
- Modify: `src/mps/build.jl`
- Modify: `src/mps.jl`
- Modify: `test/mps_build_tests.jl`
- Create: `test/fixtures/parser/exact-rational.mps`

**Interfaces:**
- Consumes: `MPSAccumulator{T}` from Task 4 and `LinearProblem{T}`/`Bound{T}` from Task 5.
- Produces: `_build_mps(::MPSAccumulator{T})::LinearProblem{T}` and `read_mps(path; value_type=T)::LinearProblem{T}`.

- [ ] **Step 1: Add an exact MPS fixture and failing public-reader tests**

Create `test/fixtures/parser/exact-rational.mps` with:

```text
NAME EXACT
ROWS
 N OBJ
 E EQ
COLUMNS
 X OBJ 1.25 EQ 3D-1
RHS
 R OBJ -2.5E-1 EQ 6D-1
ENDATA
```

Add to `test/mps_build_tests.jl`:

```julia
@testset "Typed and exact MPS construction" begin
    path = joinpath(@__DIR__, "fixtures", "parser", "exact-rational.mps")
    default = @inferred read_mps(path)
    exact = @inferred read_mps(path; value_type=Rational{BigInt})
    single = @inferred read_mps(path; value_type=Float32)

    @test default isa LinearProblem{Float64}
    @test exact isa LinearProblem{Rational{BigInt}}
    @test single isa LinearProblem{Float32}
    @test exact.objective == Rational{BigInt}[5 // 4]
    @test exact.objective_constant == 1 // big(4)
    @test Matrix(exact.A) == reshape(Rational{BigInt}[3 // 10], 1, 1)
    @test bound_value(only(exact.row_lower)) == 3 // big(5)
    @test bound_value(only(exact.row_upper)) == 3 // big(5)

    maximum = string(typemax(Int))
    duplicate = "NAME SUM\nROWS\n N OBJ\nCOLUMNS\n X OBJ $maximum\n X OBJ 1\nENDATA\n"
    duplicate_error = try
        read_mps_text(duplicate; value_type=Rational{Int})
    catch exception
        exception
    end
    @test duplicate_error isa MPSParseError
    @test duplicate_error.line == 6
    @test duplicate_error.section == :COLUMNS

    ranged = "NAME RANGE\nROWS\n G ROW\nCOLUMNS\n X ROW 1\nRHS\n R ROW $maximum\nRANGES\n RNG ROW 1\nENDATA\n"
    range_error = try
        read_mps_text(ranged; value_type=Rational{Int})
    catch exception
        exception
    end
    @test range_error isa MPSParseError
    @test range_error.line == 9
    @test range_error.section == :RANGES
end
```

- [ ] **Step 2: Run MPS build tests and verify typed construction fails**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/mps_build_tests.jl")'
```

Expected: FAIL because `_build_mps` allocates Float64 arrays and `read_mps` has no `value_type` keyword.

- [ ] **Step 3: Implement checked typed aggregation**

Replace Float64 dictionaries, arrays, and literals with `T`. Aggregate matrix and objective duplicates in source order, retaining the current line number. Use these helpers for rational construction operations:

```julia
_mps_big(value::Rational) = BigInt(numerator(value)) // BigInt(denominator(value))

function _mps_checked_add(records::MPSAccumulator{T}, left::T, right::T,
                          line::Int, section::Symbol, message::String) where {T<:Rational}
    return _mps_checked_convert(T, _mps_big(left) + _mps_big(right),
                                records, line, section, message)
end
```

Add matching checked subtraction and absolute-value/range endpoint helpers. Floating methods perform the operation in `T` and call `_mps_error` if the result is non-finite. Build the sparse matrix from already aggregated `(row, column) => T` entries so `sparse(..., +)` cannot hide the source record that overflowed.

- [ ] **Step 4: Build tagged row and column bounds in `T`**

Initialize bounds exactly as:

```julia
row_lower = fill(_unbounded_bound(T), m)
row_upper = fill(_unbounded_bound(T), m)
column_lower = fill(Bound(zero(T)), n)
column_upper = fill(_unbounded_bound(T), n)
```

For equality rows, set both endpoints to `Bound(rhs)`. For `L`/`G` rows and `RANGES`, set only mathematically finite endpoints. In `_mps_column_bounds`, implement `FR`, `MI`, and `PL` with `_unbounded_bound(T)`, all finite records with `Bound(value)`, and binary/semi defaults with `zero(T)`/`one(T)`. Use `_is_fixed` and `bound_value` only after `isfinite` for consistency checks.

- [ ] **Step 5: Expose `value_type` on `read_mps`**

Use a type-valued keyword that remains inferable:

```julia
function read_mps(path::AbstractString; format::Symbol=:auto,
                  rhs_name=nothing, ranges_name=nothing, bounds_name=nothing,
                  objective_name=nothing, value_type::Type{T}=Float64) where {T<:Real}
    _supported_value_type(T) || throw(ArgumentError("unsupported MPS value type $T"))
    records = _parse_mps_file(path, T; format)
    return _build_mps(records; rhs_name, ranges_name, bounds_name, objective_name)
end
```

- [ ] **Step 6: Verify diagnostics and all MPS formats**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/mps_parser_tests.jl"); include("test/mps_build_tests.jl")'
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
```

Expected: PASS for default Float64 fixtures, exact decimals/exponents, fixed/free/automatic formats, named sets, new bound kinds, and source-aware overflow diagnostics.

- [ ] **Step 7: Commit typed MPS construction**

```sh
git add src/mps/build.jl src/mps.jl test/mps_build_tests.jl test/fixtures/parser/exact-rational.mps
git commit -m "feat: build typed models from MPS"
```

---

### Task 7: Parametric Dual-Simplex Kernel and Public Solve Contract

**Files:**
- Modify: `src/dual_simplex.jl`
- Modify: `src/solver.jl`
- Modify: `test/dual_simplex_tests.jl`
- Modify: `test/solver_tests.jl`

**Interfaces:**
- Consumes: `LinearProblem{T}`, `SolverOptions{T}`, `SimplexWorkspace{T,F}`, tagged bounds, and typed factorization.
- Produces: `DualRunResult{T}`, a single generic dual-simplex kernel, `solve(::LinearProblem{T}; options=nothing)::Solution{T}`, and exact/inexact recession policies.

- [ ] **Step 1: Add failing four-scalar public solve tests**

Add this helper and testset to `test/solver_tests.jl`:

```julia
function typed_bounded_problem(::Type{T}) where {T}
    A = JSimplex.SparseArrays.sparse(T[1 1; 1 0; 0 1])
    return LinearProblem(A, T[-3, -2]; objective_constant=T(1 // 3),
        row_lower=fill(nothing, 3), row_upper=T[4, 2, 3],
        column_lower=T[0, 0], column_upper=fill(nothing, 2))
end

function test_public_solve_type(::Type{T}) where {T}
    problem = @inferred typed_bounded_problem(T)
    result = @inferred solve(problem)
    @test result isa Solution{T}
    @test result.status == OPTIMAL
    @test result.primal isa Vector{T}
    @test result.objective_value isa T
    if T <: Rational
        @test result.primal == T[2, 2]
        @test result.objective_value == T(-29 // 3)
    else
        @test result.primal ≈ T[2, 2]
        @test result.objective_value ≈ T(-29 // 3)
    end
end

@testset "Parametric public solve" begin
    foreach(test_public_solve_type, (Float32, Float64, BigFloat, Rational{BigInt}))
    exact = typed_bounded_problem(Rational{BigInt})
    @test (@inferred solve(exact; options=SolverOptions())).status == OPTIMAL

    exact_path = joinpath(@__DIR__, "fixtures", "parser", "exact-rational.mps")
    exact_mps_result = @inferred solve(
        read_mps(exact_path; value_type=Rational{BigInt}),
    )
    @test exact_mps_result.status == OPTIMAL
    @test exact_mps_result.primal == Rational{BigInt}[2]
    @test exact_mps_result.objective_value == 11 // big(4)
end
```

- [ ] **Step 2: Run solver tests and verify the hard-coded Float64 failure**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/solver_tests.jl")'
```

Expected: FAIL in the dual kernel on Float32, BigFloat, or rational vector annotations/literals.

- [ ] **Step 3: Parameterize internal result and all kernel signatures**

Replace the result storage and remove every `Vector{Float64}`/`SparseMatrixCSC{Float64,Int}` kernel restriction:

```julia
struct DualRunResult{T<:Real}
    status::TerminationStatus
    objective_value::Union{Nothing,T}
    primal::Union{Nothing,Vector{T}}
    iterations::Int
    refactorizations::Int
    message::String
end

function dual_ratio_test(workspace::SimplexWorkspace{T},
                         tableau_row::Vector{T})::Int where {T}
    candidates = Int[]
    maximum_step = _unbounded_bound(T)
    tolerance = workspace.options.dual_tolerance
    cutoff = _is_exact(T) === Val(true) ? zero(T) :
             _positive_tolerance(T, 1 // 10^7)
    for index in eachindex(tableau_row)
        coefficient = tableau_row[index]
        _dual_pivot_eligible(workspace, index, coefficient, cutoff) || continue
        push!(candidates, index)
        signed_tolerance = coefficient < zero(T) ? -tolerance : tolerance
        relaxed_step = (workspace.reduced_costs[index] + signed_tolerance) / coefficient
        if !isfinite(maximum_step) || relaxed_step < bound_value(maximum_step)
            maximum_step = Bound(relaxed_step)
        end
    end

    entering_index = -1
    largest_pivot = zero(T)
    for index in candidates
        coefficient = tableau_row[index]
        step = workspace.reduced_costs[index] / coefficient
        within_limit = !isfinite(maximum_step) || step <= bound_value(maximum_step)
        if within_limit && abs(coefficient) > largest_pivot
            entering_index = index
            largest_pivot = abs(coefficient)
        end
    end
    return entering_index
end

function price!(tableau_row::Vector{T}, workspace::SimplexWorkspace{T},
                rho::Vector{T})::Nothing where {T}
    A = workspace.problem.A
    row_count, column_count = size(A)
    for column in 1:column_count
        value = zero(T)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            value += rho[A.rowval[position]] * A.nzval[position]
        end
        tableau_row[column] = value
    end
    for row in 1:row_count
        tableau_row[column_count + row] = -rho[row]
    end
    return nothing
end
```

Apply the same `{T}` relationship to all update, feasibility, auxiliary, recession, and solve functions. Replace allocations/literals with `zeros(T, ...)`, `zero(T)`, `one(T)`, `_typed_ratio(T, 1, 10^7)`, `_typed_ratio(T, 1, 10^4)`, and `T(1000)`. Use `ifelse(coefficient < zero(T), -tolerance, tolerance)` instead of relying on float-only sign copying.

- [ ] **Step 4: Remove infinity from the Harris and auxiliary logic**

Represent an initially unlimited Harris step with a tagged bound:

```julia
maximum_step = _unbounded_bound(T)
# For each eligible candidate:
relaxed_step = (workspace.reduced_costs[index] +
                ifelse(coefficient < zero(T), -tolerance, tolerance)) / coefficient
maximum_step = !isfinite(maximum_step) || relaxed_step < bound_value(maximum_step) ?
               Bound(relaxed_step) : maximum_step
# Second pass accepts every step while maximum_step is unbounded, otherwise
# requires step <= bound_value(maximum_step).
```

Construct auxiliary bounds as finite `Bound(zero(T))`, `Bound(one(T))`, `Bound(-one(T))`, or `Bound(±T(1000))`. All fixed/unbounded tests use `_is_fixed` and `isfinite`; bound values are read only after those tests.

- [ ] **Step 5: Dispatch exact and floating recession roundoff**

Define two methods:

```julia
_recession_row_roundoff(A::SparseMatrixCSC{T,Int}, structural::Vector{T},
                        ::Val{true}) where {T<:Rational} = zeros(T, size(A, 1))

function _recession_row_roundoff(A::SparseMatrixCSC{T,Int},
                                 structural::Vector{T}, ::Val{false}) where {T<:AbstractFloat}
    magnitudes = zeros(T, size(A, 1))
    terms = zeros(Int, size(A, 1))
    for column in axes(A, 2)
        for position in A.colptr[column]:(A.colptr[column + 1] - 1)
            row = A.rowval[position]
            magnitudes[row] += abs(A.nzval[position] * structural[column])
            terms[row] += 1
        end
    end
    for row in eachindex(magnitudes)
        relative_error = T(terms[row]) * eps(T)
        magnitudes[row] = relative_error < one(T) ?
            relative_error / (one(T) - relative_error) * magnitudes[row] : T(Inf)
    end
    return magnitudes
end
```

Call with `_is_exact(T)`. Exact feasibility, optimality, ray checks, and Harris cutoff use zero; floating paths retain non-finite checks and current tolerance semantics.

- [ ] **Step 6: Make every solver exit return `Solution{T}`**

Change the public entry and result helper to:

```julia
function solve(problem::LinearProblem{T}; relax_integrality::Bool=false,
               options=nothing)::Solution{T} where {T<:Real}
    typed_options = options === nothing ? SolverOptions(T) : SolverOptions(T, options)
    context = SolveContext(time_ns(), typed_options.time_limit)
    @logmsg typed_options.log_level "Starting solve" name=problem.name algorithm=typed_options.algorithm
    time_limit_reached(context) &&
        return _finish_solve(T, context, typed_options, TIME_LIMIT,
                             "time limit reached")
    typed_options.algorithm == :dual ||
        return _finish_solve(T, context, typed_options, ALGORITHM_NOT_SUPPORTED,
                             "only the dual simplex algorithm is supported")
    error = _validation_error(problem)
    isnothing(error) ||
        return _finish_solve(T, context, typed_options, INVALID_MODEL, error)
    if !relax_integrality && !is_continuous(problem)
        return _finish_solve(T, context, typed_options, MIP_NOT_SUPPORTED,
                             "discrete domains require relax_integrality=true")
    end

    continuous_problem = JSimplex.relax_integrality(problem)
    presolved = identity_presolve(continuous_problem)
    scaling = identity_scaling(presolved.problem)
    working_problem = _minimization_problem(presolved.problem)
    time_limit_reached(context) &&
        return _finish_solve(T, context, typed_options, TIME_LIMIT,
                             "time limit reached")
    run = _solve_continuous_dual(
        working_problem, typed_options;
        stop_requested=() -> time_limit_reached(context),
    )
    run.status == OPTIMAL || return _finish_solve(
        T, context, typed_options, run.status, run.message;
        iterations=run.iterations, refactorizations=run.refactorizations,
    )

    primal = postsolve_primal(presolved, unscale_primal(scaling, run.primal))
    objective = dot(problem.objective, primal) + problem.objective_constant
    if !isfinite(objective) ||
       !_within_primal_bounds(primal, continuous_problem.column_lower,
                              continuous_problem.column_upper,
                              typed_options.primal_tolerance) ||
       !_within_primal_bounds(continuous_problem.A * primal,
                              continuous_problem.row_lower,
                              continuous_problem.row_upper,
                              typed_options.primal_tolerance)
        return _finish_solve(
            T, context, typed_options, NUMERICAL_ERROR,
            "restored primal failed original-model feasibility checks";
            iterations=run.iterations, refactorizations=run.refactorizations,
        )
    end
    return _finish_solve(
        T, context, typed_options, OPTIMAL, run.message;
        primal, objective_value=objective, iterations=run.iterations,
        refactorizations=run.refactorizations,
    )
end

function _finish_solve(::Type{T}, context::SolveContext,
                       options::SolverOptions{T}, status::TerminationStatus,
                       message::String; primal=nothing, objective_value=nothing,
                       iterations::Int=0, refactorizations::Int=0) where {T<:Real}
    statistics = SolveStatistics(; iterations, refactorizations,
                                 elapsed_seconds=elapsed_seconds(context))
    @logmsg options.log_level "Solve terminated" status iterations refactorizations elapsed_seconds=statistics.elapsed_seconds
    return Solution{T}(status, objective_value, primal, statistics, message)
end
```

`_minimization_problem`, restoration validation, zero-row solving, MIP rejection, algorithm rejection, invalid-model, iteration-limit, time-limit, infeasible, unbounded, numerical-error, and optimal exits must all retain the problem's `T`. Keep `SolveContext` and elapsed seconds Float64.

- [ ] **Step 7: Add resource/status type-stability coverage**

Add a type-parameterized helper and invoke it for all four supported acceptance types:

```julia
function test_typed_statuses(::Type{T}) where {T}
    sparse = JSimplex.SparseArrays.sparse
    infeasible = LinearProblem(sparse(reshape(T[1], 1, 1)), T[1];
                               row_lower=T[2], column_upper=T[1])
    unbounded = LinearProblem(JSimplex.SparseArrays.spzeros(T, 0, 1), T[1];
                              objective_sense=MAX_SENSE)
    pivoting = LinearProblem(sparse(T[1 0; -1 1]), T[1, 1];
                             row_lower=T[1, 1])
    discrete = LinearProblem(JSimplex.SparseArrays.spzeros(T, 0, 1), T[-1];
                             column_upper=T[1], variable_domains=[INTEGER])
    numerical = LinearProblem(sparse(reshape(T[1], 1, 1)), T[1]; row_lower=T[1])
    invalid = deepcopy(pivoting)
    empty!(invalid.objective)

    cases = (
        (@inferred(solve(infeasible)), INFEASIBLE),
        (@inferred(solve(unbounded)), UNBOUNDED),
        (@inferred(solve(pivoting; options=SolverOptions(T; iteration_limit=0))),
         ITERATION_LIMIT),
        (@inferred(solve(pivoting; options=SolverOptions(T; time_limit=0.0))),
         TIME_LIMIT),
        (@inferred(solve(discrete)), MIP_NOT_SUPPORTED),
        (@inferred(solve(pivoting; options=SolverOptions(T; algorithm=:primal))),
         ALGORITHM_NOT_SUPPORTED),
        (@inferred(solve(invalid)), INVALID_MODEL),
        (@inferred(solve(numerical; options=SolverOptions(T; zero_tolerance=T(2)))),
         NUMERICAL_ERROR),
    )
    for (result, expected) in cases
        @test result isa Solution{T}
        @test result.status == expected
        @test isnothing(result.primal)
        @test isnothing(result.objective_value)
    end

    refactorized = @inferred solve(
        pivoting; options=SolverOptions(T; refactorization_interval=1),
    )
    @test refactorized.status == OPTIMAL
    @test refactorized.statistics.iterations == 2
    @test refactorized.statistics.refactorizations == 2

    maximum = LinearProblem(JSimplex.SparseArrays.spzeros(T, 0, 1), T[2];
        objective_constant=T(1), objective_sense=MAX_SENSE,
        column_lower=T[0], column_upper=T[3])
    @test (@inferred solve(maximum)).objective_value == T(7)
    @test (@inferred solve(discrete; relax_integrality=true)).status == OPTIMAL
end

foreach(test_typed_statuses, (Float32, Float64, BigFloat, Rational{BigInt}))
```

Preserve the existing tests proving logger and callback exceptions propagate instead of becoming `NUMERICAL_ERROR`.

- [ ] **Step 8: Run dual, solver, and complete package tests**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/dual_simplex_tests.jl"); include("test/solver_tests.jl")'
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
```

Expected: PASS for all scalar types and every termination status; rational expected values compare exactly.

- [ ] **Step 9: Commit the generic solver kernel**

```sh
git add src/dual_simplex.jl src/solver.jl test/dual_simplex_tests.jl test/solver_tests.jl
git commit -m "feat: solve LPs with parametric arithmetic"
```

---

### Task 8: Inference and Hot-Structure Acceptance Suite

**Files:**
- Create: `test/numeric_type_tests.jl`
- Modify: `test/runtests.jl`
- Modify: any `src/*.jl` file identified by the new inference checks

**Interfaces:**
- Consumes: all typed public and internal APIs from Tasks 1–7.
- Produces: mandatory `@inferred`, ambiguity, scalar-preservation, and hot-field regression gates.

- [ ] **Step 1: Create the cross-cutting acceptance test file**

Add `include("numeric_type_tests.jl")` after all focused component tests, then create `test/numeric_type_tests.jl` with:

```julia
function abstract_numeric_storage(field)
    field === Any && return true
    field <: AbstractVector || return false
    element = eltype(field)
    return element === Real || element === Number ||
           (element isa DataType && isabstracttype(element) && element <: Number)
end

function test_numeric_inference(::Type{T}) where {T}
    problem = typed_bounded_problem(T)
    options = @inferred SolverOptions(T)
    relaxed = @inferred JSimplex.relax_integrality(problem)
    presolved = @inferred JSimplex.identity_presolve(relaxed)
    scaling = @inferred JSimplex.identity_scaling(presolved.problem)
    workspace = @inferred JSimplex.initialize_workspace(problem, options)
    factor = workspace.factorization
    run = @inferred JSimplex._solve_continuous_dual(problem, options)
    solution = @inferred solve(problem)
    eta = JSimplex.PackedEta{T}(Int[1], T[one(T)], 1)

    @test @inferred(JSimplex.forward_solve(
        factor, zeros(T, size(problem.A, 1)))) isa Vector{T}
    @test @inferred(JSimplex.recompute!(workspace)) === workspace
    @test @inferred(JSimplex.postsolve_primal(
        presolved,
        JSimplex.unscale_primal(scaling, zeros(T, size(problem.A, 2))),
    )) isa Vector{T}
    @test solution isa Solution{T}

    for instance in (problem, options, workspace, factor, scaling, presolved,
                     run, solution, eta, first(problem.row_lower))
        for field in fieldtypes(typeof(instance))
            @test field !== Any
            @test !abstract_numeric_storage(field)
        end
    end
end

@testset "Numeric type stability" begin
    foreach(test_numeric_inference, (Float32, Float64, BigFloat, Rational{BigInt}))
    exact_path = joinpath(@__DIR__, "fixtures", "parser", "exact-rational.mps")
    fixed_path = joinpath(@__DIR__, "fixtures", "parser", "basic-fixed.mps")
    free_path = joinpath(@__DIR__, "fixtures", "parser", "basic-free.mps")
    @test @inferred(read_mps(exact_path)) isa LinearProblem{Float64}
    @test @inferred(read_mps(exact_path; value_type=Rational{BigInt})) isa
          LinearProblem{Rational{BigInt}}
    @test @inferred(read_mps(fixed_path; format=:fixed,
                             value_type=Rational{BigInt})) isa
          LinearProblem{Rational{BigInt}}
    @test @inferred(read_mps(free_path; format=:free,
                             value_type=Rational{BigInt})) isa
          LinearProblem{Rational{BigInt}}

    records = @inferred JSimplex._parse_mps_file(
        exact_path, Rational{BigInt}; format=:free,
    )
    for field in fieldtypes(typeof(records))
        @test field !== Any
        @test !abstract_numeric_storage(field)
    end
    @test isempty(Test.detect_ambiguities(JSimplex; recursive=true))
end
```

Also move or expose `typed_bounded_problem` from `solver_tests.jl` in a top-level test helper section so it is available when this file is included. Add explicit field checks rejecting `AbstractVector{<:Real}`, `Vector{Real}`, and abstract factorization storage, not merely `Any`.

- [ ] **Step 2: Run the acceptance file and record the first inference mismatch**

Run:

```sh
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/solver_tests.jl"); include("test/numeric_type_tests.jl")'
```

Expected: FAIL if any constructor, workspace operation, MPS keyword path, solve status, or factorization backend returns a wider inferred type than its runtime result.

- [ ] **Step 3: Tighten dispatch at each reported boundary**

For each mismatch, split on type parameters rather than adding return assertions or `Any`. The allowed patterns are:

```julia
function operation(value::Container{T}) where {T}
    result = zeros(T, length(value.data))
    return result
end

policy(::Type{T}) where {T<:Rational} = exact_policy(T)
policy(::Type{T}) where {T<:AbstractFloat} = floating_policy(T)
```

Use concrete tuple recursion for postsolve steps and concrete backend wrapper dispatch for factorization. Small `Union{Nothing,T}` result fields are allowed; abstract numeric containers, `base::Any`, and broad exception catches are not.

- [ ] **Step 4: Run the complete mandatory suite twice**

Run:

```sh
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
```

Expected: both runs PASS, demonstrating that ambient compilation order does not hide inference or ambiguity failures.

- [ ] **Step 5: Commit mandatory stability gates**

```sh
git add test/numeric_type_tests.jl test/runtests.jl test/solver_tests.jl src/JSimplex.jl src/numeric.jl src/options.jl src/model.jl src/transformations.jl src/mps.jl src/mps/records.jl src/mps/parser.jl src/mps/build.jl src/factorization.jl src/simplex.jl src/dual_simplex.jl src/solver.jl
git commit -m "test: enforce numeric type stability"
```

---

### Task 9: Development-Only JET Validation

**Files:**
- Modify: `dev/Project.toml`
- Create: `dev/tests/jet_tests.jl`
- Modify: `dev/tests/runtests.jl`
- Modify: source files only when JET reports actionable runtime dispatch in the selected kernels

**Interfaces:**
- Consumes: representative nonempty Float64 and `Rational{BigInt}` solve/workspace calls.
- Produces: development-only `JET.@test_opt` gates without changing root dependencies.

- [ ] **Step 1: Add JET to the development project and failing checks**

Add this dependency only under `dev/Project.toml` `[deps]`:

```toml
JET = "c3a54625-cd67-489e-a8e7-0a5a0ff4e31b"
```

Create `dev/tests/jet_tests.jl`:

```julia
using JET

@testset "JET typed solver kernels" begin
    float_problem = LinearProblem(JSimplex.SparseArrays.sparse([1.0 1.0]),
                                  [-1.0, -2.0]; row_upper=[3.0])
    rational_problem = LinearProblem(
        JSimplex.SparseArrays.sparse(Rational{BigInt}[1 1]),
        Rational{BigInt}[-1, -2]; row_upper=Rational{BigInt}[3],
    )
    float_workspace = JSimplex.initialize_workspace(float_problem, SolverOptions(Float64))
    rational_workspace = JSimplex.initialize_workspace(
        rational_problem, SolverOptions(Rational{BigInt}),
    )

    JET.@test_opt target_modules=(JSimplex,) JSimplex.recompute!(float_workspace)
    JET.@test_opt target_modules=(JSimplex,) JSimplex.recompute!(rational_workspace)
    JET.@test_opt target_modules=(JSimplex,) solve(float_problem)
    JET.@test_opt target_modules=(JSimplex,) solve(rational_problem)
end
```

Include it at the end of `dev/tests/runtests.jl`.

- [ ] **Step 2: Instantiate development dependencies and run JET tests**

Run:

```sh
julia --startup-file=no --project=dev -e 'using Pkg; Pkg.develop(path="."); Pkg.instantiate()'
julia --startup-file=no --project=dev dev/tests/runtests.jl
```

Expected: dependency setup succeeds; JET may initially report runtime dispatch at remaining untyped boundaries.

- [ ] **Step 3: Resolve only actionable JSimplex inference findings**

Fix reports originating in JSimplex by adding parametric method relationships or concrete local initialization. Suppress neither JSimplex reports nor entire call stacks. Reports exclusively inside Julia, UMFPACK, or JET itself may be isolated with the narrowest call boundary and a test comment containing the exact upstream frame and why it is outside JSimplex's control.

- [ ] **Step 4: Re-run development, package, and GLPK reference checks**

Run:

```sh
julia --startup-file=no --project=dev dev/tests/runtests.jl
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
julia --startup-file=no --project=dev dev/run_suite.jl --dataset afiro --compare-glpk
```

Expected: all commands PASS; AFIRO status/objective matches GLPK; no `Manifest.toml` is staged.

- [ ] **Step 5: Commit the isolated development analysis**

```sh
git add dev/Project.toml dev/tests/jet_tests.jl dev/tests/runtests.jl src/JSimplex.jl src/numeric.jl src/options.jl src/model.jl src/transformations.jl src/mps.jl src/mps/records.jl src/mps/parser.jl src/mps/build.jl src/factorization.jl src/simplex.jl src/dual_simplex.jl src/solver.jl
git commit -m "test: add development JET checks"
```

---

### Task 10: Documentation, Release Metadata, and Final Verification

**Files:**
- Modify: `README.md`
- Modify: public docstrings in `src/model.jl`, `src/options.jl`, `src/mps.jl`, and `src/solver.jl`
- Modify: `Project.toml`
- Review: `.github/workflows/ci.yml`
- Review: `.github/workflows/extended.yml`

**Interfaces:**
- Consumes: the completed public API and all acceptance commands.
- Produces: version `0.4.0`, English migration documentation, reproducible examples, and final clean-tree evidence.

- [ ] **Step 1: Write documentation assertions before editing prose**

Run this scan and keep its expected missing topics as the documentation checklist:

```sh
rg -n 'Bound|bound_value|value_type|Rational\{BigInt\}|BigFloat|setprecision|dense LU|UMFPACK|SolverOptions\(T' README.md src/model.jl src/options.jl src/mps.jl src/solver.jl
```

Expected before the edit: several required public terms are absent or old text still claims that all arrays are Float64.

- [ ] **Step 2: Rewrite model, option, MPS, and solve documentation**

Document these exact contracts with runnable Julia examples:

```julia
rational_problem = LinearProblem(
    sparse(Rational{BigInt}[1 1]), Rational{BigInt}[1, 2];
    row_lower=Rational{BigInt}[1], row_upper=[nothing],
)
exact_mps = read_mps("test/fixtures/parser/exact-rational.mps";
                     value_type=Rational{BigInt})

setprecision(BigFloat, 256) do
    big_problem = LinearProblem(sparse(BigFloat[1 1]), BigFloat[1, 2];
                                row_lower=BigFloat[1])
    solve(big_problem)
end
```

Explain type inference, integer-only Float64 fallback, `value_type=T`, `Bound{T}`, `nothing`, accepted signed float infinities, `isfinite(bound)`, `bound_value`, exact zero rational defaults, option conversion, typed result fields, Float64 UMFPACK versus generic dense LU, fixed-width rational limitations, and unchanged Float64 time measurement. Add a migration note showing how code that previously read numeric bound fields must now use the public bound helpers.

- [ ] **Step 3: Update release and development documentation**

Set:

```toml
version = "0.4.0"
```

Update the development section to list JET alongside GLPK and BenchmarkTools, while stating that root production dependencies are still only `LinearAlgebra`, `SparseArrays`, and `Logging`. Keep Julia 1.13 commands, fixture/data registry instructions, MPS feature tables, and time/iteration-limit text intact.

- [ ] **Step 4: Check documentation, dependency isolation, and workflows**

Run:

```sh
rg -n 'Float64 arrays|Use `-Inf` and `Inf` for infinite bounds' README.md src
git diff --check
git diff -- Project.toml dev/Project.toml
```

Expected: obsolete Float64-only/bound instructions are absent; whitespace checks pass; root `Project.toml` changes only the version; JET appears only in `dev/Project.toml`; CI still targets Julia 1.13 and extended validation still invokes the development tests.

- [ ] **Step 5: Run the complete final verification matrix**

Run:

```sh
julia --version
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
julia --startup-file=no --project=dev dev/tests/runtests.jl
julia --startup-file=no --project=dev dev/run_suite.jl --dataset afiro --compare-glpk
git diff --check
git status --short
```

Expected: Julia reports 1.13.x; all package and development tests pass; AFIRO agrees with GLPK; diff check is clean; status contains only intended source/test/doc/project changes and no manifest.

- [ ] **Step 6: Commit the release documentation**

```sh
git add README.md Project.toml src/model.jl src/options.jl src/mps.jl src/solver.jl
git commit -m "docs: release parametric numeric types"
```

- [ ] **Step 7: Perform post-commit cleanliness and history verification**

Run:

```sh
git status --short
git log --oneline --decorate -10
```

Expected: the worktree is empty and the ten task commits form a reviewable sequence ending in the `0.4.0` documentation/release commit.
