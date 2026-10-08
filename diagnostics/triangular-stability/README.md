# Stable row-spike elimination in FT and SS

## Reproduction and cause

Baseline: `136b55d6c4cd1acb1c4a7b96d2f3e5d46dfc357d`.
Both public Forrest–Tomlin and Suhl–Suhl updates eliminate a moved row against
unchanged upper-factor rows. Previously they always divided by the current
upper diagonal, even when the moved-row coefficient was much larger. This
could store huge multipliers and upper coefficients in a well-conditioned
final basis. The Bartels–Golub implementation already uses row pivoting.

A portable two-row example starts from the identity, replaces column 1 with
`[tiny, 1]`, and column 2 with `[1, 1]`. For `tiny = 1e-16`, the final basis has
condition number below 3, but the old FT/SS normalized residual reaches 1/3
and the upper factor reaches 1e16. BG stays at rounding accuracy. The first
basis in this sequence is ill-conditioned; the error persists after it is
replaced by the well-conditioned basis. With `tiny = 1e-8`, above the normal
factor update pivot threshold, the old residual already reaches 2.04e-9.

The initial portable Float32/Float64/BigFloat regression failed 24 of 84 checks
on the baseline and passed after the repair. `reproduce/small.jl` records the
Float64 comparison against fresh LU without a simplex trajectory.

## Repair

During row-spike elimination, interchange the current upper row and the moved
row when the finite moved-row coefficient has greater magnitude than the finite
diagonal. Eliminate after the interchange. This bounds each finite elimination
multiplier by one. Retain a swap even if its subsequent multiplier is zero.
Invalid nonfinite/zero-diagonal cases continue through existing failure checks.

Record swapped row indices alongside the elimination history. Replay swaps
before forward eliminations, and after reversed transposed eliminations.
The composed dense cache incorporates swaps in its physical-coordinate map;
indexed-vector application preserves support through the same operations.
Row interchanges invalidate the optional row-incidence index for the remainder
of that update. SS also updates columns beyond the shortened rotation endpoint.

All three history arrays are recycled under the existing shared-prefix ownership
rule. An initial optional-union representation caused a 32-byte allocation per
update on some paths. A concrete recycled integer vector removed that regression;
the original allocation budgets were not relaxed. Existing constructor arities
remain usable. There is no precision promotion, additional refactorization,
residual correction, or change to simplex candidate selection in this repair.

## Validation protocol

- Directed tests cover multiple swaps in one update, SS trailing columns,
  zero-diagonal swaps without elimination, dense/compiled/indexed forward and
  transpose application, exact rational arithmetic, copied histories and reuse.
- Fixed-history replay uses the preserved interval-sweep harness and its exact
  input hashes, with only scheduled refactorizations. Entering-column FTRAN,
  dense FTRAN and unit-vector BTRAN are checked against independent fresh LU
  every 80 exchanges and at the final exchange. Thresholds remain 1e-10 for
  normalized residual and 1e-6 for relative solution difference.
- Baseline and repaired public SS replay the same runtime history; baseline and
  repaired direct SS replay the same fast0507 history. Other affected manager
  and backend arms use the same preserved histories. Direct managers remain
  experimental; their harness source is not merged into production.
- Broader semantic tests, external LP relaxations, and full dual runtime solves
  run sequentially with one Julia/BLAS thread and the existing 8 GiB VM,
  6 GiB available-RAM and 1 GiB swap guards.

Raw attempts, including the failing baseline and allocation-regression attempt,
are retained in `.superpowers/triangular-stability`. No old histories or snapshots
are overwritten.

## Fixed-history results

Each replay contains all 2,560 recorded exchanges and 96 independent probes.
Seven repaired replays passed all 672 probes. These are the same basis sequences
as the preserved histories, not different simplex trajectories. At interval
1600 there is exactly one scheduled refactorization; at 320 there are seven.

| Manager/backend | History | Interval | Maximum normalized residual | Result |
| --- | --- | ---: | ---: | --- |
| Baseline direct-suhl_suhl-native | fast0507-1000 | 320 | 4.476e-10 | fail |
| Baseline suhl_suhl-native | runtime-40000 | 1600 | 1.972e-07 | fail |
| direct-forrest_tomlin-native | runtime-40000 | 1600 | 3.072e-14 | pass |
| direct-suhl_suhl-native | fast0507-1000 | 320 | 4.799e-15 | pass |
| direct-suhl_suhl-native | runtime-40000 | 1600 | 5.671e-14 | pass |
| forrest_tomlin-markowitz | runtime-40000 | 1600 | 1.620e-14 | pass |
| forrest_tomlin-native | runtime-40000 | 1600 | 3.787e-14 | pass |
| suhl_suhl-markowitz | runtime-40000 | 1600 | 1.103e-14 | pass |
| suhl_suhl-native | runtime-40000 | 1600 | 2.843e-14 | pass |

The baseline SS runtime replay first fails at exchange 1120; the baseline direct
SS fast0507 replay first fails at sampled exchange 640. The repaired factors
pass those points and all later sampled checks. All recorded repaired finite
multipliers have magnitude at most one. Timing here includes diagnostics and
fresh-LU reference work; it is not a solver speed benchmark.

The repaired public implementation is also used by the preserved direct-factor
harness. This verifies that shared code path; it does not promote the direct
prototypes or change their experimental status. Compact provenance, memory and
probe summaries are in `results/replays.json`. Other histories and intervals
are not claimed to have been exhaustively recertified by this repair.

### Provenance conventions

Replay report digests hash `Project.toml` and `src/**/*.jl`, with relative path,
NUL and file bytes, sorted as Julia strings. The Python runner's pinned digest
sorts `Path` objects and therefore has a different traversal order. Both were
independently verified against the corresponding source bytes. Baseline process
metadata pins the repaired launcher workspace; the baseline **report** digest
identifies the executed master project. These are different roles, not identical
hash conventions. The compact replay summary retains the report digests.

## Validation startup attempts

Three standalone SS runtime attempts were interrupted before any solver startup
or iteration message, after approximately 641, 396 and 345 seconds. The first
used a direct public call; the second isolated the public call with `invokelatest`;
the third used the diagnosed entry point. Each retained attempt exited 143 after
an explicit signal to its verified owned process. None produced a result report,
and none is counted as a completed numerical solve. A supported one-second Julia
profile was requested in the first attempt; its `-g0` frames were unnamed and did
not establish an exact root cause. No RAM/swap/VM guard triggered in these attempts.

The subsequent numerical validation warms FT and SS on afiro (primal and dual)
in the same process, then solves runtime with unchanged numerical settings,
`verbose=false`, `-g1`, and a diagnostic observer recording event counts and maximum
completed primal magnitude. Those startup and logging differences are explicit;
this is a correctness check, not a cold-start or speed comparison. The interrupted
cold-start behavior remains separate from the row-spike numerical repair.

The independent stored-factor application in
`../numerical-guard-repair/reproduce/ss_replay_probe.jl` now also honors recorded
row swaps. At fast0507 exchange 640, applying the repaired stored Float64 factors
in 256-bit precision gives normalized residual 8.82e-16; native probes through
that diagnostic prefix stay below 2.84e-15. Higher precision is diagnostic only.

## Completed regression checks

The final directed regression passes 380 checks, including native and Markowitz
refactorization, Float32/Float64/BigFloat, exact rational operations, multiple
swaps, shortened SS updates, zero-multiplier swaps, sparse support, compiled
application, copy ownership, and nonempty no-swap history recycling. The initial
84-check regression had 24 failures on the baseline before the implementation
changed.

The normal-compilation targeted suite passes 21,630 checks with the original
allocation budgets. The initial optional-metadata implementation had 16 allocation
failures; its report is retained and the concrete recycled-vector implementation
passes those same checks. A separate `--compile=min` semantic suite passes
15,689 checks. Allocation results come from normal compilation only.

All 100 unique external combinations (afiro, adlittle, pk1, flugpl, fast0507;
primal/dual; native/Markowitz; PFI/HH/FT/SS/BG) finish OPTIMAL, match their manifest
references and satisfy original primal feasibility. All ten pilotnov
manager/backend combinations also finish OPTIMAL with the original feasibility
certificate and reference objective.

## Full runtime validation

The warmed SS/native1600 dual solve finishes OPTIMAL after 68,108 iterations.
Its objective is 51,425,691.76210316 and its returned point passes the original
model's feasibility check. The measured solve call takes 1,175.05 seconds,
including 35.16 seconds attributed to compilation; process peak RSS is
2,372,952 KiB (2.26 GiB). The call allocates 22.04 GB cumulatively, which is not
retained memory or peak RSS.

Existing numerical safeguards remain active: this SS run records 21,776 correction
attempts, 21,767 corrections, ten rejected pivots and ten pivot-triggered
refactorizations, alongside 41 interval-triggered refactorizations. Two terminal
certifications and two cleanup events are recorded. The maximum completed primal
magnitude is 3.12e12 during the trajectory. The final certificate, not the absence
of large intermediate values, establishes success. Diagnostic counters do not
include a dedicated original-LP restart counter; `verbose=false` also suppresses
that message, so this report does not infer a restart count from absent log lines.

FT/native1600 also finishes OPTIMAL: 69,900 iterations, objective
51,425,691.76208826, and original-model primal feasibility. Its measured solve
call takes 1,161.73 seconds including 32.58 seconds attributed to compilation.
Process peak RSS is 2,489,448 KiB (2.37 GiB); cumulative allocations are
22.82 GB. FT records 21,453 correction attempts, 21,443 corrections, eleven
rejected pivots and eleven pivot-triggered refactorizations, alongside 40
interval-triggered refactorizations. It also records two certifications and
two cleanup events. Neither full solve records a precision boost.

These full solves validate the production FT/SS implementations and original
certificates on the current core. Historical interval-sweep runs used a different
core; their elapsed times and iteration counts are not an isolated before/after
performance comparison for this patch.

### Whole-suite limit

A normal-compilation `test/runtests.jl` attempt did not complete. The 600-second
wall-time guard terminated its owned process group (exit 75); the captured stack
was in LLVM machine-instruction scheduling while compiling
`test/primal_initial_tolerance_tests.jl:3`. No test failure had been reported.
Peak RSS was 2,870,136 KiB; neither the RAM/swap guard nor the VM limit triggered.
This attempt is retained as incomplete and is not counted as a whole-suite pass.
The independent targeted normal-compilation checks, semantic checks and full
solver results above remain separate evidence.

The interrupted initial-tolerance test was subsequently run alone with
`--compile=min`: all eight checks passed. This verifies its semantics, not the
completion of the whole suite or normal-compilation performance.

The final audit verifies 100 unique external combinations, ten pilotnov
combinations, both full runtime certificates, all seven repaired replay histories
and the independent stored-factor probe. `results/validation.json` retains
source/file digests, commands, statuses, memory, elapsed times and raw-log hashes,
including all three incomplete startup attempts and the incomplete project suite.
The compact report is reproducible with `reproduce/audit.py RAW_DIRECTORY`; the
replay summary is produced by `reproduce/summarize.py RAW_DIRECTORY OUTPUT_JSON`.
The raw directory for this session is `.superpowers/triangular-stability`.
