# Runtime audit with unchanged numerical decisions

Baseline: `28708c7` (the complete source is compared, not isolated replacement
functions). This audit follows the allocation work and prioritizes repeated
simplex operations. It covers the solver, native and Markowitz factorizations,
triangular basis updates, pricing/ratio tests, presolve, scaling/model ownership,
MPS input and MOI translation/results.

## Implemented first batch

1. **Unlimited time limit:** `time_limit_reached` returns false for positive
   infinity without reading the clock. Finite limits still execute the original
   clock calculation/comparison, and stop callbacks retain their call sites.
   Initial warmed CPU profiles of small Netlib solves repeatedly attributed
   samples to `time_ns` even with the default unlimited budget.
2. **Bound-flipping ratio sorting:** retain each already validated breakpoint in
   private workspace storage for the current call. Sorting reads those values
   instead of repeating multiplication and division for every comparison. The
   stable sort, eligibility checks, signed-zero ordering, ties, Harris fallback,
   and bound traversal are unchanged. Storage grows on demand and retains its
   capacity; keys are rebuilt on each call.
3. **Packed upper-factor updates:** pass the binary-search position already found
   by the indexed setter to its write helper. Arithmetic, zero tests, insertion
   and deletion order, and row incidence updates are unchanged.
4. **Markowitz writes:** determine a nonzero insertion from the row-length change
   after the same two dictionary writes. The zero branch keeps its membership
   test. This removes one redundant hash lookup per nonzero update without
   changing dictionary iteration order or pivot selection.

No tolerances, pivot rules, reduction order, arithmetic formulas, factorization
algorithms, threading settings, or fast-math options were changed. Elapsed time
naturally differs; identical stopping iterations under a finite wall-clock
budget are not a numerical-equivalence requirement.

## Measured results

Raw samples and all source hashes are in `runtime_before_after.toml`.
The warmed ratio test with 256 candidates showed median paired speedups of
**1.36× (Float32), 1.37× (Float64), 8.64× (BigFloat), and 5.30×
(Rational{BigInt})**. The exact-number benefit comes from eliminating repeated
breakpoint construction during comparisons. Allocated bytes in that probe fell
from 1,388,472 to 199,992 for BigFloat and from 5,034,456 to 874,648 for
Rational{BigInt}; the Float32/Float64 probes did not increase warmed allocations.

The overwrite-only packed setter probe measured **1.64×**, and the Markowitz
setter probe **1.08×**. These are local kernel results, not whole-factorization
speedups.

Across **32 complete Float64 solves** (afiro, adlittle, sc50a, kb2; primal/dual;
PFI/Bartels–Golub; native/Markowitz; presolve and scaling disabled), the median
paired speedup was **1.071×**, corresponding to a median **6.6% shorter runtime**.
Individual speedups ranged from 1.004× to 1.153×. Unchanged parse/presolve controls
ranged from 0.968× to 1.053×, so the smallest differences are within observed
timing noise. The measurements support a useful first batch, not a uniform
project-wide speedup. All recorded residual compilation times were zero.

Numerical comparison used `isequal`, including signed zeros, rather than a
tolerance. All 32 complete-solve comparisons retained the exact primal/objective,
status, message, iteration count and refactorization count. A boxed 3-by-4 LP
also retained **1,152 recorded states across 192 configurations** (four scalar
types, four basis-update methods, two refactorization backends, three pricing
methods, and both algorithms). States include basis indices/statuses, primal,
reduced costs, costs, pricing weights, and forward/transposed basis solves.

## Verification

- All production test files covered: **223,947 passed** across two invocations.
  The initial full-suite command passed 223,286 checks, then stopped before MOI
  because the launcher omitted the repository project from `LOAD_PATH`.
  Adding `push!(LOAD_PATH, pwd())` made the direct MathOptInterface import
  available; all remaining **661 MOI checks passed**. No numerical or allocation
  assertion failed in that run, and no existing limits were relaxed.
- Development suite: **450 passed**, including JET and JuMP integration.
- Factorization-specific regressions: **734 passed**. Two deterministic
  membership-count assertions failed before the Markowitz change and passed
  afterwards; the state/order assertions passed on both versions.
- Solver-specific regressions: **166 passed**, covering deadline semantics, stable breakpoint sorting,
  fallbacks, and BigFloat precision changes between calls. Allocation budgets for
  BigFloat/rational breakpoint construction failed on the baseline and passed after caching.
- Independent source review found no blocking or important issues. Its request
  for mixed-precision BigFloat coverage was incorporated.
- All 30 measured production-source hashes identify the first-batch source tree.
  Subsequent basis/Markowitz changes and their separate measurements are covered
  in [the follow-up report](basis_runtime_report.md).

## Remaining opportunities from source inspection

The basis lookup and Markowitz maximum candidates below have since been addressed
in [the follow-up report](basis_runtime_report.md). The remaining rows are candidates,
not measured speedup claims or completed changes.

| Area | Opportunity | Required safeguards / priority |
| --- | --- | --- |
| Markowitz pivot search | Reuse column maxima within one pivot search | Profile repeated scans first; preserve candidate order and stored BigFloat precision; invalidate between pivots. |
| Triangular updates | Reuse lookup positions across read/modify/write operations | Preserve cancellation and row incidence; measure full replacement kernels. |
| Recompute/refactorization | Avoid duplicate basis validation where no caller code can mutate the basis | Logging callbacks make blindly removing the second validation unsafe. |
| Presolve | Share row adjacency across unchanged passes in one invocation | Keep CSC traversal order and stored-zero handling; invalidate on structural changes; no global identity cache. |
| Incremental propagation | Avoid comparing a snapshot known unchanged by the dispatcher | Preserve pending rows, including reverse propagation chains. |
| Model/scaling | Transfer newly owned arrays instead of copying them again | Keep public copying, validation, binary normalization, and mixed BigFloat precision. |
| MPS | Avoid interning ordinary data tokens as header symbols and unnecessary comment regex work | Preserve keyword-shaped names, continuation records, whitespace, and errors. |
| MOI | Avoid unused variable-constraint result evaluation | Internal index/evaluation bookkeeping needs a separate compatibility review. |

The native LU reuse paths, ordered coefficient aggregation, scaling safety checks,
postsolve arithmetic and precision-aware MOI result calculations did not reveal
another immediately justified change with the same small risk as the first batch.

## Reproducing the comparison

Export the baseline source, then run the probe from the repository root:

```sh
mkdir -p /tmp/jsimplex-runtime-baseline
# Omit this export if that directory already contains the frozen baseline.
git archive 28708c7 src | tar -x -C /tmp/jsimplex-runtime-baseline
JULIA_DEPOT_PATH=/tmp/jsimplex-precommit-depot:/home/jspitz/.julia \
  julia --startup-file=no --compiled-modules=existing --project=dev \
  diagnostics/runtime_probe.jl /tmp/jsimplex-runtime-baseline/src \
  diagnostics/runtime_before_after.toml
```

The probe freezes and hashes both source trees, loads them in separate modules,
warms calls, and alternates before/after measurement order. Each case records 15
paired samples, allocation bytes, and residual compilation time. BLAS uses one
thread. Inputs and preparation are outside the measured kernels. Timing should
run without concurrent test/benchmark processes. Small unchanged cases serve as
noise controls; a single benchmark does not establish a universal speedup.
Complete-solve timings cover Float64, four fixtures and PFI/Bartels–Golub with
both refactorization backends. The setter microbenchmarks cover warmed overwrites,
not insertion/deletion or initial storage growth. Iteration-equivalence checks
cover all four update methods and four scalar types.
