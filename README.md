# JSimplex.jl

JSimplex is a proof-of-concept dual simplex solver for linear programming in
Julia 1.13. It includes a native fixed/free MPS reader and preserves integer and
semi-continuous variable domains for explicit LP relaxation. It is experimental:
correctness, numerical robustness, and performance are not guaranteed for general
models. Use an established solver for production optimization.

The numerical core includes a two-pass Harris ratio test, dual steepest-edge
pricing, cost shifting, sparse LU factorization, and product-form basis updates.
Runtime dependencies are Julia standard libraries only: `LinearAlgebra`,
`SparseArrays`, and `Logging`. GLPK and BenchmarkTools belong to the optional
development environment.

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
may download Julia registry metadata even though the runtime has no third-party
packages. The package tests use only local fixtures and standard libraries.

## Construct and solve an LP

In Julia started with `julia --startup-file=no --project=.`:

```julia
using JSimplex, SparseArrays

# Minimize x + 2y subject to x + y >= 1 and x, y >= 0.
problem = LinearProblem(sparse([1.0 1.0]), [1.0, 2.0];
                        row_lower=[1.0], row_upper=[Inf], name="example")
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

`LinearProblem(A, objective; ...)` accepts a sparse matrix and copies its input
data into `Float64` arrays. Rows mean `row_lower <= A*x <= row_upper`; columns
have `column_lower` and `column_upper` bounds. The objective is
`dot(objective, x) + objective_constant`. Defaults are minimization
(`MIN_SENSE`), constant zero, unbounded rows, nonnegative columns with no upper
bound, and `CONTINUOUS` domains. Set `objective_sense=MAX_SENSE` to maximize.
Optional `row_names` and `column_names` must be empty or match their dimensions.
Construction validates dimensions, finite coefficients, bounds, and domains and
throws `ArgumentError` for invalid input. Use `-Inf` and `Inf` for infinite
bounds. Treat the model's array fields as read-only; solving leaves them unchanged.

### Options and termination

`SolverOptions` supports these keyword defaults:

| Option | Default | Meaning |
| --- | --- | --- |
| `primal_tolerance` | `1e-7` | Primal feasibility tolerance |
| `dual_tolerance` | `1e-7` | Dual feasibility tolerance |
| `zero_tolerance` | `1e-12` | Numerical zero threshold |
| `iteration_limit` | `100_000` | Maximum completed simplex pivots |
| `time_limit` | `Inf` | Wall-clock seconds; `Inf` disables the deadline |
| `refactorization_interval` | `20` | Basis update interval before full factorization |
| `log_level` | `Logging.Debug` | Level emitted through Julia's logging system |
| `algorithm` | `:dual` | Only implemented algorithm |

Tolerances and the refactorization interval must be positive; limits must be
nonnegative. A zero time limit returns `TIME_LIMIT` immediately. Deadline checks
use a monotonic clock; they do not interrupt an in-progress numerical operation.
The deadline starts when `solve` is called and is checked before algorithm/model
validation. Algorithms such as `:primal` and `:auto` return
`ALGORITHM_NOT_SUPPORTED`.

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
```

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
| `SC`, `SI` | Semi-continuous/semi-integer domain with the given positive active upper bound and active lower bound `1` unless an `LO` record is supplied |

`FR`, `MI`, and `PL` take no numeric value; all other bounds except `BV`
require one. Parsing rejects malformed input and unsupported extensions,
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

The isolated development environment installs GLPK and BenchmarkTools. These
commands resolve JSimplex to this checkout when run from the repository root:

```sh
julia --startup-file=no --project=dev -e 'using Pkg; Pkg.develop(path="."); Pkg.instantiate()'
julia --startup-file=no --project=dev dev/tests/runtests.jl
julia --startup-file=no --project=dev dev/run_suite.jl --dataset afiro --compare-glpk
julia --startup-file=no --project=dev dev/run_suite.jl --tag quick
julia --startup-file=no --project=dev dev/benchmarks.jl afiro
```

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

### Large and private datasets

`dev/datasets.toml` records instance paths, SHA-256 checksums, tags, and optional
expected results. Its commented schema describes the provenance, license,
version, and source metadata required for external collections.
`dev/Artifacts.toml` is the location for immutable collection bindings and
verified download hashes. No external collection is currently bound or downloaded
automatically, and no external NETLIB/MIPLIB collection runs in CI.

After registering a real collection with redistribution-compatible sources,
install its artifact explicitly with Julia's `Pkg.Artifacts` tools. A registered
artifact instance can instead use `--data-root /path/to/collection`; the path is
relative to that root and its checksum is still checked. This option does not
override repository fixtures or discover unregistered files. Supply private data
locally and do not commit restricted datasets. Missing files, bindings, and
checksum mismatches produce actionable errors.

## Limitations and extension points

Only dual simplex is implemented. Presolve and scaling currently apply identity
transformations. There is no primal simplex, effective presolve, non-identity
scaling, public warm-start API, MOI/JuMP adapter, branch-and-bound, or support
for quadratic, SOS, or indicator models. Difficult or ill-conditioned models
may terminate with `NUMERICAL_ERROR` or a resource limit.

The internal pipeline separates model validation, presolve, scaling, simplex
workspaces, basis factorization, and restoration of the original primal solution.
These boundaries are intended for future primal simplex, reversible presolve,
scaling, and alternative factorization/update strategies. Future MOI/JuMP
adapters can build `LinearProblem` objects, and a future MIP layer can repeatedly
solve LPs with modified bounds. These internal structures are not exported public
APIs. The supported interface is the exported model/options/result types, enums,
`is_continuous`, `read_mps`, and `solve`; use Julia help (for example `?solve`)
for their docstrings.

## License

Released under the [MIT license](LICENSE).
