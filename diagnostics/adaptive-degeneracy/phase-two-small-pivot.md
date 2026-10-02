# Feasible bound flips beside unusable primal pivots

This follows the Phase-II endpoint recorded in
[the native phase-transfer report](phase-transfer-recovery.md). The baseline is
`f43b4ef`, production SHA-256
`4ec571a4c968dca505cee5c193411bc3b55a73ab8dbf82a168887fc8b6dc4957`.
The saved endpoint is at iteration 128,873, with snapshot SHA-256
`41ff2e3ae30e0585a20a198f4e7c54783e7d27d0facbab97b69261bd181cf409`.

## Reproduced cause

One production candidate pass reproduces `primal pivot is below the zero tolerance` without completing an iteration. It prices 47 distinct entering
variables, with one repeated candidate across the native refactorization:
48 direction-price checks pass and all 48 ratio tests return a zero step with
a pivot smaller than the absolute `1e-12` zero tolerance. Selected absolute
pivots range from 2.9381e-72 to 3.5055e-15. Merely refreshing the basis does not
change this outcome.

Every candidate has a finite opposite bound at distance approximately `1e-5` (the stored widths range from `1e-5` to
`1.0000000006081523e-5`). This entering
bound sets the Harris relaxed limit in every case. Tiny nonzero direction
components at basic variables already on or slightly beyond their bounds give
strict ratios of zero after clipping. The second Harris pass selects these tiny
basic pivots and never considers the entering bound again. The later pivot
threshold correctly rejects them, even though no basis exchange is needed to
complete the entering variable's bounded move.

For example, entering variable 31983 has reduced cost 181.61944692694584 and
direction -1. Its selected basic row 21128 has value -100.00000000000001,
lower bound -100, and direction coefficient -3.6775281722455827e-16. The negative
raw ratio is clipped to zero. The implied direction price agrees with the
stored price; this endpoint is not another direction-price mismatch.

An independent prediction applies each of the 48 captured directions to the
common workspace saved after the failed candidate pass. It moves the candidate
to its opposite bound, updates all basic values, and restores that common point
afterward. **All 48 predicted points pass the existing full stored-point
certificate**. This checks directions at that shared endpoint, not separately
captured primal vectors from every call; the first direction was observed before
the single refactorization.
The maximum bound violation over these trials is 9.982596842974829e-8, below the
unchanged 1e-7 tolerance. These are individual trials, not a claim that all flips
can be applied together without further checks.

## Bounded core correction

After the existing Harris search, the native Float32/Float64 ratio path may
return the entering-bound flip when all of the following hold:

- No selected Harris pivot exceeds `zero_tolerance`.
- The opposite entering bound and its step are finite, the step is positive,
  and it does not exceed the existing relaxed limit.
- Every predicted basic value is finite and satisfies the existing per-bound
  feasibility tolerance.

The shared bound predicate also performs the unchanged final Harris feasibility
check. The ordinary flip application, recomputation, stored-point recovery and
terminal certification remain in place. The ratio predicate alone is not a
full point certificate. No tolerance, basis pivot threshold, pricing rule,
adaptive schedule or precision policy changes.

The existing native row-validation predicate limits this new branch. Checked,
refined, recovery, incremental and staged workspaces retain their prior paths;
so do BigFloat and rational arithmetic. A usable basic pivot keeps its priority.
This is a feasible bounded step in the numerical core, not a heuristic switch
or permission to ignore an otherwise blocking constraint.

## Targeted verification

The new portable regression initially failed on the original error: 128 failed
assertions in the original 192-assertion positive testset. It now covers both
hardware precisions, both directions, all four basis managers and both strategy
names, with optional numerical switches isolated. Cases include exact bound
contact and a tolerated initial bound violation, rejection of an infeasible
longer flip, usable-pivot priority, no finite opposite bound, and excluded policy
and scalar-type paths. A rational scope fixture was corrected to use an explicit
nonzero coefficient/tolerance rather than deriving zero from its exact defaults.

The combined simplex semantic run passes **8,852 assertions** with `--compile=min`.
On the actual saved endpoint, the production candidate pass now accepts its first
candidate: one `1e-5` flip, iteration 128,874, with no new refactorization or basis
exchange. No diagnostic override changes numerical selection; the probe only
records calls, and the pre-existing isolated-pricing override remains unchanged.

## Reproduction

Run one numerical Julia process at a time with the existing memory guard,
Julia 1.13.0/aarch64, one Julia thread and one BLAS thread. Do not solve the
excluded large inputs. Preserve the prior capture and local environments.

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/probe_phase_two_small_pivot.jl .superpowers/adaptive-degeneracy/phase-transfer-recovery/runtime-phase-continuation-final.bin /tmp/phase-two-pivot
julia --project=. diagnostics/adaptive-degeneracy/reproduce/analyze_phase_two_ratio.jl .superpowers/adaptive-degeneracy/phase-two-small-pivot/phase-two-pivot.bin /tmp/phase-two-ratio.toml
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/phase_two_flip_semantics.jl
```

The first two diagnostic reports describe the baseline when run at `f43b4ef`;
on corrected sources the first pass completes a flip. The analyzer command uses
the retained baseline pass, not the output of that corrected probe: its entering
variable would already be at the opposite bound. Binary captures remain
local and are not exact outer-driver restart points. UMFPACK reconstructs native
factorization objects from its serialized inputs when needed.

## Production continuation and the next boundary

With only this core correction, the recorded Phase-II endpoint completes **47
bound flips**, no pivots and no pivot refactorizations, and passes its reduced
problem terminal certificate at iteration **128,920**. It then enters the normal
original-model postsolve. The whole continuation returns `NUMERICAL_ERROR`,
`primal feasibility lost`, after 13.327 seconds with 39,057 cumulative
refactorizations. The overall original-input optimum is **not** certified.

A separate observational replay captures the postsolved target and the original
basis immediately before and after projection. Its numerical result is the same;
its longer time includes writing these captures. The target fails the existing
original-space primal certificate, so projection correctly returns `nothing`.
The restored basis has primal infeasibility 3,436,849.0446019256 before projection;
this is distinct from the much smaller infeasibility of the supplied target.

To distinguish an existing transformation/cleanup issue from the new flips,
`probe_small_pivot_original_point.jl` rebuilds and compares the working model,
then postsolves the **pre-flip** point as well. Independent 256-bit matrix-vector
products evaluate the stored original coefficients; no LP or basis is solved
or factored at higher precision. Both before and after the 47 flips, **21 column
bounds and 65 rows** violate the unchanged original 1e-7 tolerance. Both have
maximum violation **0.0010642815553997648**. For example, original variables
`C6569`, `C6570` and `C6571` have that negative value against a zero lower bound
in both points. The original-space feasibility problem predates this correction.

The postsolved objective is 51,425,691.78019489 before the flips and
51,425,691.70615497 afterward. The latter is below the certified dual reference
51,425,691.762103125 because the target is infeasible; it is not a better optimum.
The original certificate remains authoritative and prevents a false success.
The next investigation should follow these original-bound violations through
scaling/presolve and the failed basis recovery, using the retained captures.
No correction to that separate boundary is included here.

The real-model verification in this change is a reconstructed continuation of
the captured Phase-II endpoint, with a reset time budget. A fresh whole-MPS
trajectory is not claimed. The full Phase-I prefix is not repeated before the
now-localized original-space failure is understood.

Normal-compilation regressions pass **1,612 assertions**, including the portable
flip cases and existing allocation checks. These and the 8,852 semantic checks
are focused suites, not a claim of a complete project-suite pass.

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_transfer_recovery_continue.jl runtime primal both 3600 /tmp/runtime-small-pivot-continuation .superpowers/adaptive-degeneracy/phase-transfer-recovery/runtime-phase-continuation-final.bin
julia --project=. diagnostics/adaptive-degeneracy/reproduce/capture_small_pivot_postsolve.jl runtime primal both 180 /tmp/runtime-small-pivot-postsolve .superpowers/adaptive-degeneracy/phase-transfer-recovery/runtime-phase-continuation-final.bin
julia --project=. diagnostics/adaptive-degeneracy/reproduce/probe_small_pivot_original_point.jl /tmp/runtime-small-pivot-postsolve-target.bin .superpowers/adaptive-degeneracy/phase-transfer-recovery/runtime-phase-continuation-final.bin /tmp/phase-two-original-point.toml
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_two_flip_compiled.jl
```

The external matrix suite passes **80 solves / 245 assertions** over five
permitted inputs, both simplex algorithms, four basis managers, and native/
Markowitz refactorization. Every result has the reference objective and certified
original primal feasibility. Sequential numerical processes use the established
8-GiB virtual-memory cap, 6-GiB available-RAM floor and 1-GiB swap ceiling.

Committed text evidence is in
[results/phase-two-small-pivot](results/phase-two-small-pivot/). Large snapshots,
logs and executed scripts remain in
`.superpowers/adaptive-degeneracy/phase-two-small-pivot/`, with a committed hash
manifest. The corrected production SHA-256 is
`54bb0b5741f1619571bde0f2f6a985c85384bafbeffa06c75a4e3353c7c45de3`.

```sh
python3 diagnostics/adaptive-degeneracy/reproduce/validate_phase_two_small_pivot.py
```
