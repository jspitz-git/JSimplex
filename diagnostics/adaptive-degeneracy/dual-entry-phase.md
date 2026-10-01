# Preserve the actual simplex algorithm during dual entry and cleanup

Base: `a7f1fac` on `codex/adaptive-degeneracy`.
This addresses the remaining JuMP-reader `stocfor2` failure after
[driver local reconstruction](driver-local-reconstruction.md).

## Cause

The isolated corpus reported `primal feasibility lost` at iteration 1957.
Observational captures reproduce that endpoint and show that the final
presolved/scaled point is still fully certified: its 1852-by-1719 working model
has zero reported primal and dual infeasibility. The failed point belongs to
the **original** 2157-by-2031 model, with no additional pivot and two additional
refactorizations. Its restored basis is dual feasible but primal infeasible
(reported violation about 9951.41).

`cleanup_original` correctly chooses dual cleanup when projection cannot supply
a usable primal basis. However, the workspace inherits `algorithm=:primal` from
the user's main solve. `_solve_continuous_dual!` previously retained this option.
After dual initialization, the original-objective driver therefore dispatched
primal simplex from an infeasible basis when optional feasibility recovery was
disabled. The error was a phase-dispatch defect, not a failed final primal pivot.

The first instrumented capture inadvertently re-enabled the separate weak-pivot
preference by re-including primal source. Its endpoint differed and it is not
used as evidence. The retained capture explicitly reapplies and verifies the
same pricing-isolation hash as the baseline, then reproduces iteration 1957.
The snapshot probe hashes CSC storage arrays, avoiding a dense traversal of a
sparse matrix under minimal compilation.

## Core correction

The explicit dual entry temporarily installs `algorithm=:dual`. Its existing
initialization, solve, exception handling and recovery all run under that
context. An outer `finally` restores the caller's original options on success,
limits and exceptions. Numerical policy, tolerances, precision and budgets are
unchanged.

The direct original-cost primal cleanup inside the legacy dual path bypasses
the shared phase driver. It now temporarily installs `algorithm=:primal` as well,
so native primal point safeguards remain active after the dual-entry correction.
Its nested `finally` restores the dual context before the outer entry restores
the caller's settings. This does not add an adaptive intervention or change
which method the existing cleanup flow requests.

## Independent regressions

A one-variable LP, minimize `x` subject to `x >= 1`, starts with a dual-feasible,
primal-infeasible slack basis and inherited primal options. It must complete
one dual pivot, including when entered through `cleanup_original`. Before the
fix, 70 of 126 assertions failed; after it, all 126 pass. These tests span
Float32, Float64, BigFloat and exact rationals, with all four Float64 managers,
and preserve the caller's already-consumed iteration budget and policy.

A second test introduces a valid working-cost shift after a completed dual
pivot, after entry has excluded the adaptive driver path. Restoring original
costs then requires a real primal cleanup. Without the nested phase scope, four
of its initial 14 assertions fail because cleanup retains dual options and
primal guards are disabled. Tests also cancel or throw inside this primal phase
and check that both nested option scopes are restored. Separate cases cover an
exhausted iteration budget, immediate cancellation, callback exceptions and
numerical exceptions from observers.

## Reproduction and full-input check

Keep one numerical process, one Julia and BLAS thread, and the established
8 GiB virtual-memory guard with a 6 GiB available-RAM floor and 1 GiB swap
ceiling. Preserve local `precompile_workload=false` and do not commit manifests
or binary captures.

- `reproduce/stocfor2_point_capture.jl INPUTS REFERENCES JOBS OUTPUT_PREFIX`
  uses the same arguments as `broad_corpus.jl`, adding bounded point snapshots.
  Reproduce the original failure on the base commit.
- `reproduce/stocfor2_point_probe.jl SNAPSHOT...` reports model dimensions,
  feasibility, basis and sparse-model identity for the saved boundaries.
- `test/dual_entry_phase_tests.jl` runs portable entry and cleanup regressions.
- `reproduce/dual_entry_regression.jl` also runs neighboring postsolve-cleanup
  tests with individual summaries under normal compilation.
- `reproduce/dual_entry_semantics.jl MOD010_BOUNDARY_PREFIX OUTPUT_TOML` adds
  phase, postsolve, driver and precision-entry coverage to the previous semantic
  runner, using `--compile=min`.
- The complete paired jobs and original targeted job are under
  `results/stocfor2-point`; snapshots remain local with recorded SHA-256 hashes.

The fresh targeted JuMP `stocfor2` solve now reaches **OPTIMAL in 2322 iterations**,
with 34 refactorizations. Objective `-39024.40853788206` matches the independent
HiGHS reference `-39024.40853788211`; both reader-model and original unscaled
primal certificates pass. No original-LP retry occurs.

Production source SHA-256:
`90207a20d1dfa07cf548706f456191f31401f4dd98907342db138a2a9149e8a0`.

## Verification scope

The first combined normal-compilation runner (new tests, postsolve cleanup,
postsolve hints) reached its 300-second guard in `postsolve_hint_tests.jl:17`.
Its termination stack is in Julia compiler type inference and garbage collection,
not a reported failing assertion. This incomplete combined run is not counted as
a complete pass. The hint tests are included in the broader semantic runner
under minimal compilation, while the smaller normal runner above isolates the
new tests and adjacent cleanup tests.

## Paired external results

The final paired corpus has **30 verified optima out of 30**, versus 29 optima
and one numerical error on the base. JuMP `stocfor2` is the only changed case;
the other 29 configurations retain status, iterations, refactorizations, phase
sequence and objective exactly. There are no time limits, harness exceptions or
original-LP retry attempts. See [all paired outcomes](results/stocfor2-point/models.md).

The corpus retains the same Float64, steepest-edge, native refactorization every
80 updates, 90-second model limit and 1,000,000-iteration limit. Stagnation,
adaptive pricing, primal/dual perturbations and Phase I are the only enabled
adaptive switches. The separate weak-pivot preference and original-LP retry
remain disabled diagnostically. Native, JuMP and permuted reader orders are
represented; this selected set does not establish general simplex convergence.
Runtime and medium are not rerun for this phase-dispatch correction.

The expanded semantic runner passes **11,402 assertions** with `--compile=min`,
including the new phase-context tests, postsolve cleanup/hints, driver and
precision-entry tests, and the previously established semantic chain. Counts
include overlap between existing runners rather than distinct tests. Independent
read-only review confirmed both option scopes and their exception handling.
This is not a complete project-suite pass; the previously documented full-suite
compilation limits remain, and the new combined normal run above is incomplete.

The smaller normal runner also reached its 300-second guard (exit 75), this time
in `postsolve_cleanup_performance_tests.jl:71`, with no failing assertion printed.
Its short termination log does not distinguish compilation from execution at
that location. Neither normal unit-test attempt is counted as a completed pass.
All 30 external model runs and the targeted stocfor2 run used normal compilation
and completed successfully; the completed 11,402-assertion semantic run used
`--compile=min`. The production source digest was checked against the final
paired results after all edits.
