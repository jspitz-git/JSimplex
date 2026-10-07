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

The first broad semantic run passed 15,025 assertions. The focused run after
both medium continuations passes 998 numerical assertions and 69 compiled
certification/allocation assertions, including 12 additional noncancelling FMA
boundary checks. The follow-up uses Int64 explicitly for the Float64 significand,
avoiding a 32-bit machine-Int assumption; this is type-identical on the tested
aarch64 host. The final semantic suite passes 15,681 assertions with `--compile=min`.
All **100 external solves** pass (305 assertions): five hash-matched inputs,
both algorithms, both native/Markowitz backends and all five public managers.
The audit verifies every unique combination, original primal feasibility and
reference-objective agreement. A fresh full HH/native160 dual runtime solve
finishes OPTIMAL in 55,469 iterations at objective `51425691.76210457`, with
original primal feasibility. Its timed solve block is 179.53 seconds, including
0.010 seconds of measured compilation; this is validation, not a new speed study.

The whole-project normal-compilation attempt is **not a pass**. It records
27 failed assertions and 3 test errors before the 600-second guard terminates
it in Julia/LLVM code generation at `dual_pivot_consistency_tests.jl:93`.
Isolated `--compile=min` runs of the four affected files on unchanged master
`50fdc02` and the repaired source both give 329 passed, 27 failed and 3 errors.
All failure locations, assertions and printed evaluated values agree, including
those in the compiled project attempt. The affected files are
`primal_bound_snap_tests.jl`, `primal_candidate_retry_tests.jl`,
`primal_retry_pricing_tests.jl`, and `legacy_primal_preference_work_tests.jl`.
These are existing failures, not repaired by this memory change; the rest of
the interrupted project suite remains unverified. Complete logs and the
comparison are retained in `results/project-failure-attribution.json`.

The complete medium continuations ran sequentially under the unchanged guard:
8 GiB virtual-memory cap, 6 GiB RAM floor, 1 GiB swap ceiling, one Julia/BLAS
thread, `--heap-size-hint=2G`, `-g0 -O1`, no solve time limit. Memory is sampled
externally, with no observer-triggered GC or structure traversal. **Both saved
terminal-state continuations now finish OPTIMAL**, with the same objective
`22389455.645278454` and verified original-model primal feasibility. Both use
primal cleanup; the labels identify the originating simplex algorithm.

| Saved handoff | Additional pivots | Total iterations | Cleanup seconds | Process peak RSS | Sampled peak VM |
|---|---:|---:|---:|---:|---:|
| Primal | 18,422 | 353,468 | 2238.03 | 1.849 GiB | 2.203 GiB |
| Dual | 21,205 | 233,485 | 2515.95 | 1.855 GiB | 2.191 GiB |

Times include approximately 11.3 seconds of measured compilation in each call.
They are functional observations, not paired speed benchmarks. These are
continuations from the preserved terminal states, **not fresh complete multi-hour
medium solves**. They exercise the production postsolve cleanup and terminal
certificate, without an independent external solver comparison of the final point.
The retained earlier primal attempt exited 139 in GC/GMP at peak RSS 7.068 GiB;
the repaired process completes below 1.86 GiB. The old attempt had a GC observer,
so its elapsed time is not a fair speed baseline.

The ten shared primal progress samples at iterations 335100--336000 have
identical printed pinf/dinf values. This supports preservation of that prefix,
not bitwise identity of the complete pivot sequence. Raw reports, original
handoff hashes, sampled-memory maxima and report hashes are checked by
`reproduce/audit_cleanup.py`; compact outputs are in
`results/medium-cleanup-audit.json`. An earlier task-owned interruption before
the final FTZ fix remains preserved as exit143, not a solver result.

Medium used source aggregate
`afdebdb6ede3da184ca8ca27c1ea982936bf5c59b90e1b58b89544423ac72564`
(commit9c3ca17). Subsequent verification uses the explicit Int64 spelling and
added tests; its aggregate is
`fb37933b9882dafc8886f17ad33dad14237aa4a08803cf586190c86a794082ee`.

## Independent final review

Read-only review found no remaining blocker in the native filter, exact fallback,
FTZ handling or Int64 follow-up. It independently checked the medium handoff and
source hashes, memory maxima, original feasibility, final objectives and shared
progress samples. A second evidence pass checked all 100 external combinations,
input hashes, objective comparisons, final runtime and final source aggregate.
The project-suite limitation and baseline attribution are retained explicitly.
No new Julia process was launched by the reviewer. Master is unchanged; this
repair and its results remain on `codex/cleanup-memory`, without merge or push.

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
