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

The subsequent BigFloat hypersparse regression exposed a real integration error:
precision selection attempted to build an unsupported indexed HH cache even
though the numerical kernel selected dense fallback. The fix obtains the maximum
stored precision directly from HH's factors/updates and the RHS. All 111 checks
pass for independently wider base/update/RHS values, forward/transpose solves,
forced/automatic modes and aliases. Ambient precision is restored after each call.
Precision transfer is also checked with the hypersparse policy enabled.

## External scalar results and limitations

The default-tolerance paired run completed all 48 solves, but **did not pass**:
70 assertions passed and 40 failed. Each manager certified 14 of its 24 cases.
Both HH and PFI solved afiro, adlittle, primal pk1 and flugpl in BigFloat and
Rational{BigInt}. Exact rational objective values agree exactly between managers.
Both reached the 90-second limit on dual pk1 in those two scalar types; these
interpreter-mode runs do not establish convergence or native-compiled performance.

All eight Float32 configurations failed to certify an optimum for both managers:
PFI returned NUMERICAL_ERROR in all eight; HH returned NUMERICAL_ERROR in seven
and TIME_LIMIT in dual pk1. This is not a successful full external Float32 suite.
A separate, predeclared afiro diagnostic used
`primal_tolerance=dual_tolerance=sqrt(eps(Float32))`, keeping the same input and
all other options. Both managers and both algorithms then returned certified
OPTIMAL with objective `-464.75317f0` (12 checks passed). This establishes usable
single-precision solving on that control, and implicates default-tolerance
sensitivity there; it does not explain every other Float32 failure. No solver
defaults, tolerances, pivot heuristics or recovery limits were changed.

Raw statuses, objectives, timing, input digests and source commits are retained in
[the scalar report](results/scalars.json). Timings use `--compile=min` and are not
speed comparisons. The paired runner intentionally fails if a case is not
certified, retaining all records before its failing exit. Reproduce the separate
tolerance diagnostic with `reproduce/float32-tolerance.jl OUTPUT.toml`.

## Final integration checks

The clean integration branch contains only the scalar extension and its BigFloat
hypersparse fix, without the experimental triangular incidence-slot changes.
All 2,783 HH component, allocation, type, precision-transfer, public solve and MOI
checks passed with normal `-g0 -O2` compilation on that source. Earlier broader
semantic checks passed 11,617 existing assertions plus 762 scalar/transfer checks.

All 12 Float64 external controls passed and match the previously certified HH
trajectory fields exactly: objective, iterations, refactorizations, restarts,
primal-vector bits and progress-log digest. Runtime dual returned OPTIMAL at
61,705 iterations, 788 refactorizations and zero restarts, with objective
51,425,691.762104705. Its solve took 166.439 seconds, including 0.005 seconds of
compilation. The full process (including warmup and fast0507) peaked at
1,263,540 KiB RSS; this is not an isolated runtime allocation measurement.
These controls establish preserved Float64 behavior, not a measured speedup.

The expanded Float32/Float64 PrecompileTools workload built successfully with
`-g0 -O2`: 746.950 seconds, peak RSS 14,556,764 KiB (13.88 GiB), one compiler/image
worker, a 2 GiB GC hint, and the 16 GiB virtual-memory ceiling. A fresh process
verified all 20 native solve configurations and four Markowitz backend cases.
The 20 sequential solve calls totaled 0.02447 seconds, including 0.02248 seconds
of residual compilation; these are shared-process samples, not 20 independent
cold starts. The previous default `-g1` memory limitation was not retested or
fixed by this change. BigFloat and rational specializations still compile on
demand, as for the other managers.

[The final integration report](results/final.json) binds these results to source,
input, harness and environment digests. Run `reproduce/audit.py` after collecting
the local reports to repeat the trajectory/cache audit. Cache build and latency
scripts require a separate workload-enabled environment pointing at the tested
checkout; do not change the development checkout's disabled local preference.

The shared hypersparse pipeline storage, kernel and subtraction checks, plus
public HH solves with explicit hypersparse policy in Float16, Float32, BigFloat
and Rational{BigInt}, passed all 1,905 checks in interpreter mode. Reproduce with
`julia --compile=min --project=. diagnostics/huangfu-hall-precision/reproduce/pipeline.jl`.

The full project suite was attempted with normal `-g0 -O2` compilation and a
300-second wall guard. It was interrupted during Julia inference/inlining in
`simplex_strategy_separation_tests.jl:78`; peak RSS was 1,446,532 KiB. Before
that timeout, three older primal test files reported 25 failed assertions and
two errors. A separate interpreter-mode comparison reproduced exactly the same
313 passes, 25 failures and two errors on both the unmodified master
`efd7a97329be7391fcedc95a852d8a8713760c7e` and the integration branch. The failing
files are `primal_bound_snap_tests.jl`, `primal_candidate_retry_tests.jl` and
`primal_retry_pricing_tests.jl`; they do not exercise HH. The failures concern
expected bound-snap values, candidate rejection and refactor diagnostic reasons.
They remain open baseline failures, not a passing full suite or failures fixed
by this scalar extension. No unrelated primal behavior or assertions were changed.
