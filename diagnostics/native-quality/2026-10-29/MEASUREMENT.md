# Native quality finite validation and transposed term counters

Base: `235eedf33901fe8c4cc06a3d8c3508ef2fcbb718`. User authorized short whole-function comparisons of two source-derived possibilities, followed by autonomous integration of accepted variants with independent review. Scope: Float32/Float64 only; excluded prior multiprecision ABC variants remain excluded.

## Decision from one short measurement

A (SIMD finite validation) proceeds to integration validation. B (local integer term counter in ordinary CSC BTRAN) and AB are rejected for this integration. No conditional B variant, threshold tuning or B rerun is implied.

72 fixtures cover Float32/64, n=16/128/384, CSC with approximately3 or15 stored entries/column and dense matrices, FTRAN/BTRAN and correct/incorrect solutions. Three warmups per arm precede12 alternating measured four-arm pairs. There are3456 measured windows,864 pair groups and864 warmup records. All measured compile/recompile and in-window GC times are zero. Fixture preparation and warmup costs are separately retained in measurement-1.toml. Scratch construction is outside measured windows and unchanged across variants; no claim is made that its absolute cost was measured.

Every fixture compares whole SolveQuality fields, every scratch field and all matrix/vector inputs; warm scratch states also match. Small/rectangular/empty, explicit zeros, nonfinite/subnormal/extreme values, aliases and invalid CSC partial scratch are covered. The ordinary equivalence testset passed6434 checks. Deliberately invalid components compare exception types and partial scratch; valid whole-function cases must succeed and cannot silently accept a shared missing-helper exception.

A's per-fixture median paired ratios span0.794–1.019. Sparse category median ratios:

| Type | Storage | FTRAN | BTRAN |
| --- | --- | --- | --- |
| Float32 | sparse3 |0.810|0.864|
| Float32 | sparse15 |0.826|0.914|
| Float64 | sparse3 |0.851|0.885|
| Float64 | sparse15 |0.864|0.933|

Dense results are near parity, without a demonstrated material gain. Individual short-window outliers remain in raw records; ratios are from a single process/session on synthetic matrices, not LP trajectory or end-to-end solver measurements.

B regresses sparse3 BTRAN by approximately11–20% across per-fixture medians. It helps Float32 sparse15 BTRAN but has no consistent Float64 benefit. The six overlap checks and per-column exception handling are included in whole-function costs. B is not promoted.

All three variants have EXACTLY equal bytes and allocation events to reference in every paired window. The measurement wrapper records192–272 bytes and3–5 events per batch, not zero allocation; those records must not be mislabeled as exact kernel-only allocations. No candidate-specific allocation reduction is claimed.

## Computational work and retained memory

A reuses the existing native Vector SIMD boolean reduction. It preserves the finite-input validation passes over CSC values, x, rhs and both working vectors; dense matrix validation and unsupported/custom/multiprecision vectors use the original all(isfinite,...) fallback. No matrix arithmetic order, numerical tolerance, underflow/roundoff safeguard, compensation/wide fallback, solve count, copy, conversion, scratch storage or cache is added or removed.

Exceptional-path tradeoff: a native vector with an early nonfinite value is scanned to its end rather than short-circuited. This can increase rejection work by the remaining vector length. Outer short-circuit sequencing between arrays stays intact. This is explicitly accepted as a bounded cost, with no additional retained memory.

B retains every floating product/subtraction/scale/check in original order, but reduces integer counter traffic from per-nonzero to per-column and adds overlap eligibility and exception bookkeeping. Measurements show the added work is not justified generally, hence rejection.

## Provenance and review

The first prepared driver and intermediate fixes are retained but were never executed. Independent prelaunch review caught missing isolated-module dependencies, exception-as-success risk, missing large/warmed scratch comparisons, discarded warmup compilation records and supervisor acceptance handling. The final admitted driver was executed once. An accidental unrelated row temporary in the existing compensated branch was removed before launch.

Reviewer native_quality_review admitted driver-admitted.jl SHA2562ecd2aacaa9cb405fc87c6d4a6215028ffa2792adb84dedd3ceaaf33728e730c. Reviewer native_quality_integration_review independently reconciled raw pairs and confirmed A-only work/memory scope, contingent on production/regression tests. Production helper placement was moved before the solve_quality! docstring, without executable change.

measure-1: clean guarded exit0 in14.08s inclusive, maxRSS477844KiB, no timeout or pressure intervention, launch pins unchanged and full group/session postflight clear. Inclusive process time includes compilation and is not a kernel benchmark.

The source hash32e360786c33c9bd3bcb6c5c9b62a0d923e5248282b7732b6e0e4b59fc227c8a attached to the worktree src/simplex_numerics.jl in measurement/RED pins now maps only to the preserved original.jl after production integration. Raw inventories are unchanged, with no retroactive launch pins. Green pins bind the actual integrated source separately.

No accepted earlier raw files, scripts, reviews or tests were rewritten. CI remains disabled and HH reuse is unchanged.
