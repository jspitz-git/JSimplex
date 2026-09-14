# JSimplex Modernization for Julia 1.13

Date: 2026-09-14

## Goal

Convert the pre-1.0 Julia proof-of-concept dual simplex implementation into a
proper package for Julia 1.13. The new package will replace the original public
API, have no production dependency on GLPK, and provide native fixed- and
free-format MPS loading. Its architecture must provide clear extension points
for a future primal simplex method, scaling, presolve, MathOptInterface/JuMP
integration, and a MIP solver.

The first release solves linear programs only. It can load MIP models and retain
their variable domains, but it can solve them only when the caller explicitly
requests an LP relaxation.

All repository documentation, docstrings, comments, diagnostics, and other
developer-facing text will be written in English.

## First-release scope

The conversion includes:

- a modern Julia package structure with `Project.toml`, a `JSimplex` module,
  tests, and a documented public API;
- a new linear-problem model independent of input formats and solvers;
- a native fixed- and free-format MPS parser;
- modernization of the existing dual simplex core and product-form basis
  updates;
- separate production, test, and development environments;
- fast deterministic tests without an external solver and optional reference
  comparisons with GLPK in the development environment;
- reproducible management of large test collections.

The first release excludes the primal simplex method, effective presolve
transformations, non-identity scaling, branch-and-bound, a public warm-start
API, a direct MOI/JuMP adapter, quadratic models, SOS constraints, and indicator
constraints. Adding these later must not require replacing the core model or
breaking the public `solve` API.

## Package structure

The proposed layout is:

```text
Project.toml
LICENSE
README.md
src/
  JSimplex.jl
  model.jl
  mps.jl
  solver.jl
  dual_simplex.jl
  factorization.jl
test/
  Project.toml
  runtests.jl
  model_tests.jl
  mps_tests.jl
  solver_tests.jl
  fixtures/
    parser/
    solver/
dev/
  Project.toml
  Artifacts.toml
  datasets.toml
  run_suite.jl
  reference_glpk.jl
  benchmarks.jl
docs/
  superpowers/specs/
```

The production `Project.toml` will declare `julia = "1.13"` compatibility and
only the standard libraries required at runtime, particularly `LinearAlgebra`,
`SparseArrays`, and `Logging`. GLPK, BenchmarkTools, and any other diagnostic
tools will exist only in `dev/Project.toml`. `test/Project.toml` will contain
only dependencies needed by the fast package tests and will not require GLPK.

## Public API

Basic use will look like this:

```julia
using JSimplex

problem = read_mps("model.mps")
solution = solve(problem; relax_integrality=false,
                 options=SolverOptions())
```

The public types will include at least `LinearProblem`, `Solution`,
`SolverOptions`, `TerminationStatus`, `ObjectiveSense`, and `VariableDomain`.
The exact export list will remain small. Internal workspaces and individual
simplex operations will not be part of the compatibility contract.

`Solution` will contain a termination status, objective value, primal solution
for the original structural variables, iteration count, and statistics. For a
status without a valid solution, the primal values and objective value will be
absent instead of containing misleading numeric values.

The first release defines these termination statuses:

- `OPTIMAL`;
- `INFEASIBLE`;
- `UNBOUNDED`;
- `ITERATION_LIMIT`;
- `NUMERICAL_ERROR`;
- `INVALID_MODEL`;
- `MIP_NOT_SUPPORTED`;
- `ALGORITHM_NOT_SUPPORTED`.

`SolverOptions` will contain primal, dual, and zero tolerances; an iteration
limit; a refactorization frequency; a logging level; and an algorithm choice.
The first release implements only `algorithm=:dual`. Until implemented,
`:primal` and `:auto` return `ALGORITHM_NOT_SUPPORTED`.

## Data model

`LinearProblem` is an immutable solver input containing:

- a sparse constraint matrix `A`;
- a linear objective vector and constant;
- minimization or maximization sense;
- lower and upper row bounds;
- lower and upper variable bounds;
- `CONTINUOUS`, `INTEGER`, `BINARY`, `SEMI_CONTINUOUS`, and `SEMI_INTEGER`
  variable domains;
- a model name and optional row and column names.

Infinite bounds use `-Inf` and `Inf`, not `typemin(Float64)` and
`typemax(Float64)`. Construction validates dimensions, bound ordering, finite
coefficients, and domain consistency.

Every format adapter produces the same `LinearProblem`. A future MOI/JuMP
adapter therefore will not enter the simplex core or alter its data structures.

## MPS parser

`read_mps` automatically detects fixed- and free-format MPS. The caller can
override detection with `format=:fixed` or `format=:free`. The `rhs_name`,
`ranges_name`, `bounds_name`, and `objective_name` arguments select named sets
and the objective row. The parser supports these sections:

- `NAME`, `OBJSENSE`, and `OBJNAME`;
- `ROWS`, `COLUMNS`, `RHS`, `RANGES`, and `BOUNDS`;
- `ENDATA`.

Supported row types are `N`, `E`, `L`, and `G`. The row selected by the
`objective_name` argument, the `OBJNAME` section, or—when neither is
present—the first `N` row defines the objective. Other `N` rows are not
constraints. The parser validates them but does not copy their coefficients
into `LinearProblem`. A file without an objective row produces a zero
objective.

Supported bound types are `LO`, `UP`, `FX`, `FR`, `MI`, `PL`, `BV`, `LI`,
`UI`, `SC`, and `SI`. The parser also recognizes `INTORG` and `INTEND` markers.
Default bounds and `RANGES` interpretation follow MPS conventions. Duplicate
matrix coefficients are summed.

Multiple named RHS, ranges, and bounds sets are loaded symbolically. The caller
can select a set by name; without a selection, the first set in file order is
used deterministically. Requesting a set that does not exist is an input error.

Parsing has two phases. It first reads, classifies, and validates symbolic
records, then constructs the sparse matrix and result vectors once. Diagnostics
include the file path, line number, current section, and reason. Quadratic
sections, SOS constraints, indicator constraints, and other unsupported
sections are rejected explicitly.

## Integral domains and LP relaxation

The parser always preserves integer and semi-continuous domains. `solve` never
silently relaxes a MIP. If a model is not continuous and
`relax_integrality=false`, it returns `MIP_NOT_SUPPORTED`.

With `relax_integrality=true`, `INTEGER` and `BINARY` variables become
continuous while retaining their bounds. `SEMI_CONTINUOUS` and `SEMI_INTEGER`
variables are relaxed to the convex hull of `{0} ∪ [lower, upper]`. The original
model remains unchanged.

Domains remain part of the model so that a future branch-and-bound layer can
create nodes with modified bounds and repeatedly invoke the internal LP solver.

## Solver pipeline and extensibility

Solving follows this pipeline:

```text
LinearProblem
  -> validate
  -> presolve
  -> scale
  -> SimplexWorkspace
  -> primal/dual simplex
  -> unscale
  -> postsolve
  -> Solution
```

Presolve and scaling are identity transformations in the first release. They
still have concrete representations:

- `PresolveResult` contains the working model and a stack of reversible
  transformations used to reconstruct a solution;
- `Scaling` contains row and column factors and conversions for primal and dual
  quantities;
- `Basis` separately represents basic variables and nonbasic variable states;
- `SimplexWorkspace` contains the shared mutable basis state, factorization,
  primal values, reduced costs, pricing weights, and work buffers.

Algorithm-specific operations—such as leaving-variable selection,
entering-variable selection, ratio tests, and pricing-weight updates—are
separate from shared basis management. This boundary permits a future primal
simplex method without duplicating factorization and working-model structures.

Each `solve` call creates a new workspace. The input `LinearProblem` remains
unchanged and can be solved repeatedly with different options.

## Dual simplex and factorization

The numerical core will be ported to modern Julia as faithfully as possible.
Its mathematical behavior will change only where required by the defined API
or by a focused failing test. The two-pass Harris ratio test, dual steepest-edge
pricing, cost shifting, and product-form updates will be retained.

Basis factorization will sit behind an internal interface for forward solves,
transpose solves, column replacement, and full refactorization. Initial and
periodic LU factorizations will use the current sparse `lu`; product-form
updates will remain custom. This boundary permits a different update or
factorization implementation without changes to primal or dual simplex
strategies.

Unstructured `print` output, unchecked `@assert` calls, and hard-coded limits
will be replaced with status results, validation, and controlled logging.

## Testing

`Pkg.test()` will be a fast, deterministic, network-independent suite covering:

- `LinearProblem` construction, validation, and immutability;
- fixed- and free-format MPS;
- ranges, every supported bound type, named sets, and MIP markers;
- successful LP relaxation and rejection of an unrelaxed MIP;
- small manually verified LPs for `OPTIMAL`, `INFEASIBLE`, `UNBOUNDED`, and
  `ITERATION_LIMIT`;
- AFIRO regression solving;
- malformed-input diagnostics and rejection of unsupported MPS sections.

Small inputs and their expected results are versioned under `test/fixtures`.
Mandatory tests do not invoke GLPK.

## Development environment and large data sets

`dev/Project.toml` contains GLPK, BenchmarkTools, and other development-only
dependencies. A reference script compares JSimplex statuses and results with
GLPK, but it is not part of production execution or mandatory package tests.
GREENBEA is an integration and benchmark case, not a fast unit test.

Large or externally managed collections are not committed directly to Git:

- `dev/Artifacts.toml` pins reproducible versions of freely available
  collections with hashes and source URLs;
- `dev/datasets.toml` records collections, instances, expected statuses or
  optima, exceptions, licenses, provenance, and tags such as `quick`, `full`,
  and `lp-relaxation`;
- `dev/run_suite.jl` selects collections and tags and also accepts an explicit
  local data directory for private or local instances;
- NETLIB, MIPLIB relaxations, and other collections run only when explicitly
  requested or in a separate extended CI job.

If a collection's license prohibits redistribution, its artifact or dataset
manifest contains only the required metadata and the user supplies local data.
A missing opt-in data set produces an actionable error rather than a failure
inside a test.

## Documentation and CI

The README will describe installation, the public API, supported MPS features,
LP relaxation, separate fast and extended test commands, and the limitations of
the proof-of-concept solver. Public types and functions will have docstrings.
The repository will include a separate MIT `LICENSE` consistent with the
existing README declaration.

CI for Julia 1.13 will instantiate a clean production environment and run
`Pkg.test()`. An extended job using the development environment will remain
separate and may run less frequently or manually because it downloads data sets
and uses GLPK.

## Completion criteria

The conversion is complete when:

1. the package loads in a clean Julia 1.13 environment without installing GLPK;
2. `Pkg.test()` passes without network access or an external solver;
3. the fixed- and free-format MPS parser covers the agreed sections, bounds,
   and integrality markers;
4. AFIRO reaches the expected status and solution within defined tolerances;
5. a MIP is not solved without explicit relaxation and passes through the LP
   pipeline when relaxation is requested;
6. the development script compares JSimplex with GLPK on selected instances;
7. production source files and the production project do not import GLPK or
   BenchmarkTools;
8. the input model remains unchanged after solving;
9. the pipeline and basis structures permit a primal simplex method, scaling,
   presolve, and repeated LP solves from a future MIP solver without changing
   the public model;
10. all repository documentation and source comments introduced by the
    modernization are in English.
