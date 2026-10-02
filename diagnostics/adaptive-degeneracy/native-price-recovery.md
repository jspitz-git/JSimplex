# Bounded native recovery of unreliable primal prices

Base: `06d09d2` on `codex/adaptive-degeneracy`. This follows the seed-1 mod010
price/direction disagreement left by [artificial-exchange recovery](artificial-exchange-recovery.md).

## Cause and independent evidence

With both rows and columns of mod010 permuted by `MersenneTwister(1)`, PFI reaches
iteration 272 and repeatedly selects apparently improving Phase-I variables.
The existing direction-price check rejects 1,148 candidates, including the
fresh-basis retry. The first failure has 32 basis updates; later failures have
none. Repeating candidate rejection and refactorization cannot resolve this
fresh-factorization error.

The capture retains the **last** rejected state, not the first rejected candidate.
At that state the selected cached price is `-1.9721522630525295e-31`, while its
FTRAN-implied price is zero. A fresh BTRAN with the current basic objective has
absolute residual `2.072416312633624e-16` and componentwise relative residual
`0.10137466764722537`, failing the unchanged native reliability criterion.
The existing native cleanup corrects that BTRAN to an exactly representable
solution: both residual measures become zero. Exact `Rational{BigInt}` arithmetic
certifies `B' * dual == c_B`; an independent dense 256-bit solve agrees exactly
with the corrected Float64 vector. Higher precision is diagnostic only.

The raw state/sign count of negative or improving prices falls from 1,178 to two;
those last two correspond to fixed variables excluded by primal pricing. It is
not a count of eligible entering candidates. Production selection then finds
no improving eligible variable and returns auxiliary optimality without changing
the basis, primal point, costs or iteration count. The Phase-I objective is about
`-9.58e-14`, within the existing primal tolerance; original-model optimality is
not established by this result.

## Core change

A price/direction rejection gets its own basis-preserving rejection marker.
After the existing fresh-factorization retry, the native primal candidate loop
may make **one** price-recovery attempt across both candidate-search passes.
Other rejection reasons retain their previous handling.

Recovery recomputes `B' * dual = c_B` in a private vector. It proceeds only when
the compensated residual demonstrates that this fresh solve is unreliable.
The existing native cleanup supplies one residual correction and its bounded,
certified homogeneous-term cleanup. New prices must be finite, changed, and
ready before the stop check permits publication. The corrected dual and prices
are published together, dependent caches invalidated, and ordinary candidate
selection restarted. The basis and primal state are untouched. `scratch.rho`
is not assumed to contain a persistent objective dual, since pivot operations
reuse it for individual rows.

There is no tolerance relaxation, pricing-rule change, objective perturbation,
precision increase, or model-specific condition. Phase I still uses zero price
tolerance. Failed/unchanged/reliable-solve recovery does not restart selection.
The bounded candidate rejection machinery remains active, and a second
price disagreement cannot renew the correction budget. Checked/staged kernels,
dual mode and unsupported scalar types retain their existing paths. Recovery
respects the existing refinement budget and stop callback.

## Regression evidence

A portable six-by-six integer basis, independent of the real models, reproduces
the same native BTRAN error. Its exact dual is `[1,1,0,0,0,0]`. Signed identity
columns expose spurious prices; an optional independent column with true price
`-1e-30` checks that a genuinely small improving price remains actionable.
The pre-fix additions had 104 passing and eight failing assertions; the existing
336 direction-price assertions passed. The saved mod010 replay independently
failed the expected auxiliary-optimality assertion before the fix.

The completed focused suite passes 568 assertions both with normal compilation
and with `--compile=min`, covering Float32/Float64,
all four basis managers, genuine small prices, cancellation and callback
exceptions, policy eligibility, unchanged/reliable solves, and a forced second
mismatch after publication. The broader semantic runner passes 9,389 assertions
plus seven production-only captured-state checks under `--compile=min`.
Counts include overlapping existing test runners, not distinct tests. This is
not a full project-suite result.

## Whole-model verification and limits

The 30 selected fresh runs contain 17 verified optima and 13 numerical errors,
with no time limits or harness exceptions. The disabled control has the same 17
verified optima, ten numerical errors and three time limits. The 24 unaffected
configurations retain status, iteration/refactorization counts, phase sequence
and objective exactly. See [the paired individual results](results/native-prices/models.md). Successful results require agreement with the
independent HiGHS reference and feasibility in the original unscaled model.
Native, JuMP and explicitly permuted models are checked for exact equivalence.

In six configurations, the price repair succeeds but a subsequent artificial
removal still fails: mod010 seed 1/PFI, degen2 native and JuMP, misc07 native,
and degen3 native and JuMP. For native degen2, the disabled control fails on prices at iteration 2,160,
whereas corrected pricing reaches removal at 660. JuMP degen2 runs to its
90-second limit at 868,714 iterations in the disabled control, versus removal
at 733 with corrected pricing. Native and JuMP degen3 likewise reach time limits at 109,743 and 112,654
iterations in the disabled control, versus removal at 2,345 and 2,891.
These counts demonstrate avoided spurious progress, not a timing benchmark.

This is removal of a demonstrated numerical obstacle,
**not an increase in the number of completed models**. In particular, the
captured auxiliary-optimality replay must not be described as a complete mod010
solve. Other price disagreements remain with mod010 FT/SS, native boeing1 and
both p0201 readers; native cycle and JuMP stocfor2 retain their separate failures.

All real-model runs retain the isolated policy from broad validation: Float64,
steepest-edge, native refactorization every 80 updates, relaxed integrality,
90 seconds and 1,000,000 iterations per case. Only stagnation monitoring,
adaptive pricing, primal/dual perturbations and Phase I are enabled. The separate
weak-pivot preference and original-LP rescue retry are disabled diagnostically.
Native safeguards remain active. Timings include compilation and instrumentation
and are not performance comparisons. Neither runtime nor medium was rerun here.

## Captured next boundary: artificial-removal row

The seed-1 mod010 run with corrected prices fails at `entering == 0` in
`_remove_artificials!`, before any exchange. Two artificials remain basic.
The first is column 2737 at basis row 89, with value
`-4.7941448790642755e-17`. Its independently solved BTRAN row has absolute
residual `8.20051097734489e-17` and componentwise relative residual
`0.05319148936170205`. All 56 candidates meeting the direction-strength filter
receive `:refresh` from pivot validation; 23 also have unreliable FTRAN columns.

A diagnostic-only call to the existing native cleanup corrects this unit-row
BTRAN to zero residual. Recomputing its prices then gives 33 accepted candidates
and 23 still requiring refresh. The candidate filters and pivot-validation
thresholds are unchanged. This identifies a separate pre-exchange gap: a
correct objective dual from `B' * dual = c_B` does not repair the subsequently
computed pivot row from `B' * rho = e_row`. With solve refinement disabled,
artificial removal currently rejects an unreliable row without attempting the
available certified native correction. The earlier artificial-exchange repair
only addresses reconstruction **after** an accepted exchange.

The captured row/probe is retained for the next core phase-transition change.
This commit does not alter artificial-removal arithmetic or claim that the
row-only diagnostic completes the whole model. No corresponding candidate-row
cause is inferred for the other five removal failures without their own probes.

The final production source SHA-256 is
`e2e5be10660627f80fe4c146758d116c847b1d5530e5861c79816dc74e66da16`.

## Reproduction

Use the established process/memory guard, one Julia thread and one BLAS thread;
run numerical processes serially. Keep local `precompile_workload=false`.
Input and HiGHS manifests are unchanged from `results/broad-validation`.

- `reproduce/direction_price_capture.jl` observes price rejections and saves the
  final rejected workspace and direction. The original capture was made before
  the production correction; on corrected code it follows the changed path.
- `reproduce/direction_price_probe.jl PREFIX` checks the captured BTRAN with
  native cleanup, exact residual arithmetic and the independent 256-bit solve.
- `reproduce/direction_price_regression.jl PREFIX OUTPUT` replays one production
  primal iteration without numerical overrides.
- `reproduce/direction_price_semantics.jl PREFIX OUTPUT` adds the related semantic
  suites, normally run with `--compile=min`.
- `reproduce/broad_corpus.jl INPUTS REFERENCES JOBS OUTPUT_PREFIX` runs the final
  complete models; use the local JuMP environment as in earlier reports.
- `reproduce/direction_price_ablation.jl` has the same four-argument interface;
  it disables only this new recovery, leaving other instrumentation identical.
- The existing `mod010_phase_capture.jl` captures the subsequent removal boundary.
  `direction_price_removal_probe.jl BOUNDARY_PREFIX` inspects the first remaining
  artificial's row and candidate-quality checks without changing production.

Large numerical snapshots stay local, with paths and SHA-256 hashes recorded
in the committed capture manifest. Text evidence, jobs and result reports are
committed; Manifest.toml and LocalPreferences.toml are not.
