# Code review: computational work and memory

Review every production-code change for avoidable increases in computational
work, allocations, and retained memory, alongside numerical correctness.

- Identify affected execution frequency: setup, refactorization, each iteration,
  each candidate, recovery, or final certification. Count new full-vector/matrix
  scans, basis solves, copies, conversions, and repeated invariant checks.
- Check scaling with problem dimensions, nonzeros, and update-chain length.
  Reuse owned scratch or cached immutable metadata where safe; account for cache
  invalidation, aliasing, memory retention, and all supported precisions.
- For changes in hot paths, provide a focused before/after measurement when a
  material cost change is plausible. Report work or allocation counts as well
  as elapsed time where useful. Separate compilation, initialization, ordinary
  iterations, and recovery/cleanup. Use representative sparse and dense cases.
- Do not infer a speedup from fewer iterations, one timing sample, or unchanged
  allocations alone. Distinguish changed numerical trajectories from kernel
  savings. State incomplete coverage and measurement uncertainty.
- Numerical safeguards take precedence over speed. Added work required for
  correctness is acceptable when justified; do not remove safeguards, drop small
  coefficients, change tolerances, or raise arithmetic precision merely to make
  a performance comparison look better.

The review should explicitly state whether it found unnecessary work or memory
cost and cite supporting evidence. Do not require benchmarks for documentation
changes or unrelated cold paths without a concrete performance concern.
