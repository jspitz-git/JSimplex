# Native reconstruction after a basic artificial exchange

Base: `cfbaf3f` on `codex/adaptive-degeneracy`.
This follows the permuted mod010 failure found in
[the broader corpus validation](broad-validation.md).

## Captured cause

The native MIPLib mod010 LP relaxation, with both rows and columns permuted by
`MersenneTwister(17)`, reaches the artificial-removal boundary at iteration 324.
There are 140 artificial columns, but only one remains basic. Its value is
`5.551115123125763e-17`. The selected exchange uses pivot `-1.0`, entering column
698 and leaving artificial 2773 at basis position 126. Its movement is
`-5.551115123125763e-17`.

The predicted point after this exchange passes the full primal certificate and
the primal basis residual check. The mandatory refactorization reconstructs a
point that remains finite and primal-feasible, but fails the componentwise
basis residual check. The original implementation rejects it at iteration 325,
before reaching the final original-dimension export and its native recovery.

| Checkpoint | Primal absolute residual | Componentwise relative residual | Reliable |
| --- | ---: | ---: | --- |
| Before exchange | 3.48877305645634e-15 | 4.787836793696016e-16 | yes |
| Predicted exchange | 3.5165286320719706e-15 | 4.926614671774161e-16 | yes |
| Refactorized reconstruction | 2.804700915959288e-15 | 0.003306929170191529 | no |
| Existing native recovery applied diagnostically | 5.551115123125783e-17 | 2.7755575615628914e-17 | yes |

Dual reconstruction passes after refactorization. The predicted checkpoint's
dual prices are intentionally stale until that refactorization; they are not a
basis-adoption certificate. The problem is loss of primal residual reliability
on reconstruction, not a weak pivot, infeasible predicted movement or a missing
anti-degeneracy heuristic.

## Change and limits

After refactorizing an artificial exchange, retain the existing finite-workspace
and basis-quality checks. **Only when basis quality fails**, try the same guarded
`_complete_native_phase_transfer!` used by final export, then require basis quality
again and the existing basic-bound feasibility check. The helper still certifies
the full candidate point before publishing its repaired numerical state.

There are no new numerical algorithms, thresholds or iteration controls. The
existing helper performs bounded recovery in the problem's hardware precision;
its policy eligibility, refinement budget, stop handling and rollback remain
unchanged. Reliable exchanges keep their previous acceptance path, avoiding an
extra full-point certificate on that path. Unsupported checked/staged policies,
dual mode and other scalar types retain their earlier behavior.

The original workspace remains untouched until the complete removal/export is
accepted. Work performed in the private auxiliary workspace remains charged on
failure or cancellation. Adaptive pricing and perturbation policies are unchanged.

An initial diagnostic integration called completion even on reliable exchanges.
Review identified the unnecessary extra point certificate and scan; the final
implementation restricts the call to failed basis quality. The preliminary
whole-model run is retained separately from verification of the final code.

## Portable regression

A six-by-six integer matrix, generated independently of mod010, reproduces the
same failure when exchanging an exactly zero basic artificial. Its known point
is `[1,1,0,0,0,0]`, with RHS equal to the sum of the first two columns. The last
two rows are homogeneous and involve only zero coordinates at that point.
This models a maintained feasible Phase-I point without importing a large LP
or a serialized workspace into the test suite.

Before the change, the new successful-exchange test had **32 passing and four
failing assertions**: Float64 removal failed with PFI, FT, SS and BG. The saved
mod010 boundary separately had three passing assertions and one expected failure.

After the final scope restriction, `native_phase_transfer_tests.jl` passes
**278 assertions**. It covers both Float32/Float64 and all four managers,
original-point and basis certificates, failed bound certificates, disabled
recovery budgets, cancellation and callback exceptions. Rejected or interrupted
removal preserves the original basis, point, bounds, costs and prices while
retaining consumed work. Reliable Float32 exchanges also pass with no refinement
budget and no correction events.

## Whole-model and semantic verification

The final production source digest is
`1713d57c67ee6eaf2aa3089bc2b22d81918a0f7bacac615e14388e130ecfb391`.
The complete fresh seed-17 PFI solve now reaches **OPTIMAL in 679 iterations**,
objective **6532.08333333333**, with verified original primal feasibility and
agreement with HiGHS. It previously stopped at iteration 325. The same seed-17
permutation also solves with FT (621), SS (647) and BG (622 iterations).

The selected follow-up comprises **20 complete model runs: 17 verified optima
and three numerical errors**, with no time limits or harness exceptions.
See [the individual results](results/artificial-exchange/models.md).
Other successful checks include mod010 PFI permutations with seeds 2 and 29,
mod010 native/JuMP primal and dual, and scsd6 primal with all four managers.
The 11 configurations repeated from the broader corpus, excluding the repaired
seed-17 PFI case, retain their previous status and iteration count.

The unresolved results are explicitly retained:

- mod010 permutation seed 1, PFI primal: reduced-price/direction disagreement
  at iteration 272, before any native phase-completion attempt. This is a newly
  tested permutation; no pre-change paired run is claimed for it.
- Native cycle, PFI primal: bounded feasibility recovery exhausted at 868,
  matching the prior result.
- JuMP stocfor2, PFI primal: primal feasibility lost at 1957, matching the
  prior result.

The broader semantic runner passes **8,540 assertions**, followed by **eight
captured-boundary assertions**, using `--compile=min`. It covers native cleanup,
phase construction/removal, deadlines, state and precision handling, adaptive
policy separation, pricing, perturbations, point recovery and existing regressions.
Counts include overlap among existing runners and are not distinct-test counts.
The standalone native phase-transfer suite also passes all **278 assertions**
with normal compilation. The full project test suite was not run.

All real-model runs use the same isolated configuration and observer as the
broader corpus: Float64, native refactorization, interval 80, steepest-edge,
relaxed integrality, 90 seconds and 1,000,000 iterations per case. Only stagnation
monitoring, pricing, primal/dual perturbations and Phase I are enabled; separate
weak-pivot preference and original-LP retry are disabled. Native safeguards stay
active. Results are checked against the existing independent HiGHS references
and original primal feasibility, with exact model equivalence under reader/order
changes. Timings include compilation and instrumentation and are not benchmarks.

The diagnostic coverage field `export_attempts` counts calls to the shared
completion helper, now including an unreliable artificial exchange. It must not
be interpreted as a count of final original-dimension exports. Local and component
repair counters retain their previous meanings.

## Reproduction and provenance

Run numerical processes serially through the established 8 GiB virtual-memory
wrapper and owned-process guard (available RAM at least 6 GiB, swap at most
1 GiB), with one Julia and one BLAS thread. Preserve local
`precompile_workload=false`. No Manifest or LocalPreferences is committed.

Scripts:

- `reproduce/mod010_phase_capture.jl`: runs the existing corpus harness with
  observational boundary capture and rejecting-line instrumentation.
- `reproduce/mod010_phase_replay.jl`: replays the captured removal and reports
  predicted versus reconstructed numerical state.
- `reproduce/mod010_phase_regression.jl`: checks the production removal path
  without numerical overrides against the captured boundary.
- `reproduce/mod010_phase_semantics.jl`: runs related semantic suites plus the
  production captured-boundary regression.

The 20-case follow-up uses the existing `broad_corpus.jl` and recorded jobs.
The input and HiGHS-reference manifests are unchanged from broad validation.
Run from this checkout using the same local JuMP environment:

```sh
julia --project=.superpowers/adaptive-degeneracy/broad-validation/env \
  diagnostics/adaptive-degeneracy/reproduce/broad_corpus.jl \
  diagnostics/adaptive-degeneracy/results/broad-validation/inputs.toml \
  diagnostics/adaptive-degeneracy/results/broad-validation/references.toml \
  diagnostics/adaptive-degeneracy/results/artificial-exchange/jobs.toml \
  /tmp/new-artificial-exchange-models

julia --project=. --compile=min \
  diagnostics/adaptive-degeneracy/reproduce/mod010_phase_semantics.jl \
  .superpowers/adaptive-degeneracy/artificial-exchange/mod010-phase-capture-boundary \
  /tmp/new-artificial-exchange-boundary.toml
```

The same manifest/reference interface applies to the capture runner; use the
single-case `capture-jobs.toml` and a new output prefix. Its boundary filenames
append `-boundary-phase.bin`, `-boundary-original.bin` and `-boundary-map.bin`.
Capturing on the base commit reproduces the failed endpoint; capturing after the
fix continues through the repaired transition. The replay script takes the
boundary prefix alone. It writes additional local numerical snapshots beside it.

Raw reports and logs are under `results/artificial-exchange`. Large snapshots
remain local, with paths and hashes in the capture manifest. The portable fixture
is part of the normal project test runner through `native_phase_transfer_tests.jl`.
This is a targeted correction and verification, not a full project-suite pass
or resolution of the other failures found in the broader corpus.
