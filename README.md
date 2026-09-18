# JSimplex.jl

JSimplex is a proof-of-concept solver for linear programming in Julia 1.13.
It supports dual and primal simplex, a reversible presolver, and a native
fixed/free MPS reader.
Integer and semi-continuous domains are preserved for explicit LP relaxation.
It is experimental:
correctness, numerical robustness, and performance are not guaranteed for general
models. Use an established solver for production optimization.

The primal algorithm uses an auxiliary phase I to find a feasible basis,
followed by selectable Dantzig, steepest-edge, or Devex pricing and a two-pass
Harris ratio test with entering bound flips.
The dual algorithm includes bound flipping during ratio testing, a
two-pass Harris fallback, selectable dual steepest-edge, Devex, and Dantzig
pricing, cost shifting, LU factorization, and
selectable product-form, Forrest–Tomlin, Bartels–Golub, and Suhl–Suhl basis
updates.
Model arithmetic supports floating-point and rational scalar types, including
`Float32`, `Float64`, `BigFloat`, and exact `Rational{BigInt}`.
The production package depends on Julia standard libraries and
`MathOptInterface` (MOI). JuMP is a user-selected integration dependency: install
it in the environment where you want the JuMP interface, rather than expecting it
to be installed as a dependency of JSimplex. JET, GLPK, and BenchmarkTools belong
to the optional development environment.

## Installation and quick start

Install Julia 1.13 and clone this repository. Run all shell commands below from
the repository root. To use the checkout directly:

```sh
julia --version
julia --startup-file=no --project=. -e 'using Pkg; Pkg.instantiate(); using JSimplex; p = read_mps("test/fixtures/solver/afiro.mps"); r = solve(p); @assert r.status == OPTIMAL'
```

To register the checkout in another Julia project, start Julia from the
repository root and activate that project before developing the local package:

```julia
using Pkg
Pkg.activate(temp=true)  # Replace with your application's environment path.
Pkg.develop(path=".")
using JSimplex
```

The temporary environment lasts for the current session. Initial package setup
may download Julia registry metadata and the package's declared third-party
dependencies. The package tests use local fixtures and the package's declared
dependencies; they require no network download after initial package setup.

## Construct and solve an LP

In Julia started with `julia --startup-file=no --project=.`:

```julia
using JSimplex, SparseArrays

# Minimize x + 2y subject to x + y >= 1 and x, y >= 0.
problem = LinearProblem(sparse([1.0 1.0]), [1.0, 2.0];
                        row_lower=[1.0], row_upper=[nothing], name="example")
solution = solve(problem;
    options=SolverOptions(iteration_limit=10_000, time_limit=60.0))

if solution.status == OPTIMAL
    @show solution.objective_value  # 1.0
    @show solution.primal           # [1.0, 0.0]
else
    @show solution.status solution.message
end
@show solution.statistics.iterations solution.statistics.elapsed_seconds
```

Presolve runs by default. It applies all implemented reductions automatically,
then restores the original variables and resolves the original LP from the
restored basis when cleanup is needed. Before cleanup, it tries to exchange
basic variables at original bounds for nonbasic variables held at bounds
inferred during presolve. These exchanges are not counted as simplex iterations.
As a postsolve reconstruction, they can recover an optimal original basis even
when `iteration_limit=0`.
If the reduced solve cannot certify its result, JSimplex restarts simplex on
the original LP. With `verbose=true`, this
restart logs the first status and reason. Progress iteration counts and final
statistics include iterations spent on both LPs. To solve the original LP
directly:

```julia
solution = solve(problem; options=SolverOptions(presolve=false))
```

With `verbose=true`, each `solve` logs the original row, column, and nonzero
counts at entry, announces the start of presolve, and logs the reduced counts
after it runs. If postsolve cleanup starts, it announces that step as well.
`verbose=false` suppresses these messages.

## Solve a JuMP model

JuMP is a user-selected integration dependency and is not installed as a
dependency of JSimplex. In an environment that contains both packages, use the
public, non-exported `JSimplex.Optimizer` constructor. JuMP exposes its MOI
module as `MOI` after `using JuMP`:

```julia
using JSimplex
using JuMP

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

The default optimizer uses `Float64`. Choose a supported coefficient type by
passing a typed constructor to JuMP or MOI:

```julia
JSimplex.Optimizer()
JSimplex.Optimizer{Float32}()
JSimplex.Optimizer{BigFloat}()
JSimplex.Optimizer{Rational{BigInt}}()
```

For `Optimizer{T}`, the supported constraint function--set pairs are:

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

Supported objectives are a `MOI.VariableIndex` or a
`MOI.ScalarAffineFunction{T}` (and feasibility sense). Quadratic, nonlinear,
conic, SOS, indicator, complementarity, and semi-domain constraints are not
supported by this adapter.

### JuMP optimizer attributes and LP relaxation

Use the standard JuMP attributes `set_silent(model)` (MOI `Silent`) and
`set_time_limit_sec(model, seconds)` (MOI `TimeLimitSec`) for logging and a
wall-clock limit. The stable JSimplex raw optimizer attribute names are
`relax_integrality`, `iteration_limit`, `primal_tolerance`, `dual_tolerance`,
`zero_tolerance`, `refactorization_interval`, `verbose`, `algorithm`,
`pricing`, `basis_update`, `basis_refactorization`, `scaling`, and `presolve`.
`presolve` is a Boolean and defaults to `true`. Algorithm values are
`:dual` (default) and `:primal`; pricing accepts `:steepest_edge`, `:devex`, or
`:dantzig` for both algorithms.

```julia
set_optimizer_attribute(model, "relax_integrality", true)
set_optimizer_attribute(model, "iteration_limit", 50_000)
set_optimizer_attribute(model, "pricing", :devex)
set_optimizer_attribute(model, "basis_update", :forrest_tomlin)
set_optimizer_attribute(model, "basis_refactorization", :markowitz)
set_optimizer_attribute(model, "scaling", :off)
set_optimizer_attribute(model, "presolve", false)
set_time_limit_sec(model, 60.0)
```

JSimplex has no MIP algorithm. Integer and binary models therefore return an
unsupported-MIP status unless `relax_integrality` is `true`; with that setting,
their bounds and domains are retained and the LP relaxation is solved.

The adapter is one-shot rather than natively incremental. You can edit a JuMP
model and call `optimize!` again: JuMP's MOI cache supplies the current model,
which JSimplex translates into a fresh `LinearProblem` for the next solve.
This adapter does not provide dual results (including a dual objective), warm
starts, or native incremental optimizer modification methods.

`LinearProblem(A, objective; ...)` accepts a sparse matrix and copies its input
data into a `LinearProblem{T}`. Rows mean `row_lower <= A*x <= row_upper`; columns
have `column_lower` and `column_upper` bounds. The objective is
`dot(objective, x) + objective_constant`. Defaults are minimization
(`MIN_SENSE`), constant zero, unbounded rows, nonnegative columns with no upper
bound, and `CONTINUOUS` domains. Set `objective_sense=MAX_SENSE` to maximize.
Optional `row_names` and `column_names` must be empty or match their dimensions.
Construction validates dimensions, finite coefficients, bounds, and domains and
throws `ArgumentError` for invalid input. Treat the model's array fields as
read-only; solving leaves them unchanged.

### Scalar selection and exact arithmetic

The matrix, objective, explicitly supplied objective constant, and finite bound
values determine `T` using Julia's promotion rules. A concrete `AbstractFloat`
or `Rational` type is retained; integer-only input becomes `Float64`. Mixed
floating/rational input follows ordinary Julia promotion. Omitted arguments,
`nothing`, and unbounded sentinels do not affect inference: defaults are created
in `T` afterward. `value_type=T` overrides inference and converts finite data
with validation. Integer working types and complex arithmetic are unsupported.
The matrix stores `SparseMatrixCSC{T,Int}`, the objective `Vector{T}`, and the
objective constant `T`; indices remain `Int`.

```julia
using JSimplex, SparseArrays

rational_problem = LinearProblem(
    sparse(Rational{BigInt}[1 1]), Rational{BigInt}[1, 2];
    row_lower=Rational{BigInt}[1], row_upper=[nothing],
)
exact_solution = solve(rational_problem)
@assert exact_solution.status == OPTIMAL
@assert exact_solution.primal == Rational{BigInt}[1, 0]
@assert exact_solution.objective_value == 1 // big(1)

# Explicitly select exact arithmetic for integer input.
converted = LinearProblem(sparse([1 1]), [1, 2];
                          row_lower=[1], value_type=Rational{BigInt})
@assert converted isa LinearProblem{Rational{BigInt}}

setprecision(BigFloat, 256) do
    big_problem = LinearProblem(sparse(BigFloat[1 1]), BigFloat[1, 2];
                                row_lower=BigFloat[1])
    result = solve(big_problem)
    @assert result.status == OPTIMAL
    @assert result.primal isa Vector{BigFloat}
end
```

`BigFloat` uses Julia's ambient precision; put both model construction and solve
inside `setprecision`. Internal copies and objective-sense changes preserve stored
values and their precision. Simplex arithmetic uses the precision active during
`solve`; power-of-two scaling does not discard stored coefficient bits.
After a precision reduction, an inconclusive optimality or original-objective
certificate returns `NUMERICAL_ERROR`; the objective is returned only when its
exact-value enclosure rounds to one value at the solve precision.
For exact input, use rational values or typed MPS parsing:
converting an already rounded floating value cannot recover its intended decimal.

By default, Float64 bases use sparse UMFPACK LU. Every other supported scalar
uses generic dense LU from `LinearAlgebra`, preserving `T`; empty bases are
supported too. `basis_refactorization=:markowitz` selects the sparse Markowitz
backend described below. Dense BigFloat and rational solves can consume
substantial time and memory and are intended for small models. Use
`Rational{BigInt}` for arbitrary-size exact arithmetic. Fixed-width rationals
such as `Rational{Int}` retain Julia's ordinary solve-time overflow behavior;
these exceptions are not hidden as numerical solver statuses.

### Bounds and migration from 0.3

All four bound arrays now store `Vector{Bound{T}}` instead of numeric values.
Constructors accept finite real values, convertible `Bound` values, and `nothing`
for an unbounded side. For compatibility, `-Inf` is accepted in lower bounds and
`Inf` in upper bounds, even for rational models; they become unbounded tags.
NaN and incorrectly signed infinities are invalid. An unbounded tag's direction
comes from its lower/upper array, not a numeric infinity payload.

Use `isfinite(bound)` before `bound_value(bound)`, which returns a finite value
in `T` and throws `ArgumentError` for an unbounded tag. Migrate direct bound
arithmetic or comparisons by extracting finite values with these helpers:

```julia
lower = rational_problem.row_lower[1]
upper = rational_problem.row_upper[1]
@assert isfinite(lower)
@assert bound_value(lower) == 1 // big(1)
@assert !isfinite(upper)

finite = Bound(3.0f0)                 # Bound{Float32}
unbounded = Bound{Rational{BigInt}}(nothing)
@assert bound_value(finite) === 3.0f0
@assert !isfinite(unbounded)

# Floating infinity sentinels also work with rational model arithmetic.
compatible = LinearProblem(sparse(Rational{BigInt}[1 1]), Rational{BigInt}[1, 2];
                           row_lower=[-Inf], row_upper=[Inf])
@assert !isfinite(compatible.row_lower[1])
@assert !isfinite(compatible.row_upper[1])
```

### Options and termination

`SolverOptions(T; ...)` creates `SolverOptions{T}`. `SolverOptions()` is shorthand
for `SolverOptions(Float64)`. Floating types use these keyword defaults:

| Option | Default | Meaning |
| --- | --- | --- |
| `primal_tolerance` | `1e-7` | Primal feasibility tolerance |
| `dual_tolerance` | `1e-7` | Dual feasibility tolerance |
| `zero_tolerance` | `1e-12` | Numerical zero threshold |
| `iteration_limit` | `100_000` | Maximum completed simplex steps (pivots or primal bound flips) |
| `time_limit` | `Inf` | Wall-clock seconds; `Inf` disables the deadline |
| `refactorization_interval` | `20` | Basis update interval before full factorization |
| `verbose` | `true` | Emit `Info`-level model statistics, simplex progress, and final status |
| `log_level` | `Logging.Debug` | Level emitted through Julia's logging system |
| `algorithm` | `:dual` | `:dual` or `:primal` |
| `pricing` | `:steepest_edge` | Dual or primal pricing rule: `:steepest_edge`, `:devex`, or `:dantzig` |
| `basis_update` | `:pfi` | Basis update: `:pfi`, `:forrest_tomlin`, `:bartels_golub`, or `:suhl_suhl` |
| `basis_refactorization` | `:native` | Full factorization: `:native` or `:markowitz` |
| `scaling` | `:auto` | `:auto`, `:on`, or `:off` row and column scaling |
| `presolve` | `true` | Apply all presolve reductions before simplex; `false` solves the original LP directly |

Forrest–Tomlin maintains a sparse upper factor without row swaps during an
update. Bartels–Golub may swap adjacent rows to choose a larger elimination
pivot. Suhl–Suhl moves the leaving row and column only to the last nonzero
position of the entering spike, reducing fill when the spike ends early. All
three triangular methods reuse solve buffers and store updated factors in
packed sparse columns. The `refactorization_interval` applies to all four
update methods.

With `basis_refactorization=:markowitz`, a full basis factorization chooses
sparse pivots using the Markowitz fill criterion and a column stability
threshold. Once the remaining matrix is at least half dense, it factors the
trailing core with dense LU. The sparse triangular factors use packed index
and value arrays, and solves reuse allocated buffers. This option works with
all four basis update methods and supported numeric types. `:native` remains
the default (`Float64` uses UMFPACK; other types use dense LU).

Floating tolerances are evaluated in `T`; a positive default that rounds to zero
is clamped to `nextfloat(zero(T))`. Rational primal, dual, and zero tolerance
defaults are exactly zero. Rational Harris pivot cutoffs and recession-ray
roundoff allowances are also zero, so default rational solves use exact checks.
Explicit nonzero rational tolerances are allowed. Floating tolerances must be
positive and rational tolerances nonnegative; all must be finite. The
refactorization interval must be positive and limits nonnegative.

`solve(problem; options=nothing)` creates defaults for the problem's `T`.
Explicit options are converted and validated once with `SolverOptions(T, options)`;
this preserves supplied tolerance values instead of replacing them with defaults.
In particular, passing `SolverOptions()` to a rational solve converts its nonzero
floating tolerances. Omit options or use `SolverOptions(Rational{BigInt})` for
exact defaults. Conversion can fail validation, for example when zero rational
tolerances are converted to a floating type.

With `scaling=:auto`, floating models use one pass of row scaling followed by
column scaling. Factors are powers of two; a row or column keeps factor 1 if its
candidate would turn a nonzero value into zero or a finite value into infinity.
The objective constant and sense stay unchanged. Rational models use identity
scaling by default, and `scaling=:on` is invalid for them. Use
`SolverOptions(scaling=:off)` to solve in the input model's units. Simplex
tolerances apply to the scaled working problem; returned primal values and the
objective are restored and checked against the original model.

```julia
exact_options = SolverOptions(Rational{BigInt}; time_limit=2.5)
@assert exact_options.primal_tolerance == 0
@assert exact_options.time_limit === 2.5
@assert solve(rational_problem; options=exact_options).status == OPTIMAL
single_options = SolverOptions(Float32, SolverOptions(time_limit=2.5))
@assert single_options.primal_tolerance isa Float32
```

`time_limit` and elapsed wall-clock seconds remain `Float64` for every model
type; iteration and refactorization counters remain `Int`.
A zero time limit returns `TIME_LIMIT` immediately. Deadline checks
use a monotonic clock; they do not interrupt an in-progress numerical operation.
The deadline starts when `solve` is called and is checked before algorithm/model
validation. Algorithms such as `:auto` return
`ALGORITHM_NOT_SUPPORTED`.

With `verbose=true`, `solve` first reports `rows`, `columns`, and `nnz` for the
input model. When presolve is enabled, it announces the start and reports the
counts again afterward, even when no reduction is made. A separate message
announces postsolve cleanup when it runs. The input statistics also appear when
presolve is disabled or solving stops before presolve.
`nnz` counts nonzero coefficients, excluding explicitly stored sparse zeros.
Each completed basis refactorization emits a
single-line record through Julia's logging system, for example
`iter=12 obj=4.5 pinf=0.5 (1) dinf=2.5 (1) time=0.123456s`. The parenthesized
values are the respective infeasibility counts. The `obj` field uses original
objective units; `pinf` and `dinf` use working problem units when scaling is
enabled. Phase I reports the original MIN/MAX objective including its constant
rather than its auxiliary objective.
Set `verbose=false` to suppress these records. In the MOI/JuMP adapter,
`Silent=true` also suppresses them without changing the stored raw `"verbose"`
attribute.
The last `Info` record reports the termination status, total simplex iterations,
and elapsed time. Optimal runs also report the objective; other statuses include
the termination reason.

Every termination path for `LinearProblem{T}` returns `Solution{T}` with
`objective_value::Union{Nothing,T}` and `primal::Union{Nothing,Vector{T}}`.
`Solution.status` is one of `OPTIMAL`, `INFEASIBLE`, `UNBOUNDED`,
`ITERATION_LIMIT`, `TIME_LIMIT`, `NUMERICAL_ERROR`, `INVALID_MODEL`,
`MIP_NOT_SUPPORTED`, or `ALGORITHM_NOT_SUPPORTED`. Only `OPTIMAL` has a primal
vector and objective value; both fields are `nothing` for all other statuses.
The primal vector uses original structural variables, and the objective includes
the original sense and constant. Every result retains a `message` and
`SolveStatistics` with `iterations`, `elapsed_seconds`, and `refactorizations`.

### Explicit LP relaxation

```julia
mip = LinearProblem(sparse([1.0 1.0]), [1.0, 2.0];
                    row_lower=[1.0], variable_domains=[INTEGER, BINARY])
@assert !is_continuous(mip)
@assert solve(mip).status == MIP_NOT_SUPPORTED
relaxation = solve(mip; relax_integrality=true)
@assert relaxation.status == OPTIMAL
```

All domains other than `CONTINUOUS` require explicit relaxation, including
`INTEGER`, `BINARY`, `SEMI_CONTINUOUS`, and `SEMI_INTEGER`. Integer and binary
relaxations retain their bounds; binary bounds are intersected with `[0, 1]`
when constructing the model. Semi domains allow zero or values in their active
interval; relaxation uses the convex hull of that interval and zero. The input
model retains its domains. JSimplex does not implement a MIP solver.

## Read MPS files

```julia
problem = read_mps("test/fixtures/solver/afiro.mps")  # Automatic format detection
fixed = read_mps("test/fixtures/parser/basic-fixed.mps"; format=:fixed)
free = read_mps("test/fixtures/parser/basic-free.mps"; format=:free)

selected = read_mps("test/fixtures/parser/multiple-sets.mps";
                    rhs_name="SECOND", ranges_name="WIDE",
                    bounds_name="HIGH", objective_name="OBJ")

exact_mps = read_mps("test/fixtures/parser/exact-rational.mps";
                     value_type=Rational{BigInt})
@assert exact_mps.A[1, 1] == 3 // big(10)
@assert solve(exact_mps).objective_value == 11 // big(4)
```

`read_mps(path)` defaults to `LinearProblem{Float64}`. Use `value_type=T` for
typed parsing and construction. Floating tokens are parsed directly in `T`.
Rational parsing reads decimal and `E`/`D` exponent tokens exactly, without
passing through floating-point arithmetic: `1.25` is `5//4`, `-2e-3` is
`-1//500`, and `3D+2` is `300//1`. Parsing, duplicate aggregation, and derived
range arithmetic use `Rational{BigInt}` intermediates with checked conversion to
the requested rational type. Fixed-width construction overflow raises a
source-aware `MPSParseError`; solve-time arithmetic retains Julia's ordinary
overflow behavior. Unbounded endpoints are stored as `Bound{T}` tags, including
where the feature table below uses mathematical infinity notation.

The native reader supports the following contract:

- Formats: `:auto` (default), `:fixed`, and `:free`. Fixed data uses traditional
  fields through column 61, ASCII names of up to eight characters, and blank-name
  continuation records. Free records use whitespace-separated fields. Blank lines,
  `*` comment lines, `$` comments starting at a field boundary, and `D`/`d`
  numeric exponents are accepted.
- Sections: `NAME`, optional `OBJSENSE` (also `OBJSEN`) and `OBJNAME`, `ROWS`,
  `COLUMNS`, optional `RHS`, `RANGES`, and `BOUNDS`, then `ENDATA`. Sections
  must appear in that order, except the two objective metadata sections may be
  interchanged. `OBJSENSE` accepts `MIN` or `MAX`; its default is `MIN`.
- Rows: `E` is equality, `L` is an upper bound, `G` is a lower bound, and `N`
  is a free/objective row. The objective is selected by `objective_name`, then
  `OBJNAME`, then the first `N` row. A selected name must refer to an `N` row.
  Other `N` rows are validated and excluded from the constraint matrix. Without
  any `N` row, the objective is zero.
- RHS and ranges: missing RHS values default to zero. An RHS on the objective
  row becomes the objective constant with its sign reversed. For RHS `b` and
  range `r`, an `L` row becomes `[b-abs(r), b]`, a `G` row becomes
  `[b, b+abs(r)]`, and an `E` row uses the former interval for negative `r`
  and the latter for nonnegative `r`.
- Named sets: `rhs_name`, `ranges_name`, and `bounds_name` select their sets
  independently. Each defaults to the first set encountered in file order;
  selecting a missing set raises an error. Duplicate matrix/objective
  coefficients are summed. Repeated RHS/range values use the last value, and
  bound records are applied in file order.
- Domains: quoted `INTORG`/`INTEND` marker records preserve integer columns,
  with the legacy default bounds `[0, 1]`. Other columns start continuous with
  bounds `[0, Inf]`. Domain metadata is preserved when reading.

Supported bounds are:

| Code | Meaning |
| --- | --- |
| `LO`, `UP` | Set lower/upper bound; a negative `UP` implies lower `-Inf` if no explicit lower-bound record exists |
| `FX` | Fix both bounds to the value |
| `FR` | Set bounds to `[-Inf, Inf]` |
| `MI`, `PL` | Set lower bound to `-Inf` / upper bound to `Inf` |
| `BV` | Binary domain with bounds `[0, 1]`; accepts no value or `1` |
| `LI`, `UI` | Integer domain with an integral lower/upper bound |
| `SC`, `SI` | Semi-continuous/semi-integer domain with the given positive active upper bound and active lower bound `1` unless an explicit lower-bound record (such as `LO` or `LI`) is supplied |

`SC` combines with `LI`, `UI`, or integer markers to form `SEMI_INTEGER`,
independent of declaration order. `SI` also preserves integrality when combined
with `SC`. Explicit active lower bounds are retained, including negative bounds;
LP relaxation includes zero and the entire active interval. Combining `BV` with
`SC` or `SI` in the selected bounds set is rejected as conflicting domain metadata.

`FR` accepts an optional numeric value and ignores it; `MI` and `PL` take no
numeric value. All other bounds except `BV` require one. Parsing rejects
malformed input and unsupported extensions,
including quadratic sections, SOS constraints, and indicators.
`MPSParseError` reports the source path, line, section, and reason. A bad
named-set/objective keyword selection uses line zero; an invalid `format`
raises `ArgumentError`. File access errors propagate normally.

## Tests and development

Run the package tests (no GLPK or external datasets):

```sh
julia --startup-file=no --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.precompile(); Pkg.test()'
```

After initial environment setup, run the fixture-based tests offline with:

```sh
JULIA_PKG_OFFLINE=true julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
```

The isolated development environment installs JET, GLPK, and BenchmarkTools. These
commands resolve JSimplex to this checkout when run from the repository root:

```sh
julia --startup-file=no --project=dev -e 'using Pkg; Pkg.develop(path="."); Pkg.instantiate()'
julia --startup-file=no --project=dev dev/tests/runtests.jl
julia --startup-file=no --project=dev dev/run_suite.jl --dataset afiro --compare-glpk
julia --startup-file=no --project=dev dev/run_suite.jl --tag numerical --compare-glpk
julia --startup-file=no --project=dev dev/run_suite.jl --tag quick
julia --startup-file=no --project=dev dev/benchmarks.jl afiro
```

The development tests include JET inference checks for Float64 and
`Rational{BigInt}` solver kernels. JET is not a root dependency or part of the
mandatory package-test environment.

`dev/Manifest.toml` is intentionally generated locally and ignored by Git.
Do not commit generated root manifests or local `.julia/` depots either.
Mandatory CI runs Julia 1.13 package tests without GLPK; the separate manual
**Extended validation** workflow runs the development tests and AFIRO/GLPK
comparison above.

`run_suite.jl` defaults to the `quick` tag and always solves LP relaxations.
Repeated `--dataset` and `--tag` values form unions within each selector; dataset
and tag selectors intersect. Results are sorted by name and report status,
objective, iterations, elapsed seconds, and PASS/FAIL. Failures exit nonzero.
AFIRO is checked in at `test/fixtures/solver/afiro.mps`; the larger GREENBEA
benchmark is at `dev/fixtures/greenbea.mps` and is selected with
`--dataset greenbea` or `--tag full`. GREENBEA is experimental and is outside
the required regression gate.

The standard test suite also includes seven small benchmark fixtures from
[NetLib](https://www.netlib.org/lp/data/) and
[MIPLib 2017](https://miplib.zib.de/download). They are stored under
`test/fixtures/solver/netlib/` and `test/fixtures/solver/miplib/` as plain MPS,
so tests need neither the local benchmark directories nor a network connection.
MIPLib cases are solved only as explicit LP relaxations; the listed objectives
are LP objectives, not MIP objectives. Both simplex algorithms are checked
against reference objectives obtained with GLPK, except for `pk1` as noted below.

| Fixture | Numerical behavior covered |
| --- | --- |
| NetLib `kb2` | Many equality rows and varied matrix coefficients. |
| NetLib `sc50a` | Linked equality and inequality rows with repeated structural patterns. |
| NetLib `adlittle` | Matrix coefficient range from 0.0012 to 64.3 and a much larger objective scale. |
| MIPLib [`stein9inf`](https://miplib.zib.de/instance_details_stein9inf.html) | Integer infeasibility with a feasible LP relaxation. |
| MIPLib [`flugpl`](https://miplib.zib.de/instance_details_flugpl.html) | Mixed integer domains, fractional coefficients, and large objective values. |
| MIPLib [`markshare_4_0`](https://miplib.zib.de/instance_details_markshare_4_0.html) | Dense equalities and a zero-cost LP optimum. |
| MIPLib [`pk1`](https://miplib.zib.de/instance_details_pk1.html) | The current dual method stalls on the LP relaxation; primal reaches zero objective, and dual must stop at its iteration limit or solve it. |

`dev/run_suite.jl --tag numerical --compare-glpk` checks the six cases with
reliable default-dual optima against GLPK. The `pk1` behavior is covered by
the standard regression test with a fixed iteration cap.

### Large and private datasets

`dev/datasets.toml` records instance paths, SHA-256 checksums, tags, and optional
expected results. Its commented schema describes the provenance, license,
version, and source metadata required for external collections.
`dev/Artifacts.toml` is the location for immutable collection bindings and
verified download hashes. No external collection is currently bound or downloaded
automatically, and no external NETLIB/MIPLIB collection is needed in CI. The
selected small fixtures above run with the mandatory package tests.

After registering a real collection with redistribution-compatible sources,
install its artifact explicitly with Julia's `Pkg.Artifacts` tools. A registered
artifact instance can instead use `--data-root /path/to/collection`; the path is
relative to that root and its checksum is still checked. This option does not
override repository fixtures or discover unregistered files. Supply private data
locally and do not commit restricted datasets. Missing files, bindings, and
checksum mismatches produce actionable errors.

## Limitations and extension points

Dual and primal simplex are implemented. Presolve removes fixed columns, empty
columns with a finite optimal bound, empty and singleton rows, dominated
proportional rows, and linearly dependent rows whose bounds are implied by
retained rows. It substitutes free variables from two-term equalities and
aggregates singleton columns in equality rows. Sparse equality aggregation can
remove a non-singleton column and, when the other column bounds imply its bounds,
the equality row. Objective-aware dual fixing moves a column to a finite bound
when its cost and every incident row permit that direction.
Multi-term rows propagate implied column bounds and rows implied by column
bounds are removed. Presolve repeats its reductions until a round makes no
change, with a limit of 12 rounds.
Transformed finite values must be exactly representable in the model's scalar
type, except objective coefficients created by singleton equality aggregation
for `Float32` and `Float64`. Those coefficients may be rounded when the
relative error is at most eight machine epsilons. Projected bounds and the
objective constant still require exact representation; `BigFloat` and rational
models retain the exact rule. Sparse equality aggregation
considers rows with at most eight terms and permits at most ten estimated
coefficient updates per pivot, 200,000 updates and 50,000 pivots per pass.
General rational row elimination is limited to 256 rows, 10,000 nonzeros,
and 200,000 sparse elimination operations. Floating models use reversible
row and column scaling by default. After postsolve, an optimal reduced
solution is cleaned up on the original LP from the restored basis, with a
feasibility-checked basis projection when inferred bounds moved nonbasic
columns. A basic one-shot MOI/JuMP adapter is
available. Missing features include scaling of the entire objective, public
warm-start API, native incremental optimizer modification, MIP algorithm,
or support for quadratic, SOS, or indicator models. Difficult or
ill-conditioned models may terminate with `NUMERICAL_ERROR` or a resource limit.

Floating results require conclusive numerical certificates. Even a simple LP
with equality constraints or cancellation can return `NUMERICAL_ERROR` when
rounding uncertainty prevents certification within the configured tolerances.
That status does not classify the LP as infeasible, unbounded, or optimal.
Use `Rational{BigInt}` with its default zero tolerances for exact arithmetic
on small models; construct or read the model in that type to retain exact input.

In particular, a narrow class of Float64 models with an ambiguous recession
certificate can return `MOI.NUMERICAL_ERROR` through the MOI adapter. Exact
rational arithmetic can certify the corresponding unbounded model. This is a
conservative limitation for ambiguous Float64 recession cases, not a claim that
all unbounded Float64 models are unclassified.

The internal pipeline separates model validation, presolve, scaling, simplex
workspaces, basis factorization, and restoration of the original primal solution.
These boundaries allow additional reversible presolve rules and alternative
factorization/update strategies. A future MIP layer can
repeatedly solve LPs with modified bounds. These internal structures are not
exported public APIs. The supported interface is the exported model/options/result
types, enums, `Bound`, `bound_value`, `isfinite(::Bound)`, `is_continuous`,
`read_mps`, and `solve`; use Julia help (for example `?solve`) for their
docstrings.

## License

Released under the [MIT license](LICENSE).
