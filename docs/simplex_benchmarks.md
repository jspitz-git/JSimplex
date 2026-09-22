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
The adaptive profile currently enables `stable_ratio`; use a policy file with
`stable_ratio = false` to isolate its effect while retaining the profile.
`--policy=PATH` accepts a TOML file with internal numerical overrides:
`solve_tolerance`, `pivot_error_tolerance`, `max_refinements`,
`max_pivot_candidates`, `max_recovery_rounds`, `stagnation_window`,
`max_precision_bits`, and `max_lp_refinements`. Stage switches have the names
in `NUMERICAL_SWITCHES` in `src/simplex_numerics.jl`; an unimplemented stage
cannot be enabled. Unknown keys and invalid values are errors. These controls
do not replace the user's primal/dual tolerances.

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
