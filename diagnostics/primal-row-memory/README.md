# Native row certification and bounded exact fallback

This change starts at master `50fdc02`. It targets the excessive memory churn
observed during original-model cleanup of the saved HH/native-160 `medium.mps`
terminal states, following the certificate/postsolve repairs documented in
`diagnostics/native-certificate-recovery`.

## Evidence and cause

The old `_refined_primal_rows_feasible` converted every column value to
`Rational{BigInt}` before checking whether that column contributed to an
inconclusive row. It also created new rational products and sums for every
contribution. This fallback is reachable from ordinary legacy primal point
validation, so its allocation cost can repeat at every pivot.

On the saved primal target, 185 rows are inconclusive in the initial interval
scan. Only 26,398 of 420,526 columns contribute to those rows, but the old check
allocates about 168 MB per call. Repeating that same check 500 times, without
any basis factorization or simplex iteration, reproduces substantial memory
and collection overhead. A throwaway lazy-conversion probe reduces this to
34 MB per call but retains per-coefficient arbitrary-precision churn.

The final filter takes about 4.7 MB per call on the same target. Most of that
is the temporary row-slot map. After full collection at the same sample points,
RSS stays around 0.5 GiB. The old and new checks agree that this particular
postsolved primal target is infeasible; this isolated result is not an optimal
medium solve. `results/repeat-summary.json` summarizes the recorded calls;
raw logs preserve the collection and process-memory measurements.

## Production change

The existing inexpensive interval scan remains first. For rows it cannot
certify, a native Float32/Float64 filter now keeps a leading sum and an outward
interval for the exact product/summation residual. Guarded FMA and FastTwoSum
handle ordinary finite values. Bounds are compared through compensated
differences, so a large bound does not erase the absolute tolerance. The filter
can prove feasibility or infeasibility; unsupported rounding/FTZ settings,
extreme products, uncertain ranges or unresolved bounds delegate only the
remaining rows to the exact fallback.

The fallback represents each stored binary value on a common integer lattice.
Its scale also represents a product of the two smallest subnormals exactly.
It reuses private BigInt term/value buffers and one accumulator per unresolved
row instead of creating rational temporaries per coefficient. The native range
check and exact bound-plus-tolerance comparisons are preserved. This does not
increase solver precision, change pricing, relax tolerances, or add an adaptive
heuristic. Arbitrary precision is a last resort for an inconclusive certificate,
not the normal per-pivot calculation.

Float decomposition and zero detection in the exact fallback use stored bits.
The independent review exposed an FTZ case where floating zero comparisons
would discard a nonzero subnormal. Explicit Float32/Float64 bit decomposition
fixes it; the four initially failing cases now pass with hardware FTZ enabled.

## Validation

Tests cover exact cancellation after native overflow, out-of-range final sums,
subnormal products, signed zero, nonfinite coefficients, absolute tolerance
boundaries and independent rational dot-product comparisons. Moderate shuffled
cancellation cases explicitly require a native Boolean decision. Allocation
profiling checks that a conclusive native check creates no BigInt objects;
a separate allocation contract checks the bounded exact fallback on a long row.

The first broad semantic run passed 15,025 assertions. The final focused run
before the full medium continuation passed 986 numerical assertions and 69
compiled certification/allocation assertions. Additional noncancelling FMA
boundary tests and final full-suite validation are pending.

The complete medium continuations run sequentially under the unchanged guard:
8 GiB virtual-memory cap, 6 GiB RAM floor, 1 GiB swap ceiling, one Julia/BLAS
thread, `--heap-size-hint=2G`, `-g0 -O1`, no solve time limit. Memory is sampled
externally, with no observer-triggered GC or structure traversal. Their results
remain pending; passing the previous crash point alone is not a completed solve.

## Reproduction

`reproduce/repeat_rows.jl HANDOFF` repeats the same selected-row check 500 times.
Run it once with project sources at `50fdc02` and once with this branch, under
the established Julia wrapper and memory guard. The handoffs and their hashes
are documented in the preceding certificate-recovery directory. The same
underlying model and primal vector are used in every repetition.

The complete cleanup uses
`diagnostics/native-certificate-recovery/reproduce/handoff_cleanup.jl HANDOFF REPORT Inf`.
Preserve all process failures and interrupted attempts. Do not interpret a
missing report, a time limit or a successful reduced certificate as a completed
original-model optimum.
