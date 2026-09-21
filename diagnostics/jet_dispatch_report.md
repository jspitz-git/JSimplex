# Presolve and retry dispatch fixes

Baseline: `b7b2b93`. The two JET checks on `solve` reported 21 dynamic dispatch
sites each for Float64 and Rational{BigInt}.

## Changes

- Presolve selects its nine passes with explicit branches and specializes the
  per-pass wrapper on the function type. The order, twelve-round limit and
  incremental propagation rules are unchanged.
- Individual passes keep their tuple histories. The complete presolve history
  uses a vector whose element type is a union of the six concrete record types
  parameterized by the model scalar type. This prevents the growing tuple from
  changing the aggregate result's type on every reduction. Primal and basis
  restoration traverse that vector in reverse and explicitly dispatch each
  record type. Existing tuple restoration remains available.
- Singleton and propagation passes distinguish the identity result by type,
  preventing a spurious third return variant from widening their histories.
  Exact interval predicates explicitly distinguish fully finite intervals before
  calling concrete comparison helpers. The helpers remain out of line to retain
  the existing allocation budgets for dependent and parallel row reductions.
- Retry options preserve both basis strategy type parameters through the
  existing validated constructor. Retry calls the dual or primal algorithm
  directly, preserving budgets, callbacks and accumulated counters.

No JET filtering or report suppression was added. The repaired solver testset
also exposes a pre-existing MOI test assertion that demanded a fully concrete
strategy type from mutable optimizer attributes. Its replacement checks that
inference retains `SolverOptions{Float32}`, then checks the concrete strategies
before and after changing those attributes. The separate JET check remains.

## Verification

- Entire production suite: **223,044 passed**, including the unchanged allocation
  budgets. The initial inline-only interval fix failed 27 allocation checks;
  explicit finite-interval specialization restored all of them.
- Entire development suite: **450 passed**, including JET and JuMP integration.
- Retry regressions: **622 passed**, covering every basis mode/backend, generic
  scalar types, stored BigFloat precision, both algorithms and exhausted budgets.
- Aggregate history regressions: **72 passed**, covering inferred restoration,
  reverse replay against the existing tuple implementation, empty histories and
  independent output arrays.
- Interval and related allocation regressions: **3,400 passed**, including
  **338** finite/unbounded interval comparisons against a set-based oracle.
  Existing allocation limits were retained.
- Independent review found no blocking semantic defects.

A matched diagnostic loaded complete before/after source snapshots in separate
Julia processes. Across **96 histories** (24 deterministic seeds for each of
Float32, Float64, BigFloat and Rational{BigInt}), reduced coefficients, bounds,
objectives, record order and reconstructed values matched exactly.

Afiro/adlittle complete solves with primal/dual algorithms retained OPTIMAL,
identical objective values and iteration counts. Warmed minimum allocated bytes
(five samples after three warmups, inputs outside measurement) were:

| Case | Before | After |
| --- | ---: | ---: |
| afiro presolve | 675,176 | 668,040 |
| afiro dual solve | 810,056 | 801,064 |
| afiro primal solve | 785,784 | 776,744 |
| adlittle presolve | 3,216,424 | 3,209,848 |
| adlittle dual solve | 3,962,232 | 3,955,992 |
| adlittle primal solve | 4,232,040 | 4,223,464 |

These figures cover the combined correction and do not imply allocation-free
presolve or a universal speedup. Measurement ran with Julia 1.13 and one BLAS
thread. Session diagnostics are `/tmp/jsimplex-dispatch-comparison.jl` and
`/tmp/jsimplex-dispatch-before.toml` and
`/tmp/jsimplex-dispatch-after-final.toml`.
