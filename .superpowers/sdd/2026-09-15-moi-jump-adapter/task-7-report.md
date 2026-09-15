# Task 7 Report: Selected MOI Conformance Coverage

## Scope

Added a selected, function-reference MOI.Test gate and included it after the
focused MOI result tests. The gate uses the required bridge-backed,
non-incremental optimizer setup and does not use substring test filters.

The adapter now advertises support for `MOI.ObjectiveSense`, which is required
by the selected supported-LP tests and is consistent with the translated
objective-sense interface.

## RED Evidence

Initial selected-conformance command:

```bash
julia --startup-file=no --project=. -e 'using JSimplex, Test; import MathOptInterface as MOI; include("test/moi/conformance_tests.jl")'
```

Exit 1: 21 passed, 9 errored, 30 total. Each error was an MOI.Test
`RequirementUnmet` for `MOI.supports(model, MOI.ObjectiveSense())`.

Focused ObjectiveSense regression before the adapter change:

```bash
julia --startup-file=no --project=. -e 'using JSimplex, Test; import MathOptInterface as MOI; include("test/moi/optimizer_tests.jl")'
```

Exit 1: 24 passed, 1 failed, 25 total. The new assertion
`MOI.supports(JSimplex.Optimizer(), MOI.ObjectiveSense())` was false.

After adding `MOI.ObjectiveSense` support, the selected harness reached its
remaining boundary conditions: exit 1 with 212 passed, 1 failed, and 9 errored
(222 total). The failed function was
`MOI.Test.test_linear_DUAL_INFEASIBLE`; the nine errors were independent
`MOI.DualObjectiveValue` requests inside the selected integration functions.

## Diagnosis and Task Rulings

MOI 1.53.0 stores `Config.exclude` as exact `Any` entries, and
`MOI.Test._supports(config, attribute)` is `!(attribute in config.exclude)`.
Consequently, excluding `MOI.ConstraintDual` does not exclude the separately
checked `MOI.DualObjectiveValue`. Since dual results are outside the approved
API, the Task 7 ruling added `MOI.DualObjectiveValue` to `Config.exclude`.

The selected `test_linear_DUAL_INFEASIBLE` model translates to the Float64 LP
with row `-x + 2y <= 0`, bounds `x, y >= 0`, and objective `min -x - y`.
A hand-built direct `LinearProblem{Float64}` has equal matrix, objective,
bounds, domains, and names, and produces the same core result:

```text
NUMERICAL_ERROR
auxiliary direction has uncertain feasibility or objective improvement
SolveStatistics(1, <elapsed>, 0)
```

The path is `MOI.optimize!` to `solve`, then `_solve_continuous_dual`, then
`_make_dual_feasible!`. `src/dual_simplex.jl` converts an ambiguous recession
direction to that exact `NUMERICAL_ERROR`; the adapter faithfully maps the core
status to `MOI.NUMERICAL_ERROR`. Existing core tests establish that Float64
recession certification can deliberately return `NUMERICAL_ERROR`, while exact
rational arithmetic certifies unboundedness. Per the ruling, Task 7 does not
change the core classification or mask it in the adapter, and removes only
`MOI.Test.test_linear_DUAL_INFEASIBLE` from the Float64 selected tuple.

The focused direct-MOI regression records this behavior: the model returns
`MOI.NUMERICAL_ERROR` and the core raw message for `Float64`, and
`MOI.DUAL_INFEASIBLE` with zero primal results for `Rational{BigInt}`.

## GREEN Evidence

Focused optimizer and result suites:

```bash
julia --startup-file=no --project=. -e 'using JSimplex, Test; import MathOptInterface as MOI; include("test/moi/optimizer_tests.jl"); include("test/moi/result_tests.jl")'
```

Exit 0: 178 passed, 178 total. This includes 53 optimizer assertions and 125
result assertions, including the seven recession-status assertions.

Selected conformance command:

```bash
julia --startup-file=no --project=. -e 'using JSimplex, Test; import MathOptInterface as MOI; include("test/moi/conformance_tests.jl")'
```

Exit 0: 209 passed, 209 total.

Complete root verification:

```bash
julia --startup-file=no --project=. test/runtests.jl
```

Exit 0: 11,692 passed, 11,692 total, 1m22.0s. The transport retained the
complete final root result through its active terminal session; chunked root
execution was not needed.

## Files Changed

- `src/moi/attributes.jl`
- `test/moi/optimizer_tests.jl`
- `test/moi/result_tests.jl`
- `test/moi/conformance_tests.jl`
- `test/runtests.jl`
- `.superpowers/sdd/2026-09-15-moi-jump-adapter/task-7-report.md`

## Self-Review and Concerns

No separate self-review was performed, following the explicit Task 7
instruction not to review this work. `git diff --check` is run before commit.

The selected suite intentionally excludes all dual-result assertions, including
the independently gated `MOI.DualObjectiveValue`, because duals are not part of
the declared adapter interface. The Float64 ambiguous-recession limitation is
documented by the focused regression; exact rational input still reports the
standard unbounded status.
