# Review and verification record

Base: `1ffdbc2f6abf951c31c4ae5676a47dcc92924600`.
Production tip: `01c6dd7`.

Implementation was sequential in `fix/simplex-basis-cleanup-performance`, with one numerical Julia job at a time. Each feature was committed after focused verification. Independent read-only reviews covered the basis history representation, cleanup, native marginal-price repair, primal retry guards, active upper columns and the complete branch. The reviewer ran no Julia jobs.

Findings addressed before committing:

- Preserve caller logger exception identity during cleanup instead of swallowing a numerical exception raised by the logger.
- Exclude mixed adaptive policies and journals from native working-price repair; recheck cancellation before precision fallback.
- Bound the weak-candidate preference search and retain refresh bookkeeping when recursive pricing exhausts candidates.
- Independently invalidate upper-column caches before mutation; copied factors start dirty, including cases with no appended history or sparse cache.

The final whole-branch review found no blocker. The subsequent three-line small-pivot point-preservation correction also passed separate review. It uses the existing certification gate and adds no clipping or tolerance relaxation.

Verification evidence:

- 33,117 factor, arithmetic-replay, sparse, copy/reset, alias and allocation checks after the final factor optimization.
- 11,972 workspace, presolve, solver, precision and budget checks for the cleanup feature.
- 2,290 marginal dual-price and related guard checks.
- 623 final focused primal numerical, retry, point-preservation and Harris checks.
- 225 final corpus assertions:72/72 external solves are OPTIMAL, reference-matched and original-input primal-certified;71 final cleanup assertions also pass.
- Real runtime and medium measurements are recorded in the accompanying README and raw artifacts.

These counts describe separate focused suites with overlapping coverage; they must not be added as a count of distinct tests. Functional suites used `-O1`; performance measurements used default optimization. A full package test run is not claimed.

Remaining limitations: no completed medium solve is established here; early-history replay does not cover arbitrary late fill. Primal runtime degeneracy and refactorization storms require the full-model result in the README to be considered independently of the passing small regressions. The other machine's exact Julia/build environment remains unknown.
