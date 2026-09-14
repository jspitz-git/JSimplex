# Task 1 Report: Create the package shell and result contracts

## Implementation summary

Created the Julia 1.13 package shell and public result contracts. The package declares only the required standard-library dependencies, exports the termination statuses and contract types, validates solver option limits, and provides statistics and solution containers.

## Files changed

- `Project.toml`
- `src/JSimplex.jl`
- `src/options.jl`
- `test/Project.toml`
- `test/runtests.jl`
- `test/options_tests.jl`

Legacy root files were left untouched.

## RED evidence

Command:

```text
julia --startup-file=no --project=. -e 'include("test/runtests.jl")'
```

Result: failed as expected because package `JSimplex` was not installed/available before `src/JSimplex.jl` existed:

```text
ArgumentError: Package JSimplex [68c30f08-d64b-42cf-ac89-1dfed499aac3] is required but does not seem to be installed
```

The first mandated `Pkg.test()` invocation was additionally blocked by the sandbox's read-only default Julia depot while Pkg attempted registry setup. That environmental issue was avoided for subsequent verification with a writable temporary depot and the existing depot as a read-only fallback.

## GREEN evidence

Command:

```text
JULIA_DEPOT_PATH=/tmp/julia-depot:/home/jspitz/.julia JULIA_PKG_OFFLINE=true julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
```

Result: exit code 0; package tests passed:

```text
Test Summary: | Pass  Total  Time
JSimplex      |   11     11  0.2s
Testing JSimplex tests passed
```

Focused direct include also passed with 11/11 tests. `git diff --check` passed.

## Final test results

`Pkg.test()` passes all 11 tests, offline and without GLPK. Julia emitted a non-fatal warning that it could not reach the registry server; all required packages were available locally. The generated local `Manifest.toml` was removed because it is not part of this task's requested files.

## Self-review findings

- Package identity, Julia compatibility, and dependency boundary match the brief exactly.
- Public exports include all nine termination statuses and all four contract types.
- Option defaults, conversions, and validation messages match the brief.
- Statistics and solution field types match the brief.
- No legacy root file was modified.
- No GLPK, JuMP, MathOptInterface, or BenchmarkTools dependency was added.

## Concerns

The execution environment has no network access and its default Julia depot is read-only. Verification therefore uses `JULIA_DEPOT_PATH=/tmp/julia-depot:/home/jspitz/.julia` and `JULIA_PKG_OFFLINE=true`; this produces a harmless registry-download warning but does not affect test results.
