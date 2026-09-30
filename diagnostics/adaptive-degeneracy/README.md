# Isolated adaptive anti-degeneracy investigation

Base: `621380f35f1b5ea6e9352067b6fc39d578723595` (master).
The unrelated scan-performance experiments remain on
`codex/simplex-scan-performance`; none are included here.

## Respect the pricing policy during stagnation monitoring

The legacy zero-step Dantzig trigger has already been removed from the numerical
core. A separate adaptive trigger in `_observe_workspace_stagnation!` still
selected Dantzig when the dual monitor reported stagnation, even with
`adaptive_pricing=false`. Thus enabling only the monitor could change pricing,
confounding isolated anti-degeneracy experiments.

The trigger now also requires `adaptive_pricing`. With it disabled, monitoring
continues to advance and report stalled windows, but does not set the dual
Dantzig fallback. The existing positive case with adaptive pricing enabled is
unchanged. Numerical recovery of invalid edge weights remains independent;
this change does not reset an already active pricing fallback with stale weights.

The new regression observed three expected failures before the fix: effective
pricing became Dantzig, the fallback flag was set, and a fallback event was
emitted. Its three monitoring assertions already passed. All six assertions
pass after the added policy guard.

`reproduce/focused.jl` passes **2,764 checks** with Julia 1.13.0 aarch64,
`--compile=min`, one Julia thread and one BLAS thread. It covers numerical/strategy
separation, legacy dual policy, stagnation, both perturbation mechanisms and
adaptive pricing, including existing positive and disabled cases. The run uses
the existing owned-process memory guard and finishes within its 240-second
budget (testset time 68.4 seconds). See `results/policy-isolation.log`.

Reproduce from this checkout through the established wrapper:

```sh
python3 /home/jspitz/JSimplex.jl/.worktrees/primal-direction-prices/.superpowers/primal-prices/guard.py --seconds 240 \
  /home/jspitz/JSimplex.jl/.worktrees/primal-direction-prices/.superpowers/primal-prices/julia.sh \
  --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/focused.jl
```

Independent read-only review found no blocking issue. This is targeted semantic
verification, not a full-suite pass or a real-model convergence result. No
medium/runtime solve or anti-degeneracy intervention has been performed in this
change. Isolated experiments still need explicit policy settings for the other
adaptive mechanisms; `simplex_strategy=:adaptive` alone enables several defaults.
Phase-I perturbation eligibility and original-model cleanup are unchanged.
