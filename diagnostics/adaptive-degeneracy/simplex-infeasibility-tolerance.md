# Simplex infeasibility certificates and primal tolerance

Base: `ada39e9` on `codex/adaptive-degeneracy`.

## Reproduction and cause

The [presolve investigation](presolve-tolerance.md) left an independent core
counterexample: `1024*x >= 1024.25`, `0 <= x <= 1`, zero objective, and
`primal_tolerance = 1/1024`. The original certificate accepts
`x = 1 + 1/4096`, but both simplex algorithms report `INFEASIBLE`, even without
presolve. The strict model is inconsistent; its configured tolerance envelope
is not.

The floating row-combination certificate enclosed roundoff but minimized over
exact working bounds. Primal phase I used the same helper for floating types,
and a separate exact-bound helper for rational types. Rational dual simplex did
not check this row-combination certificate before declaring infeasibility.

## Correction

For a row multiplier `y`, write `q = [A' * y; -y]` for the structural and row
activity coefficients. If `m` is a lower bound on the minimum of `q' * z` over
the stored bounds, the minimum over bounds relaxed by allowances `delta[j]`
is bounded below by `m - sum(abs(q[j])*delta[j])`. Infeasibility requires this
lower bound to be strictly positive. Otherwise the proof is inconclusive.

Use the configured tolerance in original units. This repository stores
`x_work = column_factor*x_original` and
`activity_work = activity_original/row_factor`, so the respective allowances
are `tolerance*column_factor` and `tolerance/row_factor`. Artificial columns
appended in auxiliary workspaces retain their working-unit allowance. The
primal terminal checks use the original-dimension workspace, not artificial
bounds. Reduced-model failures already go through the existing original-LP
retry before publication by the public solver.

The floating helper encloses coefficient magnitude, allowance multiplication,
subtraction and accumulation outward in the existing scalar precision. It
subtracts a separate penalty rather than adding tolerance to stored bounds,
which preserves sub-ulp allowances next to large bounds. Nonfinite penalties
are inconclusive. The rational implementation performs exact operations in its
existing type; bounded-integer overflow is caught only inside the proof and
also makes it inconclusive. No precision escalation is introduced.

Both dual simplex and the two primal phase-I implementations now use this
shared proof. This is a core certification rule independent of adaptive
pricing, perturbations or recovery policy. It runs only at the existing
infeasibility decision; pivot selection and ordinary iterations are unchanged.

## Scope

Rejecting an invalid infeasibility certificate is not a feasible-point search.
The solver may return `NUMERICAL_ERROR` for an inconclusive proof even though a
tolerance-feasible witness exists. This change does not enlarge the stored LP
bounds or claim to solve that remaining feasibility-recovery problem. Runtime
and medium convergence are not established by this change.

## Reproduction

Use the existing guarded Julia wrapper with one Julia/BLAS thread and
`precompile_workload=false`. Keep the 8 GiB virtual-memory limit, 6 GiB available
RAM floor, and 1 GiB swap ceiling.

- `test/simplex_infeasibility_tolerance_tests.jl`: independent proof/public-solve
  regressions, including both signs, row and column scaling, both primal phase-I
  implementations, exact zero tolerance, boundary equality, unbounded columns,
  mixed-precision BigFloat, subnormal allowances and bounded-rational overflow.
- `reproduce/simplex_infeasibility_focused.jl`: normal-compilation regression.
- `reproduce/simplex_infeasibility_semantics.jl PREFIX OUTPUT_TOML`: expanded
  semantic chain with `--compile=min`; use the existing
  `native-prices/direction-price-removal-boundary` snapshot prefix.
- `reproduce/presolve_tolerance_core_probe.jl OUTPUT_TOML`: public status probe.
- `reproduce/broad_corpus.jl INPUTS REFERENCES JOBS OUTPUT_PREFIX`: paired
  real-model corpus, using `results/broad-validation/{inputs,references}.toml`
  and the unchanged `results/presolve-tolerance/jobs.toml`.

## Verification history

The first independent proof regression failed on the unchanged base with
42 passes and 16 failures (`red.log`). The initial correction passed 74
proof/public checks (`green.log`). The first expanded semantic run completed
15,951 pre-existing checks successfully but had one new test setup error:
floating solver options reject zero tolerance. The zero-tolerance case was
restricted to rational arithmetic; no solver validation was weakened. That
run is retained as `semantics-invalid-zero-tolerance.log`.

Read-only review identified the bounded-rational overflow case. The added
regression reproduced `OverflowError` at the penalty subtraction; the other
147 expanded checks, including mixed BigFloat rounding and subnormal mapped
allowances, passed (`overflow-red.log`). The final proof catches only this
arithmetic overflow and remains in the original scalar type. Final read-only
review found no further blocking issues.

The first normal-compilation focused runner completed the new regression and
entered the original primal tests, but its 300-second guard terminated LLVM
compilation at `test/primal_simplex_tests.jl:171` (selectable factorization
backends). There was no assertion failure before the cutoff. This is not a
completed focused-suite pass; its log is retained as `focused.log`.

## Paired real-model validation

All **104/104** real-model configurations reach independently verified optima:
76 dual and 28 primal. All 104 preserve status, objective, iteration count,
refactorizations, phase sequence, diagnostic events and repair coverage exactly
relative to `ada39e9`. No original-LP retry is attempted. Both pilotnov readers
remain optimal (1806 native / 2524 JuMP iterations).

The corpus is the unchanged 33-model set, with native/JuMP reader orders,
selected permutations and selected cases across all four basis managers. Both
original and reader-model primal certificates pass, and objectives match the
independent HiGHS references. This validates terminal-rule integration without
claiming a speed improvement. The existing isolated adaptive policy and
suppression of weak-pivot preference/original retries are unchanged.

See [dual comparison](results/simplex-infeasibility-tolerance/dual-comparison.md)
and [primal comparison](results/simplex-infeasibility-tolerance/primal-comparison.md).

## Final semantic and public-status verification

The final expanded semantic run passes **16,099/16,099** checks in 2m59.1s
with `--compile=min`: 148 new checks plus the unchanged 15,951-check semantic
chain. Both legacy and general primal phase I, rational/float dual proofs,
zero rational tolerance, strict contradictions and tolerance-boundary cases
are covered. The completed normally compiled external corpus uses the same
final source as this semantic run.

The dedicated public probe confirms the original witness remains accepted.
With and without presolve, dual now returns `NUMERICAL_ERROR` at zero iterations
(`row combination does not certify infeasibility at primal tolerance`), and
primal returns `NUMERICAL_ERROR` at one iteration (`phase I infeasibility
certificate is inconclusive`). Neither returns the previous false `INFEASIBLE`.
No tolerance-feasible witness is returned by these four solves. The next
separate core task is a bounded feasibility recovery that can find and certify
such a point without changing original bounds or weakening final certificates.

The final production SHA-256 is
`40d6fa0140556827f9e353987417296ef513e64c0618ea4afa3fcc8bddcb3718`.

## Main suite: pre-existing legacy test failures

The final normal-compilation `test/runtests.jl` attempt hit the 300-second guard
(exit 75) during Julia code generation in
`test/simplex_strategy_separation_tests.jl:78`. Before that cutoff it recorded
**23 assertion failures and 2 test errors** in these existing testsets:

- `Bound snapping checks each tolerated violation independently`: 16 failures.
- `Legacy primal rejects an unsafe sole pivot without mutating the basis`:
  2 failures and 1 error.
- `Legacy primal accepts a tolerated bound snap that stays feasible`: 1 failure.
- `Legacy primal tries another entering variable before failing a ratio test`:
  1 failure.
- `Legacy primal does not report optimality after exhausting unsafe candidates`:
  2 failures and 1 error.
- `Legacy primal searches beyond eight unsafe entering candidates`: 1 failure.

These are **not regressions from this certificate change**. Isolating
`primal_bound_snap_tests.jl` and `primal_candidate_retry_tests.jl` gives exactly
**297 passes, 23 failures and 2 errors** both on the final candidate and on an
exact source snapshot of base `ada39e9`. Failure locations and evaluated values
match the full-suite log as well. The baseline source hash matches
`63a1d98176bd2b626eeeaad17b820cbaedd34a5e58d3d80d66f828cf7b5e8d69`.

The baseline uses an isolated active environment and snapshot, both retaining
`precompile_workload=false`, with `--compiled-modules=no --compile=min`; its
log contains dependency import warnings. Candidate controls use `--compile=min`.
The matching full-suite failures use normal compilation. No old worktree or
local environment was modified for this check.

A separate five-case point probe covers the sole-small/sole-unit pivot and
one/two/nine-candidate fixtures. All five accepted pivots retain original
feasibility, verified both by the unchanged solver certificate and independent
exact-rational evaluation of the stored floating point. Row residuals are
exactly zero; the retained column violation is approximately `7e-8`, below
`1e-7`. Thus rejection of those pivots is no longer required for feasibility.
The two test errors dereference `terminal.status` when a valid pivot returns
`nothing`. This indicates stale trajectory/rejection expectations in the
sampled cases, not an observed infeasible point. A complete rewrite/audit of
these older tests remains separate; none of their expectations were relaxed
in this change.

See `legacy-comparison.json`, `legacy-base.log`, `legacy-candidate.log`,
`full-suite.log`, and `legacy-points.toml` in the result directory. Reproduce the
controls using `reproduce/simplex_infeasibility_legacy_checks.jl`; reproduce the
independent point checks with
`reproduce/simplex_infeasibility_legacy_points.jl OUTPUT_TOML`.
This is **not a whole-project test pass**.
