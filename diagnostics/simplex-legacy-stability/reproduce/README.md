# Reproducing the legacy stability measurements

Run from the repository root, using the Julia and dependency versions in
`../environment.json`. Set `JULIA_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1`.
Run numerical jobs sequentially. Dataset files are external and are not included.

The recorded Linux runs also used `ulimit -v 25165824` in their Bash launcher
(24 GiB of virtual address space). The environment record distinguishes this
limit from measured resident memory.

## Repository checks

```sh
JULIA_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 julia --startup-file=no --project=. test/runtests.jl
JULIA_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 julia --startup-file=no --project=dev dev/tests/runtests.jl
JULIA_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 julia --startup-file=no --project=dev dev/run_suite.jl --tag numerical --compare-glpk
```

See `../report.md` and `../validation.json` for the recorded monolithic timeout,
fresh-process continuation, shared-logger fixture replay, completed-file
coverage, and successful development/GLPK checks. The timeout is not reported as
a successful monolithic production run. Local diagnostic launchers and full
logs remain in `.superpowers/stability` in the preserved worktree.

## Small external corpus

The preparation script checks the decompressed input hashes and writes plain MPS
copies without changing the originals. Adjust `original_path` entries in
`quick-inputs.toml` if the datasets are installed elsewhere.

```sh
python3 diagnostics/simplex-legacy-stability/reproduce/prepare-corpus.py /tmp/jsimplex-stability-corpus
JSIMPLEX_CORPUS_MANIFEST=/tmp/jsimplex-stability-corpus/quick-inputs.toml JULIA_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 julia --startup-file=no --project=. diagnostics/simplex-legacy-stability/reproduce/quick-corpus.jl
```

This performs 64 LP solves, including relaxed MIPLib inputs, and writes
`quick-corpus.toml` beside the script. It checks status, independent reference
objective, and feasibility against the original input.

## Timed solves

Arguments are input, algorithm, update backend, time limit in seconds, sample
count, output path, policy mode, and warmup mode. Use `default` for the policy
mode. `full` warms up with the same input; `afiro` warms up with the small bundled
fixture. Each runtime/medium completion attempt receives 360 seconds.

```sh
JULIA_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 julia --startup-file=no --project=. diagnostics/simplex-legacy-stability/reproduce/solve-bench.jl /home/jspitz/mps/runtime.mps primal bartels_golub 360 1 /tmp/runtime-primal.toml default afiro
```

The settings include legacy simplex, steepest-edge pricing, native
refactorization, interval 80, an iteration limit of 1,000,000, and relaxed
integrality. Repeat sequentially for dual and PFI. For fast0507, use three samples
and `full` warmup. An unsuccessful solve stops further repetitions.

`seconds` is solver-reported elapsed time; `outer_seconds` also includes caller
overhead and compilation. Allocated bytes are cumulative allocations, not memory
residency. Peak RSS is the process-wide high-water mark. TIME_LIMIT does not
establish a solution or a matching objective.

## Diagnostic primal run

`primal-progress-probe.jl` uses the reported runtime settings with a 360-second
limit and records phases, repair events, and nested kernel timers. Its input path
is `/home/jspitz/mps/runtime.mps`; adjust it if needed. Diagnostic timings are not
interchangeable with the timed solves above, and nested timers must not be added.

Do not solve or factorize `big.mps`, `largo.mps`, or `AnyMod.mps` as part of these
measurements.
