# Optional dual row adapter

Enable it explicitly with `SolverOptions(dual_row_adapter=true)`, or set the MOI
raw optimizer attribute `"dual_row_adapter"` to `true`. The default is `false`.
This option affects the dual iteration, independently of optional presolve passes.

The adapter supports native Float32/Float64 PFI, Forrest–Tomlin, Suhl–Suhl,
Bartels–Golub and Huangfu–Hall factors in the legacy strategy. It retains the
original path for other arithmetic/backends, partial pricing or the adaptive strategy,
hypersparse/sparse-pricing/stable-ratio policies, diagnostic observers and stop
callbacks that may mutate numerical state. In particular, opting in with
BigFloat preserves that intent through option copies but uses the original
numerical kernels. Staged pivot attempts also retain the original path.

For a transpose solution with at most 1% exact nonzeros, CSC pricing records its
ascending exact-nonzero output support. Harris/BFRT can traverse that support if
it occupies at most 1/16 of the full row; larger output supports retain the
original residual check and dense ratio traversal. When `rho` itself exceeds
1% nonzeros, pricing simultaneously computes the original tableau-row residual
over current basic columns. It keeps
both accumulation orders and consumes the residual once. A malformed basis map
falls back to the original pricing and row check.

No nonzero coefficients are dropped. All finite checks, residual thresholds,
pivot safeguards, corrections, refactorizations and final original-model
certification remain in place. No arithmetic precision or tolerance changes.

## Work and memory

Every enabled pricing attempt counts nonzeros in `rho` (O(rows)). Fused pricing
also builds an epoch map over basis indices and tests column/slack membership;
it replaces the separate traversal of coefficients in basic columns. Support
pricing tests each output for exact zero and retains its indices. There are no
additional basis solves, numerical-vector copies or conversions.

Scratch is lazy and owned by each workspace. On a 64-bit system its two index
arrays require approximately `16 * (rows + columns)` bytes, plus support capacity
and headers. Scratch persists for the workspace lifetime and holds no model or
workspace reference. Context flags reset at every attempt/reprice; stages and
recovery cannot publish another workspace's context. With the option disabled,
no adapter arrays are allocated or scanned; the scratch object has one extra
optional reference.

The preceding prototype measurements showed a small runtime.mps benefit and
mixed MIPLib timings. This option is experimental and does not guarantee a
speedup. Microkernel times do not measure a complete solver speedup.

## Targeted verification

The integration tests are `dual_row_adapter_options_tests.jl`,
`dual_row_adapter_kernel_tests.jl` and `dual_row_adapter_integration_tests.jl` in
`test/`, registered in `test/runtests.jl`. They cover Float32/Float64, all five
managers and fixed/automatic pricing, exact results for both routes, tie/flip
ordering, tiny nonzeros, nonfinite values, rejection, malformed basis fallback,
epoch rollover, unsupported gates, native mode after refactorization, staging
ownership, option copies/MOI and exception accounting. Warmed consumed pricing,
residual and ratio calls also check zero per-call allocations, including a row
index above Julia's small-Int boxing cache.

A separate full runtime.mps integration audit matched the preceding verified
prototype in event/guard/sample-state hashes and counts, objective bits, whole
primal SHA, 28,973 iterations and 125 refactorizations. Every cached residual,
pricing output and support ratio result was independently recomputed during that
audit; the original-model primal feasibility and actual certification passed.
The instrumented audit is not a speed benchmark. The multi-hour complete test
suite is outside this targeted validation scope.
