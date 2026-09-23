# Simplex numerical benchmarks

Run from the repository root with the development environment prepared. Each
case runs in a separate Julia process that verifies `pathof(JSimplex)` against
`--source`. The selected source can be a checkout or an extracted snapshot with
its dependencies available. Solver warmup and every measured solve start from
the original input, not a previously solved basis.

```bash
julia --project=dev dev/simplex_benchmarks.jl --source=. --suite=quick --algorithm=both --samples=7 --time-limit=60 --iteration-limit=100000 --output=/tmp/simplex-quick.toml
julia --project=dev dev/simplex_benchmarks.jl --source=. --file=/home/jspitz/MIPLib/pk1.mps.gz --algorithm=both --samples=7 --time-limit=60 --output=/tmp/simplex-pk1.toml
```

The default roots are `/home/jspitz/NetLib`, `/home/jspitz/MIPLib`, and
`/home/jspitz/mps`; override them with `--netlib-root`, `--miplib-root`, and
`--mps-root`. All complete runs explicitly request LP relaxation, including
MIPLib cases. Integer reference objectives are not used. The initial runner
uses Float64; the production diagnostic hooks also support the solver's other
numeric types.

`dev/simplex_cases.toml` freezes quick, degenerate, ill_conditioned, phase_one,
sparse_large, holdout, and stress selections. Selected solve cases have source
and decompressed SHA-256 identities. Holdout content is excluded from calibration
suites using decompressed hashes. Collection discovery records file inventories
without solving every discovered model. Generated fixtures have analytic LP
objectives and deterministic coefficients; the scaled diagonal fixture uses
2^-40 and 2^40.

## Measurement and results

TOML reports retain input errors, numerical failures, timeouts, and resource
stops. A completed worker is not necessarily a solved LP: inspect each sample's
status. Input or reference-validation errors produce a nonzero runner exit code.
Missing inputs remain present as error records.

Reports include source and runner hashes, data hashes, options, numeric type,
BLAS configuration, statuses, elapsed time, allocated bytes, process peak RSS,
iterations, refactorizations, and diagnostic counters. Original-unit primal and
objective errors are evaluated at 256-bit precision. Original-unit dual errors
are reported only when a compatible original-model witness can be reconstructed;
otherwise their unavailability is explicit. A residual measurement does not
replace the solver's original-model certificate. Raw dual diagnostics do not
round small multipliers to zero: a multiplier pointing toward an absent bound
produces infinite complementarity error, even when its sign violation is near
machine precision. Interpret that value together with `dual_sign_error`; it is
not a new solver termination status.

Diagnostics default to on. Use `--diagnostics=off` for matched uninstrumented
timing comparisons, including comparisons to old source snapshots that lack
diagnostic support. Observer time and compilation time are reported separately;
kernel timings are enabled only by `--kernel-timing=on`. The timed kernels cover
the principal iteration solves, pricing, and refactorization; they are not a
complete accounting of all auxiliary solves. Do not compare instrumented timing
to an uninstrumented baseline as an algorithmic speedup or slowdown.

Eligible large local solves can explicitly request the WSL memory allowance
with `--memory-limit-mib=24576`; the runner clips it to OS-reported total memory.
The default 4096 MiB address-space cap is a screening budget and can stop a
worker even when WSL has substantial free RAM. The separate stress protocol
retains its explicit 4 GiB budget.

The solver time limit applies to each solve. Parsing and warmup also have a
bounded worker allowance. Workers use one BLAS thread. Run performance samples
without concurrent tests or benchmarks; use seven paired small-case samples and
three larger-case samples with matching limits. Report unsuccessful solves
separately from timings on jointly solved cases.

Use `--simplex-strategy=legacy` (default) or `adaptive` for fresh solves.
Reports include the effective numerical policy as well as SolverOptions.
The adaptive profile currently enables `stable_ratio`, `pivot_validation`,
`solve_refinement`, `recovery`, `feasibility_recovery`, `incremental_primal`,
`incremental_primal_pivots`, `adaptive_refactor`, `adaptive_stalling`, and
`adaptive_dual_perturbation`, `adaptive_primal_perturbation`, `adaptive_pricing`,
and `partial_pricing`.
Set a switch to `false` in a policy file to isolate its effect.
Disabling `solve_refinement` retains the F04 pivot-specific corrections while
turning off broader basis-solve refinement. Disabling `pivot_validation` turns
off the independent pivot-quality gate. Recovery can still stage and retry
failed iterations, restore checkpoints or exchange basis columns. Disable both
`pivot_validation` and `recovery` to turn off transactional retry application.
Other stages remain controlled by their own switches.
Disabling `adaptive_stalling` removes the progress monitor and restores the
legacy zero-step Dantzig trigger. Stagnation emits `stagnation_watch`,
`stagnation_stalled`, and `stagnation_fallback` counters; use these alongside
iterations and solve counts when evaluating degeneracy. Set `refactor_timing=false`
in both arms of a diagnostic comparison to exclude clock-based refactor decisions.
Disabling `adaptive_dual_perturbation` retains the earlier 1024-zero-step cost
perturbation trigger. Automatic adaptive cost shifts also require
`adaptive_stalling` and `feasibility_recovery`; disabling either dependency
retains the earlier trigger. Compare `perturbation`, `restore_perturbations`, and
`phase_cleanup` counters and include cleanup time in the result. Perturbation
levels are bounded and user dual tolerances remain unchanged.
`adaptive_primal_perturbation=false` disables outward basic-bound shifts. The
primal action also requires the progress monitor and feasibility recovery;
phase I and objective cleanup never apply it. Compare the same perturbation,
restoration, and cleanup counters, and include restoration in timings. Basic
bounds have their own escalation history within the shared journal. Exact
arithmetic receives neither primal bound shifts nor dual cost shifts.
Use `--pricing=steepest_edge|devex|dantzig|auto` for fresh solves; replay retains
its stored pricing option. `adaptive_pricing=false` disables progress-driven
switches for `pricing=auto`, while preserving recovery of unreliable weights.
Compare automatic pricing with its disabled adaptation and with explicit
steepest edge. Record pricing kernel time/calls together with iterations and
`pricing_devex`, `pricing_dantzig`, `pricing_reset`, and `pricing_weight_rejected`.
Mode/reset counters record committed state; weight rejections also count failed
attempts. These switches are numerical/progress decisions, independent of clocks.
`--policy=PATH` accepts a TOML file with internal numerical overrides:
`solve_tolerance`, `pivot_error_tolerance`, `max_refinements`,
`max_pivot_candidates`, `max_recovery_rounds`, `stagnation_window`,
`max_precision_bits`, and `max_lp_refinements`. Stage switches have the names
in `NUMERICAL_SWITCHES` in `src/simplex_numerics.jl`; an unimplemented stage
cannot be enabled. Unknown keys and invalid values are errors. These controls
do not replace the user's primal/dual tolerances.
For partial-pricing ablations, set `partial_pricing=false` versus `true` while
keeping strategy and scoring rule fixed. `pricing_scanned_entries` and
`pricing_scored_entries` count full/block-domain visits and valid candidate score evaluations;
`pricing_full_scan`, `pricing_block_scan`, and `pricing_pool_hit` distinguish
complete scans, block passes, and reuse. Rechecking the cached pool is not a
full/block-domain visit; its valid candidates contribute to scored entries.
Full-pricing baselines record scan work too. These aggregate work counters include discarded attempts and do not
publish solver-state observer events. Compare them with pricing kernel cost,
iterations, and refactorizations; fewer scanned entries alone do not prove a
faster complete solve. These counters cover candidate selection; feasibility
checks, weight validation, and updates may still scan full vectors.

For F16 component/solver ablations, use `sparse_pricing=false` versus `true`;
this switch is disabled by default in both strategies. Kernel diagnostics add
`row_index` for lazy row-index construction inside pricing. Its time overlaps
`pricing`, so do not add the two. The complete short-solve timing includes index
construction, support discovery, and copying the output into dense consumers.
Run `julia --project=dev dev/sparse_pricing_benchmarks.jl /tmp/sparse-pricing.toml`
for the fixed generated sparse/dense-RHS component comparison.

Stress `--stress-operation=components` additionally checks indexed row pricing
on the bounded extracted block and cancellation/reinsertion. It constructs no
simplex workspace or full-sized basis factorization. The separate F17 probe
factorizes only a derived component bounded by 64x64. Reports distinguish `component_error`
from `reader_error`; index/scratch storage counts describe active arrays.

Snapshots retain the effective policy. Replay uses its stored strategy and
can apply `--policy` overrides to that working policy; `--simplex-strategy=adaptive`
is a fresh-solve option and is rejected with replay. Old source snapshots that
lack policy support remain benchmarkable in legacy mode without overrides.
Serialized replay artifacts still require a matching Julia/source environment;
this is not a cross-version serialization format.

## Stress-only inputs

`big.mps`, `largo.mps`, and `AnyMod.mps` (locally `AnyMOD.mps`) cannot enter a
complete solve, even through explicit file selection, capitalization, a symlink,
or `.gz` compression. Stress mode requires explicit time, memory, and read limits.

```bash
julia --project=dev dev/simplex_benchmarks.jl --source=. --suite=stress --mode=stress --time-limit=60 --memory-limit-mib=4096 --read-limit-mib=256 --output=/tmp/simplex-stress.toml
```

The default operation inspects at most 256 MiB without parsing a prefix as an
LP. Partial reads have range-labelled prefix hashes; unavailable full hashes
are not invented. `--stress-operation=reader` opts into guarded full parsing,
with a maximum 300-second deadline. Reader and component probes also enforce
`--read-limit-mib` on source length before full hashing and on decompressed
length before parsing. `--stress-operation=components` uses a
separate extracted block of at most 256 rows/columns and 50,000 stored entries
for matrix-vector pricing; its overall deadline is at most 60 seconds. Neither
operation constructs a full-size basis or invokes a complete simplex solve.

Linux workers use external `timeout` and `prlimit` controls. The enforced memory
ceiling is address space (`RLIMIT_AS`), not a promise about available RSS. If
required resource controls are unavailable, the operation is reported as skipped.
Resource stops are valid bounded-stress outcomes, not successful full parses.
Stress results never enter solved-LP or speed scores.

Compressed inputs use `gzip` with an argument vector and disposable output.
The default decompression/disk quota is 2 GiB, configurable through
`--decompression-limit-mib`; incomplete temporary outputs are removed.

## Numerical replay

The first serious basis repair in an instrumented sample exports a snapshot
beside the report, under `<output>.replays`. It owns the working model, basis,
states, costs/bounds, options, precision, and counters, with checksums in an
adjacent TOML file.

```bash
julia --project=dev dev/simplex_benchmarks.jl --source=. --replay=/tmp/simplex-quick.toml.replays/netlib_afiro-dual-1.bin --time-limit=60 --iteration-limit=100000 --output=/tmp/simplex-replay.toml
```

Replay rebuilds a fresh factorization and therefore does not reproduce drift
accumulated in an update chain. Its status describes the working snapshot LP,
which may be an auxiliary phase, and is not a new certificate for the original
input. Use `--trace=on` to retain initial states and the
pivot/flip/refactorization sequence with factor/update state. Trace output is
bounded to 16 MiB per sample; truncation is reported explicitly. Julia's UMFPACK
serialization rebuilds native base-factor state when needed, so trace data do
not promise identical native pointer/cache state. Trace artifacts support drift
inspection and must not be confused with the fresh-factor replay command.

Replay files are task-owned local serialized artifacts for the matching
Julia/source environment; hashes detect accidental corruption. External corpus
files and replay binaries do not belong in repository commits.

F17 bounded component workers additionally select up to 64 occupied rows/columns
within 50000 scanned stored entries. They construct a row-normalized, strictly
diagonally-dominant synthetic square component and verify native/Markowitz base
solves in both directions. This is not a basis of the original LP or a full LP
solve. The report retains selection metadata, factor/adapter construction costs,
reference checks, and bounded storage sizes. Oversized-model exclusions still
apply before any complete solve.

`julia --project=dev dev/hypersparse_factor_benchmarks.jl /tmp/base-solves.toml`
measures fresh LU, adapter construction (including UMFPACK scaling verification),
and repeated solves on a fixed generated matrix. It separates already-indexed
inputs from dense input/output conversion costs. These opt-in measurements do
not run with the mandatory offline test suite.

F18 component workers additionally check bounded update histories on the leading
at-most-32-dimensional block of the synthetic F17 basis. All four methods and
both backends are compared with a 256-bit direct reference after each update;
copies and refactorization reset are checked separately. Construction, update,
copy, refactorization, and active-cache storage costs remain visible. These cold
component timings can include compilation. The existing 60-second overall
component-worker ceiling still applies, even with a larger requested limit.

`julia --project=dev dev/hypersparse_update_benchmarks.jl /tmp/update-solves.toml`
measures setup and warmed solves separately on a generated 1024-dimensional
fixture, before and after inverse updates restore the basis. It includes both
backends, every update method, sparse/dense RHS, transpose solves, and explicit
input/output materialization costs. This is an opt-in kernel experiment, not
a complete simplex speed comparison.
