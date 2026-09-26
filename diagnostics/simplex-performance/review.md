# Whole-branch review and fix pass

A fresh read-only reviewer examined `b69e266..ae47d1c`. Numerical jobs remained
with the implementer. No critical defect was found. Two important findings
entered the fix pass:

1. The native compensated fallback treated `_PriceAuditMatrix` as a dense
   matrix. This implicit sparse-plus-identity operator could therefore cause
   quadratic traversal. A counted-input regression reproduced four failures:
   29,952 reads instead of 272. Native accumulation now dispatches to the same
   sparse entries and implicit identities in both orientations. The regression
   passes all 12 checks after the repair.
2. Exact-input tests did not cover the acceptance boundary or exceptional range
   through direct wide refinement. Added Float32/Float64 and transpose cases
   bracket the exact rational backward error with adjacent floating tolerances,
   require ambiguous native checks to fall back, and cover underflow, nonzero
   subnormals and overflow cancellation. All 45 added checks pass. This was a
   coverage gap, not a demonstrated false-acceptance bug; no artificial failing
   production behavior was invented for it.

The reviewer also verified compensated operation order, stable breakpoint
ordering and SIMD validity semantics. One minor remains deferred: explicit
assertions of every scratch buffer's scalar type, beyond the current allocation,
behavior and source checks.

The reviewer set aside complete-solver performance and final full-suite success
because those sequential gates were still pending at review time. The implementer
subsequently completed them, with evidence linked below. Broad HiGHS/Clp parity
and unmeasured long-update histories are not established by kernel benchmarks
or prefix profiles.

During the same fix pass, an exact-input test also reproduced false native
acceptance when the caller enabled flush-to-zero arithmetic: 3 checks passed
and 4 failed across Float32 and Float64. Native compensated evaluation now
declines that mode and uses the existing wide fallback. All 132 native residual
checks then passed, including the seven mode checks and restoration of the
caller's mode. The broader quality/refinement/primal-update run passed
8,789/8,789 checks before this additional mode guard. Julia documents the
thread-local mode in its [numeric API](https://docs.julialang.org/en/v1.13-dev/base/numbers/#Base.Rounding.set_zero_subnormals).

The final frozen-source gates passed: production 254,083/254,083; development
1,208/1,208 including 249 JET checks; numerical GLPK comparisons 6/6; external
corpus 104/104 checks across 32 solves. The [main report](report.md) and
[verification artifact](verification.json) retain the evidence and limitations.
Runtime and medium remain unresolved in the six-minute completion attempts;
the passing regression gates do not imply those numerical/performance gaps
were repaired.
