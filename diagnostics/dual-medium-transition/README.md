# Medium dual: auxiliary handoff and slow progress

Base revision: `570e9eeba212b6f577b0e67aec1d349d73938b8e`.
Input: `/home/jspitz/mps/medium.mps`, SHA-256
`79c374a584b1463305cf4b0faee8920d0364df2dd5d0468a44ab58d9e9d49dc0`.

This investigation makes **no production solver change**. It reproduces the
reported jump at iteration 35,051 and separates that transition from the slow
continuation. It does not solve medium or reproduce the million-iteration run.

## Configuration and limits

The capture uses Float64, dual simplex, legacy strategy, requested steepest-edge
pricing, PFI, native factorization, interval 80, relaxed integrality, and an
iteration limit of 1,000,000. Other options retain their defaults, including
presolve and scaling. The solver time limit is 1,200 seconds; the diagnostic
stops deliberately 2,000 pivots after the handoff (iteration 37,051).

Julia 1.13.0 runs on aarch64 with one Julia and BLAS thread. Every numerical
process is sequential and uses the existing 8 GiB virtual-memory limit and
owned-process guard (6 GiB available-RAM floor, 1 GiB swap ceiling). Local
`precompile_workload = false` is preserved. Binary snapshots remain local under
`.superpowers/dual-medium/`; their hashes are recorded in `results/validation.json`.
The observed solver-clock time is about 411 seconds, including diagnostic work;
it is not a matched timing comparison with the user's run.

## The jump is an auxiliary-bound handoff

Dual initialization first solves a bounded auxiliary problem. Its working
bounds differ from the original scaled/presolved LP, while the progress logger
still evaluates the original objective and its presolve constant on that vector.
Consequently, those values are not successive bounds on the same optimization
problem. Here the displayed objective includes a constant of `3.368156e12`.

At iteration 35,051 the auxiliary point has zero reported primal and dual
infeasibility. Its working objective is approximately `1.31e-10`, so the displayed
value is `3.368156e12`. The solver then adopts that basis for the original bounds.

An independent reconstruction of this handoff reproduces the supplied log:

| State at iteration 35,051 | Displayed objective | Primal infeasibility sum | Dual infeasibility sum |
| --- | ---: | ---: | ---: |
| Auxiliary optimum | 3.368156e12 | 0 | 0 |
| Original bounds, before bound flips | -7.0335414146415234e13 | 2.3543447352577157e9 | 332.5380015322007 |
| Original bounds, first live pricing | -7.033542412255516e13 | 2.618007369894874e9 | 0 |

The transition changes the bounds of 510,485 variables. A further 8,751 nonbasic
bound flips restore dual feasibility; these correspond exactly to the temporary
8,751 dual violations in the log. The reconstructed basis, nonbasic states,
primal values, and reduced costs match the captured live handoff exactly.
No pivot is executed from the intermediate dual-infeasible state.

The compensated absolute equation residual is approximately `1.40e-10`, and the
independent stored-row consistency check passes before and after the flips.
Thus the large jump is explained by changed bounds, not by a damaged basis in
this reproduction. The progress line is printed inside private candidate
reconstruction, before the bound flips and final handoff validation.

`pinf` and `dinf` are sums over violations larger than their tolerances; they are
not maximum violations. “Original bounds” in these diagnostics means those of
the scaled/presolved working model, not an unscaled original-input certificate.

## Requested and effective pricing differ

The auxiliary run begins with steepest-edge pricing. The legacy zero-step rule
in `_dual_after_iteration!` permanently selects Dantzig after 256 consecutive
zero dual steps. By iteration 1,000 the effective rule is Dantzig. It remains
Dantzig throughout the observed auxiliary run and is copied to the original-bound
workspace. Resetting `zero_dual_step_streak` at the handoff does not clear this
fallback flag. Weighted updates are skipped while Dantzig is active, so simply
clearing the flag would not restore valid steepest-edge weights.

This is relevant state, but it is **not a sufficient diagnosis of the slow tail**.
Two reference continuations start from the same captured handoff and fresh native
factorization. Refreshing changes neither the primal vector nor reduced costs.
One keeps the inherited rule; the other clears the Dantzig flag and initializes
a fresh Devex framework. Bounds, costs, tolerances and arithmetic are unchanged
by that intervention; normal solver cost adjustments remain enabled in both.

| After 2,000 additional pivots | Displayed objective | Primal infeasibility sum | Violating basic variables |
| --- | ---: | ---: | ---: |
| Inherited Dantzig | -7.033538004882575e13 | 1.2736117229871595e9 | 107,994 |
| Fresh Devex | -7.033537843326369e13 | 1.2851167853782754e9 | 102,714 |

Both endpoints pass stored-row consistency and have zero reported working-cost
dual infeasibility. Neither approaches a feasible optimum. The Dantzig endpoint
metrics match the uninterrupted captured continuation. A Devex reset alone does
not resolve the observed problem. The reports' `TIME_LIMIT` denotes the explicit
2,000-step diagnostic stop callback, not an exhausted 300-second clock budget.

## The tail contains dual degeneracy, not weak pivots in the sampled window

A separate 512-pivot continuation starts at the captured iteration 37,051:

- 221 dual steps are exactly zero; no primal step is zero.
- 393 dual steps have absolute magnitude at most `1e-7` (a scale reference,
  not a proposed cutoff for accepting steps).
- The median nonzero dual-step magnitude is `8.38e-11`; the maximum is `0.02736`.
- The smallest pivot relative to its direction infinity norm is approximately
  `0.499`, so this sample does not exhibit the earlier weak-pivot failure.
- The longest consecutive sequence of exactly zero dual steps is only five.
  The legacy 1,024-consecutive-zero-step perturbation rule cannot trigger here.
- The displayed objective increases by `91,750.671875`, and the primal
  infeasibility sum falls by about `9.10e6`. There is measurable progress, but it
  is small relative to the remaining infeasibility and objective scale.

Both endpoint equation certificates pass; the final absolute equation residual
is approximately `1.22e-11`. These checks do not certify every intervening point,
every direction component, or a future million-iteration trajectory. Small
working-cost adjustments occur in the continuation; endpoint dual infeasibility
is measured against those working costs, not a restored-original optimum proof.

The evidence supports investigating degeneracy and progress-based strategy
selection. It does not justify another weak-pivot veto, routine precision
increase, or a claim that restarting pricing solves medium. A separate logging
improvement should identify the active bounds/phase and avoid presenting an
intermediate handoff state as if it were a completed original-LP iterate.
Adaptive behavior and production logging are unchanged in this investigation.

## Review and verification

All four diagnostic programs were executed successfully under the guard. An
additional parser check covers the final scripts after the capture-field cleanup.
Read-only review checked the numerical claims against the reports and source,
confirmed the comparison starts from the same snapshot, and found no blocking
issue. Production source and tests remain identical to the base revision; a full
solver regression suite was not repeated for these diagnostic-only additions.

## Reproduction

Run one process at a time through the existing guarded Julia wrapper. Use fresh
output paths. From the checkout:

```sh
julia --project=. diagnostics/dual-medium-transition/reproduce/capture.jl /home/jspitz/mps/medium.mps pfi 1200 OUTPUT_PREFIX
julia --project=. diagnostics/dual-medium-transition/reproduce/reconstruct-handoff.jl OUTPUT_PREFIX.auxiliary_before_handoff.bin OUTPUT_PREFIX.original_bounds_first_pricing.bin HANDOFF.toml
julia --project=. diagnostics/dual-medium-transition/reproduce/inspect-and-continue.jl OUTPUT_PREFIX.original_bounds_first_pricing.bin baseline 300 2000 BASELINE.toml
julia --project=. diagnostics/dual-medium-transition/reproduce/inspect-and-continue.jl OUTPUT_PREFIX.original_bounds_first_pricing.bin reset_devex 300 2000 DEVEX.toml
julia --project=. diagnostics/dual-medium-transition/reproduce/trace-tail.jl OUTPUT_PREFIX.original_bounds_after_2000.bin 512 180 TAIL.toml
```

Text reports and the standard progress log are in `results/`. The capture's
published observer records omit two initial duplicate fields incorrectly named
as maxima; they contained the same sum measures as `pinf`/`dinf`. The corrected
capture omits them as well. Inspection reports compute actual maxima explicitly.
`validation.json` records this normalization and both capture-script hashes.
