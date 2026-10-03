# Huangfu–Hall scalar support

The public middle-product-form manager now uses the task scalar for factors,
update records, workspaces, unit-transpose preparation and pivot checks.
`Float32`, `BigFloat`, `Rational{BigInt}`, fixed-width rationals and `Float16`
follow the same native-backend convention as the other managers: dense LU in
that scalar, extracted into private sparse triangular factors. Float64 retains
its UMFPACK extraction, scaling verification, reusable native workspace and
recommended update optimizations. Markowitz remains unsupported for HH.

Exact types have zero default pivot tolerance. Floating defaults use the shared
typed tolerance helper. BigFloat arithmetic uses ambient precision, as elsewhere
in the solver. Explicit precision transfer/recovery can reconstruct HH in the
new type; ordinary iterations do not promote precision. MOI uses the same public
option validation for every type.

Fixed-size scalar recycling is bounded by 4 MiB per pool, accounting for both
index and scalar sizes. Variable-size BigFloat/BigInt payloads are not pooled.
Active factors/updates are never capped or truncated. Copies share immutable
active factors/records and have private scratch and recycling state. Native
Float64 still requires 64-bit indices; generic dense types do not.

## Verification protocol

Tests cover nonsymmetric row-pivoted LU, repeated updates with and without
prepared directions, forward/transpose solves and aliases, exact equations,
copy isolation, failed and dimension-changing refactorizations, small exact
pivots, scalar preservation and BigFloat coefficients below Float64 resolution
at 96/256/512 bits. Public solves cover both algorithms, both strategies,
presolve on/off and MOI. Working-precision transfer is exercised separately.

Run sequentially with one Julia/BLAS thread and an 8 GiB virtual-memory cap.
Keep `LocalPreferences.toml` with `precompile_workload=false` for ordinary tests.
Use `--compile=min` for semantic tests, but normal compilation for allocation
assertions. Cache builds use one compiler/image worker, `-g0 -O2`, and the
separately authorized 16 GiB virtual-memory cap. No excluded large MPS model is
loaded by these numerical checks.

```sh
julia --startup-file=no --compile=min --project=. -e 'using Test,JSimplex; include("test/huangfu_hall_precision_tests.jl"); include("test/huangfu_hall_scalar_integration_tests.jl")'
julia --startup-file=no -g0 -O2 --project=. -e 'using Test,JSimplex; include("test/huangfu_hall_tests.jl")'
julia --startup-file=no --compile=min --project=. diagnostics/huangfu-hall-precision/reproduce/external-scalars.jl scalar-results.toml
```

The external scalar runner compares HH with PFI on the pinned afiro, adlittle,
pk1 and flugpl inputs, both algorithms, Float32/BigFloat/Rational{BigInt}, using
native refactorization and default type-specific tolerances. Each solve must
certify original feasibility and agree with the known reference objective.
Float64 trajectory checks reuse the public promotion runner and its pinned
solution/progress digests, including the full dual runtime solve.

Initial verification on the experimental branch passed 2,652 checks with normal
`-g0 -O2` compilation, including the original Float64 allocation regressions.
The scalar regression first failed because Float32 was rejected. Its first
implementation then exposed a discarded replacement LU result in generic
refactorization; retaining the returned LU fixed all six equation failures.
A separate regression exposed eleven implicit Float64 growth-reduction results;
typed reduction seeds fixed them. Static review also found a missing 32-bit
platform guard in precision-transfer tests; only Float64-involving cases are
skipped on that platform, which was not available for execution here.
