# Presolve infeasibility and original-space primal tolerance

Base: `2f959b9` on `codex/adaptive-degeneracy`.

## Reproduced mismatch

The previous [pilotnov diagnosis](broad-validation.md#pilotnov-presolve-tolerance-discrepancy)
found a strict reduced-row contradiction of approximately `8.1601392309949e-15`.
A separately computed point passed the original-model primal certificate at
`1e-7`. The [dual pivot correction](dual-pivot-consistency.md) then made both
no-presolve runs finish at verified optima, but ordinary presolve still returned
`INFEASIBLE` before simplex.

The strict presolve proof and the tolerance-based point certificate answer
different questions. This is not evidence that the stored original LP is
feasible over exact rationals. A local allowance on the reduced row is also
insufficient: eliminating variables can multiply or combine the tolerance
allowances of several original constraints.

An independent one-variable regression fixes `x=1` and requires
`x >= 1 + 1/4096` with primal tolerance `1/1024`. The original certificate accepts
`x=1`, and both simplex algorithms with presolve disabled find the accepted
optimum. Before this correction, presolve-enabled solves return `INFEASIBLE` for
Float32, Float64, BigFloat and Rational{BigInt}: **40 passing, 8 failing** checks.
Afterwards the initial regression passes all **64** checks.

## Conservative proof check

The exact presolve passes and the existing `presolve_problem` entry point remain
unchanged. The public solver uses an internal wrapper:

1. Run strict presolve as before. A successful reduction or a zero primal
   tolerance follows the existing path.
2. Only after an `INFEASIBLE` result with positive tolerance, construct a
   proof-only feasibility model from the **original continuous LP**. Its matrix
   is `[A A I]`, its variables are `[z; e_column; e_row]`, and its objective is
   zero. Preserve the original row bounds and the original column bounds on `z`.
   Bound each error variable between `-tolerance` and `+tolerance`.
3. Run strict presolve on that proof model. If it still proves infeasibility,
   retain the original failure.
4. Otherwise discard the failed reductions and return the identity presolve
   result for the unchanged original LP. Simplex and final certification solve
   the original problem, with its original objective, bounds and tolerances.

For any point accepted by the original primal certificate, choose mathematically
`z = clamp(x, column bounds)`, `e_column = x-z`, and
`e_row = clamp(A*x, row bounds)-A*x`. Both errors have magnitude at most the
configured tolerance, and `A*z + A*e_column + e_row` satisfies the original row
bounds. Thus an infeasibility proof for this extended model safely excludes any
accepted original point. Inability to obtain that proof remains inconclusive;
it does not certify feasibility.

The proof model is never optimized, and neither its objective nor its reductions
enter postsolve. This is a numerical certification rule, independent of adaptive
pricing, perturbations or recovery switches. All `2n+m` proof variables are
continuous. The matrix has `2*nnz(A)+m` stored coefficients; this extra work occurs
only after strict presolve reports infeasibility.

Keeping the errors separate avoids adding small tolerances to huge stored
bounds, and avoids bounded-integer rational overflow in such additions. The
lower error bound uses the outer endpoint of the existing `0-tolerance` interval
operation; the upper bound retains the stored tolerance. This also encloses
mixed-precision BigFloat inputs without changing the ambient precision. Existing
strict presolve uses its usual exact internal activity arithmetic; no new solver
precision escalation is introduced.

Deadline checks occur before constructing and before reducing the proof model;
the solver retains its existing check after presolve. Strict presolve itself
still checks deadlines only at its surrounding call boundaries.

### Rejected initial representation

The first version directly expanded the original floating bounds outward. It
passed the original small regression and all 104 real-model jobs, but the wider
semantic suite found **four failures** in `Recession feasibility is certified in
the original model` (`test/dual_simplex_tests.jl`). At bounds near `1e16`, adding
`1e-7` outward widened each endpoint by `2`, unnecessarily preventing an
infeasibility proof. Public status changed from `INFEASIBLE` to `NUMERICAL_ERROR`.
The extended model above fixes that precision loss without weakening those test
expectations. The first semantic run had 15,931 passes and four failures; its log
is retained as `semantics-initial-proof.log`; the first real-model reports
are retained under `initial-*` names. The final
verification below uses only the extended model. The rejected implementation
is retained as `results/presolve-tolerance/initial-proof.patch`, applicable to
`2f959b9`; reconstructing it reproduces the initial production source hash.

## Real pilotnov completion

With ordinary presolve enabled, both reader orders now reach verified optima:

| Reader | Before | After | Refactorizations | Objective |
| --- | --- | --- | ---: | ---: |
| Native | INFEASIBLE / 0 iterations | OPTIMAL / 1806 iterations | 28 | -4497.276188218871 |
| JuMP | INFEASIBLE / 0 iterations | OPTIMAL / 2524 iterations | 34 | -4497.276188218871 |

Both original unscaled and reader-model primal certificates pass, and objectives
match the independent HiGHS reference. The iterations, refactorizations and
objective match the earlier no-presolve controls. No outer original-LP retry is
used. The input hashes, objective references and policy isolation are unchanged.

## Paired external corpus

All **104/104** configurations now reach independently verified original optima:
76 dual and 28 primal. Only the two pilotnov reader configurations change their
outcome. The other **102** retain status, iterations, refactorizations, objective,
phase sequence, diagnostic events and repair coverage exactly. There are no
numerical errors, time limits, harness exceptions or original-LP retry attempts.

The jobs use the same 33-model corpus, both readers, selected permutations and
selected four-manager cases as before. This is a paired regression, not a new
speed benchmark or a claim about every manager/model combination. See
[dual comparison](results/presolve-tolerance/dual-comparison.md) and
[primal comparison](results/presolve-tolerance/primal-comparison.md).

## Separate remaining simplex certificate issue

A strengthened independent binary-relaxation fixture exposed another issue:
`1024*x >= 1024.25`, `0 <= x <= 1`, zero cost, primal tolerance `1/1024`.
The original certificate accepts `x = 1 + 1/4096`. The new presolve proof
correctly becomes inconclusive and hands the unchanged original continuous LP
to simplex, but both algorithms still return `INFEASIBLE`, even with
`presolve=false`: dual at zero iterations (`no eligible dual pivot`), primal at
one iteration (`phase I optimum certifies infeasibility`).

The same dedicated probe on the exact base commit `2f959b9` reproduces both
no-presolve outcomes and the accepted witness. With presolve enabled, that base
rejects the fixture before any phase; the candidate enters the appropriate
simplex phase and then reaches the unchanged core outcome.

The shared `_floating_infeasibility_certified` helper minimizes a row combination
over exact working bounds. It can certify a strict contradiction of `0.25`
without testing the tolerance envelope accepted by the original-point
certificate. Fixing that requires a separate original-space analysis, including
scaling and auxiliary phases. This change does **not** repair that core issue.

The first normal focused run therefore had **1162 passes and one failure**:
its new integration assertion required this counterexample to reach an optimum.
The final integration assertion tests the actual presolve contract instead:
`:phase_dual` occurs and receives the original matrix, objective and bounds.
It does not freeze `INFEASIBLE` as a correct expected result. The tolerance witness,
proof-model checks, initial failed run, and dedicated core probe are all retained.
This limits the completion claim to presolve, rather than hiding the remaining
core inconsistency.

The first isolated baseline environment copied `LocalPreferences.toml` into the
package snapshot but omitted it from the active environment. Cache compilation
then failed with LLVM out-of-memory inside the owned 8 GiB virtual limit. The
active preference file was added, and the successful baseline probe used
`--compiled-modules=no --compile=min`. Its log includes dependency import
warnings caused by disabling caches; the four diagnostic solves completed.
The real-model and normal test environments retained `precompile_workload=false`.
Both the setup failure and successful baseline logs are retained.

## Targeted verification

The final independent tolerance regression passes **199/199** checks under
`--compile=min`, including all four scalar types, both algorithms, row and column
allowances, zero tolerance, conclusive contradictions, sub-ulp tolerances,
large finite bounds, bounded-integer rationals, mixed-precision BigFloat and
stop handling. The strengthened binary-relaxation integration check confirms
that simplex sees the unchanged original LP.

The normally compiled focused runner passes **1180/1180** checks in 4m01.0s,
including the full existing presolve tests and the presolve/solver allocation
budgets.

The expanded semantic runner passes **15,951/15,951** checks in 2m54.2s under
`--compile=min`, including the four original recession-certificate checks that
rejected the first proof representation. No production change was made to
simplex's infeasibility certificate. Independent read-only review of both the
mathematical construction and final code/tests found no blocking issue.

The separate normal-compilation `test/runtests.jl` attempt was terminated by the
300-second wall-time guard (exit 75), in LLVM while compiling the testset at
`test/simplex_strategy_separation_tests.jl:17`. It produced no failed assertion
before termination, but no completed whole-suite summary. This is **not a
full-project pass**. The completed focused runner above verifies the existing
allocation budgets with normal compilation; the larger semantic runner uses
`--compile=min`.

## Reproduction and scope

- `test/presolve_tolerance_tests.jl`: independent public-solve and proof checks.
- `reproduce/presolve_tolerance_core_probe.jl OUTPUT_TOML`: records the separate
  simplex certificate issue for both algorithms, with and without presolve.
- `reproduce/presolve_tolerance_focused.jl`: normal compilation, including existing
  presolve allocation budgets.
- `reproduce/presolve_tolerance_semantics.jl MOD010_BOUNDARY_PREFIX OUTPUT_TOML`:
  presolve/solver regressions and the previous simplex semantic chain, with
  `--compile=min`; use the documented `native-prices/direction-price-removal-boundary`
  snapshot prefix.
- Existing `reproduce/broad_corpus.jl INPUTS REFERENCES JOBS OUTPUT_PREFIX` with
  `results/broad-validation/{inputs,references}.toml` and
  `results/presolve-tolerance/jobs.toml`. The first two jobs are pilotnov.
- Existing `reproduce/compare_dual_corpus.py BASE CANDIDATE OUTPUT`, using the
  `dual-pivot-consistency/dual-models.toml` baseline for dual, and the matching
  `primal-models.toml` baseline with `--algorithm primal` for primal.

Use the existing single-process memory guard, one Julia/BLAS thread, and local
`precompile_workload=false`. Normal-compilation real-model runs use Float64,
steepest-edge, native factorization with interval 80, 90 seconds per case and
1,000,000 iterations. The isolated five adaptive switches and diagnostic
suppression of weak-pivot preference/original-LP retries remain unchanged.

This change does not guarantee that simplex can find every tolerance-feasible
point. An inconclusive presolve proof may require solving a larger original LP,
and may therefore take longer than a conclusive reduced solve. Successful
strict presolve paths do not run the extra proof. Runtime and medium are not
rerun here, and no new convergence claim is made for them.
