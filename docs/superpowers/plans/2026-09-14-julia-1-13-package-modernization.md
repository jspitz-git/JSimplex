# JSimplex Julia 1.13 Package Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the 2013 proof-of-concept into a tested Julia 1.13 package with a native fixed/free MPS reader, an idiomatic LP solve API, and no production dependency on GLPK.

**Architecture:** `LinearProblem` is the format- and solver-independent boundary. Input adapters build it, an explicit presolve/scaling pipeline creates a private `SimplexWorkspace`, and algorithm-specific code operates through a small basis-factorization interface. Fast tests are self-contained; GLPK and large data collections live only in the development environment.

**Tech Stack:** Julia 1.13, `SparseArrays`, `LinearAlgebra`, `Logging`, Julia `Test`, Julia artifacts, GLPK.jl and BenchmarkTools in `dev/` only.

**Spec:** `docs/superpowers/specs/2026-09-14-julia-1-13-package-modernization-design.md`

**MPS references:** IBM CPLEX documentation for
[standard records](https://www.ibm.com/docs/en/icos/22.1.2?topic=standard-records-in-mps-format),
[integer extensions](https://www.ibm.com/docs/en/cofz/22.1.2?topic=extensions-integer-variables-in-mps-files),
and [objective sense/name/offset](https://www.ibm.com/docs/en/icos/22.1.0?topic=extensions-objective-sense-name-offset-in-mps-files).

## Global Constraints

- Support Julia 1.13 with `julia = "1.13"` in the production project.
- Do not add GLPK, BenchmarkTools, MathOptInterface, or JuMP to the production project.
- Write all repository documentation, docstrings, comments, diagnostics, and developer-facing text in English.
- Never mutate the caller's `LinearProblem` during `solve`.
- Never relax an integral domain unless `relax_integrality=true` was passed explicitly.
- Keep primal simplex, effective presolve, non-identity scaling, branch-and-bound, MOI/JuMP adapters, quadratic sections, SOS constraints, and indicator constraints out of this implementation.
- Use `-Inf` and `Inf` for unbounded limits.
- Keep mandatory `Pkg.test()` runs deterministic, offline, and independent of GLPK.
- Give iteration and wall-clock limits distinct termination statuses.

## Target file map

- `Project.toml`: production identity, standard-library dependencies, and Julia compatibility.
- `src/JSimplex.jl`: module assembly and the deliberately small export list.
- `src/options.jl`: statuses, solver options, solution statistics, and public result types.
- `src/model.jl`: objective/domain enums, `LinearProblem`, copying, and validation.
- `src/transformations.jl`: integrality relaxation plus identity presolve/scaling and reverse mappings.
- `src/mps.jl`: public `read_mps` entry point and parser error type.
- `src/mps/records.jl`: fixed/free lexical records and parser accumulator types.
- `src/mps/parser.jl`: section state machine and symbolic MPS parsing.
- `src/mps/build.jl`: named-set selection and conversion into `LinearProblem`.
- `src/factorization.jl`: sparse LU plus product-form update implementation.
- `src/simplex.jl`: shared basis and workspace representation and initialization.
- `src/dual_simplex.jl`: dual pricing, ratio test, pivots, feasibility phase, and solve loop.
- `src/solver.jl`: public pipeline, relaxation gate, timing, and solution conversion.
- `test/*.jl`: focused unit and regression tests.
- `test/fixtures/`: small checked-in parser and solver inputs.
- `dev/`: isolated reference-solver, benchmark, artifact, and data-suite tooling.
- `.github/workflows/ci.yml`: clean Julia 1.13 package test job.
- `README.md` and `LICENSE`: English user documentation and licensing.

---

### Task 1: Create the package shell and result contracts

**Files:**
- Create: `Project.toml`
- Create: `src/JSimplex.jl`
- Create: `src/options.jl`
- Create: `test/Project.toml`
- Create: `test/runtests.jl`
- Create: `test/options_tests.jl`

**Interfaces:**
- Consumes: no earlier task interfaces.
- Produces: `TerminationStatus`, `SolverOptions`, `SolveStatistics`, and `Solution`; every later task imports these from `JSimplex` or uses them internally.

- [ ] **Step 1: Add package metadata and a failing public-contract test**

Create `Project.toml` with this exact package identity and dependency boundary:

```toml
name = "JSimplex"
uuid = "68c30f08-d64b-42cf-ac89-1dfed499aac3"
authors = ["JSimplex contributors"]
version = "0.3.0"

[deps]
LinearAlgebra = "37e2e46d-f89d-539d-b4ee-838fcccc9c8e"
Logging = "56ddb016-857b-54e1-b83d-db4d58db5568"
SparseArrays = "2f01184e-e22b-5df5-ae63-d93ebab69eaf"

[compat]
julia = "1.13"
```

Create `test/Project.toml`:

```toml
[deps]
Test = "8dfed614-e22c-5e08-85e1-65c5234f0b40"
```

Create `test/runtests.jl`:

```julia
using JSimplex
using Test

@testset "JSimplex" begin
    include("options_tests.jl")
end
```

Create `test/options_tests.jl` with tests for default values, custom limits, and invalid options:

```julia
@testset "Solver options and results" begin
    options = SolverOptions()
    @test options.algorithm == :dual
    @test options.iteration_limit == 100_000
    @test options.time_limit == Inf

    limited = SolverOptions(iteration_limit=17, time_limit=2.5)
    @test limited.iteration_limit == 17
    @test limited.time_limit == 2.5

    @test_throws ArgumentError SolverOptions(iteration_limit=-1)
    @test_throws ArgumentError SolverOptions(time_limit=-0.1)
    @test_throws ArgumentError SolverOptions(primal_tolerance=0.0)

    stats = SolveStatistics(iterations=3, elapsed_seconds=0.25,
                            refactorizations=1)
    result = Solution(OPTIMAL, 4.0, [1.0, 2.0], stats, "optimal")
    @test result.status == OPTIMAL
    @test result.objective_value == 4.0
    @test result.primal == [1.0, 2.0]
end
```

- [ ] **Step 2: Run the test and verify that the package module is missing**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: FAIL because `src/JSimplex.jl` does not exist or `SolverOptions` is undefined.

- [ ] **Step 3: Implement the module and result contracts**

Create `src/JSimplex.jl`:

```julia
module JSimplex

using LinearAlgebra
using Logging
using SparseArrays

include("options.jl")

export ALGORITHM_NOT_SUPPORTED, INFEASIBLE, INVALID_MODEL, ITERATION_LIMIT,
       MIP_NOT_SUPPORTED, NUMERICAL_ERROR, OPTIMAL, TIME_LIMIT, UNBOUNDED,
       Solution, SolveStatistics, SolverOptions, TerminationStatus

end
```

Create `src/options.jl` with these concrete contracts:

```julia
@enum TerminationStatus::UInt8 begin
    OPTIMAL
    INFEASIBLE
    UNBOUNDED
    ITERATION_LIMIT
    TIME_LIMIT
    NUMERICAL_ERROR
    INVALID_MODEL
    MIP_NOT_SUPPORTED
    ALGORITHM_NOT_SUPPORTED
end

struct SolverOptions
    primal_tolerance::Float64
    dual_tolerance::Float64
    zero_tolerance::Float64
    iteration_limit::Int
    time_limit::Float64
    refactorization_interval::Int
    log_level::LogLevel

    algorithm::Symbol

    function SolverOptions(;
        primal_tolerance::Real=1.0e-7,
        dual_tolerance::Real=1.0e-7,
        zero_tolerance::Real=1.0e-12,
        iteration_limit::Integer=100_000,
        time_limit::Real=Inf,
        refactorization_interval::Integer=20,
        log_level::LogLevel=Logging.Debug,
        algorithm::Symbol=:dual,
    )
        primal_tolerance > 0 || throw(ArgumentError("primal_tolerance must be positive"))
        dual_tolerance > 0 || throw(ArgumentError("dual_tolerance must be positive"))
        zero_tolerance > 0 || throw(ArgumentError("zero_tolerance must be positive"))
        iteration_limit >= 0 || throw(ArgumentError("iteration_limit must be nonnegative"))
        time_limit >= 0 || throw(ArgumentError("time_limit must be nonnegative"))
        refactorization_interval > 0 || throw(ArgumentError("refactorization_interval must be positive"))
        return new(Float64(primal_tolerance), Float64(dual_tolerance),
                   Float64(zero_tolerance), Int(iteration_limit),
                   Float64(time_limit), Int(refactorization_interval),
                   log_level, algorithm)
    end
end

Base.@kwdef struct SolveStatistics
    iterations::Int = 0
    elapsed_seconds::Float64 = 0.0
    refactorizations::Int = 0
end

struct Solution
    status::TerminationStatus
    objective_value::Union{Nothing,Float64}
    primal::Union{Nothing,Vector{Float64}}
    statistics::SolveStatistics
    message::String
end
```

- [ ] **Step 4: Run the package tests**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: PASS for `Solver options and results`.

- [ ] **Step 5: Commit the package shell**

```bash
git add Project.toml src/JSimplex.jl src/options.jl test/Project.toml test/runtests.jl test/options_tests.jl
git commit -m "build: create Julia 1.13 package shell"
```

### Task 2: Add the validated linear-problem model

**Files:**
- Create: `src/model.jl`
- Modify: `src/JSimplex.jl`
- Create: `test/model_tests.jl`
- Modify: `test/runtests.jl`

**Interfaces:**
- Consumes: the module shell from Task 1.
- Produces: `LinearProblem`, `ObjectiveSense`, `VariableDomain`, `is_continuous`, and internal `_validation_error(problem)::Union{Nothing,String}`.

- [ ] **Step 1: Write failing model-construction and validation tests**

Create `test/model_tests.jl`:

```julia
@testset "LinearProblem" begin
    A = sparse([1, 1, 2], [1, 2, 2], [1.0, 2.0, -1.0], 2, 2)
    problem = LinearProblem(
        A, [3.0, 4.0];
        row_lower=[1.0, -Inf], row_upper=[1.0, 5.0],
        column_lower=[0.0, -Inf], column_upper=[Inf, 7.0],
        variable_domains=[CONTINUOUS, INTEGER],
        objective_sense=MAX_SENSE, objective_constant=2.0,
        name="sample", row_names=["balance", "cap"],
        column_names=["x", "y"],
    )
    @test size(problem.A) == (2, 2)
    @test problem.objective == [3.0, 4.0]
    @test problem.objective_sense == MAX_SENSE
    @test !is_continuous(problem)

    A[1, 1] = 99.0
    @test problem.A[1, 1] == 1.0

    @test_throws ArgumentError LinearProblem(sparse([1.0 2.0]), [1.0])
    @test_throws ArgumentError LinearProblem(
        sparse(reshape([1.0], 1, 1)), [NaN],
    )
    @test_throws ArgumentError LinearProblem(
        sparse(reshape([1.0], 1, 1)), [1.0];
        column_lower=[2.0], column_upper=[1.0],
    )
end
```

Include it from `test/runtests.jl` after `options_tests.jl`.

- [ ] **Step 2: Run the focused tests and verify the API is undefined**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: FAIL with `UndefVarError: LinearProblem not defined`.

- [ ] **Step 3: Implement enums, copying construction, and validation**

Create `src/model.jl` with the following field names and constructor signature:

```julia
@enum ObjectiveSense::UInt8 MIN_SENSE MAX_SENSE
@enum VariableDomain::UInt8 begin
    CONTINUOUS
    INTEGER
    BINARY
    SEMI_CONTINUOUS
    SEMI_INTEGER
end

struct LinearProblem
    A::SparseMatrixCSC{Float64,Int}
    objective::Vector{Float64}
    objective_constant::Float64
    objective_sense::ObjectiveSense
    row_lower::Vector{Float64}
    row_upper::Vector{Float64}
    column_lower::Vector{Float64}
    column_upper::Vector{Float64}
    variable_domains::Vector{VariableDomain}
    name::String
    row_names::Vector{String}
    column_names::Vector{String}
end

function LinearProblem(
    A::SparseMatrixCSC,
    objective::AbstractVector{<:Real};
    objective_constant::Real=0.0,
    objective_sense::ObjectiveSense=MIN_SENSE,
    row_lower::AbstractVector{<:Real}=fill(-Inf, size(A, 1)),
    row_upper::AbstractVector{<:Real}=fill(Inf, size(A, 1)),
    column_lower::AbstractVector{<:Real}=zeros(size(A, 2)),
    column_upper::AbstractVector{<:Real}=fill(Inf, size(A, 2)),
    variable_domains::AbstractVector{VariableDomain}=fill(CONTINUOUS, size(A, 2)),
    name::AbstractString="",
    row_names::AbstractVector{<:AbstractString}=String[],
    column_names::AbstractVector{<:AbstractString}=String[],
)
    matrix = SparseMatrixCSC{Float64,Int}(A)
    problem = LinearProblem(
        copy(matrix), Float64.(objective), Float64(objective_constant),
        objective_sense, Float64.(row_lower), Float64.(row_upper),
        Float64.(column_lower), Float64.(column_upper),
        collect(variable_domains), String(name), String.(row_names),
        String.(column_names),
    )
    error = _validation_error(problem)
    isnothing(error) || throw(ArgumentError(error))
    return problem
end

is_continuous(problem::LinearProblem) = all(==(CONTINUOUS), problem.variable_domains)
```

Implement `_validation_error` with these exact checks in order: objective
length equals `size(A, 2)`; row-bound lengths equal `size(A, 1)`; column-bound
and domain lengths equal `size(A, 2)`; each names vector is empty or has the
corresponding dimension; matrix/objective/objective constant contain no `NaN`
and all coefficients are finite; each lower bound is not `NaN` and is no larger
than its upper bound; binary bounds intersect `[0, 1]`; semi-domain active
upper bounds are positive. Return the first English diagnostic string or
`nothing`.

Include `model.jl` after `options.jl`, export all seven enum values, both enum
types, `LinearProblem`, and `is_continuous`.

- [ ] **Step 4: Run model and package tests**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: PASS for `Solver options and results` and `LinearProblem`.

- [ ] **Step 5: Commit the model**

```bash
git add src/JSimplex.jl src/model.jl test/runtests.jl test/model_tests.jl
git commit -m "feat: add validated linear problem model"
```

### Task 3: Add relaxation, presolve, scaling, and basis boundaries

**Files:**
- Create: `src/transformations.jl`
- Create: `src/simplex.jl`
- Modify: `src/JSimplex.jl`
- Create: `test/transformations_tests.jl`
- Modify: `test/runtests.jl`

**Interfaces:**
- Consumes: `LinearProblem` and `VariableDomain` from Task 2.
- Produces: internal `relax_integrality`, `PresolveResult`, `Scaling`, `Basis`, `VariableState`, `identity_presolve`, `identity_scaling`, `unscale_primal`, and `postsolve_primal`.

- [ ] **Step 1: Write failing tests for relaxation and identity transforms**

Create `test/transformations_tests.jl`:

```julia
@testset "Solver transformations" begin
    problem = LinearProblem(
        sparse(reshape([1.0, 1.0, 1.0, 1.0], 1, 4)), zeros(4);
        column_lower=[0.0, -2.0, 3.0, 2.0],
        column_upper=[1.0, 8.0, 9.0, 7.0],
        variable_domains=[BINARY, INTEGER, SEMI_CONTINUOUS, SEMI_INTEGER],
    )
    relaxed = JSimplex.relax_integrality(problem)
    @test all(==(CONTINUOUS), relaxed.variable_domains)
    @test relaxed.column_lower == [0.0, -2.0, 0.0, 0.0]
    @test relaxed.column_upper == [1.0, 8.0, 9.0, 7.0]
    @test problem.variable_domains[1] == BINARY
    @test problem.column_lower[3] == 3.0

    presolved = JSimplex.identity_presolve(relaxed)
    scaling = JSimplex.identity_scaling(presolved.problem)
    x = [0.25, 1.0, 4.0, 3.0]
    @test JSimplex.unscale_primal(scaling, x) == x
    @test JSimplex.unscale_dual(scaling, [2.0]) == [2.0]
    @test JSimplex.postsolve_primal(presolved, x) == x
end
```

Include it from `test/runtests.jl`.

- [ ] **Step 2: Run tests and verify the transformation API is missing**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: FAIL with `UndefVarError: relax_integrality not defined`.

- [ ] **Step 3: Implement concrete no-op pipeline boundaries**

Create `src/transformations.jl`:

```julia
abstract type AbstractPostsolveStep end

struct PresolveResult
    problem::LinearProblem
    postsolve_stack::Vector{AbstractPostsolveStep}
    original_column_count::Int
end

struct Scaling
    row_factors::Vector{Float64}
    column_factors::Vector{Float64}
end

identity_presolve(problem::LinearProblem) =
    PresolveResult(problem, AbstractPostsolveStep[], size(problem.A, 2))

identity_scaling(problem::LinearProblem) =
    Scaling(ones(size(problem.A, 1)), ones(size(problem.A, 2)))

unscale_primal(scaling::Scaling, x::AbstractVector{<:Real}) =
    Float64.(x) ./ scaling.column_factors

unscale_dual(scaling::Scaling, y::AbstractVector{<:Real}) =
    Float64.(y) ./ scaling.row_factors

function postsolve_primal(result::PresolveResult, x::AbstractVector{<:Real})
    restored = Float64.(x)
    for step in Iterators.reverse(result.postsolve_stack)
        restored = postsolve_primal(step, restored)
    end
    return restored[1:result.original_column_count]
end
```

Implement `relax_integrality(problem)` by copying the model, setting every
domain to `CONTINUOUS`, retaining ordinary integer/binary bounds, and replacing
the active lower bound of each semi-domain with
`min(0.0, column_lower[j])` while replacing its upper bound with
`max(0.0, column_upper[j])`. Construct a fresh `LinearProblem` so no source
array is shared.

Create the shared basis types in `src/simplex.jl`:

```julia
@enum VariableState::UInt8 BASIC AT_LOWER AT_UPPER FREE_NONBASIC

struct Basis
    basic_indices::Vector{Int}
    states::Vector{VariableState}
end

function Basis(basic_indices::AbstractVector{<:Integer},
               states::AbstractVector{VariableState})
    return Basis(Int.(basic_indices), collect(states))
end
```

Include `transformations.jl` and `simplex.jl` after `model.jl`. Keep these
pipeline and basis types internal for this release.

- [ ] **Step 4: Run all tests**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: PASS, including `Solver transformations`.

- [ ] **Step 5: Commit the transformation boundaries**

```bash
git add src/JSimplex.jl src/transformations.jl src/simplex.jl test/runtests.jl test/transformations_tests.jl
git commit -m "feat: define solver transformation boundaries"
```

### Task 4: Parse symbolic fixed- and free-format MPS records

**Files:**
- Create: `src/mps.jl`
- Create: `src/mps/records.jl`
- Create: `src/mps/parser.jl`
- Modify: `src/JSimplex.jl`
- Create: `test/mps_parser_tests.jl`
- Create: `test/fixtures/parser/basic-free.mps`
- Create: `test/fixtures/parser/basic-fixed.mps`
- Modify: `test/runtests.jl`

**Interfaces:**
- Consumes: `ObjectiveSense` and `VariableDomain` from Task 2.
- Produces: `MPSParseError`, internal `MPSAccumulator`, `_parse_mps(io, source; format)`, and symbolic records used by Task 5.

- [ ] **Step 1: Add representative fixed/free fixtures and failing parser tests**

Create `test/fixtures/parser/basic-free.mps`:

```text
NAME BASICFREE
OBJSENSE
 MAX
ROWS
 N COST
 G DEMAND
 L CAPACITY
COLUMNS
 X COST 3 DEMAND 1
 X CAPACITY 1
 Y COST 2 DEMAND 1
 Y CAPACITY 2
RHS
 RHS1 DEMAND 1 CAPACITY 4
ENDATA
```

Create `test/fixtures/parser/basic-fixed.mps` using fixed fields (field starts
at columns 2, 5, 15, 25, 40, and 50):

```text
NAME          BASICFIX
ROWS
 N  COST
 G  DEMAND
COLUMNS
    X         COST                 1   DEMAND               1
RHS
    RHS1      DEMAND               2
ENDATA
```

Create `test/mps_parser_tests.jl`:

```julia
@testset "MPS symbolic parser" begin
    free_path = joinpath(@__DIR__, "fixtures", "parser", "basic-free.mps")
    fixed_path = joinpath(@__DIR__, "fixtures", "parser", "basic-fixed.mps")

    free_records = JSimplex._parse_mps_file(free_path; format=:free)
    @test free_records.name == "BASICFREE"
    @test free_records.objective_sense == MAX_SENSE
    @test free_records.row_order == ["COST", "DEMAND", "CAPACITY"]
    @test free_records.column_order == ["X", "Y"]

    fixed_records = JSimplex._parse_mps_file(fixed_path; format=:fixed)
    @test fixed_records.name == "BASICFIX"
    @test fixed_records.column_order == ["X"]

    auto_records = JSimplex._parse_mps_file(fixed_path; format=:auto)
    @test auto_records.column_order == fixed_records.column_order

    malformed = IOBuffer("NAME BAD\nROWS\n Z UNKNOWN\nENDATA\n")
    error = try
        JSimplex._parse_mps(malformed, "memory.mps"; format=:free)
        nothing
    catch exception
        exception
    end
    @test error isa MPSParseError
    @test occursin("memory.mps:3", sprint(showerror, error))
    @test occursin("ROWS", sprint(showerror, error))
end
```

Include it from `test/runtests.jl`.

- [ ] **Step 2: Run tests and verify the parser entry points are missing**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: FAIL with `UndefVarError: _parse_mps_file not defined`.

- [ ] **Step 3: Implement lexical records, format detection, and the section state machine**

In `src/mps/records.jl`, define:

```julia
struct MPSParseError <: Exception
    source::String
    line::Int
    section::Symbol
    message::String
end

function Base.showerror(io::IO, error::MPSParseError)
    print(io, error.source, ':', error.line, " [", error.section, "] ",
          error.message)
end

struct BoundRecord
    kind::Symbol
    column::String
    value::Union{Nothing,Float64}
    line::Int
end

mutable struct MPSAccumulator
    source::String
    name::String
    objective_sense::ObjectiveSense
    objective_name::Union{Nothing,String}
    row_order::Vector{String}
    row_types::Dict{String,Char}
    column_order::Vector{String}
    coefficients::Vector{Tuple{String,String,Float64,Int}}
    rhs_sets::Dict{String,Vector{Tuple{String,Float64,Int}}}
    rhs_order::Vector{String}
    ranges_sets::Dict{String,Vector{Tuple{String,Float64,Int}}}
    ranges_order::Vector{String}
    bounds_sets::Dict{String,Vector{BoundRecord}}
    bounds_order::Vector{String}
    marker_domains::Dict{String,VariableDomain}
end
```

Provide a constructor `MPSAccumulator(source::AbstractString)` with the source
copied to `String`, empty ordered vectors/dictionaries, and `MIN_SENSE`. Parse
numeric tokens after replacing `D`/`d` exponents with `E`/`e`; reject
non-finite values.

For fixed records, pad lines to 61 ASCII characters and slice fields
`2:3`, `5:12`, `15:22`, `25:36`, `40:47`, and `50:61`. For free records,
split on whitespace. Auto-detection treats a data line as free when any fixed
separator column (4, 13, 14, 23, 24, 37, 38, 39, 48, or 49) is nonblank;
otherwise it uses fixed parsing. Section headers are always recognized after
stripping whitespace.

In `src/mps/parser.jl`, implement a state machine for `:NAME`, `:OBJSENSE`,
`:OBJNAME`, `:ROWS`, `:COLUMNS`, `:RHS`, `:RANGES`, `:BOUNDS`, and `:ENDATA`;
accept both `OBJSEN` and `OBJSENSE` headers. Accept comment lines whose first
nonblank character is `*`, and ignore the remainder of a data record beginning
with a `$` comment field. Validate section
order, row types, unique row names, referenced rows, and paired row/value
fields. In fixed format, a blank column or set-name field continues the
preceding column or set and is an error when no preceding name exists. Treat
`'MARKER' 'INTORG'` and `'MARKER' 'INTEND'` records as an integer mode toggle,
record columns encountered in integer mode as `INTEGER`, and give such columns
default bounds `[0, 1]` unless a selected bounds set changes them. Reject an
unterminated marker block at `ENDATA`.

Create `src/mps.jl`:

```julia
include("mps/records.jl")
include("mps/parser.jl")
include("mps/build.jl")

function _parse_mps_file(path::AbstractString; format::Symbol=:auto)
    open(path, "r") do io
        return _parse_mps(io, String(path); format=format)
    end
end
```

Create an empty `src/mps/build.jl` so module assembly succeeds. Include
`mps.jl` after `model.jl`, and export `MPSParseError`.

- [ ] **Step 4: Run parser and package tests**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: PASS, including fixed, free, auto-detected, and malformed records.

- [ ] **Step 5: Commit symbolic MPS parsing**

```bash
git add src/JSimplex.jl src/mps.jl src/mps test/runtests.jl test/mps_parser_tests.jl test/fixtures/parser
git commit -m "feat: parse fixed and free MPS records"
```

### Task 5: Build `LinearProblem` values from complete MPS semantics

**Files:**
- Modify: `src/mps/build.jl`
- Modify: `src/mps.jl`
- Modify: `src/JSimplex.jl`
- Create: `test/mps_build_tests.jl`
- Create: `test/fixtures/parser/bounds-and-ranges.mps`
- Create: `test/fixtures/parser/all-bounds.mps`
- Create: `test/fixtures/parser/multiple-sets.mps`
- Create: `test/fixtures/parser/unsupported-quadratic.mps`
- Modify: `test/runtests.jl`

**Interfaces:**
- Consumes: `MPSAccumulator` from Task 4 and `LinearProblem` from Task 2.
- Produces: `read_mps(path; format=:auto, rhs_name=nothing, ranges_name=nothing, bounds_name=nothing, objective_name=nothing)::LinearProblem`.

- [ ] **Step 1: Add failing tests for rows, ranges, bounds, domains, and named sets**

Create `test/fixtures/parser/bounds-and-ranges.mps`:

```text
NAME DOMAINS
ROWS
 N OBJ
 E EQ
 L LE
 G GE
COLUMNS
 MARK0 'MARKER' 'INTORG'
 XI OBJ 1 EQ 1
 XMARK LE 1
 MARK1 'MARKER' 'INTEND'
 XB LE 1
 XSC GE 1
 XSI EQ 1
RHS
 R OBJ 6 EQ 5
 R LE 8
 R GE 2
RANGES
 RNG EQ -4 LE 3
BOUNDS
 LI B XI -2
 UI B XI 9
 BV B XB
 SC B XSC 10
 LO B XSC 2
 SI B XSI 7
 LO B XSI 3
ENDATA
```

Create `test/fixtures/parser/all-bounds.mps`:

```text
NAME ALLBOUNDS
ROWS
 N OBJ
COLUMNS
 XLO OBJ 1
 XUP OBJ 1
 XFX OBJ 1
 XFR OBJ 1
 XMI OBJ 1
 XPL OBJ 1
BOUNDS
 LO B XLO -2
 UP B XUP 5
 FX B XFX 3
 FR B XFR
 MI B XMI
 PL B XPL
ENDATA
```

Create `test/fixtures/parser/multiple-sets.mps`:

```text
NAME SETS
ROWS
 N OBJ
 L LIMIT
COLUMNS
 X OBJ 1 LIMIT 1
RHS
 FIRST LIMIT 1
 SECOND LIMIT 2
RANGES
 NARROW LIMIT 1
 WIDE LIMIT 3
BOUNDS
 UP LOW X 4
 UP HIGH X 9
ENDATA
```

Create `test/fixtures/parser/unsupported-quadratic.mps`:

```text
NAME QUADRATIC
ROWS
 N OBJ
COLUMNS
 X OBJ 1
QMATRIX
 X X 1
ENDATA
```

Create `test/mps_build_tests.jl`:

```julia
@testset "MPS model construction" begin
    root = joinpath(@__DIR__, "fixtures", "parser")
    problem = read_mps(joinpath(root, "bounds-and-ranges.mps"); format=:free)
    @test problem.variable_domains ==
          [INTEGER, INTEGER, BINARY, SEMI_CONTINUOUS, SEMI_INTEGER]
    @test problem.column_lower == [-2.0, 0.0, 0.0, 2.0, 3.0]
    @test problem.column_upper == [9.0, 1.0, 1.0, 10.0, 7.0]
    @test problem.row_lower == [1.0, 5.0, 2.0]
    @test problem.row_upper == [5.0, 8.0, Inf]
    @test problem.objective_constant == -6.0

    all_bounds = read_mps(joinpath(root, "all-bounds.mps"); format=:free)
    @test all_bounds.column_lower == [-2.0, 0.0, 3.0, -Inf, -Inf, 0.0]
    @test all_bounds.column_upper == [Inf, 5.0, 3.0, Inf, Inf, Inf]

    selected = read_mps(
        joinpath(root, "multiple-sets.mps");
        rhs_name="SECOND", ranges_name="WIDE", bounds_name="HIGH",
    )
    @test selected.row_lower == [-1.0]
    @test selected.row_upper == [2.0]
    @test selected.column_upper == [9.0]

    @test_throws MPSParseError read_mps(
        joinpath(root, "multiple-sets.mps"); rhs_name="MISSING",
    )
    @test_throws MPSParseError read_mps(
        joinpath(root, "unsupported-quadratic.mps"),
    )
end
```

The expected equality-range bounds above follow the negative range rule:
`rhs - abs(range) <= row <= rhs`.

- [ ] **Step 2: Run tests and verify `read_mps` is undefined**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: FAIL with `UndefVarError: read_mps not defined`.

- [ ] **Step 3: Implement named-set selection and model construction**

In `src/mps/build.jl`, implement `_select_set` so an explicit missing name
raises `MPSParseError`, no explicit name selects the first item from the
corresponding order vector, and an absent section yields an empty record list.

Build row and column index dictionaries from their order vectors. Select the
objective by this precedence: `objective_name` keyword, parsed `OBJNAME`, first
`N` row, no objective. Exclude every `N` row from `A`. Send coefficients on the
selected objective row to `objective`; ignore coefficients on other `N` rows.
Send all other entries to parallel row, column, and value vectors and call
`sparse(rows, columns, values, m, n, +)` so duplicates are summed. If the
selected RHS set contains a value `v` for the selected objective row, set
`objective_constant = -v`; otherwise use zero.

Initialize row bounds from RHS value `b` using these formulas:

```julia
E: lower = b;    upper = b
L: lower = -Inf; upper = b
G: lower = b;    upper = Inf
```

Apply range value `r` using:

```julia
E, r >= 0: lower = b;          upper = b + abs(r)
E, r < 0:  lower = b - abs(r); upper = b
L:         lower = b - abs(r); upper = b
G:         lower = b;          upper = b + abs(r)
```

Initialize every column as continuous with `[0, Inf]`. Give marker-delimited
integer columns `[0, 1]`, then process selected bound records:

```julia
LO -> lower=value
UP -> upper=value
FX -> lower=value, upper=value
FR -> lower=-Inf, upper=Inf
MI -> lower=-Inf
PL -> upper=Inf
BV -> domain=BINARY, lower=0, upper=1; accept no value or the value 1
LI -> domain=INTEGER, lower=value
UI -> domain=INTEGER, upper=value
SC -> domain=SEMI_CONTINUOUS, active upper=value, active lower defaults to 1
SI -> domain=SEMI_INTEGER, active upper=value, active lower defaults to 1
```

Pre-scan each column for an explicit `LO`, so it overrides the default active
lower bound for `SC` or `SI` regardless of record order. If an `UP` value is
negative and the selected set contains no explicit lower bound for that column,
set its lower bound to `-Inf`. Reject missing required values, unexpected values
on `FR`/`MI`/`PL`, values other than one on `BV`, unknown columns, duplicate
objective selection, nonintegral `LI`/`UI` values, and unsupported sections
using `MPSParseError` with the source line.

Implement the public wrapper in `src/mps.jl` with the exact signature from the
Interfaces block. Export `read_mps` from `JSimplex.jl`.

- [ ] **Step 4: Run MPS and package tests**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: PASS for all parser/model construction tests.

- [ ] **Step 5: Commit complete native MPS loading**

```bash
git add src/JSimplex.jl src/mps.jl src/mps/build.jl test/runtests.jl test/mps_build_tests.jl test/fixtures/parser
git commit -m "feat: build linear models from MPS"
```

### Task 6: Port basis factorization and product-form updates

**Files:**
- Create: `src/factorization.jl`
- Modify: `src/JSimplex.jl`
- Create: `test/factorization_tests.jl`
- Modify: `test/runtests.jl`
- Reference: `pfi.jl`

**Interfaces:**
- Consumes: Julia `SparseArrays` and `LinearAlgebra` from the module shell.
- Produces: internal `PFIFactorization`, `forward_solve`, `transpose_solve`,
  `replace_column!(factor, tableau_column, pivot_row; zero_tolerance=1e-12)`,
  and `refactorize!`.

- [ ] **Step 1: Write failing algebraic equivalence tests**

Create `test/factorization_tests.jl`:

```julia
@testset "Product-form basis factorization" begin
    B = sparse([2.0 1.0; 1.0 3.0])
    factor = JSimplex.PFIFactorization(B)
    rhs = [5.0, 7.0]
    @test JSimplex.forward_solve(factor, rhs) ≈ Matrix(B) \ rhs
    @test JSimplex.transpose_solve(factor, rhs) ≈ Matrix(B)' \ rhs

    replacement = [4.0, -1.0]
    tableau_column = JSimplex.forward_solve(factor, replacement)
    JSimplex.replace_column!(factor, tableau_column, 1)
    B2 = sparse([4.0 1.0; -1.0 3.0])
    @test JSimplex.forward_solve(factor, rhs) ≈ Matrix(B2) \ rhs
    @test JSimplex.transpose_solve(factor, rhs) ≈ Matrix(B2)' \ rhs

    JSimplex.refactorize!(factor, B2)
    @test isempty(factor.updates)
    @test JSimplex.forward_solve(factor, rhs) ≈ Matrix(B2) \ rhs
end
```

Include it from `test/runtests.jl`.

- [ ] **Step 2: Run tests and verify `PFIFactorization` is undefined**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: FAIL with `UndefVarError: PFIFactorization not defined`.

- [ ] **Step 3: Implement a non-mutating modern port of `pfi.jl`**

Create these types in `src/factorization.jl`:

```julia
struct PackedEta
    indices::Vector{Int}
    values::Vector{Float64}
    pivot_row::Int
end

mutable struct PFIFactorization
    base::Any
    updates::Vector{PackedEta}
end
```

For a tableau column `a` and pivot row `p`, construct an eta vector containing
`1 / a[p]` at `p` and `-a[i] / a[p]` at every nonzero non-pivot position.
Implement this in
`replace_column!(factor, a, p; zero_tolerance::Real=1.0e-12)` and throw
`LinearAlgebra.ZeroPivotException(p)` when the pivot's absolute value is at
most the provided tolerance.

`forward_solve` copies its RHS, solves with the base LU, then applies eta
columns in insertion order: save `x[p]`, set it to zero, and add the saved value
times every packed eta entry. `transpose_solve` copies its RHS, applies eta rows
in reverse order by replacing `x[p]` with the packed dot product, then solves
with `adjoint(base)`. Neither method mutates its caller's RHS.

`replace_column!` appends an eta. `refactorize!` replaces `base` with
`lu(SparseMatrixCSC{Float64,Int}(B))` and empties `updates`. Include this file
before `simplex.jl`.

- [ ] **Step 4: Run factorization and package tests**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: PASS, including both updated-basis solve directions.

- [ ] **Step 5: Commit the factorization port**

```bash
git add src/JSimplex.jl src/factorization.jl test/runtests.jl test/factorization_tests.jl
git commit -m "feat: port product-form basis factorization"
```

### Task 7: Build the shared simplex workspace and initialization

**Files:**
- Modify: `src/simplex.jl`
- Create: `test/simplex_workspace_tests.jl`
- Modify: `test/runtests.jl`
- Reference: `jlSimplex.jl:29-280`

**Interfaces:**
- Consumes: `LinearProblem`, `SolverOptions`, `Basis`, and `PFIFactorization`.
- Produces: internal `SimplexWorkspace`, `initialize_workspace`, `recompute!`, `basis_matrix`, `primal_infeasibility`, and `dual_infeasibility`.

- [ ] **Step 1: Write failing slack-basis initialization tests**

Create `test/simplex_workspace_tests.jl`:

```julia
@testset "Simplex workspace" begin
    problem = LinearProblem(
        sparse([1.0 2.0; -1.0 1.0]), [3.0, 1.0];
        row_lower=[1.0, -Inf], row_upper=[1.0, 4.0],
        column_lower=[0.0, 0.0], column_upper=[Inf, Inf],
    )
    workspace = JSimplex.initialize_workspace(problem, SolverOptions())
    nrows, ncols = size(problem.A)
    @test workspace.basis.basic_indices == collect(ncols + 1:ncols + nrows)
    @test all(workspace.basis.states[ncols + 1:end] .== JSimplex.BASIC)
    @test size(JSimplex.basis_matrix(workspace)) == (nrows, nrows)
    @test JSimplex.primal_infeasibility(workspace) >= 0.0
    @test JSimplex.dual_infeasibility(workspace) >= 0.0
end
```

Include it from `test/runtests.jl`.

- [ ] **Step 2: Run tests and verify workspace initialization is missing**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: FAIL with `UndefVarError: initialize_workspace not defined`.

- [ ] **Step 3: Implement the common working model and slack basis**

Extend `src/simplex.jl` with:

```julia
mutable struct SimplexWorkspace
    problem::LinearProblem
    options::SolverOptions
    costs::Vector{Float64}
    lower::Vector{Float64}
    upper::Vector{Float64}
    basis::Basis
    primal::Vector{Float64}
    reduced_costs::Vector{Float64}
    pricing_weights::Vector{Float64}
    factorization::PFIFactorization
    iterations::Int
    refactorizations::Int
    perturbed::Bool
end
```

Append one logical slack variable per row with coefficient `-1`, zero cost, and
the row's lower/upper bounds. Initialize all slacks as `BASIC`. Initialize a
structural variable at its finite lower bound, otherwise its finite upper bound,
otherwise zero; set its state to `AT_LOWER`, `AT_UPPER`, or `FREE_NONBASIC`.

`basis_matrix` assembles structural basis columns from `A` and slack columns as
negative unit vectors. `recompute!` performs these exact operations:

1. Set every nonbasic primal to the bound implied by its state, or zero when
   free.
2. Form `rhs = -N * x_N`: subtract structural nonbasic contributions and add
   each nonbasic slack value because a slack column is a negative unit vector.
3. Solve `B * x_B = rhs` and scatter into basic indices.
4. Solve `B' * y = costs[basic_indices]`.
5. Compute structural reduced costs as `c - A' * y` and slack reduced costs as
   `c_slack + y`, setting basic reduced costs to zero.

`primal_infeasibility` sums basic bound violations beyond the primal tolerance.
`dual_infeasibility` sums sign violations of nonbasic reduced costs beyond the
dual tolerance. Refactorization calls `basis_matrix`, resets PFI updates, and
increments `refactorizations`.

- [ ] **Step 4: Run workspace and package tests**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: PASS, including the two-row slack basis.

- [ ] **Step 5: Commit the common simplex workspace**

```bash
git add src/simplex.jl test/runtests.jl test/simplex_workspace_tests.jl
git commit -m "feat: add shared simplex workspace"
```

### Task 8: Port the dual simplex algorithm

**Files:**
- Create: `src/dual_simplex.jl`
- Modify: `src/JSimplex.jl`
- Create: `test/dual_simplex_tests.jl`
- Modify: `test/runtests.jl`
- Reference: `jlSimplex.jl:283-721`

**Interfaces:**
- Consumes: `SimplexWorkspace` and factorization operations from Tasks 6-7.
- Produces: internal `DualTermination`, `DualRunResult`,
  `dual_edge_selection`, `dual_ratio_test`, `price!`, `dual_iteration!`,
  `make_dual_feasible!`, and `_solve_continuous_dual`.

- [ ] **Step 1: Write failing bounded, infeasible, and unbounded LP tests**

Create `test/dual_simplex_tests.jl`:

```julia
@testset "Dual simplex core" begin
    bounded = LinearProblem(
        sparse(reshape([1.0, 1.0], 1, 2)), [1.0, 2.0];
        row_lower=[1.0], row_upper=[Inf],
    )
    bounded_run = JSimplex._solve_continuous_dual(bounded, SolverOptions())
    @test bounded_run.status == OPTIMAL
    @test bounded_run.objective_value ≈ 1.0 atol=1.0e-7
    @test bounded_run.primal ≈ [1.0, 0.0] atol=1.0e-7

    infeasible = LinearProblem(
        sparse(reshape([1.0], 1, 1)), [1.0];
        row_lower=[2.0], row_upper=[Inf],
        column_lower=[0.0], column_upper=[1.0],
    )
    @test JSimplex._solve_continuous_dual(infeasible, SolverOptions()).status ==
          INFEASIBLE

    unbounded = LinearProblem(
        spzeros(0, 1), [-1.0];
        column_lower=[0.0], column_upper=[Inf],
    )
    @test JSimplex._solve_continuous_dual(unbounded, SolverOptions()).status ==
          UNBOUNDED
end
```

Include it from `test/runtests.jl`.

- [ ] **Step 2: Run tests and verify the dual solve entry point is missing**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: FAIL with `UndefVarError: _solve_continuous_dual not defined`.

- [ ] **Step 3: Port pricing, the Harris ratio test, and pivot updates**

Create `src/dual_simplex.jl`. Port the legacy routines under these names and
replace integer constants with `VariableState` values:

```julia
struct DualTermination
    status::TerminationStatus
    message::String
end

struct DualRunResult
    status::TerminationStatus
    objective_value::Union{Nothing,Float64}
    primal::Union{Nothing,Vector{Float64}}
    iterations::Int
    refactorizations::Int
    message::String
end

dual_edge_selection(workspace)::Int
dual_ratio_test(workspace, tableau_row::Vector{Float64})::Int
price!(tableau_row::Vector{Float64}, workspace, rho::Vector{Float64})::Nothing
update_duals!(workspace, tableau_row, leaving_index, entering_index, dual_step)::Nothing
update_primals!(workspace, tableau_column, entering_index, leaving_row, primal_step)::Nothing
update_dse!(workspace, rho, tableau_column, entering_index, pivot)::Nothing
dual_iteration!(workspace, stop_requested)::Union{Nothing,DualTermination}
```

`dual_edge_selection` maximizes squared bound violation divided by the
variable's pricing weight. The first ratio-test pass accepts coefficients above
`1e-7`, computes the relaxed maximum step with `dual_tolerance`, and records
candidates. The second pass chooses the eligible candidate with largest
absolute pivot. If a dual-feasible row has no candidate, return `INFEASIBLE`.

For a pivot, compute `rho = B' \ e_p`, price the full tableau row, compute the
entering column, solve `B \ a_q`, update primal/reduced-cost/DSE vectors,
append the product-form update, switch variable states, and replace the basic
index. Refactor when the number of pivots reaches
`options.refactorization_interval`; immediately before refactorization, return
`DualTermination(TIME_LIMIT, "time limit reached")` if `stop_requested()`.

- [ ] **Step 4: Port feasibility handling and the dual solve loop**

Implement `make_dual_feasible!(workspace, stop_requested)` by porting legacy
bound flips, cost shifting, and the auxiliary phase-I model. Use a separate
workspace for phase I, copy back only the basis, pricing weights, iteration
count, and shifted costs, then recompute against the original bounds. Check
`stop_requested()` in every phase-I iteration. Do not mutate
`workspace.problem`.

Implement
`_solve_continuous_dual(problem, options; stop_requested::Function=()->false)`
as follows:

```julia
workspace = initialize_workspace(problem, options)
phase_terminal = make_dual_feasible!(workspace, stop_requested)
isnothing(phase_terminal) || return _internal_solution(workspace,
                                                        phase_terminal.status,
                                                        phase_terminal.message)
while workspace.iterations < options.iteration_limit
    stop_requested() && return _internal_solution(workspace, TIME_LIMIT,
                                                   "time limit reached")
    primal_infeasibility(workspace) <= options.primal_tolerance && break
    terminal = dual_iteration!(workspace, stop_requested)
    isnothing(terminal) || return _internal_solution(workspace, terminal)
    workspace.iterations += 1
end
```

Before phase I, handle zero-row models exactly: if every reduced cost has a
finite improving bound, return the corresponding bound solution; if any
improving direction has no finite bound, return `UNBOUNDED`; otherwise return
`OPTIMAL`. After removing cost shifts, recompute original reduced costs. Return
`OPTIMAL` only when both primal and dual infeasibility are within tolerance;
return `ITERATION_LIMIT` when the loop exhausts its limit and `NUMERICAL_ERROR`
when factorization or a pivot raises `SingularException`, `ZeroPivotException`,
or produces a non-finite iterate.

Implement `_internal_solution(workspace, status, message)` to copy only the
first `size(problem.A, 2)` primal values, compute the objective as
`dot(problem.objective, primal) + problem.objective_constant` for `OPTIMAL`,
and copy iteration/refactorization counters into `DualRunResult`. Use `nothing`
for the objective and primal fields of every other status in this release;
later algorithms may expose a separately certified feasible incumbent.

Include `dual_simplex.jl` after `simplex.jl`.

- [ ] **Step 5: Run dual-core and package tests**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: PASS for bounded, infeasible, unbounded, and all earlier tests.

- [ ] **Step 6: Commit the dual simplex port**

```bash
git add src/JSimplex.jl src/dual_simplex.jl test/runtests.jl test/dual_simplex_tests.jl
git commit -m "feat: port dual simplex algorithm"
```

### Task 9: Add the public solve pipeline and stopping limits

**Files:**
- Create: `src/solver.jl`
- Modify: `src/JSimplex.jl`
- Create: `test/solver_tests.jl`
- Modify: `test/runtests.jl`

**Interfaces:**
- Consumes: transformation APIs from Task 3 and `_solve_continuous_dual` from Task 8.
- Produces: `solve(problem::LinearProblem; relax_integrality=false, options=SolverOptions())::Solution`.

- [ ] **Step 1: Write failing public API, relaxation, immutability, and limit tests**

Create `test/solver_tests.jl`:

```julia
@testset "Public solve pipeline" begin
    problem = LinearProblem(
        sparse(reshape([1.0, 1.0], 1, 2)), [1.0, 2.0];
        row_lower=[1.0], row_upper=[Inf],
        name="public-api",
    )
    original_A = copy(problem.A)
    result = solve(problem)
    @test result.status == OPTIMAL
    @test result.objective_value ≈ 1.0 atol=1.0e-7
    @test result.statistics.elapsed_seconds >= 0.0
    @test problem.A == original_A

    integer_problem = LinearProblem(
        sparse(reshape([1.0], 1, 1)), [1.0];
        row_lower=[0.5], row_upper=[Inf],
        variable_domains=[INTEGER],
    )
    @test solve(integer_problem).status == MIP_NOT_SUPPORTED
    @test solve(integer_problem; relax_integrality=true).status == OPTIMAL

    @test solve(problem; options=SolverOptions(algorithm=:primal)).status ==
          ALGORITHM_NOT_SUPPORTED
    @test solve(problem; options=SolverOptions(algorithm=:auto)).status ==
          ALGORITHM_NOT_SUPPORTED
    @test solve(problem; options=SolverOptions(iteration_limit=0)).status ==
          ITERATION_LIMIT
    @test solve(problem; options=SolverOptions(time_limit=0.0)).status ==
          TIME_LIMIT
end
```

Include it from `test/runtests.jl`.

- [ ] **Step 2: Run tests and verify `solve` is undefined**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: FAIL with `UndefVarError: solve not defined`.

- [ ] **Step 3: Implement orchestration, deadline checks, and result conversion**

Create `src/solver.jl`. Define an internal `SolveContext` containing
`start_ns::UInt64` and `time_limit_seconds::Float64`. Define:

```julia
elapsed_seconds(context) = (time_ns() - context.start_ns) / 1.0e9
time_limit_reached(context) =
    elapsed_seconds(context) >= context.time_limit_seconds
```

Check a zero time limit before validation work. Pass the context into the dual
solve loop and check it before each iteration and immediately before a full
refactorization. A deadline hit returns `TIME_LIMIT`; an exhausted iteration
budget returns `ITERATION_LIMIT`.

Implement `solve` in this order:

1. Create the clock context.
2. Return `ALGORITHM_NOT_SUPPORTED` unless `algorithm == :dual`.
3. Return `INVALID_MODEL` with `_validation_error` when validation fails.
4. Return `MIP_NOT_SUPPORTED` for a noncontinuous model without explicit
   relaxation.
5. Apply `relax_integrality`, `identity_presolve`, and `identity_scaling`.
6. Normalize maximization by negating the working objective.
7. Invoke `_solve_continuous_dual` with
   `stop_requested=()->time_limit_reached(context)`.
8. Unscale and postsolve a valid primal vector.
9. Recompute the original objective as
   `dot(problem.objective, primal) + problem.objective_constant`.
10. Return `Solution` with final elapsed seconds, iteration count,
    refactorization count, and an English message.

Catch only expected numeric failures and convert them to `NUMERICAL_ERROR`;
allow programming errors to propagate. Include `solver.jl` after
`dual_simplex.jl` and export `solve`. Replace the legacy unconditional output
with `@logmsg options.log_level` records at solve start, each refactorization,
and termination. The default `Logging.Debug` level keeps ordinary solves quiet
under Julia's default logger while allowing callers to enable progress output.

- [ ] **Step 4: Run all package tests**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: PASS, including distinct `ITERATION_LIMIT` and `TIME_LIMIT` results.

- [ ] **Step 5: Commit the public solve pipeline**

```bash
git add src/JSimplex.jl src/solver.jl src/dual_simplex.jl test/runtests.jl test/solver_tests.jl
git commit -m "feat: add public solve pipeline and limits"
```

### Task 10: Add AFIRO regression coverage and remove the legacy entry points

**Files:**
- Move: `AFIRO.SIF` to `test/fixtures/solver/afiro.mps`
- Move: `GREENBEA.SIF` to `dev/fixtures/greenbea.mps`
- Create: `test/regression_tests.jl`
- Modify: `test/runtests.jl`
- Delete: `jlSimplex.jl`
- Delete: `pfi.jl`
- Delete: `test.jl`

**Interfaces:**
- Consumes: `read_mps` and `solve` from Tasks 5 and 9.
- Produces: a package-level NETLIB regression and removal of every pre-1.0 load path.

- [ ] **Step 1: Move existing models and write the failing AFIRO regression**

Use `git mv` for both MPS files so history is preserved. Create
`test/regression_tests.jl`:

```julia
@testset "AFIRO regression" begin
    path = joinpath(@__DIR__, "fixtures", "solver", "afiro.mps")
    problem = read_mps(path)
    result = solve(problem)
    @test result.status == OPTIMAL
    @test result.objective_value ≈ -464.7531428571429 atol=1.0e-6 rtol=1.0e-8
    @test length(result.primal) == size(problem.A, 2)
end
```

Include it last from `test/runtests.jl`.

- [ ] **Step 2: Run the regression and observe any numerical mismatch**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: PASS if the port is faithful. If it fails, the failure must be a
focused parser or numerical mismatch while the small tests remain green.

- [ ] **Step 3: Correct the port against the legacy algorithm and AFIRO**

If the regression fails, first invoke `superpowers:systematic-debugging`.
Compare the failed invariant with the corresponding legacy routines in
`jlSimplex.jl`: initialization (`initialize`), leaving selection
(`dualEdgeSelection`), ratio test (`dualRatioTest`), pivot (`iterate`), cost
updates (`updateDuals`), primal updates (`updatePrimals`), DSE updates
(`updateDSE`), phase I (`makeFeasible`), and bound flips (`flipBounds`). Make
the smallest formula or sign correction demonstrated by the failing focused
test. Add that focused regression to `test/dual_simplex_tests.jl` before changing
the implementation, then rerun it to red and green.

- [ ] **Step 4: Remove legacy source and script files**

After AFIRO passes, delete `jlSimplex.jl`, `pfi.jl`, and `test.jl`. Verify no
source, test, or documentation file contains `require(`, old `type` syntax,
`typealias`, `GLPK.Prob`, or `SolveMPSWithGLPK`:

Run: `rg -n 'require\(|^type |typealias|GLPK\.Prob|SolveMPSWithGLPK' . --glob '!docs/superpowers/**'`

Expected: no matches.

- [ ] **Step 5: Run the complete offline suite**

Run: `julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'`

Expected: PASS, including AFIRO.

- [ ] **Step 6: Commit the regression migration**

```bash
git add src test dev/fixtures jlSimplex.jl pfi.jl test.jl AFIRO.SIF GREENBEA.SIF
git commit -m "test: migrate NETLIB regression to package suite"
```

### Task 11: Isolate development dependencies and data-suite tooling

**Files:**
- Create: `dev/Project.toml` through `Pkg`
- Create: `dev/Artifacts.toml`
- Create: `dev/datasets.toml`
- Create: `dev/datasets.jl`
- Create: `dev/reference_glpk.jl`
- Create: `dev/run_suite.jl`
- Create: `dev/benchmarks.jl`
- Create: `dev/tests/runtests.jl`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: public `read_mps`, `solve`, `Solution`, and the moved MPS fixtures.
- Produces: `resolve_dataset(manifest, name; repository_root, data_root=nothing)`, an opt-in suite CLI, and GLPK result comparison outside production code.

- [ ] **Step 1: Write failing development data-resolution tests**

Create `dev/tests/runtests.jl`:

```julia
using Test
include(joinpath(@__DIR__, "..", "datasets.jl"))

@testset "Development data registry" begin
    manifest = load_dataset_manifest(joinpath(@__DIR__, "..", "datasets.toml"))
    afiro = resolve_dataset(manifest, "afiro";
                            repository_root=normpath(joinpath(@__DIR__, "..", "..")))
    @test isfile(afiro)
    @test bytes2hex(open(sha256, afiro)) ==
          "28c80012b6e7da7df5d2e1e7220ee26e4f684a34b6958f77b14f0277225d65fd"
    @test_throws ArgumentError resolve_dataset(manifest, "unknown";
                                               repository_root=pwd())
end
```

- [ ] **Step 2: Create and instantiate the isolated development project**

Run:

```bash
julia --startup-file=no -e 'using Pkg; Pkg.activate("dev"); Pkg.develop(path="."); Pkg.add(["BenchmarkTools", "GLPK", "SHA", "TOML", "Test"]); Pkg.compat("julia", "1.13"); Pkg.instantiate()'
```

Expected: `dev/Project.toml` and `dev/Manifest.toml` are generated and GLPK does
not appear in the root `Project.toml`.

Add `dev/Manifest.toml` and `.julia/` to `.gitignore`; commit the development
project but not its manifest.

- [ ] **Step 3: Implement the dataset manifest and resolver**

Create `dev/datasets.toml` with checked-in smoke cases and the external-artifact
schema:

```toml
[datasets.afiro]
kind = "repository"
path = "test/fixtures/solver/afiro.mps"
sha256 = "28c80012b6e7da7df5d2e1e7220ee26e4f684a34b6958f77b14f0277225d65fd"
expected_status = "OPTIMAL"
expected_objective = -464.7531428571429
tags = ["quick", "netlib"]

[datasets.greenbea]
kind = "repository"
path = "dev/fixtures/greenbea.mps"
sha256 = "5325334a80524944761ded6faeb8c994aa4e9fbadea1de26f7cff97fd4549d09"
tags = ["full", "netlib"]

[registry]
artifacts_toml = "Artifacts.toml"
```

Create `dev/Artifacts.toml` with an English header explaining that
`Pkg.Artifacts.bind_artifact!` writes immutable `git-tree-sha1` bindings after a
collection has been assembled from license-compatible source URLs and verified
against its dataset manifest. An external collection entry in `datasets.toml`
must use `kind="artifact"`, name its artifact binding and relative instance
path, and record SHA-256, source URL, version, provenance, license, expected
status/objective, and tags. Do not add a collection until all those concrete
values are known; do not add fake hashes or unavailable URLs.

In `dev/datasets.jl`, use `TOML`, `SHA`, and `Pkg.Artifacts`. Implement
`load_dataset_manifest(path)=TOML.parsefile(path)`. `resolve_dataset` must:

1. resolve `kind="repository"` relative to the repository root and verify the
   declared SHA-256;
2. resolve `kind="artifact"` through `artifact_hash` and `artifact_path` using
   `dev/Artifacts.toml`;
3. allow an explicit `data_root` to override an artifact root for private
   collections;
4. throw an English `ArgumentError` naming the missing data set and the command
   or option needed to provide it.

Run: `julia --startup-file=no --project=dev dev/tests/runtests.jl`

Expected: PASS for manifest resolution and checksum verification.

- [ ] **Step 4: Implement GLPK reference comparison and the suite CLI**

In `dev/reference_glpk.jl`, wrap the GLPK C API in `try/finally`:

```julia
function solve_with_glpk(path::AbstractString)
    problem = GLPK.glp_create_prob()
    try
        code = GLPK.glp_read_mps(problem, GLPK.GLP_MPS_FILE, C_NULL, path)
        code == 0 || throw(ErrorException("GLPK could not read $path (code $code)"))
        solve_code = GLPK.glp_simplex(problem, C_NULL)
        solve_code == 0 || throw(ErrorException("GLPK could not solve $path (code $solve_code)"))
        return (status=GLPK.glp_get_status(problem),
                objective=GLPK.glp_get_obj_val(problem))
    finally
        GLPK.glp_delete_prob(problem)
    end
end
```

Implement `dev/run_suite.jl` with `--dataset NAME`, `--tag TAG`,
`--data-root PATH`, and `--compare-glpk` arguments. For each selected instance,
load it with `read_mps`, call `solve` with `relax_integrality=true`, compare any
declared expected status/objective, and map `GLP_OPT`, `GLP_NOFEAS`, and
`GLP_UNBND` to `OPTIMAL`, `INFEASIBLE`, and `UNBOUNDED`. Optionally compare
GLPK's objective within `max(1e-7, 1e-7 * abs(reference))`. Exit nonzero when
any comparison fails and print a summary table containing instance, status,
objective, iterations, and elapsed seconds.

Create `dev/benchmarks.jl` using `BenchmarkTools.@benchmark solve($problem)` for
a selected data-set name; keep benchmark assertions out of `Pkg.test()`.

- [ ] **Step 5: Verify production and development dependency separation**

Run:

```bash
julia --startup-file=no --project=. -e 'using Pkg; Pkg.instantiate(); using JSimplex'
julia --startup-file=no --project=dev dev/tests/runtests.jl
julia --startup-file=no --project=dev dev/run_suite.jl --dataset afiro --compare-glpk
```

Expected: all commands succeed, and `rg -n 'GLPK|BenchmarkTools' Project.toml src test`
returns no matches.

- [ ] **Step 6: Commit development tooling**

```bash
git add .gitignore dev/Project.toml dev/Artifacts.toml dev/datasets.toml dev/datasets.jl dev/reference_glpk.jl dev/run_suite.jl dev/benchmarks.jl dev/tests
git commit -m "dev: add isolated reference and data-suite tooling"
```

### Task 12: Add English documentation, licensing, CI, and final verification

**Files:**
- Rewrite: `README.md`
- Create: `LICENSE`
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/extended.yml`
- Modify: public source files for docstrings where absent

**Interfaces:**
- Consumes: all public APIs and commands from Tasks 1-11.
- Produces: user-facing installation/API guidance and an automated Julia 1.13 verification gate.

- [ ] **Step 1: Write README command smoke tests before documentation**

Create a temporary clean depot and run the commands that the README will show:

```bash
tmp_depot=$(mktemp -d)
JULIA_DEPOT_PATH="$tmp_depot" julia --startup-file=no --project=. -e 'using Pkg; Pkg.instantiate(); using JSimplex; p = read_mps("test/fixtures/solver/afiro.mps"); r = solve(p); @assert r.status == OPTIMAL'
```

Expected: PASS without installing GLPK in the temporary production depot.

- [ ] **Step 2: Rewrite README and add public docstrings**

Write an English README with these sections and verified commands:

- project status and proof-of-concept warning;
- Julia 1.13 installation with `Pkg.develop(path=".")`;
- `LinearProblem` construction and `read_mps` examples;
- `solve`, `SolverOptions(iteration_limit=10_000, time_limit=60.0)`, status handling,
  and explicit `relax_integrality=true`;
- supported fixed/free MPS sections, rows, bounds, markers, and named sets;
- `Pkg.test()` for offline tests;
- development-environment setup and `dev/run_suite.jl` examples;
- current limitations and the planned primal simplex, scaling, presolve,
  MOI/JuMP, and MIP extension points.

Add English docstrings to every exported type, enum, `read_mps`, and `solve`.
Run:

`julia --startup-file=no --project=. -e 'using JSimplex; println(Base.Docs.doc(JSimplex.solve))'`

Expected: a nonempty English docstring.

- [ ] **Step 3: Add the MIT license**

Create `LICENSE` using the standard MIT text with this copyright line:

```text
Copyright (c) 2013-2026 JSimplex contributors
```

Retain the permission grant, warranty disclaimer, and liability disclaimer from
the canonical MIT license without adding project-specific restrictions.

- [ ] **Step 4: Add Julia 1.13 CI**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: julia-actions/setup-julia@v2
        with:
          version: '1.13'
      - uses: julia-actions/cache@v2
      - uses: julia-actions/julia-buildpkg@v1
      - uses: julia-actions/julia-runtest@v1
```

Do not put the GLPK comparison in the mandatory CI job. Document the exact
extended-suite command. Create `.github/workflows/extended.yml` as a separate
manual job:

```yaml
name: Extended validation

on:
  workflow_dispatch:

jobs:
  reference:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: julia-actions/setup-julia@v2
        with:
          version: '1.13'
      - uses: julia-actions/cache@v2
      - run: julia --startup-file=no --project=dev -e 'using Pkg; Pkg.develop(path="."); Pkg.instantiate()'
      - run: julia --startup-file=no --project=dev dev/tests/runtests.jl
      - run: julia --startup-file=no --project=dev dev/run_suite.jl --dataset afiro --compare-glpk
```

Keep external NETLIB/MIPLIB artifact runs out of this job until immutable
bindings and redistribution-compatible download sources have been added.

- [ ] **Step 5: Run the final verification matrix**

Run:

```bash
julia --version
julia --startup-file=no --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.precompile(); Pkg.test()'
julia --startup-file=no --project=dev dev/tests/runtests.jl
julia --startup-file=no --project=dev dev/run_suite.jl --dataset afiro --compare-glpk
git diff --check
rg -n 'require\(|^type |typealias|GLPK\.Prob|SolveMPSWithGLPK' . --glob '!docs/superpowers/**'
rg -n 'GLPK|BenchmarkTools' Project.toml src test
git status --short
```

Expected: Julia reports `1.13.x`; all Julia commands pass; both ripgrep checks
produce no output; `git diff --check` produces no output; only the intended
documentation/CI changes remain in `git status` before the final commit.

- [ ] **Step 6: Commit documentation and CI**

```bash
git add README.md LICENSE .github/workflows/ci.yml .github/workflows/extended.yml src
git commit -m "docs: document the modern JSimplex package"
```

- [ ] **Step 7: Verify the committed tree once more**

Run:

```bash
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
git status --short
```

Expected: all tests pass and the working tree is clean.
