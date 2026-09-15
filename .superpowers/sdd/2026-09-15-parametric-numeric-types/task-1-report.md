# Task 1 Report: Numeric Policy and Tagged Bounds

## Implementation summary

Added the typed `Bound{T}` representation and numeric policy foundation. Bounds support finite values and inert unbounded tags, reject non-finite bounded payloads, expose `Base.isfinite`, and provide `bound_value`. Added exactness, typed-ratio, supported-type, and bound-normalization helpers with signed-infinity and NaN validation. Included the new source before options and exported `Bound` and `bound_value`.

## Files changed

- `src/numeric.jl` (new): numeric policy, `Bound`, constructors, equality, finite/unbounded helpers, and normalization.
- `src/JSimplex.jl`: include and exports.
- `test/numeric_tests.jl` (new): focused Task 1 tests.
- `test/runtests.jl`: includes numeric tests before options tests.

## Self-review

Ran `git diff --check` successfully. Reviewed the complete tracked diff and verified the new files and module ordering. The implementation is limited to the requested numeric foundation; `LinearProblem` and solver parameterization were not changed.

## TDD evidence

RED:

```text
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/numeric_tests.jl")'
```

Failed before implementation with `UndefVarError: Bound not defined in Main`, confirming the focused tests exercised the missing API.

GREEN:

```text
JULIA_DEPOT_PATH=/tmp/julia-depot julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/numeric_tests.jl")'
```

Passed: `Numeric policy and tagged bounds | 17 17`.

Full package verification:

```text
JULIA_DEPOT_PATH=/home/jspitz/.julia JULIA_NUM_THREADS=1 julia --startup-file=no --compiled-modules=no --project=. test/runtests.jl
```

Passed: `JSimplex | 2024 2024`.

The exact requested `julia ... -e 'using Pkg; Pkg.test()'` command could not complete because the sandbox cannot resolve/download the Julia General registry. The direct package test entrypoint provided equivalent suite coverage and passed.

## Concerns

`Pkg.test()` remains unverified in its exact form due solely to unavailable registry/network access; the full test entrypoint passed with compiled modules disabled.

## Fix Round 1

### Changed behavior

Finite `Bound` inputs are now accepted by `_normalize_bound` before the generic `Real` guard. Their finite payload is read with `bound_value` and converted to the requested target type. The existing early return for unbounded bounds remains unchanged and never reads the inert payload.

### Test coverage

Added finite-bound normalization coverage to `test/numeric_tests.jl`, converting the existing `Float32` bound to a `Float64` bound and checking the resulting value.

### TDD and verification

RED regression run:

```text
JULIA_DEPOT_PATH=/tmp/julia-depot julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/numeric_tests.jl")'
```

Failed at the new test with `ArgumentError: column lower bound must be a real value or nothing`, caused by the `input isa Real` guard rejecting `Bound`.

GREEN and full-suite runs:

```text
JULIA_DEPOT_PATH=/tmp/julia-depot julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/numeric_tests.jl")'
```

Passed: `Numeric policy and tagged bounds | 18 18`.

```text
JULIA_DEPOT_PATH=/home/jspitz/.julia JULIA_NUM_THREADS=1 julia --startup-file=no --compiled-modules=no --project=. test/runtests.jl
```

Passed: `JSimplex | 2025 2025`.

### Self-review

Reviewed the diff and ran `git diff --check`. The fix is localized to `_normalize_bound` and the requested numeric regression test; no solver or `LinearProblem` parameterization was introduced.

## Controller verification supplement

The controller reran the exact requested command outside the restricted
subagent sandbox:

```text
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
```

It passed `JSimplex | 2024 2024` on commit `623be0e`. The generated root
`Manifest.toml` was deleted immediately afterward.
