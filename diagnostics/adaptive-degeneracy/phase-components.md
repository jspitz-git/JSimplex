# Coupled homogeneous roundoff at Phase-I export

The fresh run recorded in [postsolve-full-run.md](postsolve-full-run.md) reaches
an auxiliary optimum but rejects the exported primal basis at iteration 82,000.
The detached final workspace reproduces the failure directly: its full primal
point passes feasibility, but 31 basis equations fail the independent
componentwise residual check. The dual reconstruction is repaired by the
existing single native correction; the primal reconstruction is not.

## Cause and bounded correction

One compensated-residual FTRAN correction reduces the largest primal absolute
residual from `2.843740924052249e-9` to `9.317969588122391e-11`. The remaining
failures predominantly involve tiny roundoff terms. The existing eight local
reconstruction sweeps preserve the tiny nonzero right-hand sides and remove
most failures, but three homogeneous equations remain mutually coupled.
Five active coordinates (basis positions 4909, 4920, 9151, 15150, 16336) keep
passing residuals around the cycle. Values shrink to roughly `1e-42`, while
componentwise relative error remains one. Increasing sweep count does not
address this mechanism.

A targeted diagnostic clears those five coordinates and passes every basis
equation. Some of these coordinates also occur in nonhomogeneous rows; their
removal must therefore be certified against the full system. Broadly clearing
all tiny values would again erase meaningful tiny right-hand sides, the failure
already documented in [phase-transfer-residuals.md](phase-transfer-residuals.md).

The production change is confined to native primal phase export. After the
existing local reconstruction fails, it proposes clearing a component seeded
by still-failing homogeneous rows. It follows other homogeneous rows only when
all their active coordinates fit the existing correction-based cutoff. It does
not propagate through a nonzero RHS or a larger active value. All proposed
changes remain private until the unchanged compensated full-system certificate
passes; the outer export still checks the complete primal point and bounds.
Cancellation or an exception cannot publish a partially cleared point.

No solve tolerance, feasibility tolerance, precision, pricing rule, adaptive
switch, iteration policy, or ordinary factor solve is changed. The graph walk
visits each reached row and column at most once. This is numerical reconstruction
in the core, not a new anti-degeneracy heuristic.

## Targeted evidence

The new portable regression initially failed eight assertions. It now verifies
Float32 and Float64, propagation through a satisfied neighboring homogeneous
row, preservation of a separate tiny nonzero RHS, rejection when clearing
would damage a tiny RHS, cutoff enforcement, large neighboring values, and
cancellation/exception during private component clearing.

The actual fresh-run snapshot now passes all 19 export and rollback checks.
Maximum primal change is `8.058123057708144e-10`; nonbasic values are bitwise
unchanged. Primal componentwise error is `4.279104961145463e-15`; dual error is
`1.0205625548027057e-16`. Both pass the existing threshold. This export alone
is not a whole-model optimality claim.

- Semantic regressions: **9,090 / 9,090** with `--compile=min` (113.8 s).
  This run precedes the extra reviewer-requested boundary/cancellation tests.
- Compiled phase-transfer and native cleanup regressions: **250 / 250** (57.3 s),
  including those added tests.
- The earlier captured runtime phase export still passes **19 / 19** checks (8.5 s).
- Independent static review found no blocking issue; its two requested test
  extensions are included in the compiled run.

These counts overlap and are not a full project-suite claim. All numerical
runs use Julia 1.13.0/aarch64, one Julia/BLAS thread and the existing owned-process
memory guard. No excluded large model is solved or factored.

## Reproduction

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_component_replay.jl .superpowers/adaptive-degeneracy/postsolve-full-run/runtime-postsolve-full-final.bin /tmp/phase-component-replay
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/postsolve_hint_semantics.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_component_compiled.jl
```

Use the established memory wrapper around these commands. Input snapshot
SHA-256: `059b41cabc711553cc0193ec2d3c14193c835c735765c47e3f274a813262ccc4`.
Production source digest for this correction:
`7a0e1517d0685035eb496f1c6c73d4dac5ffe644a1fdb18fd9c05bf771a97e76`.
Text evidence is in [results/phase-components](results/phase-components/);
local binary and exploratory artifacts remain under
`.superpowers/adaptive-degeneracy/phase-components/`.

## Fresh whole-MPS verification

**The new solve from MPS reaches OPTIMAL.** It loads no snapshot. All 79 sampled
Phase-I pivot records match the preceding failed run in objective, primal/dual
infeasibility, dimensions and pricing. At iteration 82,000 the same trajectory
now passes export and starts Phase II. The reduced optimum is followed by
original-model cleanup starting at iteration 105,080; final original primal
feasibility is independently checked by the runner.

| Item | Result |
| --- | --- |
| Status | `OPTIMAL`, `optimal solution found` |
| Original objective | `51425691.762104236` |
| Iterations | 106,252 |
| Refactorizations | 1,341 |
| Solver time | 846.283890920 s |
| Peak RSS | 1,924,358,144 bytes (about 1.79 GiB) |
| Original primal feasibility | Certified |
| Original-LP restart | Disabled; none |

The objective agrees with the earlier certified dual reference
`51425691.762103125` to about `2.16e-14` relative difference. There are 105,762
completed pivots, 490 bound flips and 14 rejected candidates. Eleven temporary
Dantzig trials end through eight productive returns and three expirations.
No perturbation event is recorded. Precision boosting and LP refinement remain
disabled. The process exits normally; neither a time nor memory guard fires.
Cumulative allocated bytes (36,402,100,160) are not simultaneous memory usage.

This is the same **isolated adaptive configuration** as the preceding failed
full run: Float64, primal, steepest-edge, PFI, native refactorization, interval
80, integrality relaxation, stalling/pricing/perturbation switches and internal
Phase I enabled. Other numerical/adaptive switches are disabled. Existing
diagnostic overrides disable weak-pivot preference and original-LP retry; the
phase-export, simplex iterations apart from that documented preference, and
postsolve paths use production methods. The solve limit is 7,200 s and 1,000,000
iterations, with an outer 7,500-s guard. This one solve is not a convergence
claim for other managers, medium.mps, or the full default adaptive profile.

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_transfer_recovery_runtime.jl runtime primal both 7200 /tmp/runtime-phase-components-full
```

The input digest, source digest, policy, complete events and trajectory are
recorded in `results/phase-components/runtime.toml`; the local artifact manifest
covers the final detached workspace, exploratory probes and exact runner copies.
