# Native primal completion and stale pricing tests

Base: `44db0771ef53abcd8bfa1a3458377fefa3beb36b` (merged CSC pricing optimization).

## Findings

The six previously recorded partial-pricing failures were stale fixture
assumptions after numerical kernels were separated from adaptive heuristics.
`simplex_strategy=:adaptive` no longer implicitly selects transactional or
incremental primal updates. Explicitly selecting the internal `:checked`
numerical profile makes all 219 original partial-pricing assertions pass.

- The cancelled-pool test requires transactional rollback and now explicitly
  selects that profile.
- The wide-flip test now covers both native and checked profiles. Candidate-pool
  reuse is expected only for incremental flips; ordinary native reconstruction
  legitimately invalidates the pool.
- Expanded primal regressions exposed another stale expectation: the Harris
  ratio test must use the same per-bound feasibility rule under both public
  strategies. The test now checks that rule directly.

Investigation also found a real native primal core bug. A pivot or bound flip
changed the basis/state, incremented the iteration counter, and emitted its
completion event before reconstructing primal values and reduced costs. A stop
request at that point returned `TIME_LIMIT` with new basis states and old values.
A bound flip could also be applied after cancellation at `:pivot_proposed`.

The one-row reproducer minimizes `-x`, with `0 <= x <= 1` and `x <= r`.
For `r=0.5`, cancellation at pivot completion left the old point `[0,0]` and
prices `[-1,0]` under the new basis; reconstruction gives `[0.5,0.5]` and
`[0,-1]`. For `r=2`, cancellation at flip completion similarly left `[0,0]`
instead of `[1,1]`. These are consistency failures, not slow convergence.

## Change

Check cancellation after the proposal and immediately before step application.
Once the native step is applied, finish the existing reconstruction and point
recovery before delivering completion and honoring a new stop request. Keep
staged events buffered under the existing transactional publication mechanism.
Preserve the actual leaving row in completion metadata even if point
certification fails. Ordinary arithmetic, precision, pricing, ratio tests and
basis-manager operations are unchanged.

The completion regression covers Float32, Float64, BigFloat and Rational{BigInt},
both strategies, all four basis managers for Float64, flips and pivots,
refactorization intervals 1 and 80, cancellation before/after application, and
exceptions from completion observers. Recovery tests additionally require the
observer to see the corrected point and the actual leaving row on failure.
This is not a general atomicity guarantee for arbitrary exceptions inside native
factorization, refactor logging or numerical reconstruction.

## Reproduction

Run from the checkout root, sequentially through the existing guarded Julia
wrapper (8 GiB virtual-memory cap, low-RAM/swap guard, one Julia/BLAS thread).
Local manifests and preferences remain uncommitted.

- `reproduce/boundary-probe.jl`: `--compile=min`; prints live and reconstructed
  points after proposal/completion cancellation. It also runs against the base.
- `reproduce/regressions.jl`: `--compile=min`; includes the complete extended CSC
  pricing regression selection and native/checked primal, recovery and
  publication suites. This is a selected suite, not the whole project suite.
- `reproduce/real-models.jl OUTPUT_DIRECTORY`: normal compilation, full fast0507
  primal solve (300-second solver limit) and runtime dual solve (600 seconds).
- `python3 reproduce/compare.py OUTPUT_DIRECTORY`: checks input hash, status,
  objective, final-vector hash, ordered pivot/step hash, iteration/refactorization
  counts, original primal certificate and diagnostic counters against the
  previously committed records. Completion-state checkpoint hashes are excluded
  because the observer now correctly sees the reconstructed point.

No excluded large model is solved or factorized. Runtime primal convergence is
outside this fix; a timeout without numerical failure would not establish it.

## Validation

The final selected semantic suite passes **16,155 / 16,155** assertions with
`--compile=min` (123.6 seconds). This includes all previously failing partial
pricing tests, the stale Harris expectation, the new native completion tests,
and existing primal update, pivot atomicity/application/retry, point recovery,
strategy separation, phase logging, driver and CSC pricing checks.
See `results/regressions.log`.

Both normally compiled real-model solves reach `OPTIMAL` and retain exactly the
reference pivot/step trace, final primal vector, objective, iteration and
refactorization counts, and every diagnostic counter. Both pass the original
primal feasibility certificate.

| Input / algorithm | Iterations | Refactorizations | Objective |
|---|---:|---:|---:|
| fast0507 / primal | 4,923 | 63 | 172.14556667654887 |
| runtime / dual | 62,853 | 793 | 51425691.762103125 |

Instrumented elapsed times were 54.97 seconds (fast0507, including compilation)
and 197.14 seconds (runtime, zero compilation); these are validation runs, not
performance comparisons. Runtime dual also exercises native primal cleanup.
Its completion-state checkpoint hash therefore changes along with fast0507's,
as expected, while ordered pivot/step and final-vector hashes remain identical.
See `results/equivalence.json` and the per-model TOML records.

The small cancellation reproducer now returns points/prices identical to an
independent fresh reconstruction for every case; proposal cancellation preserves
zero completed steps, while completion cancellation retains one coherent step.
See `results/boundary-before.log` and `results/boundary-after.log`.
