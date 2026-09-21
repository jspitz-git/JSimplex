# Allocation audit: first presolve round

Measured on 2026-09-19 with Julia 1.13.0, aarch64-linux-gnu, one Julia thread,
nine BLAS threads, native basis refactorization and PFI updates. The baseline
solver was commit `4fb2026`; the same audit script measured both revisions.
Values below are minimum allocated bytes from three warmed calls. No measured
call reported compilation time. These counters describe cumulative Julia heap
allocations, not peak memory or all memory allocated inside native libraries.

## Changes

- Bound propagation caches exact column bounds lazily within each pass. A
  successful exact tightening updates the cache immediately. Inactive columns
  are not converted, and caches do not persist across changed models or calls.
- Three per-row temporary vectors are reused throughout propagation. Removing
  an unbounded term returns the existing finite activity instead of subtracting
  a newly constructed rational zero.
- Exact sparse elimination avoids eagerly constructing a `Rational{BigInt}` zero
  for dictionary hits, multiplication by one, and subtraction when the terms
  cancel exactly. Source coefficients are not mutated.

The exact arithmetic, representability checks, reduction order, and public
interfaces are unchanged.

## End-to-end results

| Model | Presolve before (B) | After (B) | Reduction | Dual solve before (B) | After (B) | Reduction |
|---|---:|---:|---:|---:|---:|---:|
| afiro | 1,471,952 | 1,209,720 | 17.8% | 1,646,176 | 1,381,288 | 16.1% |
| adlittle | 6,142,736 | 5,060,600 | 17.6% | 7,161,768 | 6,081,696 | 15.1% |
| kb2 | 16,280,344 | 13,348,528 | 18.0% | 16,865,592 | 13,933,616 | 17.4% |
| sc50a | 6,015,216 | 4,354,560 | 27.6% | 6,432,560 | 4,773,312 | 25.8% |
| flugpl | 1,650,592 | 1,518,192 | 8.0% | 1,778,840 | 1,646,760 | 7.4% |

Primal solves with presolve reduced allocated bytes by 7.2–26.0% on these models.
All 20 combinations (five models, primal/dual, presolve on/off) returned
`OPTIMAL` before and after. Objectives and iteration counts were identical.
The `recompute`, forward-solve and transpose-solve cases allocated zero bytes
on all five initial slack bases. This does not establish zero allocations for
arbitrary updated bases or arbitrary-precision arithmetic.

For `adlittle`, standalone propagation fell from 1,445,600 to 1,169,048 bytes
(19.1%) and dependent-row reduction from 1,092,680 to 861,160 bytes (21.2%).
Presolve allocation count fell from 154,219 to 121,569 (21.2%). Standalone
reductions run on the original model, so they must not be summed to explain
the actual multi-pass presolve total.

## Reproduction

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --output=allocations.toml
julia --startup-file=no --project=dev dev/allocations.jl adlittle --samples=3 --profile=presolve --sample-rate=0.01 --output=profile.toml
julia --startup-file=no --project=dev dev/allocations.jl afiro --samples=3 --basis-update=forrest_tomlin --basis-refactorization=markowitz
```

In a read-only package-cache environment, add `--compiled-modules=existing`
before `--project=dev`. This was used for the reported measurements.
Machine-readable measurements are in `allocations-before.toml` and
`allocations-after.toml` beside this report. Timings are recorded for investigation;
these runs also overlapped test execution, so no runtime-speedup claim is made.

## Remaining targets

The post-change sampled `adlittle` presolve profile still points to exact number
conversions, rational multiplication/subtraction, and representability checks.
Before pursuing more invasive arithmetic work, measure larger sparse models,
incremental propagation with only a few active rows, and difficult numerical
recovery paths. The audit also exposes MPS input, MOI translation, scaling,
initialization, refactorization, and postsolve reconstruction for subsequent
rounds. Full solves cover original-space cleanup and certification; the standalone
postsolve stage only measures primal reconstruction.

New mandatory tests enforce warmed allocation budgets for propagation,
dependent-row reduction and complete presolve, alongside exact sparse-elimination
checks. Development tests exercise setup exclusion, fresh mutable inputs,
profile collection, pipeline coverage, MOI translation, and report serialization.

The development suite's two JET checks on `solve` (`Float64` and
`Rational{BigInt}`, `dev/tests/jet_tests.jl:22–23`) still fail on runtime dispatch.
Both failures were reproduced in an isolated copy of baseline commit `4fb2026`;
all 42 reported dispatch findings were identical before and after. The new audit
tests passed all 27 checks. The dataset/GLPK development checks also passed (104
checks). A smoke audit with Forrest–Tomlin updates and Markowitz refactorization
returned `OPTIMAL` for all four `afiro` solve configurations.

The complete mandatory suite passed **14,103/14,103** tests. The separate JuMP
integration run passed **23/23** checks (run separately because the earlier JET
failure stops the combined development script before it reaches JuMP).
