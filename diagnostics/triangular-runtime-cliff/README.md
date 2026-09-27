# Triangular basis update performance

Baseline: `358f15a`. The user confirms the supplied log was produced with that revision on the same computer and with legacy dual, steepest-edge pricing, native factorization, and an initial refactorization interval of 80. The other computer's Julia version was not recorded. Local measurements use Julia 1.13.0, Linux aarch64, one Julia/BLAS thread, and a 24 GiB virtual-memory ceiling. Allocated bytes are cumulative, not resident memory. A later process inspection found a VS Code Julia analysis process consuming another core; the host was not idle (see `results/environment-note.md`). Separate-run timing ratios are therefore indicative, not controlled performance guarantees.

## The apparent performance cliff

The configured interval is an initial value, as documented in `SolverOptions`. `_note_stable_dual_refactorization!` can increase the effective interval even in legacy mode. Progress output is emitted at refactorizations. The supplied log changes from 80 to 160 iterations between progress records after iteration 19,377 for BG, 15,697 for SS, and 18,257 for PFI. Thus elapsed time between adjacent records is not directly comparable across the transition.

Normalized costs around the first doubled interval are 8.789 -> 8.753 ms/iteration for SS, 3.878 -> 3.850 for PFI, and 15.703 -> 19.216 for BG. SS and PFI have no corresponding jump at that first transition; BG has a real additional cost. Subsequent fill and history growth also matter. No interval policy is changed by this branch.

The local BG diagnostic prefix reaches the iteration limit at 26,000 in 248.624 seconds. Its effective interval remains 80, so it does **not** reproduce the other computer's interval transition. At the same update age of 63, upper storage nevertheless grows from 40,638 entries at iteration 8,000 to 479,285 at iteration 24,000. This independently explains why fixed update counts cannot guarantee a constant iteration cost.

## Identical real pivot histories

Four histories capture 320 actual basis exchanges after refactorizations at iterations 16,017, 19,217, 20,817, and 24,017. Each manager replays the same starting basis and exchanges. These are diagnostic replays, not completed optimization runs. Cold post-update solves and warmed solves are reported separately from replacement time. Native factorization and full actual-basis residual checks are retained.

At 19,217, cumulative replacement times for 320 updates are approximately 0.043 s for PFI, 1.325 s for FT, 1.358 s for SS, and 3.536 s for BG. Warm solve times are much closer. The triangular implementations maintain an initially identity update factor above an immutable base LU; they do not directly update that base LU. The update factor reaches about two million entries in this replay. Comparing only the number of history records misses this fill and its repeated traversal.

At iteration 19,217, the final all-manager replay reports:

| Manager | Baseline replacement time, 320 updates | Candidate replacement time, 320 updates |
| --- | ---: | ---: |
| PFI (unchanged control) | 0.043 s | 0.050 s |
| Forrest–Tomlin | 1.325 s | 1.245 s |
| Suhl–Suhl | 1.358 s | 1.217 s |
| Bartels–Golub | 3.536 s | 3.062 s |

## BG persistent row incidence

Row incidence now stores stable basis-position identifiers using the existing column permutation and inverse. A replacement updates membership for that column alone. Rotating logical columns no longer rebuilds every row's incidence. Row swaps, rotations, and elimination map identifiers back to current column positions. Floating-point arithmetic and each column's operation sequence are preserved. Lazy reconstruction after copy/refactorization has independent storage. Failed refactorization preserves valid metadata.

The first prototype replay reduced BG replacement time by 23–30%. The final allocation-preserving implementation (`de3006e`) reduces it by 15–18% across the four histories (3.291/3.536/3.676/3.797 s to 2.781/2.998/3.025/3.100 s). Every residual and storage field is identical to baseline. Timing variation between runs is material; these are replacement timings, not full-solver speedups. Allocation tests additionally exposed leading-vector deletion consuming reserved capacity; overlapping buffer copies now retain that capacity. The final factor regression run passes 33,281 checks, including exact scalar pivot/factor comparisons, Float32/Float64/BigFloat/rational arithmetic, sparse solves, ownership, reset, allocation, and atomicity coverage.

## Shared triangular coefficient loops

Commit `df05ee1` removes redundant bounds checks only from three internal loops over owned packed coefficients. Input dimensions, source indexing, pivot validation, and alias guards remain checked. Every arithmetic operation and its order is unchanged. Independent review verified the invariants, including the hypersparse dense fallback. Another full 33,281-check factor suite passed.

Interleaved checked-reference and candidate runs in the same process on the same factor at iteration 19,217 after 320 updates give minimum times of 1.430 -> 1.129 ms for spike construction, 1.391 -> 1.294 ms for backsolve, and 1.522 -> 1.472 ms for transpose solve. All results match exactly. `reproduce/compare-kernels.jl` contains the baseline checked loops and reproduces this comparison.

The all-manager replay has 64 identical residual/storage checkpoints. Across four segments, replacement time falls by 6–8% for FT, 9–14% for SS, and 13–21% for BG versus the initial baseline. These are single-run diagnostic timings; PFI controls also vary, so do not interpret small end-to-end differences as precise causal estimates. The direct kernel comparison isolates the shared-loop gain more reliably.

## Rejected experiment

A two-pass bulk row-incidence builder passed 33,453 checks but gave no consistent speedup, so it was removed. Its patch is retained only as an experiment, not applied production code. Additional assertions added to that saved patch after the successful suite were not executed. `results/replay-after` refers to this rejected experiment, not the final implementation.

## Reproduction and evidence

- `runtime-dual-all-user.log` is the byte-identical supplied CRLF log. `reproduce/analyze-log.py` produces the parsed summary and hash.
- `reproduce/profile-prefix.jl INPUT METHOD OUTPUT ITERATIONS SECONDS` records effective intervals, fill, kernel times, profiles, and serialized histories. Its default is a diagnostic 26,000-iteration prefix, with 360 seconds available.
- `reproduce/replay-segments.jl OUTPUT_DIRECTORY HISTORY...` replays histories through all managers. `CLIFF_METHODS` optionally restricts type names.
- Serialized histories contain model data and remain local; regenerate them with the prefix script. Measurements and test output are archived under `results`.
- Excluded oversized models (`big.mps`, `largo.mps`, `AnyMod.mps`) are not solved or factorized.

## Solver validation

The identical profiled prefix through iteration 26,000 takes 248.622 seconds on baseline and 166.011 seconds on the candidate (about 33% less). All 14 printed prefix states match in objective, actual interval, update age, refactorization count, upper fill, and history storage. The four serialized starting bases and their 320-exchange histories are byte-identical as well.

The first completion attempt allowed 600 seconds and logged iteration 58,000 at 591.507 seconds. Its final report export failed on a missing objective, so its final solver status is **not available** and no optimum is claimed from that run. The driver now preserves the report in binary first and omits missing objectives from TOML; all six export regression checks pass. The raw failed-attempt log is retained. The final attempt with the established `solve-profile.jl` driver ends with **TIME_LIMIT**, 61,663 iterations, 771 refactorizations, and 900.011 solve seconds (959.334 outer measured seconds). Peak RSS is 6.58 GiB; cumulative allocations are 37.62 GiB. It does not reach an optimum or postsolve cleanup, so there is no original-input solution certificate from this runtime run. No numerical failure is reported. This driver uses verbose output and no pivot observer; its timing is not directly comparable to the matched-prefix experiment.

All 72 external LP relaxations (nine inputs, both simplex algorithms, all four managers) finish optimally and pass original-input primal feasibility and hash-matched independent objective checks: 225 assertions. Inputs come from NetLib, MIPLib, and mps, including fast0507. These tests use `-O1` for functional coverage; their timings are not optimization benchmarks.

## Remaining structural limit

This branch does not make triangular updates comparable to PFI in replacement cost. The extra upper factor still fills substantially, and every replacement reconstructs its spike by traversing that factor. BG also permutes packed rows. Shortening the refactorization interval can hide those costs but would change the workload and is not used as the fix here. Achieving the update-history behavior of a solver that directly updates sparse LU requires a separate representation/algorithm change, with dedicated fill management and numerical validation. The present changes remove measured overhead while preserving the existing numerical trajectory.
