# S0: frozen baseline and coverage boundary

Preflight: 2026-10-11. This record reuses completed measurements; it does not
claim a new solve or benchmark. Machine-readable hashes, phase dimensions and
attempt audit: [preflight.json](results/S0/preflight.json).

## Repository and process state

- Production baseline: `fe839aa72171d7496c9c931d9393278448c7317e`.
  Local master, origin/master and live `git ls-remote origin refs/heads/master`
  agreed at preflight. Planning HEAD was `7d6a8e1` (diagnostics `6ded1fc`).
- New implementation checkout:
  `/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl`, branch
  `codex/simplex-core-architecture`, created from `7d6a8e1` using the app tool.
- Original planning checkout and all older worktrees are preserved. Main's
  `.vscode/settings.json` is modified by the user. Both original checkouts have
  untracked Manifest.toml and LocalPreferences.toml. Neither is staged.
- The new environment files are byte-for-byte copies of the planning environment;
  `[JSimplex] precompile_workload = false` is preserved. No instantiation,
  dependency update, cache cleanup or precompilation was requested or performed.
- Host-level `ps -C python,python3,julia` and a `/proc` Julia scan found no
  numerical job. PID namespace visibility was checked using an escalated host
  command; a sandbox-only empty process list was not accepted as sufficient.
  Old current.json files refer to finished attempts, not active ownership.
- The launcher still uses Julia 1.13.0, one Julia/BLAS thread, heap hint 2G,
  8 GiB address-space cap, offline shared depots and disabled automatic precompile.
  Its own script and the additional depot-path script are hashed. Shared depots
  and dynamically loaded system libraries are not byte-for-byte frozen.

## Existing evidence, not repeated

| Slice | Actual algorithm/phase | Rows | Structural columns | Nonzeros | Steps | Manager |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| medium-dual | dual auxiliary prefix | 360982 | 186497 | 961843 | 4000 | HH/native320 |
| medium-primal | primal phase I, including artificial columns | 360982 | 239057 | 1014403 | 2000 | HH/native320 |
| cleanup-dual | primal cleanup of dual-origin handoff | 586972 | 420526 | 1446423 | 256 | HH/native160 |
| cleanup-primal | primal cleanup of primal-origin handoff | 586972 | 420526 | 1446423 | 256 | HH/native160 |

Working vector lengths also include one row variable per row. Exact options
are in `simplex-time-budget/reproduce/measure_counted.jl` and saved cleanup
[metadata](../simplex-time-budget/results/metadata/handoffs.toml): legacy strategy,
steepest-edge pricing, partial pricing disabled, native Float64, normal tolerances
(primal/dual 1e-7, zero 1e-12), presolve and auto scaling for fresh solves.
Do not reinterpret disabled optional recovery policies in legacy metadata as
permission to remove its always-on residual/certificate safeguards.

Four completed reference/census attempts have process exit 0, unchanged pins and
matching status, iteration count, event/state fingerprints. The two prefix
sampling comparisons also passed in the earlier audit. All four results have
`ITERATION_LIMIT`: successful *measurements of bounded slices*, not solved LPs.
Cleanup counters are 212280 + 256 and 335046 + 256. The preserved
`cleanup-dual-1` sampling stall has exit 137, only a reference report and unchanged
pins. `metadata-1` exited 0. No missing census/profile is counted as successful.

Measured call counts include 16004 `_finite_workspace` calls in 4000 dual steps
and 2003 `recompute!` calls in 2000 primal steps. Timing/GC/allocation attribution
remains exactly as reported in [RESULTS](../simplex-time-budget/RESULTS.md).
The ordinary DSE helper already reuses its successful local check at baseline.

## Input identity and coverage

The existing five-case external manifest is frozen by hash; all five resolved
files match their declared SHA-256. They cover 5 inputs x 2 algorithms x 5 public
managers = 50 combinations per refactorization backend (100 across native and
Markowitz, subject to actual supported combinations). Runtime, medium, the
separately failing test.mps, and both historical cleanup snapshots are hashed.
The report also hashes big.mps, largo.mps and the actual case-sensitive file
AnyMOD.mps *without parsing, solving or factorizing them*. No permitted input
has a forbidden byte digest. Resolve symlinks and compare decompressed bytes for
compressed inputs as well; renamed or reformatted models require provenance,
not merely a different digest. This is not semantic MPS equivalence detection.

Portable sparse/dense input definitions and validation matrix are frozen in
[fixtures.toml](reproduce/fixtures.toml). These are integer recipes without RNG
or BLAS-version dependence; materialize in each supported precision. Do not claim
measured representativeness until the named sparse/dense experiments run.

## Guarded attempts

[guarded_run.py](reproduce/guarded_run.py) freezes explicit files and complete
source-directory membership, then refuses changed/deleted/added pins, an existing
attempt, another runner's ownership lock, a live Julia process, or unsafe RAM/swap.
It creates an owned process group, enforces the 8 GiB virtual-memory limit and
one-thread environment, and records boot identity, PID, start ticks, command,
resource samples, exit reason and post-run pins. Termination targets only its
own group. Keep all attempt directories, including failures.

The lock is advisory and host-wide per user, at `/tmp/jsimplex-numerical-UID.lock`.
Use its default for every numerical run. Old runners and manually launched Julia
are detected before launch but cannot be atomically coordinated by an advisory
lock they do not use. Therefore never launch numerical work from another chat or
outside this runner while it owns a job. Run it on the host, not in a restricted
PID namespace. Python-only tests use private temporary locks and children.

Freeze source `src`, relevant test trees, Project/Manifest/preferences, executable,
launcher **and its depot-path dependency**, all included Julia/Python diagnostic
scripts, fixtures, external manifest and every actual input. Keep generated reports
outside pinned trees. Always give `--heap-size-hint=2G --startup-file=no` through
the established launcher and an explicit `--project` for the candidate checkout.
The generic guard cannot discover Julia `include`, deserialize or shell imports;
the experiment owner must enumerate these before creating pins. Treat command
exit 0 and unchanged pins as process evidence only; audit result/certificate
files separately before accepting a solve.

Safety tests run without Julia. The initial 12 tests failed because the runner
was absent; all 12 passed after implementation. Additional review regressions and
final test totals belong in REVIEW.md. No numerical baseline rerun was needed
for diagnostic Python and prose changes.

## Remaining S0 gates

[LONG-PHASE-II.md](LONG-PHASE-II.md) defines the live-state long-run method,
chronological accounting and calibration gate. Implementation/calibration and
the reference itself remain pending; the old snapshots are not full pricing-state
checkpoints. No whole-medium improvement claim is allowed before that reference.
The local S1 ownership investigation is independent of this long-run gap.
