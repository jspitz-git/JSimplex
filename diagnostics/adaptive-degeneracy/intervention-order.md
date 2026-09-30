# Method-specific progress and ordered adaptive interventions

Baseline: `9763a3c`, including the certified native midpoint recovery. This work
changes adaptive policy only. The experiments retain Float64, PFI/native/80 and
isolated stagnation, pricing and perturbation switches. Other adaptive features
and the independent weak-pivot preference remain disabled.

## Observed causes and bounded changes

The previous medium capture reports progress at iteration 5568 while the
auxiliary objective slightly worsens: the shared monitor accepted a decrease
in dual infeasibility. In both optimization loops, pricing observation precedes
perturbation, so a single stalled window could start both interventions.

The first change makes workspace progress depend on the running method:

- Primal simplex requires improvement in its working objective, including an
  artificial-variable objective in Phase I. Price changes at a fixed primal
  point do not establish progress.
- Dual simplex also accepts a decrease in primal infeasibility. This preserves
  useful feasibility work during a constant-objective plateau.
- All objective and feasibility metrics remain available diagnostically. The
  generic standalone monitor retains its prior all-metric default. Scale,
  significance tolerance, hysteresis, step recording and context resets remain
  unchanged.

The second change is evaluated separately: automatic perturbations wait
while a temporary pricing trial is active. An unsuccessful trial can expire
before a shift is attempted. A successful pricing return leaves the monitor
productive and does not immediately trigger a shift. Existing shifts may stay
active through later trials, but no new adaptive cost/bound shift is introduced during
one. Numerical repairs remain independent. The original restoration, numerical checks and three-level caps remain
in force. Perturbation-only operation and explicitly requested Dantzig do not
need an adaptive pricing trial.

This orders evaluations without asserting that Dantzig or perturbation cures
degeneracy. The initial metric-only runs keep the old concurrent scheduling to
separate the two changes. Earlier baseline reports are in
`results/balanced-point`; new reports and logs are in `results/intervention-order`.

## Focused regression evidence

The method-specific metric regression first reproduced eight failures in its
20 primal assertions. After the change, the metric and existing adaptive suite
passed 3,321 assertions with `--compile=min`. This change is committed as
`1193efc` before intervention ordering is changed.

The scheduling regression first passed 167 and failed 101 assertions. With the
gate, all 268 pass. They cover both methods, Float32/Float64/BigFloat, preserved
LP data and unconsumed perturbation levels during a trial, failed trial expiry,
productive returns, explicit Dantzig, disabled adaptive pricing, and cancellation
before publication. The final combined semantic runner passes 3,739 assertions.
These counts overlap; they are not a whole-project test result.

The first broad scheduling check exposed 48 failed assertions and two accesses
to absent journals in older fixtures. The short perturbation-only chains had
implicitly enabled adaptive pricing and assumed concurrent shifts. They now
explicitly disable pricing, preserving their original perturbation and cleanup
assertions. The combined dual test covers both a short cycle that reaches the
optimum during a trial and a longer cycle that reaches expiry, shifting and
original-cost cleanup. Cancellation at a Phase-I shift now requires the pricing
trial to have expired, instead of asserting the former overlap. Independent
read-only review found no actionable issue in the changes.

Completing a whole solve during a trial does not by itself rewrite the final
workspace's pricing state. Existing phase handoff and cleanup resets still
prevent a temporary trial from crossing phases. Returned solution certification
continues to require original bounds and costs.

## Separate primal measurements

All rows below use a 300-second solve budget, one Julia/BLAS thread and the same
input hashes. The original-LP retry is disabled. Final objective entries are
**uncertified observations of the auxiliary workspace**, not returned original
solutions. All runs end at `TIME_LIMIT` in Phase I; none establishes convergence.
Compilation, guard overhead and single-run variability preclude speed claims.

| Model | Policy revision | Iterations | Refactorizations | Last observed auxiliary objective | Rejected candidates |
| --- | --- | ---: | ---: | ---: | ---: |
| medium | prior metric and concurrent actions (`9763a3c`) | 6,778 | 85 | 160,015,999.98996 | 30 |
| medium | method-specific metric only (`1193efc`) | 2,471 | 31 | 160,015,999.98655 | 348 |
| medium | metric plus ordered actions (`dd7188d`) | 2,819 | 36 | 162,059,999.98611 | 0 |
| runtime | prior metric and concurrent actions (`9763a3c`) | 4,539 | 1,287 | 603,523.37563 | 304,345 |
| runtime | method-specific metric only (`1193efc`) | 4,719 | 1,321 | 603,474.51286 | 311,862 |
| runtime | metric plus ordered actions (`dd7188d`) | 7,694 | 1,763 | 601,096.58700 | 156,533 |

The metric-only runtime run matches the earlier objective, infeasibility and
pricing observations at iterations 1,000 through 4,000. Its different stopping
iteration is not evidence of changed numerical behavior or a speed gain.

On medium, metric-only scheduling shifts bounds at iterations 192, 320 and 512;
the first two occur during a pricing trial. Ordered scheduling shifts at 448,
896 and 1344, each after a failed trial. All six completed pricing trials expire
and a seventh remains active at the time limit. There are no productive returns
based only on dual-price changes. Nevertheless, its final auxiliary objective
is worse than in the earlier runs; this is not a medium convergence improvement.
It still needs 1,848 certified point preservations (including two midpoints).

On runtime, ordered scheduling permits seven productive pricing returns and two
expired trials, with no open trial at termination. The first actual bound shift
occurs only at iteration 6656, after the second expired trial. The first expired
trial does not independently satisfy all perturbation eligibility conditions.
There is partial objective progress after shifting, but 156,533 rejected
candidates, 1,692 pivot-triggered refactorizations and 1,862 preserved points
remain substantial work. One perturbation level is used. No numerical error or
precision boost is reported in either coordinated primal run. Runtime still
shows very large auxiliary dual infeasibility (about `9e17` near its bound shift
and `8e12` at termination). Avoiding an error status does not establish numerical
stability or certify these terminal workspace observations.

Production-source digests distinguish the interventions:

- Metric only: `f25db4691ad5dd57fc572a09db0f29c8ead15ca8893798f79cfdb6b9434a9b2e`.
- Metric and scheduling: `5c5583c763661dc41c0678e035b0521c53515e50c26e6da18a0f5e5a8a297ab7`.

The final normal-compilation runner passes 300 assertions. The event validator
rejects the recorded pre-gate overlap and passes all three coordinated reports;
the lifecycle validator also confirms bounded trials. A trial still active at a
solve time limit is reported as open, not as a productive return.

## Extended dual measurement

The coordinated medium dual run uses the same production digest and isolated
policy for 900 seconds. It ends at `TIME_LIMIT` after 39,163 iterations and
490 refactorizations, without an original-LP retry or a numerical error. It
neither reaches an optimum nor establishes a remedy for late stagnation.

The auxiliary phase completes at iteration 35,395 (about 816.1 seconds). Both
its departing workspace and the original workspace report a pricing phase
reset: steepest edge, no temporary trial, and zero pricing observations. The
auxiliary objective is approximately `-1.11e-10` with zero reported primal and
dual infeasibility. Restoring the original problem still produces an objective
near `-7.37362e13` and primal infeasibility near `1.28412e9`. Correct pricing
reset does not remove this large change of working-problem values.

There are 64 temporary pricing trials, all in the auxiliary workspace, all
ending in productive returns; none expires or remains open. No adaptive
perturbation is applied anywhere in this run. The auxiliary workspace forbids
perturbations, and the original workspace does not trigger a stalled trial
within the remaining budget. Consequently this run checks method-specific
progress and phase isolation on medium dual, but does not exercise actual
ordered cost shifting there; the focused dual regressions cover that path.

At termination the uncertified original workspace has objective
`-7.370366633641006e13`, primal infeasibility approximately `5.38166e9`, and
reported dual infeasibility zero. These values do not demonstrate overall
feasibility progress after handoff. The monitor still reports progress in its
recent window; that local classification is not a convergence certificate.
The older pricing-only dual report uses different policy flags, so comparing
its 900-second stopping iteration would not isolate this change.

The remaining investigation should distinguish local window improvements from
sustained reduction of the active phase's target, and inspect the primal
candidate rejection work. Raising perturbation levels or adding further
simultaneous interventions is not justified by these results.

## Reproduction

Use the existing owned-process memory guard (8 GiB virtual memory, 6 GiB
available-RAM floor, 1 GiB swap ceiling). Run only one numerical Julia process
at a time. These commands assume this worktree's local environment with
`precompile_workload=false`; neither Manifest nor LocalPreferences is committed.
Allow model reading and compilation in addition to each solve limit.

```sh
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/intervention_semantics.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/intervention_compiled.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl medium primal both 300 /tmp/medium-coordinated
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl runtime primal both 300 /tmp/runtime-coordinated
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_one_first_failure.jl medium dual both 900 /tmp/medium-dual-coordinated
python3 diagnostics/adaptive-degeneracy/reproduce/validate_intervention_reports.py
```

Repeat the two primal model commands on `1193efc` for the metric-only arm,
using distinct output prefixes. The baseline reports predate these two changes
and live in `results/balanced-point`. `phase_one_first_failure.jl` verifies the
input hashes and records the disabled retry and diagnostic method overrides;
there is no hidden original-LP restart. `validate_phase_one_reports.py` can
additionally check pricing trial durations for explicitly supplied report paths.

The isolated policy enables only `adaptive_stalling`, `adaptive_pricing`,
`adaptive_primal_perturbation`, `adaptive_dual_perturbation` and `phase_one`.
Algorithm-specific and phase-specific eligibility checks still apply. In
particular, the dual auxiliary workspace keeps both perturbation permissions
false; enabling their policy flags does not override that protection. Direct
low-level perturbation calls and numerical price repairs are not scheduled by
the new automatic gate.
