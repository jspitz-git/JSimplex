# PrecompileTools workloads

This change adds native-code caching without changing numerical algorithms,
basis storage or precision policy. Stable-index experiments remain deferred.
The implementation is based on `dd200cb` and uses PrecompileTools 1.3.4.

The original measurements below describe the first native-only workload.
The current workload also covers shared Float32/Float64 Markowitz backend kernels
and Huangfu–Hall for Float32/Float64 native refactorization (Float64 requires
64-bit indices). See the
[public-manager verification record](../huangfu-hall-public/README.md) for the extension.

## Coverage and reuse

`src/precompile.jl` runs two tiny, synthetic LPs during package precompilation.
It covers Float64 and Float32, primal and dual simplex, PFI, Bartels–Golub,
Forrest–Tomlin and Suhl–Suhl, native refactorization, and presolve both on and
off. Every explicit solve checks the optimum and original primal feasibility;
two additional calls exercise default public options. Inputs are bounded and
independent of files. Ordinary imports do not run the workload. Global numeric
precision, thread counts and solver policies are unchanged.

PrecompileTools saves concrete call signatures. Reuse was measured in fresh
processes with different LP coefficients and iteration limits from the workload.
The standard `precompile_workload = false` package preference disables both
setup and execution; see the root README for configuration.

## Measurements

Julia 1.13.0, Linux aarch64, default optimization and bounds-check settings,
`--startup-file=no`, one Julia/BLAS thread. Cache generation used one precompile
worker and one image-generation thread. The task used a private first depot,
existing dependency caches and a 24 GiB virtual-memory ceiling. No downloads
were needed. Other editor processes were running, including a concurrent
compiler during part of the initial build; timings are observations on this
machine, not isolated-hardware benchmark claims.

| Measurement | Before | Cached, fresh process | Second fresh process |
| --- | ---: | ---: | ---: |
| Sixteen public solves, total | 294.503 s | 0.0237 s | 0.0234 s |
| Compilation within those solves | 294.500 s | 0.0209 s | 0.0210 s |
| Package loading for that probe | 3.766 s | 1.461 s | 0.996 s |
| 468 existing regression assertions | 94.693 s | 55.884 s | — |
| Compilation within those tests | 94.501 s | 55.625 s | — |

The sixteen-call matrix contains both scalar types, both algorithms and all
four managers. Later calls share compilation from earlier calls in the same
process; these are not sixteen independent cold-process timings. All numerical
checks passed in both cached runs. The loading baseline may include ordinary
package cache construction and is reported separately from solve latency.

The first workload-enabled cache build took **649.976 s**. Its native image was
about **213 MiB**, versus about 4.5 MiB without workloads. At these observed
costs the build is amortized after approximately three complete public-solve
probe runs, or seventeen runs of the selected internal test set. Editing solver
sources, changing dependencies, preferences or incompatible compiler settings
can require another build. This tradeoff matters for short edit/test cycles.

The representative existing tests became about **41% faster**, rather than
losing all compilation cost. They define their own callback types and directly
exercise internal functions. Those signatures still compile in each new test
process. Arbitrary future observer/cancellation types, every recovery path,
BigFloat and rational variants are not covered by this native workload. This
change does not claim complete precompilation of the full test suite.

## Preference verification

With a temporary local `[JSimplex] precompile_workload = false` preference,
the first Float64/primal/PFI solve took 47.555 s, almost entirely compilation.
Removing that task-created preference restored the existing enabled cache:
package loading took 0.997 s and the first solve 0.000480 s with zero reported
compilation. No second ten-minute build was needed. The preference file was
removed after this check and is not committed.

## Numerical verification

- The 468 representative regression assertions passed before and after caching.
- The existing factorization/update verification passed all 19,895 assertions.
- Nine external models from `/home/jspitz/NetLib`, `/home/jspitz/MIPLib` and
  `/home/jspitz/mps` passed all 72 solves (both algorithms and four managers):
  afiro, adlittle, kb2, sc50a, pk1, flugpl, stein9inf, markshare_4_0 and fast0507.
  All 225 corpus assertions passed, checking hashes, optimal status, original
  primal feasibility and independently established reference objectives.
  Iteration counts matched the preceding branch's recorded runs in every case.
- The full test suite was not rerun. The preceding baseline attempt exceeded
  900 seconds while compiling test-specific precision variants; the workload
  does not claim to eliminate that remaining compilation.

The corpus uses the existing hash-checked manifest and preparation script in
`diagnostics/simplex-basis-cleanup-performance/reproduce/`. No excluded large
models were solved or factorized. Factor verification uses
`diagnostics/triangular-update-kernels/reproduce/verify-factors.jl`.

## Reproduction

From the repository root, first instantiate the chosen environment. Keep
compiler flags and the depot consistent between cache preparation and tests:

```sh
JULIA_NUM_PRECOMPILE_TASKS=1 JULIA_IMAGE_THREADS=1 julia --startup-file=no --project=. diagnostics/precompile-workloads/reproduce/build-cache.jl /tmp/build-cache.toml
julia --startup-file=no --project=. diagnostics/precompile-workloads/reproduce/first-solve.jl /tmp/first-solve.toml
julia --startup-file=no --project=. diagnostics/precompile-workloads/reproduce/first-solve.jl /tmp/repeated-solve.toml
julia --startup-file=no --project=. diagnostics/precompile-workloads/reproduce/test-latency.jl /tmp/test-latency.toml
```

`first-solve.jl OUTPUT --single` restricts the probe to Float64/primal/PFI for
checking the opt-out. The latency acceptance experiment required less than one
second of total compilation in the full probe: it failed before the change and
passed twice after cache preparation. This is an experimental check, not a
machine-sensitive timing assertion added to the normal tests.

`Pkg.test()` normally uses `--check-bounds=yes`; that requires a matching cache
variant. The measurements above use direct scripts with the default bounds
setting. The root README documents preparing the bounds-checked variant.

Raw timing records are in `results/`. Measurements were collected before the
feature commit, so probe revision fields identify the base; `environment.toml`
records hashes of the measured source changes. Local manifests, preferences, compiled
images and external datasets are intentionally excluded from version control.
