# Numerical guard cost and repeated DSE validation

This investigation starts from `d1978a1`. It measures guard overhead without
removing numerical safeguards or changing pricing, pivots, arithmetic order,
tolerances, or precision. The production change reuses a successful validation
of an unchanged workspace in `update_dual_pricing_weights!`. Joint pricing and
row-residual prototypes remain diagnostic only.

## Production change and work audit

After `update_dse!`, the old code validates the complete workspace, then performs
exactly the same validation again on its successful path, with no intervening
operation. Return `true` immediately after that first successful validation.
The failure path still recovers invalid weights, validates the recovered state,
updates Devex for the current pivot, and validates that new state again.

Frequency: one successful dual steepest-edge weight update per ordinary DSE
pivot, across all basis managers. The saved work is one scan each of primal
values, reduced costs, costs, and weights: `4(n+m)` element checks. There are no
new solves, arithmetic updates, conversions, allocations, scratch arrays,
retained memory, or validity caches. Devex, Dantzig, recovery, and primal code
retain their existing checks. The control-flow argument also applies to generic
scalar types; it does not depend on floating-point reassociation.

An isolated diagnostic counts actual calls to the unchanged validation predicate:
Float32, Float64, and BigFloat each failed the one-check budget before the change
(two calls), then passed afterward (one call). This process-local instrumentation
is not part of production or the project test suite. Production regression tests
cover valid updates in Float32, Float64, BigFloat, and Rational{BigInt}; non-finite
primal/cost/reduced-cost values; weight recovery with an invalid primal iterate;
and a Devex update that overflows after successful recovery. Existing tests cover
successful DSE-overflow recovery and ordinary fallback behavior.

The independent review found this repeated validation unnecessary. No new
computational or memory cost was found in the production change. It also checked
that recovery can mutate state and that both validations on that path remain.

## Focused timing

`weights-bench.jl` compares the frozen original method against production on an
identical initial slack basis. It excludes setup, restores weights outside each
timed batch, alternates order over 15 rounds, and uses 10 updates per batch.
Both methods are warmed; timed compilation is asserted zero and resulting
weights must be exactly equal. Hardware: WSL aarch64, Julia 1.13.0, `-O2`, one
Julia/BLAS thread, precompile workload disabled. Both versions allocate zero
bytes in these timed batches. Individual paired timing ratios are noisy
(0.35–1.28 for dense, 0.61–1.40 for sparse, 0.66–1.26 for large sparse);
the table reports ratios of medians, not a statistical confidence interval.

| Matrix fixture | Dimensions | Old median | New median | Change |
| --- | --- | ---: | ---: | ---: |
| Dense | 512 × 768 | 2.83 μs | 2.40 μs | −15.2% |
| Sparse | 32,768 × 49,152 | 144.27 μs | 115.04 μs | −20.3% |
| Large sparse | 360,982 × 186,497 | 1.379 ms | 1.056 ms | −23.4% |

These are **weight-update kernel** results, including its solve, on initial slack
bases with no update chain. Matrix density is represented, but a dense or long
updated basis is not. The saved validation work is independent of factor fill;
its relative benefit shrinks when solves become more expensive. This is not a
claim of a 15–23% solver speedup. All individual timing samples are retained.

## Baseline guard attribution

The instrumented baseline uses HH/native320, Float64, steepest edge, legacy,
partial pricing disabled, default presolve/scaling, and relaxed integrality.
Runtime and fast0507 run to completion; medium uses intentional iteration
prefixes. All numerical jobs are sequential, with the established 8 GiB virtual
memory limit, 6 GiB available-RAM floor, and 1 GiB maximum swap usage.

| Run | Iterations | Instrumented total | Workspace finite checks | Row residual | Direction residual |
| --- | ---: | ---: | ---: | ---: | ---: |
| fast0507 dual, OPTIMAL | 6,736 | 8.57 s | 0.897 s / 33,688 calls | 0.025 s | 0.030 s |
| medium dual, prefix | 4,000 | 62.85 s | 5.479 s / 20,004 calls | 1.791 s | 2.415 s |
| medium primal, prefix | 2,000 | 61.70 s | 0.658 s / 2,001 calls | 1.012 s | — |
| runtime dual, OPTIMAL | 54,591 | 185.00 s | 7.335 s / 220,524 calls | 15.866 s | 13.124 s |

The medium prefixes contain no correction or repair events. They predominantly
measure ordinary iterations, including setup, phase entry, and scheduled
refactorization. They do not cover late stagnation, later phase transitions, or
postsolve. Runtime and fast0507 include recovery and
terminal work. The selected guards are not an exhaustive profile of safeguards.
The row-residual helper is also used in primal pivot validation.

Timing uses wrappers around frozen original methods, in one diagnostic process;
solver source is not rewritten. Guard times are inclusive and may overlap with
other diagnostic timers. Initial AFIRO warmup is followed by counter resets.
Reported outer compilation is 0.346 s for fast0507, zero for both medium prefixes,
and 0.041 s for runtime. Snapshot I/O, trace hashing, and instrumentation affect
the total; snapshot I/O is outside row-guard timing. First-use compilation can
still affect individual guard measurements. RSS in per-case reports is process
high-water RSS, cumulative over the four cases, not each case's independent peak.
These observations identify avoidable work but do not explain the entire gap
between JSimplex and other solvers.

## Rejected shared pricing/residual prototypes

CSC pricing traverses `Z` matrix entries, then the residual check revisits `Z_B`
entries belonging to structural basic columns. A fused traversal can avoid
those repeated loads. Its pricing and residual sums must remain separate and
in their original per-column operation order; deriving a residual from a
completed price would change rounding.

Two diagnostic variants were measured. The first prices nonbasic columns then
visits basics in basis order. It regressed medium synthetic cases. The second
uses one contiguous CSC traversal and basis-state membership, retaining the
separate sums. It saves traversal, **not the specified product count**: both
variants perform `Z+Z_B` operand-ordered products. The fused variant also adds
membership branches across `n+m` columns and basic-index validation. No new
factor solves or persistent scratch are required.

Synthetic random basis/rho experiments showed large apparent gains for medium
and runtime, but they overstated the benefit. We therefore captured actual
presolved simplex rows and compared 22 snapshots, over 11 alternating warmed
rounds each, with exact output/residual equality and zero timed allocations.

| Actual captured states | Fused/separate median time |
| --- | ---: |
| fast0507 dual, five snapshots | 1.013–1.032 |
| medium dual, five snapshots | 1.021–1.122 |
| medium primal, four snapshots | 1.018–1.127 |
| runtime dual, iteration 10,000 | 0.717 |
| runtime dual, iteration 30,000 | 0.574 |
| runtime dual, iteration 50,000 | 0.505 |

Early runtime snapshots also include regressions. Therefore the shared traversal
is **not integrated into either simplex method**. Later runtime gains are real
for this isolated kernel, but are insufficient grounds for a general default.
In particular, early medium has mostly slack basics and very sparse transpose
rows: extra branching costs more than the structural traversal it saves.

The prototypes require a valid, unique basis whose states agree with its indices.
They are not substitutes for the production helper's malformed-input handling.
Finite synthetic inputs and captured states are not exhaustive evidence for
NaN/Inf, threshold cancellation, all precisions, or sparse/hypersparse pipeline
integration. A future proposal would need those checks and representative later
medium states before adoption. No simplex candidate-selection heuristic was added.

## Reproduction and evidence

Raw jobs are preserved under `.superpowers/dual-pricing-residual/`; each has a
preflight digest manifest, command, process status, and log. The local row `.bin`
files contain matrix/basis/rho data for diagnostic replay, not solver checkpoints.
They are not committed. Compact reports and logs are in `results/`.

Run from this checkout, with no other numerical Julia process:

```sh
python3 diagnostics/dual-pricing-residual/reproduce/run.py \
  .superpowers/dual-pricing-residual/new-capture 1800 -O2 \
  diagnostics/dual-pricing-residual/reproduce/capture.jl \
  .superpowers/dual-pricing-residual/new-capture
```

Use fresh output directories. `snapshots.jl` accepts the capture directory and an
output TOML. `probe.jl` measures synthetic matrices/bases; `weights-bench.jl`
compares the frozen old DSE validation with production. `finite-check-budget.jl`
is an isolated work-count check. The guarded wrapper references existing local
environments/guards and refuses another Julia process. It pins source, tests,
inputs and scripts for each job and verifies them again afterward.

The first synthetic run used `split-prototype.jl` as `prototype.jl`; the contiguous
version is now selected. The saved per-job digests distinguish these revisions.

## Paired solver verification

The same capture harness was run before and after the production change.
All four pairs have identical pivot/flip event hashes, state hashes (basis,
states, primal values, prices, costs, and weights every 80 iterations, plus
the last observed workspace after completion), diagnostic event counts, statuses, iterations, and refactorizations.
Optimal cases also have identical objectives and pass original primal feasibility.
Other measured guard call counts are unchanged. Source manifests distinguish the
two implementations even though the runs preceded the implementation commit.

| Run | Finite checks before → after | Instrumented seconds before → after |
| --- | ---: | ---: |
| fast0507 dual | 33,688 → 26,952 | 8.57 → 9.05 |
| medium dual, 4,000-iteration prefix | 20,004 → 16,004 | 62.85 → 63.01 |
| medium primal, 2,000-iteration prefix | 2,001 → 2,001 | 61.70 → 60.72 |
| runtime dual | 220,524 → 214,772 | 185.00 → 186.62 |

Runtime finishes OPTIMAL at 54,591 iterations and objective
`51425691.76210138`, with original primal feasibility. Fallback pricing limits
how often the DSE-only optimization applies. These single instrumented timing
pairs do **not** establish an end-to-end speedup; the measured whole-solve time
is slightly higher for both completed dual problems. No iterations or numerical
safeguards were traded for the kernel saving. Medium was not rerun for hours;
its late behavior is outside this check's coverage.

Completed checks: 9 isolated work-budget assertions, 71 new production regression
assertions, and 15,689 broader semantic assertions (`--compile=min`). The normal
compilation project-suite outcome is recorded separately below.

The complete `-O2 test/runtests.jl` attempt did **not** finish: the 300-second
wall-time guard stopped it in `legacy_primal_direction_price_tests.jl:142`
(exit 75; process elapsed 310 s including termination). The log reports no
assertion failure before termination, but gives no completed suite summary.
It also does not separate compilation from execution, so this is classified as
an incomplete normal-compilation attempt, not a proven LLVM fault or numerical
failure. Its maximum resident set was approximately 1.14 GiB, with no swaps.
The full log is preserved as `results/project-suite.log`; the full suite is not
claimed to pass. The independent code and paired-result reviews found no blocker
in the narrow production change; the broader semantic coverage above passed.

`reproduce/audit.py` verifies all paired fields, non-target guard call counts,
zero kernel allocations, digest preservation, the exact expected pre-change
budget assertion failures, and the explicitly classified suite timeout. It
archives compact raw reports and source/script identities. Its successful exit
means these evidence checks passed, **not** that the incomplete project suite did.
