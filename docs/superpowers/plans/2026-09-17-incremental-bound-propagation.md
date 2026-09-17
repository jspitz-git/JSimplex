# Incremental Bound Propagation Plan

1. Add tests for dirty rows caused by row bounds, column bounds, coefficient
   changes, and removed columns. Add a chained propagation test that requires
   revisiting an earlier row after a column bound tightens.
2. Add an internal dirty-row propagation entry point while keeping the existing
   full-scan API. During a pass, add later rows incident to tightened columns.
3. Track the previous propagation model and compose row and column maps across
   reductions. Compare mapped sparse columns exactly to build the next dirty
   set, with a full-scan fallback when mapping is unavailable.
4. Run focused tests and differential checks against the full-scan pipeline.
   Benchmark `runtime.mps` and `medium.mps`, then run the complete test suite.
