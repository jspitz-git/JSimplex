# Active upper columns

Source before: `707fbb6`. After: private active-column cache, with all other production sources unchanged. Same captured medium basis at iteration2000 and next320 exchanges; Julia1.13.0, one Julia/BLAS thread. The external model and serialized snapshot remain local.

Only Float32/Float64 skip stored singleton positive-unit diagonal columns. Explicit off-diagonal zeros remain active. Every nonidentity operation retains its order; copies and mutations independently invalidate the cache. Other scalar types retain the full scan.

At320 updates (warmed individual solves in milliseconds; cumulative320 first FTRANs after update in seconds):

| Manager | FTRAN ms before → after | BTRAN ms before → after | First FTRAN total s before → after |
| --- | --- | --- | --- |
| PFI | 0.655 → 0.691 | 0.736 → 0.748 | 0.233 → 0.232 |
| ForrestTomlin | 3.597 → 1.123 | 3.495 → 1.055 | 1.295 → 1.170 |
| SuhlSuhl | 3.441 → 1.121 | 3.623 → 1.084 | 1.285 → 1.131 |
| BartelsGolub | 3.673 → 1.053 | 3.611 → 1.035 | 1.318 → 1.183 |

The last column includes lazy cache rebuilding, unlike warmed solves. This early history mostly comprises pure permutations; results are not a whole-solver or late-fill claim. All tested forward/transposed relative residuals are zero. PFI is an unchanged timing control.

Validation: six new cache checks failed before implementation. After implementation33,117/33,117 factor, differential replay, copy/reset, alias, sparse and allocation checks passed (`-O1`). Read-only review found no blocker. Reproduction: `capture-history.jl INPUT SNAPSHOT 2000 320`, then `replay-history.jl SNAPSHOT OUTPUT.toml` using `--project=.` and one thread, under the24GiB process limit.
