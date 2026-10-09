# Independent review

The reviewer inspected the production diff, packed-column mutation invariants,
PFI safety tests, measurement harnesses and completed reports without starting
another Julia process. No production blocker was found.

## Computational work and memory

PFI performs one paired-axis compatibility check per eta, retaining indirect
bounds checks. The upper solve performs one endpoint check per active column
and retains the original fallback. Neither adds basis solves, vector/matrix
scans, coefficient copies, precision conversions, caches or retained buffers.
Review found no unnecessary work or memory increase. This is supported by
compiled allocation regressions, exact total-zero-batch checks and focused
before/after measurements; it is not inferred solely from allocation counts.

## Findings addressed

- Oversized PFI payloads, cancellation and signed zeros were added to safety
  coverage; unique ordered upper rows are asserted in history probes.
- Timing grids and external combinations are audited against their expected
  Cartesian products. Ratios are recomputed; runtime metadata, input hashes,
  objective references and complete passing test summaries are checked.
- Short-chain regressions and mixed BTRAN results remain visible.
- HH index-payload savings are distinguished from total factor/process memory.
  A strict batch-allocation diagnostic exposed symmetric 16-byte harness cost
  hidden by integer averaging; raw totals and isolated measurement follow-ups
  are preserved rather than claiming the original reports proved zero bytes.
- Both full PFI/BG pairs match all recorded hashes/counts and finish OPTIMAL with
  original feasibility. The BG baseline profile intervention excludes its full
  timing from performance comparisons; its existing recovery behavior is not
  represented as fixed by this optimization.

The README states incomplete coverage: the complete project suite was not
rerun, whole-solve pairs are not repeated performance experiments, and native
Float64 kernel timings do not establish speedups for other precisions/backends.
