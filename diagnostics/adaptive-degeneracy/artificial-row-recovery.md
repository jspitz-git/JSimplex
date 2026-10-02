# Native pivot-row recovery during artificial removal

Base: `0ee115e` on `codex/adaptive-degeneracy`.
This follows the [captured artificial-removal row failure](native-price-recovery.md)
left after correcting native reduced-price reconstruction.

## Cause and bounded change

The seed-1 permutation of mod010 with PFI reached auxiliary optimality at
iteration 272, but could not replace its first remaining basic artificial.
The unit-row solve `B' * rho = e_89` had absolute residual
`8.20051097734489e-17` and componentwise relative residual
`0.05319148936170205`. Every one of the 56 strength-eligible columns was rejected
by unchanged pivot validation because the shared BTRAN row was unreliable.
Correcting the objective dual in `B' * dual = c_B` does not repair this separate
unit-row solve.

The prior diagnostic showed that the existing native cleanup corrected the
row to zero residual. With the corrected row, 33 candidates passed validation;
23 still required refresh because of their FTRAN columns. This was not evidence
that candidate checks should be relaxed.

The production change adds one native recovery opportunity immediately after
the unit-row BTRAN in `_remove_artificials!`. It uses the same ordinary residual
quality criterion as pivot validation. Only an unreliable row, in the supported
native primal kernel with a positive refinement budget, invokes the existing
`_native_cleanup_solve!`. Reliable rows retain their numerical values. The helper
uses a bounded correction and certified homogeneous-term cleanup in the problem's
Float32/Float64 precision. No new correction algorithm or numerical threshold
is introduced.

Prices are then computed from the accepted row. Candidate filtering, FTRAN,
pivot validation, the final `prepare_update=true` solve and its independent
validation, predicted-point checks, refactorization and original-model export
certificates remain mandatory and unchanged. A failed correction ends removal.
The row is local to the private auxiliary workspace; the original numerical
state is adopted only after complete export succeeds. Stop exceptions propagate
and consumed work remains charged even on failure.

There is no adaptive heuristic, pricing switch, tolerance relaxation or precision
increase. Checked/staged policies, workspaces in dual mode, unsupported scalar types and a zero
refinement budget retain their earlier paths.

## Regressions and isolation

The portable six-by-six integer fixture uses an exactly representable unit-row
solution `[1,1,0,0,0,0]`. A duplicate first column supplies the zero basic
artificial. A zero RHS isolates BTRAN reconstruction from primal reconstruction.
The original removal method fails in all eight Float32/Float64 and manager
combinations (eight passing point certificates, eight failed removals).
The corrected implementation removes the artificial in one iteration and
certifies the exported original point and basis.

An initial nonzero-RHS version repaired the row but exposed a separate Float32
export reconstruction failure after the exchange. Its diagnostic log is retained;
the initial `artificial-row-green.log` contains its four Float32 failures.
Using zero RHS prevents that separate limitation from confounding this row test.
The final passing focused log is `artificial-row-final-unit.log`.
No production change was made to the export routine to make this fixture pass.

All 264 focused assertions pass both with normal compilation and with
`--compile=min`. They additionally cover disabled budgets and unsupported
policies, stop and callback exceptions after a correction attempt, rejection
by a stringent pivot certificate, and a successful auxiliary exchange that must
still fail against infeasible original bounds. Rejected export preserves the
original numerical state while retaining the one consumed exchange. Reliable
Float32, Float64 and exact rational rows also succeed with no refinement budget
and no correction events.

The broader semantic runner passes **9,653 assertions**, followed by eight
captured-boundary assertions, with `--compile=min`. These counts include overlap
between existing runners and are not a count of distinct tests.

A normal-compilation attempt of the full project entry point,
`julia --project=. test/runtests.jl`, was bounded to 300 wall seconds. The guard
terminated the owned process group (exit 75) while LLVM was compiling a call
from `test/native_primal_completion_tests.jl:3`. The saved stack trace records
LLVM instruction scheduling. The project suite did **not** complete; neither
the focused results nor the partial project attempt establish a full-suite pass.
The interrupted test file was then run separately with `--compile=min`; all
2,072 assertions passed. Its reproducer is:

```sh
julia --project=. --compile=min -e 'using Test,JSimplex; include("test/native_primal_completion_tests.jl")'
```

The production-only saved mod010 boundary had three passing checks and one failed
removal before the change. It now passes all eight checks, removing both
artificials and exporting a certified original point at iteration 274.

## Whole-model verification

The same 30 configurations as the preceding price-recovery report are run from
fresh models, with their earlier results retained as the comparison arm. The
seed-1 mod010/PFI model now reaches a verified optimum in 598 iterations instead
of failing artificial removal at 272. This is a complete solve from MPS,
not only a captured-boundary continuation.

All configurations retain Float64, steepest-edge, native refactorization every
80 updates, relaxed integrality, 90 seconds and 1,000,000 iterations per case.
Only stagnation monitoring, adaptive pricing, primal/dual perturbations and
Phase I are enabled; the separate weak-pivot preference and original-LP restart
remain disabled diagnostically. Native safeguards stay active. Model equivalence
under native/JuMP/permuted reading, original unscaled feasibility and objective
agreement with the independent HiGHS references are checked by the existing
corpus runner. Compilation and diagnostics are included in recorded timings;
these are not performance measurements. Runtime and medium are not rerun here.

The selected batch now has **21 verified optima and nine numerical errors**,
compared with 17 optima and 13 numerical errors on the base commit. There are
no time limits or harness exceptions. Besides mod010 seed 1/PFI, the newly solved
cases are native degen2 (1,034 iterations), JuMP degen2 (1,031) and native misc07
(263). Their objectives are respectively -1435.178, approximately -1435.178,
and 1415.0, with verified original primal feasibility.

The 24 unchanged configurations retain status, iteration/refactorization counts,
phase sequence and objective exactly. Native and JuMP degen3 now complete 22
and three artificial exchanges, reaching iterations 2,367 and 2,894 before
removal still fails. Their next failure has not been attributed to the repaired
row without a separate probe. The seven other numerical errors are unchanged:
mod010 seed 1 with FT/SS, native boeing1, both p0201 readers, native cycle and
JuMP stocfor2. See [the paired individual outcomes](results/artificial-row/models.md).

Final production source SHA-256:
`6500645441568dfbee1cc3d20e2cc952fb3b223fc5a62948a92e8a6c006de9af`.

## Reproduction and provenance

Use the established 8 GiB virtual-memory wrapper and owned-process guard, with
one Julia and one BLAS thread. Run numerical processes serially. Preserve local
`precompile_workload=false`; no local environment manifests are committed.

- `test/native_artificial_row_tests.jl` is included by the project test runner.
- `reproduce/artificial_row_fixture_probe.jl` reconstructs and traces the initial
  nonzero-RHS fixture, retaining the separate Float32 export limitation.
- `reproduce/artificial_row_regression.jl BOUNDARY_PREFIX OUTPUT_TOML` replays the
  production removal path without numerical overrides.
- `reproduce/artificial_row_semantics.jl BOUNDARY_PREFIX OUTPUT_TOML` adds the
  related semantic suites, run with `--compile=min`.
- `reproduce/broad_corpus.jl INPUTS REFERENCES JOBS OUTPUT_PREFIX` runs the real
  models using the same local JuMP environment and recorded jobs as before.

The boundary prefix is locally
`.superpowers/adaptive-degeneracy/native-prices/direction-price-removal-boundary`;
its binary paths and checksums are recorded in `results/native-prices/captures.json`.
New text results and reproducible inputs are retained under
`results/artificial-row`; any new binary snapshots remain local with hashes.
