# Reused staging buffers in sparse equality aggregation

Round 26 reuses the three temporary change vectors in
`aggregate_sparse_equalities`: objective, row-bound, and matrix-coefficient
updates. Each vector is allocated lazily when a candidate first reaches its
staging phase. Subsequent candidates empty it and reuse its capacity. This
preserves the allocation behavior of paths that never reach that phase.

The buffers remain private to one pass. Rejected candidates cannot commit partial
updates, and their staged entries are cleared before the next relevant attempt.
Dictionary updates, numerical checks, pivot selection, and postsolve records
retain their previous behavior. Singleton aggregation is unchanged because its
candidate selection retains a possible rounded candidate while considering
other candidates; its change-vector lifetime is different.

## Method and results

Measurements used Julia 1.13.0, aarch64-linux-gnu, one Julia thread, and native/PFI
factorization. Each case was warmed twice and sampled three times with setup
outside measurement and garbage collection before each sample. Tables report
minimum allocated bytes. All 37 measurements per run recorded zero compilation
time. The baseline includes the preceding 25 rounds.

Runs used `--startup-file=no --compiled-modules=existing --project=dev`. Timings
overlapped validation; no runtime-speedup claim is made. Values are allocated
bytes per call, not peak or retained memory.

The repeated-update probe from the
[preceding report](aggregation_defaults_allocation_report.md) has 64 equalities
`xᵢ + y = 1`, free variables, objective `sum(xᵢ) + 2y`, and one additional row
`sum(xᵢ) + 2y ≤ 100`. Sparse aggregation fell from **697,248 to 668,688 bytes
(4.10%)**, and from 18,296 to 17,918 allocations. The 378 removed allocations
correspond to reusing three vectors and their backing storage across the
remaining 63 pivots. The unchanged singleton probe retained 8,950 allocations;
its byte total varied from 354,040 to 353,992.

| Model | Sparse pass before | After | Allocations before → after | Full presolve before | After |
| --- | ---: | ---: | ---: | ---: | ---: |
| afiro | 277,344 | 273,216 | 6,424 → 6,386 | 1,173,320 | 1,168,536 |
| adlittle | 194,000 | 192,912 | 3,277 → 3,267 | 4,869,464 | 4,866,984 |
| kb2 | 200,504 | 197,624 | 3,787 → 3,755 | 13,166,416 | 13,161,968 |
| sc50a | 414,200 | 403,480 | 9,340 → 9,239 | 4,297,328 | 4,279,984 |
| flugpl | 236,408 | 236,168 | 6,262 → 6,252 | 1,506,336 | 1,504,112 |

Full presolve and both whole-solve algorithms each removed 30 allocations on
afiro, 11 on adlittle, 25 on kb2, 177 on sc50a, and 27 on flugpl. Whole-solve byte
totals with presolve decreased by 1,088–16,096 bytes. These small differences
include run-to-run variability: unchanged paths without presolve varied from
-208 to +160 bytes with identical allocation counts. Counts and the repeated
pivot probe are stronger evidence than small byte changes on individual models.

All 15 model snapshots (five fixtures × singleton/sparse/full presolve) matched
exactly: CSC arrays, objective and constant, sense, bounds, domains, names, and
original column count. All 20 whole-solve combinations remained `OPTIMAL`, with
identical status, objective, complete primal vector, and iteration count
(`isequal`).

Machine-readable results:
[`aggregation-scratch-allocations-before.toml`](aggregation-scratch-allocations-before.toml)
and [`aggregation-scratch-allocations-after.toml`](aggregation-scratch-allocations-after.toml).

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=aggregate_sparse_equalities --output=aggregation-scratch-audit.toml
```

For the synthetic probe, use the complete `aggregation_probe` example in the
[preceding report](aggregation_defaults_allocation_report.md#reproduction), with
`sparse_pass = true`.

## Regression coverage

The direct-call allocation test failed before the change at 685,120 bytes against
a 665,000-byte limit and now passes. Its equivalent model construction and call
context differ from the warmed benchmark harness, so its byte count is not the
table's benchmark result.

The 108 new semantic checks exercise candidates rejected after partial staging
of objective, bound, or coefficient updates, followed by an accepted independent
pivot. They verify that no rejected entries reach the resulting model, that the
objective constant and postsolve map are correct, and that reconstruction and
input preservation hold. These deliberately inexact cases cover Float32,
Float64, and BigFloat. The preceding round's 178 tests additionally cover repeated
successful pivots and Rational{BigInt}; all 287 targeted checks pass.

Independent review found no issue. Its 150 differential cases across six numeric
types matched models, maps, records, reconstructed solutions, and source
preservation. A no-eligible-candidate probe allocated 1,968 bytes both before and
after the change.

The complete mandatory suite passed **16,764/16,764** tests, including the 109 new
checks. `git diff --check` passed. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
