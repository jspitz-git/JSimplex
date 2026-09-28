# Sequential basis optimization series

The five proposals were developed in order, with one worktree and branch per
proposal. Each branch starts at the verified predecessor. The first-proposal follow-up
05f9fc3 is merged into the combined fifth tree at 553f367; intermediate trees
retain their historical checkpoints. Master remains at
`dbf3cc0`; the series has not been merged into master or pushed.

| Proposal | Worktree under `.worktrees/` | Branch | Verified commit |
|---|---|---|---|
| Selective entering-column preparation | basis-selective-preparation | perf/basis-selective-preparation | a5fdf58, 05f9fc3 |
| Incremental auxiliary lists | basis-incremental-metadata | perf/basis-incremental-metadata | e8e6194 |
| Fused solve transfers and diagonal access | basis-fused-solves | perf/basis-fused-solves | a1adfb4 |
| Legacy immutable-LU hypersparse trial | basis-legacy-hypersparse | perf/basis-legacy-hypersparse | 0065856 |
| Direct LU updates and diagonal normalization | basis-direct-lu | perf/basis-direct-lu | 04fdc93, 30eaf18, integration 553f367 |

## Disposition

The first three proposals change production legacy solve/update paths. Whole-runtime
validation caught a regression in the initial selective preparation: extending
cache lifetime changed update rounding and produced a 900-second timeout during
cleanup. Follow-up 05f9fc3 preserves the original cache eviction while omitting
auxiliary payload copies/scans. A controlled lifecycle override restored the
certified optimum in 62,939 iterations / 317.834 seconds, matching the old iteration
count. Incremental metadata and fused transfers preserve fixed-history arithmetic
exactly. The first-tree follow-up passed 33,919 assertions; the integrated final
tree passed 1,885 lifecycle, metadata, fused and normalized-direct assertions.
Generic precision and adaptive behavior remain covered by focused tests.

The hypersparse trial is deliberately not a default or a new public solver option.
Even with one immutable base graph and all conversion/build costs included, the
runtime bundles regress by 18–49%. It is available through an explicitly loaded
diagnostic factory for further experiments.

Direct native Float64 LU is also an explicit diagnostic opt-in. Actual packed U
replaces the correction U over a full frozen LU. Diagonal normalization addresses
a measured early-medium regression, but update cost and LP trajectories still
vary. With the final cache-lifetime policy, runtime dual FT reached a certified
optimum in 55,508 iterations / 235.988 seconds, versus 62,939 / 317.834 in the
correction control (separate single runs). The first 2,000 medium iterations took
49.365 versus 54.064 seconds, with identical logged numerical states; no full
medium optimum is claimed. Native combined-solve refinement is absent. Other
precisions/backends and
adaptive options retain the ordinary implementation. The two diagnostic factories
must be evaluated in separate Julia processes.

## Evidence and reproduction

- [Selective preparation](../basis-selective-preparation/README.md): focused tests,
  80 external primal/dual solves, and three paired replay histories.
- [Incremental metadata](../basis-incremental-metadata/README.md): exact replay and
  metadata/copy/failure regressions.
- [Fused solve stages](../basis-fused-solves/README.md): 33,155 affected assertions,
  final alias/preparation cases, exact replay, and 40 external solves.
- [Hypersparse trial](../basis-legacy-hypersparse/README.md): 321 assertions,
  corrected warmup, paired bundles including PFI, and five independent LP solves.
- [Direct LU trial](../basis-direct-lu/README.md): both representations,
  independent dense and wider-precision references, componentwise residuals,
  copied/unprepared updates, fallback transitions and external LP trajectories.

The final integrated production corpus passed all 80 solves / 245 assertions:
NetLib afiro/adlittle, MIPLib pk1/flugpl and mps fast0507, native/Markowitz,
primal/dual, FT/SS/BG/PFI. Every result was OPTIMAL, primal-feasible in the original
LP and matched its reference objective. See results/external-final.toml and .txt.
After the lifecycle fix, native dual fast0507 FT/SS use 6,012/6,237 iterations,
matching the prior baseline, rather than the retained-cache 6,211/7,528.
These final production checks do not automatically enable either diagnostic trial.

All numerical jobs ran sequentially with one Julia and one BLAS thread and bounded
memory/time. Dataset inputs come from NetLib, MIPLib and mps; hashes are retained.
The excluded big/largo/AnyMod models were not solved or factorized. Measurements
are Linux aarch64 Julia 1.13.0; Windows behavior is not inferred from these runs.

The normal-compiled full-project test attempt in stage 1 hit its 900-second LLVM
compilation timeout. No assertion failure was printed, but this is not a full-suite
pass. The affected automatic-pricing/start/phase-one/recovery checks subsequently
passed under `--compile=min`; timing measurements used normal compilation. That
full-suite limitation applies to the series, alongside the narrower positive tests.
