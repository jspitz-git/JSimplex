# Measurement and validation scripts

These are the small harnesses used for the recorded observations, including
their original local paths. Run numerical jobs sequentially from the repository
root, with Julia 1.13, one Julia/BLAS thread and a 24-GiB address-space limit.
The parent [report](../report.md) explains warmups, limits and interpretation.

- `solve-bench.jl`: input, algorithm, strategy, time limit, measured sample
  count, output TOML, optional policy mode, optional warmup mode.
- `residual-bench.jl`, `breakpoint-bench.jl`, `finiteness-bench.jl` and
  `profile.jl`: the original feature-stage kernel and profile harnesses.
- `runtime-diagnostics.jl` and `primal-runtime-recovery-probe.jl`: separate
  diagnostic runs, not the primary performance comparisons.
- `highs-reference.py` and the three reference/certification Julia scripts:
  copy to `.superpowers/performance/` before running, as described in the
  parent report. The Python script requires the installed HiGHS library path.
- `production-gate.jl`: copy to `.superpowers/performance/` and run with
  `--project=.`. It executes `test/runtests.jl` with per-file progress messages.
  Running `julia --project=. test/runtests.jl` executes the same test inventory.
- `quick-corpus.jl` and `quick-inputs.toml`: copy together to a scratch directory.
  Provide the eight uncompressed MPS inputs at the manifest's `path` entries,
  adjusting those paths for another checkout. For `.gz` originals, decompress
  without modifying the model. The script verifies the uncompressed hashes
  before solving. Run with `--project=.`; output TOML is written beside it.

The other final gates are `julia --project=dev dev/tests/runtests.jl` and
`julia --project=dev dev/run_suite.jl --tag numerical --compare-glpk`.
Install the project/developer dependencies before reproducing these commands.
Raw logs and local dependency manifests remain in the worktree; published JSON
records identify them by hash. Never substitute timed-out or failed solves for
successful completion times.
