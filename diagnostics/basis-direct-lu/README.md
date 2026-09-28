# Direct native LU update experiment

This explicit diagnostic opt-in replaces the full frozen LU backend with its
lower factor, initializing packed U and the basis column permutation from native
LU. For `P*S*B*E=L*U`, backend `B0=inv(S)*P'*L` preserves the existing triangular
update identity `B=B0*inv(R)*U*Q'`. Native Rs interpretation is verified before use;
unavailable scaling falls back to full native LU and identity correction U.
The package does not load this prototype. Adaptive, Markowitz and non-Float64
paths retain their ordinary implementation.

Copies share only immutable lower coefficients/permutations/scaling and own
scratch. Refactorization builds the complete candidate before replacing live
state. The backend performs CSC unit-lower substitution; native combined-solve
iterative refinement is no longer present. This remains a numerical limitation
requiring own-trajectory validation, not a reason to assume equivalent stability.

## Initial unscaled experiment

Baseline 0065856 (production kernels identical to a1adfb4). 1,074 diagnostic
assertions passed, including independent dense references, original matrix
residuals, unprepared reconstruction with actual U, divergent copied updates,
failed/resized refactorization, direct/fallback transitions, indexed dense fallback,
all manager/backend/strategy dispatch combinations, and wider-precision
componentwise residuals for scaled cancellation-heavy matrices. Wider precision
is used only by the reference test, never by the prototype. Independent review
found no implementation defect; its requested validation additions were included.

Two alternating paired repetitions cover 320 exchanges for all three managers on
three histories. First-call warmup uses separate nontrivial factors. All measured
solves/updates and each factor construction are included below. Normwise scaled
residual checks pass at 20/80/160/320; these alone are insufficient to certify
ill-conditioned LP solutions. Raw files retain storage and component timings.

Julia 1.13.0 Linux aarch64, one Julia and BLAS thread. Ratios include initial
construction + two FTRAN + update + unit-RHS BTRAN, direct/correction.

| History | Manager | Ratio |
|---|---|---:|
| ft-late.toml.history.30000.bin | BartelsGolubFactorization | 1.018 |
| ft-late.toml.history.30000.bin | ForrestTomlinFactorization | 1.063 |
| ft-late.toml.history.30000.bin | SuhlSuhlFactorization | 1.015 |
| ft-late.toml.history.40000.bin | BartelsGolubFactorization | 1.156 |
| ft-late.toml.history.40000.bin | ForrestTomlinFactorization | 1.007 |
| ft-late.toml.history.40000.bin | SuhlSuhlFactorization | 0.949 |
| medium-history.bin | BartelsGolubFactorization | 1.248 |
| medium-history.bin | ForrestTomlinFactorization | 1.496 |
| medium-history.bin | SuhlSuhlFactorization | 1.405 |

The direct upper factor is smaller on runtime, but more expensive updates and
construction offset solve savings. Early medium is slower. A probe shows its
lower factor is identity (360,982 stored diagonals), while every direct-U diagonal
is non-unit, making every upper column active despite very few off-diagonals.
Diagonal transfer into the lower backend is the next bounded experiment in this
same worktree; no default change is justified by the initial results.

## Reproduce

Run reproduce/check.jl. Paired runner takes a fresh output directory and the three
history paths identified by SHA-256 in results, optionally JSIMPLEX_PROBE_REPEATS=2.
The external runner takes the predecessor external-inputs.toml and a fresh output
path. For a dedicated diagnostic Julia process:

```julia
using JSimplex
Base.include(JSimplex, joinpath(pkgdir(JSimplex), "diagnostics", "basis-direct-lu",
    "reproduce", "direct.jl"))
JSimplex._install_trial_direct!()
```

Only native Float64 legacy FT/SS/BG solves opt in. Restart Julia to opt out.
The installation is a development-only internal interface, not a public API.

All five independent unscaled dual-FT LP solves reached certified optima (20
assertions). Fast0507 took 7,175 iterations, versus correction predecessor 6,211.
The separate elapsed times are not a controlled performance comparison. This
commit records the verified initial prototype; normalization and larger independent
LP trajectory checks are still pending before closing proposal 5.
