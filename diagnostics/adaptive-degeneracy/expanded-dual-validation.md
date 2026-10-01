# Dual PFI verification on the complete 33-model corpus

Source commit: `14f04a8`, with production digest
`90207a20d1dfa07cf548706f456191f31401f4dd98907342db138a2a9149e8a0`.
This extends the [nine-model paired dual check](dual-corpus-validation.md).
There is no production-code change in this verification.

## Scope and controls

The original broad-validation input manifest contains 33 models. Excluding the
nine models just verified leaves 24 models, run through both native and JuMP
readers: **48 fresh whole-model runs**. The 18 native/JuMP dual PFI records from
the earlier nine-model run are reused only after checking identical production
source, instrumentation, policy, Julia/JuMP versions and thread settings. The
combined report has exactly one native and one JuMP record for each model:
**66 configurations over 33 models**, not 66 independent LPs.

The unchanged `broad_corpus.jl` harness checks input hashes and exact equivalence
of reader models after mapping rows and columns by name. A verified optimum
requires an OPTIMAL status, primal feasibility in both the reader model and the
original unscaled model, and an objective match to the existing independent
HiGHS reference (`rtol=1e-8`, `atol=1e-7`). Integrality is relaxed.

All new jobs use Float64, dual simplex, PFI, steepest-edge pricing, native
refactorization every 80 updates, a 1,000,000-iteration limit and 90 seconds per
model. Only stagnation monitoring, adaptive pricing, primal/dual perturbations
and Phase I are enabled among the numerical switches. The separate weak-pivot
preference and original-LP retry remain disabled diagnostically. Other adaptive
features, higher precision and optional feasibility recovery remain disabled.

The process uses normal compilation, Julia 1.13.0, one Julia/BLAS thread,
`precompile_workload=false`, the established 8 GiB virtual-memory limit,
6 GiB available-RAM floor and 1 GiB swap ceiling. The whole-process wall guard
is 5100 seconds, allowing all per-model budgets and compilation. Only one
numerical process runs at a time. No excluded large model is solved or factored.

## Main results

| Group | Configurations | Verified OPTIMAL | Presolve INFEASIBLE | Numerical errors | Time limits |
| --- | ---: | ---: | ---: | ---: | ---: |
| New 24 models | 48 | 46 | 2 | 0 | 0 |
| Earlier nine models, native/JuMP PFI only | 18 | 18 | 0 | 0 | 0 |
| Combined 33 models | 66 | 64 | 2 | 0 | 0 |

Both readers therefore have **32/33 verified optima**. There are no harness
exceptions, failed optimal-point certificates or original-LP retry attempts.
Peak RSS of the new corpus process is about 2258 MiB; no guard fires. The largest
relative objective error in the new runs is `3.195920916195531e-13`.
See [all 33 paired reader outcomes](results/dual-expanded/summary.md), the
machine-readable `summary.json`, and the full `models.toml`/`models.log` reports.

The more degenerate models that previously exhausted the primal time budget
also solve with dual PFI in this run:

| Model | Native iterations | JuMP iterations |
| --- | ---: | ---: |
| air04 | 4483 | 4483 |
| air05 | 1469 | 1469 |
| 10teams | 1505 | 1505 |

This is evidence of successful dual solves, not a controlled current primal-vs-dual
speed comparison. The earlier primal results used an older revision. These
runs do not establish current primal convergence on those models.

## Remaining presolve discrepancy

`pilotnov` is rejected with `INFEASIBLE` before any simplex phase or iteration:
`row 21 contradicts current column bounds` with the native reader, and row 290
with JuMP. No simplex workspace exists at these endpoints. The harness names
potential failure-snapshot paths but does not write a snapshot; `captures.json`
explicitly distinguishes these placeholders from existing files.

This reproduces the [previously diagnosed presolve tolerance discrepancy](broad-validation.md#pilotnov-presolve-tolerance-discrepancy).
The presolve sources are unchanged since `cfbaf3f`, which recorded that diagnosis.
The earlier independent reference point passed the original-model check at
`1e-7`, whereas a strict exact-rational activity-bound comparison of the reduced
floating-point model found a gap of approximately `8.16e-15`. This does not prove
exact rational feasibility of the original input. It does establish that a
presolve tolerance-policy issue remains separate from these dual iterations.

## Reproduction and limits

Run the existing `broad_corpus.jl INPUTS REFERENCES JOBS OUTPUT_PREFIX` through
the existing guarded Julia wrapper and broad-validation environment. Use the
input/reference manifests from `results/broad-validation` and the new
`results/dual-expanded/jobs.toml`.

Then combine results with:

```text
python3 diagnostics/adaptive-degeneracy/reproduce/summarize_expanded_dual.py \
  diagnostics/adaptive-degeneracy/results/dual-corpus/candidate.toml \
  diagnostics/adaptive-degeneracy/results/dual-expanded/models.toml \
  diagnostics/adaptive-degeneracy/results/broad-validation/inputs.toml \
  diagnostics/adaptive-degeneracy/results/dual-expanded/summary
```

The summary checks all expected model/reader pairs, source and policy equality,
input identities and certificate flags. It retains the report of origin for each
record instead of presenting the nine-model results as new runs. Provenance
hashes and the 48-job manifest are retained alongside the reports.

This is a selected external dual PFI corpus with isolated adaptive settings,
not a full-default-policy test, a full unit-suite pass, or validation of all
basis managers. No local/component phase-transfer reconstruction is entered in
the new 48 runs. `runtime.mps` and `medium.mps` are not included, and their
convergence is not claimed. The successful bounded runs expose no new dual
numerical failure to repair; they do not establish universal robustness.

## Separate pilotnov control without presolve: a new core failure

To distinguish the presolve rejection from simplex behavior, two additional
controls change **only `presolve=false`**. They are excluded from the 66-case
main summary. The guarded runner is `reproduce/broad_without_presolve.jl`, with
the same four arguments as `broad_corpus.jl`; the two jobs are retained in
`results/dual-expanded/pilotnov-no-presolve-jobs.toml`. Its output explicitly
records `presolve=false` and the modified diagnostic runner hash. The guard for
these two-job controls is 600 seconds, with the same memory thresholds.

Both controls terminate with `NUMERICAL_ERROR`, reporting a singular native
factorization: native reader at iteration **164**, JuMP at **142**. Fresh
factorization of both captured terminal bases also fails. Each has 975 distinct
basic indices, so this is not a duplicated basis-column index. Independent SVD
shows near-zero singular values, but SVD alone is not used as an exact rank proof.

An observational rerun audits fresh factorization before and after each accepted
dual pivot. It reproduces both termination iterations, messages, refactorization
counts, phase sequences and diagnostic-event counts exactly. The first
unfactorable proposed bases are created by the following accepted pivots:

| Reader | Completed iterations before pivot | FTRAN pivot | BTRAN tableau coefficient | Entering index |
| --- | ---: | ---: | ---: | ---: |
| Native | 163 | `1.4459312478093505e-6` | `-1.52587890625e-5` | 191 |
| JuMP | 141 | `-5.235008835211553e-8` | `2.384185791015625e-7` | 191 |

In each case fresh native factorization succeeds before the pivot and fails
afterwards. The forward and transpose estimates have **opposite signs**.
The dual path with optional pivot validation disabled performs a direction
residual test, but ordinarily
has no mandatory forward/transpose pivot-agreement check. Such an agreement
check is reached only through optional checked-pivot validation or a failed
residual followed by a native direction correction. Consequently the ordinary
acceptance path can admit this contradictory pair.

Exact rational rank diagnosis independently confirms the damaging basis change.
Eliminating nonzero singleton rows/columns preserves nonsingularity and reduces
the 975-coordinate matrices to small cores. Exact LU on their Float64 values
converted to `Rational{BigInt}` yields:

| Reader | Core before | Exact before | Core after | Exact after |
| --- | ---: | --- | ---: | --- |
| Native | 72 | nonsingular | 76 | singular |
| JuMP | 68 | nonsingular | 68 | singular |

Thus the exact pivot for these captured matrices is zero, although the native
FTRAN supplied a value above the solver cutoff. This is a demonstrated numerical
safety gap in the dual core, not evidence that a degeneracy heuristic is missing.
All solver runs remained Float64; exact arithmetic was used only for this
independent diagnostic. No tolerance, precision policy or production code was
changed, and no fix is claimed.

Diagnostic scripts and retained evidence:

- `pilotnov_basis_probe.jl OUTPUT_TOML SNAPSHOT...`: fresh native factorization
  and independent singular values of the saved terminal bases (300-second guard).
- `pilotnov_pivot_audit.jl INPUTS REFERENCES JOBS OUTPUT_PREFIX`: observes accepted
  pivots during the no-presolve controls (600-second guard).
- `pilotnov_exact_basis.jl OUTPUT_TOML PIVOT_SNAPSHOT...`: singleton elimination
  and bounded exact rank diagnosis (300-second guard).
- `pilotnov-no-presolve.*`, `pilotnov-audit.*`, `pilotnov-audit-pivots.toml`,
  `basis-probe.*` and `exact-basis.*` retain the results. Binary hashes are in
  `pilotnov-captures.json`; binary files remain local.

The pivot snapshots contain the actual matrices and direction. The separately
saved workspace at the audit hook is an observation **during** pivot publication:
primal/dual values have already changed while the basis indices have not. It is
not a restart-safe pre-pivot workspace and must not be used as one.

The next focused repair should prevent publication of an inconsistent dual pivot,
using native-precision verification/correction and the bounded retry machinery.
It needs an independent regression plus these two no-presolve reproductions;
merely adding more rejection counts or declaring the presolve discrepancy fixed
would not resolve the observed core failure. The main 64/66 result and these two
separate core failures must remain distinct.
