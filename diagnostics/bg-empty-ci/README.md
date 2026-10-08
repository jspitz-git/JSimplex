# Empty BG reset and CI workload verification

Verified on 2026-10-08, based on master `3807f50a222ab888a4efcc031bd7d0d7266f7692`.

## Scope

This integrates the existing empty Bartels–Golub reset fix from experimental
commit `3ac023f90605ef29a01256b6708090a68b0958da` (cherry-picked as `ca67313`).
Resetting an already empty upper factor to dimension zero now returns before
constructing an unused `UpperRowOrder`. Retained-capacity validation still runs.
This removes two 32-byte allocations. The older 32-byte BTRAN boxing fix is a
separate change already present in master.

CI now generates a package-scoped `LocalPreferences.toml` containing
`[JSimplex]` and `precompile_workload = false` before cache/build/test steps.
The preference file is not committed. The package default is unchanged;
ordinary compilation, coverage, bounds checks, and the full CI test suite remain
enabled. Dependency workloads are not disabled by this package preference.

## Verification

Environment: Julia 1.13.0, aarch64 Linux, one Julia and BLAS thread, 8 GiB virtual
memory cap, the existing 6 GiB available-RAM / 1 GiB swap guard, 600-second job
limit. Normal compilation used `-g0 -O1`; no `--compile=min` allocation claims.

| Check | Result | Process wall time |
| --- | --- | ---: |
| Targeted allocation and triangular-factor regressions | 5709 / 5709 | 23.05 s |
| Same tests with `--code-coverage=user --check-bounds=yes` | 5709 / 5709 | 26.04 s |
| Actual `Pkg.test` preference propagation smoke | 2 / 2 | 6.03 s |

The targeted tests include:

- `test/markowitz_core_reuse_allocation_tests.jl`
- `test/triangular_reset_allocation_tests.jl`
- `test/triangular_transpose_allocation_tests.jl`
- `test/triangular_capacity_tests.jl`
- `test/bartels_golub_rows_tests.jl`

The empty BG tests previously failed four assertions with 64 bytes allocated on
the base commit, including under coverage and bounds checks. They pass with the
existing fix. Coverage also includes nonempty resets, dimension transitions,
capacity limits, row copies, solves, and the separate BTRAN allocation regression.

The preference smoke used a scratch project with copies of this checkout's
Project, local Manifest, LocalPreferences, and test/Project files, and a symlink
to its source. Only the scratch test entry point was replaced. It ran
`Pkg.test(; coverage=true, julia_args=["--check-bounds=yes",
"--compiled-modules=yes", "--depwarn=yes", "-g0", "-O1"], allow_reresolve=false)`
and asserted that `Base.get_preferences(Base.PkgId(JSimplex).uuid)
["precompile_workload"] === false` and `Base.JLOptions().check_bounds == 1`.
The preference was observed inside Pkg's temporary test environment. This smoke
used existing compilation caches; it does not measure cold CI compile savings.

An independent read-only review found no blockers in the source fix, workflow
ordering, or validation evidence. Raw local logs are preserved under
`.superpowers/bg-empty-ci` in the integration worktree.

## Limits

This is not a claim that the full project suite or GitHub CI passes. Previous
completed CI runs have additional semantic test failures outside this change.
Recent CI jobs stopped during precompilation before running tests; available
logs show a shutdown signal but do not establish an out-of-memory cause.
Disabling this workload reduces optional compilation work; subsequent GitHub
runs must establish its effect on that environment (Julia 1.13.1, x86_64).
