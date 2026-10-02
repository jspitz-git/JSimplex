# Symmetric numerical refactorization protection

The native primal kernel now shares the dual kernel's bounded protection against
repeated inaccurate solves with updated basis factors. The protection works with
`adaptive_refactor=false`; when adaptive scheduling is enabled, it imposes a
numerical ceiling on the economic update interval.

## Trigger and recovery

A second inaccurate updated solve within three clean factorization cycles limits
subsequent update chains to at most half the earliest observed failure age,
with a minimum of one. A clean scheduled cycle that reaches the active limit
doubles a shortened limit toward the configured interval. Shorter economic
cycles cannot relax it. A final clean cycle at the configured limit releases
the adaptive cap, represented internally by `typemax(Int)`. Repeated failures
can reimpose that exact configured limit, including an interval of one. Legacy scheduling never grows beyond that interval.
Once the protection recovers completely, adaptive scheduling can again use its
existing larger hard ceiling.

The primal trigger is a nonfinite BTRAN result or a failed BTRAN residual check
after the existing native correction. Relative pivot disagreement, weak-pivot
sensitivity, nonfinite pricing, price/direction disagreement, cautious refresh
for an extremely small pivot, candidate deferral, or a zero step does not by
itself count as an inaccurate updated factorization. Failures of a fresh factor cannot accumulate
update-chain repair evidence. Existing feasibility and pivot checks are unchanged.

An adaptive residual or factor-growth trigger takes precedence over a coincident
update limit. Such a cycle cannot relax the numerical ceiling. Repairs owned by
the shared protection do not also shrink the adaptive economic interval: doing
both would leave native solves stuck at the latter's shortened value when their
clean cycles provide no `latest_quality` record.

A `refactor_pivot` reason alone is now an unknown adaptive cycle, rather than
proof of factor inaccuracy. This also applies to checked-profile pivot-relative
uncertainty when solve-quality evidence remains reliable. Pivot rejection and
forced refresh remain in place; unreliable solve quality still marks a failed
cycle. Independent adaptive factor-growth and storage triggers remain active.

## State and scope

The historical four `dual_*` workspace fields store the shared protection. Their
names and layout are retained for local diagnostic snapshots. Existing candidate
copies and phase handoffs already transfer these fields; a freshly adopted phase
basis resets the evidence to its own factorization state. Staged primal steps
now retain whether a repair occurred before their scheduled refactorization.

This change does not introduce an anti-degeneracy heuristic, change pricing,
enable weak-pivot preference, relax feasibility tolerances, or change precision.
It can change a solve's trajectory through earlier native refactorization.

## Reproduction

Use Julia 1.13.0, one Julia thread and one BLAS thread, with the established owned
process memory guard (8 GiB virtual memory; at least 6 GiB available RAM; no more
than 1 GiB swap in use). Keep `LocalPreferences.toml`'s precompile workload disabled.

- `julia --project=. --compile=min diagnostics/refactor-safety/reproduce/checks.jl`
- `julia --project=. -e 'using JSimplex, Test; include("test/refactorization_safety_tests.jl")'`
- The existing `diagnostics/adaptive-degeneracy/reproduce/runtime_reader_full.jl`
  and `broad_corpus.jl` run the isolated adaptive regression profile: stalling,
  temporary pricing and bound/cost perturbations enabled; weak-pivot preference,
  partial pricing, adaptive refactorization and outer original-LP retry disabled.
  Set `JSIMPLEX_EXPECTED_SOURCE` to the current production digest for runtime runs.

The targeted tests inject inaccurate factors into real workspaces for both
methods, both native floating types and all four update managers. They also cover
clean recovery, competing economic intervals, numerical trigger priority,
degenerate steps, small-pivot deferrals and fresh-factor failures.

## Rejected trigger and regression evidence

The first implementation treated every failed native primal pivot validation as
updated-factor inaccuracy. On `runtime.mps`, the first shortened limit occurred at
iteration 23245 after relative pivot disagreements at ages 63 and 1. The new
trajectory eventually failed artificial removal at iteration 81004. This trial
is preserved in `results/superseded-runtime-native-primal.*` and the reason trace
in `results/superseded-repair-causes.log`; it is not a successful validation.

A four-row regression reproduces the classification error independently: a tiny
factor perturbation creates a sensitive pivot in a scaled column while the BTRAN
residual remains acceptable. The original implementation incorrectly shortened
80 updates to 1. The corrected classification preserves both protective
refactorizations and the feasible solution, without counting them as failed
factor solves or shortening either the numerical or economic interval. Failed
BTRAN corrections still shorten the numerical interval in both methods and all
four basis managers. Existing evidence from successful native corrections remains
available to adaptive residual scheduling.

## Verification

Verified production digest:
`67b162566ae3b98dc42f15005c95d6cdf35ce89b97ee7dcd49de7ee5f9f43011`.

- 5,916 targeted regression checks passed with `--compile=min`.
- 16,279 phase-transition, failure-recovery and simplex semantic checks passed
  with `--compile=min`, including replay of the native phase-removal boundary.
- All 775 focused protection checks also passed with normal compilation.

Full native-reader `runtime.mps` runs completed with the isolated adaptive profile
specified above, PFI/native refactorization and configured interval 80:

| Method | Status | Iterations | Refactorizations | Solver seconds |
| --- | --- | ---: | ---: | ---: |
| Dual | OPTIMAL | 61,387 | 775 | 266.61 |
| Primal | OPTIMAL | 106,252 | 1341 | 864.29 |

Both runs used Float64. A separate process evaluated each returned point against
all original constraints using exact rational arithmetic over the stored Float64
coefficients and values. Maximum row/column violations were respectively
`6.671e-8` / `9.197e-8` (dual) and `9.102e-9` / `3.324e-12` (primal), below the
unchanged `1e-7` primal tolerance. This exact arithmetic was verification only.
The objectives were `51425691.762099` and `51425691.762104236`.

The dual run's entire recorded non-timing trace matches the merged reference
in `diagnostics/adaptive-degeneracy/results/runtime-failure-repair/final-native-dual.toml`.
The primal run has the same iteration count as the historical successful native
run; that historical record predates the latest merged repairs and is not a fresh
master comparison. These timings are observations, not a speedup claim.

The external corpus passed all 104 solves on 33 models: 76 dual and 28 primal,
using native, JuMP and permuted input representations. Every case reached the
reference optimum and passed original-model primal feasibility. Iterations,
refactorizations and objective values match the previously merged corpus results
for every case. The corpus includes `degen2`, `degen3`, `cycle`, pilot and air
models, and `mod010`; no excluded large model was solved or factorized.
See `results/models.toml`, `comparison.json` and `validation.json` for per-case
results, comparisons, commands and process limits.

This is not a passing full-project test suite. A preliminary normal-compilation
run reached its 300-second guard while LLVM compiled `native_reliable_price_tests`.
The separate `legacy_primal_preference_work_tests` testset “Exhaustion after fresh
pricing retains the refresh budget” has two failures and one error reproduced
unchanged on master; it is excluded from the targeted runner. The corresponding
baseline and preliminary logs are retained in `results/`.
