# Original-space recovery from an approximate postsolve point

This follows [the Phase-II small-pivot correction](phase-two-small-pivot.md).
The baseline is `a43671d`. The saved runtime endpoint is iteration 128,873,
SHA-256 `41ff2e3ae30e0585a20a198f4e7c54783e7d27d0facbab97b69261bd181cf409`.
The input is `/home/jspitz/mps/runtime.mps`, SHA-256
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`.

## Boundary diagnosis

Independent 256-bit matrix-vector evaluation (no high-precision solve or
factorization) separates three coordinate systems. At the saved pre-flip point:

| Coordinates | Column violations above 1e-7 | Row violations above 1e-7 | Maximum violation |
| --- | ---: | ---: | ---: |
| Scaled working model | 0 | 0 | 9.982596843594038e-8 |
| Unscaled reduced model | 18 | 65 | 0.0010642815553997648 |
| Original model after presolve reversal | 21 | 65 | 0.0010642815553997648 |

For `C6569`, `C6570`, and `C6571`, the stored scaled value is
`-6.495859102781768e-8` and the column factor is `2^-14`.
Unscaling divides by that factor, producing `-0.0010642815553997648`.
All presolve steps retain this same value for these three columns. This is
amplification of an accepted scaled-unit error, not loss of digits in unscaling.
The other three column violations are `C8651`, `C8652`, and `C8653`, restored
by the first singleton-equality aggregation. Each inherits the existing
`-3.259258127675907e-7` value of `C12064` while its other contributing terms are
zero; this is propagation of input infeasibility, not erroneous postsolve arithmetic.
The documented simplex tolerance is in scaled units; the original-model
certificate correctly refuses this target.

Two bounded diagnostic alternatives did not produce a certified original point:

- Clipping original variables to their bounds removed column violations but
  increased the number of violated rows from 65 to 95.
- Adapting the existing joint-point projection to stricter original-unit bounds
  failed before any sweep while holding nonbasic values fixed. Reduced row 1594
  is nonbasic at its lower bound with stored value `-5.3396607817902315e-8`;
  its fixed zero row bound allows only `2.5e-8` in scaled units. The two admissible
  intervals do not intersect. Allowing all coordinates to move in a disposable
  point trial reduced the maximum native row violation to about `3.262e-6`
  after eight sweeps, but the exact original certificate still rejected it.

Neither alternative is incorporated into production. A point with changed
nonbasic assignments is never resumed as an unchanged simplex basis.

## Cause in the recovery path

`_project_postsolve_basis!` required the *supplied target* to pass the original
primal certificate before attempting any exchange. That is unnecessarily strong
for the native cleanup path: the target only selects candidate entering columns
and bound states. Its values are never installed as the accepted primal point.
The method reconstructs the exchanged basis and independently checks its actual
values against all original bounds and rows before returning success.

A diagnostic removing only this initial gate completed 342 basis exchanges,
reduced the stored infeasibility from 3,436,849.0446019256 to zero, and passed the
original-model certificate. Normal original-cost cleanup then reached OPTIMAL.
This establishes a useful recovery path without changing simplex tolerances or
repairing the approximate target itself.

## Bounded correction and verification

Float32/Float64 workspaces satisfying the existing `_native_primal_kernel`
predicate may use a finite approximate target as an exchange hint. Other scalar
types and non-native policies retain the initial feasible-target requirement.
That predicate excludes pivot validation, recovery, and incremental primal
implementations; it does not by itself exclude standalone solve refinement or
feasibility recovery. With no displaced columns, an infeasible target still
returns `nothing`. After exchanges, all existing finite-value, bound-feasibility,
and original-model certificates remain mandatory. Failed exchanges are discarded
by `cleanup_original`, which restores the incoming basis before its normal solve.

The new regression first produced 96 passes and 32 failures on unchanged sources.
The finalized semantic suite passes 9,074 assertions with `--compile=min`.
The normally compiled suite passes 2,120 assertions, including presolve's
allocation limit and the existing simplex allocation checks. These are targeted
regressions, not a complete project-suite run.
It covers both hardware precisions, four basis managers, both strategy names,
original-cost cleanup, invalid inputs, cancellation, excluded policies/types,
rejection of an infeasible reconstructed basis, and restoration of the incoming
basis after that rejection. Its failure-status assertion compares with cleanup
without a target: the deliberately infeasible fixture returns the same numerical
failure on both paths, rather than a claimed infeasibility certificate. The first
combined run also included a presolve allocation assertion under `--compile=min`;
that file is tested with normal compilation instead. The failed initial log is
retained. No adaptive trigger or precision policy changes.

On production sources (without the experimental postsolve-method override),
reconstructed continuation reaches **OPTIMAL**, objective
**51,425,691.76210431**, at iteration **130,052**, with **39,075** cumulative
refactorizations, in **25.513 seconds** after resetting the continuation clock.
It completes 47 bound flips and 1,132 primal cleanup pivots. The existing
original-model primal certificate passes. The relative objective difference
from the previous certified dual reference 51,425,691.762103125 is about 2.3e-14.

This is a continuation from the retained Phase-II endpoint, not a fresh whole-MPS
solve or an exact outer-driver checkpoint restart. The standard input transforms
are rebuilt and compared; the normal postsolve and final certification run.
The existing isolated pricing/perturbation configuration is retained, including
its weak-pivot-preference and original-retry diagnostic overrides. No additional
adaptive function is enabled. Cleanup uses the previously implemented adaptive
pricing trials; two expire and restore steepest-edge, and a third remains active
when the solve terminates. No bound perturbation or precision boost is introduced.

The external regression matrix also passes **80 solves / 245 assertions**:
`afiro`, `adlittle`, `pk1`, `flugpl`, and `fast0507`, with both algorithms,
all four basis managers, and native/Markowitz refactorization. Every result has
the reference objective and certified original-model primal feasibility.

## Reproduction

Use the established guard with one Julia process/thread and one BLAS thread:
8-GiB virtual-memory limit, stop the owned process group below 6 GiB available
RAM or above 1 GiB swap. The continuation uses a 300-second solver budget and
420-second outer wall limit. Small saved-point diagnostics use 300 seconds.
Do not solve or factor the excluded large models.

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/trace_postsolve_units.jl .superpowers/adaptive-degeneracy/phase-two-small-pivot/runtime-small-pivot-postsolve-target.bin .superpowers/adaptive-degeneracy/phase-transfer-recovery/runtime-phase-continuation-final.bin /tmp/postsolve-units.toml
julia --project=. diagnostics/adaptive-degeneracy/reproduce/phase_transfer_recovery_continue.jl runtime primal both 300 /tmp/runtime-postsolve-production .superpowers/adaptive-degeneracy/phase-transfer-recovery/runtime-phase-continuation-final.bin
julia --project=. --compile=min diagnostics/adaptive-degeneracy/reproduce/postsolve_hint_semantics.jl
julia --project=. diagnostics/adaptive-degeneracy/reproduce/postsolve_hint_compiled.jl
julia --project=. diagnostics/basis-selective-preparation/reproduce/external.jl diagnostics/basis-selective-preparation/reproduce/external-inputs.toml /tmp/postsolve-hint-external.toml
```

Results and artifact hashes are stored under `results/postsolve-hints`.
Local snapshots, diagnostic prototypes, and logs are retained under
`.superpowers/adaptive-degeneracy/postsolve-hints`. Prototypes are evidence of
rejected alternatives or an isolated hypothesis; they are not production methods.

The production source digest (sorted `Project.toml` and `src/**/*.jl`, each path
followed by NUL and its contents) is
`05cdf44e84749dd1bf94f2d02be60900f06cf95219c64c180eae11504a808725`.

```sh
python3 diagnostics/adaptive-degeneracy/reproduce/validate_postsolve_hints.py
```

The subsequent [fresh whole-MPS verification](postsolve-full-run.md) fails at a
different Phase-I export state. The successful continuation reported here must
not be read as evidence that a fresh runtime solve now completes.
