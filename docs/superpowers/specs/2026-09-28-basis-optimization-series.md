# Sequential triangular basis optimization

Implement the five proposals accepted on 2026-09-28, in order and in separate,
stacked worktrees. Keep each verified feature in its own commit. Do not merge
or push this series without a subsequent instruction.

1. Prepare the next basis update only for an entering-column FTRAN in the
   legacy solver. Preserve the public solve API and provenance safeguards.
2. Maintain active upper columns and row incidence using only affected regions.
3. Reduce dense copies and permutation passes between solve stages.
4. Add independently selectable hypersparse legacy solve kernels, beginning
   with BTRAN, without changing the adaptive simplex strategy.
5. Investigate and implement direct LU updates as an explicit experimental
   alternative; retain the existing implementation until accuracy and total
   runtime comparisons justify replacement.

Use problem precision. Preserve finite/nonfinite, alias, signed-zero, copy,
refactorization and recovery behavior. Numerical trajectories may change, but
original-problem feasibility and objective checks must still pass. Include FT,
SS and BG; retain PFI as a performance/control reference. Native and Markowitz
backends and Float32, Float64, BigFloat and exact arithmetic require compatible
fallbacks.

Measure fixed exchange histories and independent solves separately. Use local
NetLib, MIPLib and mps data, including runtime and bounded medium runs. Never
solve or factorize big.mps, largo.mps or AnyMod.mps (including aliases).
Run one numerical process at a time, with one Julia/BLAS thread, bounded time
and memory. Keep repository artifacts in English. Do not investigate allocation
counts or change adaptive strategy as part of this work.
