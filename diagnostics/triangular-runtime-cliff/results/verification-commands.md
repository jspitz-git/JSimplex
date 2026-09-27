# Verification commands

Run from the worktree with the same Julia project/depot, `JULIA_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, and a 24 GiB virtual-memory ceiling (`ulimit -v 25165824` on Linux). `julia` below denotes Julia 1.13.0 with `--startup-file=no`. Use an instantiated project; local Manifest and serialized model histories are not committed. Run only one numerical process at a time.

## Factor regressions

The factor driver includes these tests under a single `@testset` with `using JSimplex, Test, Logging`:

```
bartels_golub_incidence_tests.jl
triangular_active_upper_tests.jl
bartels_golub_rows_tests.jl
triangular_composed_rows_tests.jl
bartels_golub_rotation_tests.jl
factorization_tests.jl
triangular_reset_allocation_tests.jl
triangular_column_reuse_allocation_tests.jl
triangular_history_reuse_allocation_tests.jl
factorization_allocation_tests.jl
hypersparse_update_tests.jl
hypersparse_update_sequence_tests.jl
hypersparse_update_edge_tests.jl
hypersparse_update_allocation_tests.jl
hypersparse_update_overflow_tests.jl
pivot_atomicity_tests.jl
```

Use `julia -O1 --project=. diagnostics/triangular-runtime-cliff/reproduce/factor-tests.jl`. Each successful feature gate passed 33,281 checks. The normal `test/runtests.jl` also includes the new regression file. This was a focused regression run, not a claim that every repository test was executed.

## Runtime and identical histories

```bash
julia --project=. diagnostics/triangular-runtime-cliff/reproduce/profile-prefix.jl /home/jspitz/mps/runtime.mps bartels_golub BASE.toml 26000 360
julia --project=. diagnostics/triangular-runtime-cliff/reproduce/replay-segments.jl OUTPUT_DIRECTORY BASE.toml.history.16000.bin BASE.toml.history.19200.bin BASE.toml.history.20800.bin BASE.toml.history.24000.bin
julia --project=. diagnostics/triangular-runtime-cliff/reproduce/compare-kernels.jl BASE.toml.history.19200.bin
julia --project=. diagnostics/triangular-runtime-cliff/reproduce/profile-prefix.jl /home/jspitz/mps/runtime.mps bartels_golub FINAL.toml 1000000 600
python3 diagnostics/triangular-runtime-cliff/reproduce/compare-replays.py BASELINE_DIRECTORY CANDIDATE_DIRECTORY
python3 diagnostics/triangular-runtime-cliff/reproduce/compare-prefix.py BASE.toml FINAL.toml
julia -O1 --project=. diagnostics/triangular-runtime-cliff/reproduce/report-tests.jl
julia --project=. diagnostics/simplex-basis-cleanup-performance/reproduce/solve-profile.jl /home/jspitz/mps/runtime.mps dual 80 900 COMPLETION.toml
```

Generate `BASE.toml` and the baseline replay on revision `358f15a`; use the final revision for the candidate. Compare runs on the same machine. The profile driver warms a small model before measurement; reported solve times exclude process startup and that warm-up.

## External LP corpus

```bash
python3 diagnostics/simplex-basis-cleanup-performance/reproduce/prepare-corpus.py LOCAL_CORPUS_DIRECTORY
JSIMPLEX_CORPUS_MANIFEST=LOCAL_CORPUS_DIRECTORY/quick-inputs.toml JSIMPLEX_CORPUS_OUTPUT=OUTPUT.toml julia -O1 --project=. diagnostics/simplex-basis-cleanup-performance/reproduce/quick-corpus.jl
```

The manifest hashes the decompressed input and uses independent reference objectives. Nine inputs from NetLib, MIPLib, and mps exercise both algorithms and all four managers (72 solves); integrality is relaxed. Oversized excluded models are never solved or factorized.

Final completion result: `TIME_LIMIT`, 61,663 iterations, 900.011 solve seconds. The first attempt's surviving printed prefix can be checked with `compare-logged-prefix.py results/bg-before.toml results/bg-attempt-600.log`; this verifies 14 printed states, not the unsaved full sample array.
