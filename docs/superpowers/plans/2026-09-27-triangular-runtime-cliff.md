# Triangular runtime slowdown investigation and implementation plan

> Execution: sequential in this worktree using `superpowers:executing-plans`; one numerical Julia job at a time, one independent branch review at the end. Commit each verified feature.

**Goal:** Explain the reported runtime.mps slowdown and reduce unnecessary triangular basis-update work without weakening numerical checks or changing adaptive policies.

**Baseline:** `358f15a`. User confirms the new all-manager log uses this master and the previous configuration on the same computer: legacy dual, steepest-edge, native factorization, initial interval80. The other machine's exact Julia version remains unrecorded.

**Evidence and scope:** The legacy dual interval is documented as an initial value; stable productive cycles can double it independently of the adaptive strategy. User-log progress records change from80 to160 after19377 (BG),15697 (SS), and18257 (PFI). Normalize time by actual iteration differences. This explains part of the apparent jump but not the triangular managers' overall disadvantage. Preserve current interval semantics while isolating their effect experimentally.

## Task 1: Establish the cause

- [x] Preserve the supplied CRLF log byte-for-byte, hash it, parse all four runs, and compute per-iteration costs.
- [x] Trace progress logging and legacy interval growth; distinguish configured and effective intervals.
- [x] Profile a BG diagnostic prefix through26000 iterations with actual update age, upper/history storage and solve kernels. Capture identical real exchanges around16000/19200/20800/24000.
- [x] Replay identical histories through all managers, separating replacement cost, cold and warm solves, and numerical residuals. Locate excessive work before choosing a production change.

## Task 2: Implement only confirmed bottlenecks

- [x] Record the bounded design and its evidence. Do not change interval semantics merely to conceal the slowdown.
- [x] Add differential/work regressions that fail on the confirmed issue. Preserve arithmetic order, supported scalar types, sparse solves, aliases, copy/reset ownership and failure handling.
- [x] Implement the smallest reusable correction, run factor and relevant solver checks, benchmark the same real histories, and commit the verified feature.

## Task 3: Validate and report

- [x] Compare matched runtime progress before/after; completion attempts allow at least360s. Cover BG, SS, FT and PFI; clearly label diagnostic prefixes and incomplete solves.
- [x] Run external NetLib/MIPLib LP/mps functional coverage and original-input certificates. Never solve big.mps, largo.mps, AnyMod.mps or their aliases. Keep one numerical job and a24GiB virtual-memory ceiling.
- [x] Obtain independent read-only branch review, archive English results/scripts, and commit. Do not merge or push without a new user request.

### Confirmed first change: bulk row-incidence reconstruction

The BG prefix profile attributes4735 of24731 visible samples to the call rebuilding row incidence; the replay at19217 attributes734 of1512 update samples there. All coefficient arithmetic remains outside this metadata construction. Replace repeated per-entry `push!` with two passes: count each row's entries, resize its owned vector once, then fill ascending column indices directly. Use a private reusable integer scratch vector in each triangular factor's existing cache. Apply the same construction to the filtered FT/SS index only if replay confirms a benefit. Keep the old two-argument builder as the independent oracle. Validate empty/dense/sparse matrices, row ranges, reused owners and independent copies, then all existing factor/sparse/allocation tests. No public option or numerical policy changes.

The bulk-fill prototype passed33,453 factor checks but did not reduce measured replacement time consistently across the four real segments. It was removed from production; its patch and measurements are retained as a rejected experiment. Additional scratch-allocation assertions added after that suite were not run and are not claimed as verified.

### Selected replacement: persistent BG incidence with stable column identities

Use existing `column_order`/`positions` to store stable basis-position identifiers in BG row incidence. Build lazily on construction/copy or after refactorization. Before packing the replacement, update only rows where that column's structural presence changes. Column rotations then require no incidence rebuild. Row swaps/rotations map stable identifiers back to current upper positions; elimination visits independent columns in stable-identifier order while preserving every column's numerical operation sequence. Retain identity-mapping defaults for standalone helpers and the scalar reference oracle. Copies own empty, initially invalid metadata; successful refactorization invalidates it, failed refactorization preserves it.

RED:52 incidence assertions fail before implementation across Float32/Float64/BigFloat/Rational;112 existing properties pass. Verify cache integrity after every replacement, copied nonidentity histories, successful/failed refactorization, all existing arithmetic/sparse/alias/allocation tests, and the same real-history timings before accepting.

### Shared packed coefficient loops

Second bounded optimization: checked public solves own dimension validation; upper packed row indices and paired index/value arrays are maintained internally. Profiles show repeated bounds checks/getindex consuming shared packed-column kernels. Suppress bounds checks only inside the three coefficient loops in _prepare_spike!, _upper_backsolve!, _upper_transpose_solve!, leaving tableau indexing, pivot checks, public dimension/alias guards, arithmetic and iteration order unchanged. Validate existing exact-arithmetic and scalar-reference factor tests plus explicit invalid pivot/short/long inputs before accepting. Compare all four managers on identical real histories. This does not remove the O(nnz(U)) matrix passes or promise parity with a native sparse-LU updating solver.

The existing identical-history replay is the performance regression: retain this optimization only if it reduces measured work time beyond run noise while all residual/storage fields remain identical. Use existing scalar arithmetic oracles and bounds/alias tests for semantic validation, not a brittle wall-clock assertion in the CI suite.

Verified feature commits: `de3006e` (persistent BG incidence), `df05ee1` (shared coefficient loops). Both pass 33,281 factor checks; all 64 final real-history residual/storage checkpoints match baseline. Independent read-only review found no issues. Full runtime and external corpus validation follow.

Final validation: 72/72 external solves optimal and certified, 225 assertions; six report-export tests pass. Matched 26,000-iteration prefix: 248.622 -> 166.011 seconds, 14 printed numerical states and four serialized histories identical. Final full attempt: TIME_LIMIT after 61,663 iterations and 900.011 seconds, no optimal runtime solution certificate. The architectural performance gap versus PFI remains; this branch delivers bounded overhead reductions, not parity. No merge or push performed.
