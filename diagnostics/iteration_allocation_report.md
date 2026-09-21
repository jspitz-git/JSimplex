# Repeated simplex kernel allocation audit

This audit redirects the allocation work from presolve to repeated simplex
operations. It adds measurement tooling and tests; it makes no production solver
changes. The baseline includes allocation rounds 1–177.

## Measurement contract

`dev/iteration_allocations.jl` measures Float64 with native refactorization
(UMFPACK), presolve disabled, and scaling off. It separates basis assembly,
recomputation, refactorization, FTRAN, BTRAN, pricing, ratio tests, basis updates,
and complete iterations. All runs use Julia 1.13.0, aarch64-linux-gnu, one Julia
thread, two warmups and three measured samples, with GC before each sample.
Numbers below are minimum allocations/bytes per call, not retained or peak memory.

Each sample prepares a fresh state by replaying the same real solver steps
**outside measurement**. Copying a factorization loses spare vector capacity and
can overstate allocations, especially for triangular update methods. Compilation
warmup, MPS parsing, initialization, dual feasibility preparation, and primal
phase I are excluded. Primal states with artificials complete phase I and enter
phase II with artificials fixed at zero, following the solver's transition;
they are explicitly labeled in the raw data.

Snapshots are taken immediately after preparation and after five further
iterations (or earlier termination). These are early updated bases, not a claim
about late iterations or maximum update depth. Whole iterations replay pristine
states before separate probes prepare pricing caches. `primal_pricing_before_probe`
means the cache state reached naturally; `primal_pricing` measures the state after
one extra pricing call. In particular, phase I may already initialize pricing.

A refactorization row calls `recompute!(; refactorize=true)`, including basis
assembly and refreshed solution vectors. An update row calls `replace_column!`
on a genuine entering column after FTRAN; it does not include the complete pivot.
Stage counts must not be added together: kernels overlap, and materializing a
standalone return value can differ from consuming it inside an iteration.

Profiling runs separately at sample rate 1.0 and attributes allocations to the
nearest JSimplex source frame. Profile records and runtime counters need not match
(e.g. profiler overhead and library allocation accounting); use profiles to locate
work, not to reconstruct totals. These are Julia counters, not all C-library
allocations. Concurrent validation/measurement makes elapsed times unsuitable
for claiming a speed improvement.

## Five-fixture PFI survey

Fixtures: afiro, adlittle, kb2, sc50a, flugpl; both algorithms use steepest-edge
pricing. All 207 measured kernel rows had zero compilation time. Nineteen
snapshots had a real next pivot, and every measured whole iteration completed
one step with status `CONTINUE`. The remaining snapshot, primal flugpl after
requesting five steps, had already reached `OPTIMAL`; unavailable pivot stages
are omitted rather than reported as zero-cost iterations.

FTRAN, BTRAN, recomputation, dual edge selection, tableau-row pricing, dual Harris
ratio testing, and warmed primal pricing allocated **zero** in every applicable
PFI snapshot. Initial primal pricing on kb2 and sc50a allocated 2 times / 64 bytes;
other natural pricing states were already warm.

Results after five requested steps (allocations / bytes):

| Fixture | Algorithm | Complete iteration | Basis update | Refactorization |
| --- | --- | ---: | ---: | ---: |
| afiro | dual | 7 / 416 | 6 / 384 | 89 / 21,360 |
| afiro | primal | 11 / 448 | 6 / 352 | 89 / 19,872 |
| adlittle | dual | 7 / 288 | 6 / 256 | 89 / 39,296 |
| adlittle | primal | 11 / 768 | 6 / 672 | 87 / 72,712 |
| kb2 | dual | 7 / 416 | 6 / 384 | 89 / 42,272 |
| kb2 | primal | 11 / 576 | 6 / 480 | 89 / 42,208 |
| sc50a | dual | 7 / 288 | 6 / 256 | 87 / 68,072 |
| sc50a | primal | 11 / 480 | 6 / 384 | 89 / 31,952 |
| flugpl | dual | 8 / 336 | 6 / 256 | 89 / 14,976 |
| flugpl | primal | — (optimal) | — (optimal) | 87 / 39,800 |

Across all PFI snapshots, basis assembly uses 6 allocations / 624–3,088 bytes;
refactorization uses 87–89 allocations / 14,096–72,712 bytes. Updates in the
five-step states use 6 allocations each. Dual bound-flipping ratio tests use
1 allocation / 32 bytes, except flugpl after five steps (2 / 80). Standalone
primal ratio tests use 3 / 64; whole-iteration profiles also locate allocations
in the primal ratio path, so this deserves investigation beyond standalone
return-value overhead.

## Basis methods and pricing

A second survey covers adlittle with PFI, Forrest–Tomlin, Suhl–Suhl and
Bartels–Golub, each with Dantzig, Devex and steepest-edge pricing, for both
algorithms and both preparation depths. Raw data retains each combination.

All 48 snapshots were ready, all 48 measured iterations completed one step,
and all 504 kernel rows had zero compilation time. FTRAN, BTRAN, recomputation,
pricing, dual edge selection, and dual Harris ratio testing were allocation-free
for every applicable combination. Primal ratio tests remained at 3 / 64 and
bound-flipping ratio tests at 1 / 32.

The steepest-edge subset after five steps (allocations / bytes):

| Method | Algorithm | Complete iteration | Basis update | Refactorization |
| --- | --- | ---: | ---: | ---: |
| pfi | dual | 7 / 288 | 6 / 256 | 89 / 39,280 |
| pfi | primal | 11 / 768 | 6 / 672 | 87 / 72,728 |
| forrest_tomlin | dual | 11 / 736 | 10 / 704 | 315 / 47,312 |
| forrest_tomlin | primal | 13 / 640 | 8 / 544 | 313 / 80,936 |
| suhl_suhl | dual | 11 / 736 | 10 / 704 | 315 / 47,328 |
| suhl_suhl | primal | 13 / 608 | 8 / 512 | 313 / 80,936 |
| bartels_golub | dual | 8 / 480 | 7 / 448 | 315 / 47,312 |
| bartels_golub | primal | 14 / 1,136 | 9 / 1,040 | 313 / 80,936 |

The triangular methods allocate more during refactorization (313–315 allocations
in these five-step states), including rebuilding their owned triangular storage.
Pricing changes the pivot path and update size: for example, Bartels–Golub dual
Devex uses 18 allocations / 1,792 bytes for its next whole iteration, compared
with 8 / 480 for steepest edge. This compares the states reached by each method,
not identical bases forced onto different algorithms. Small byte differences
between the two independent native-refactorization runs are not an optimization
result; allocation counts agree for the overlapping configurations.

## Priorities for subsequent changes

1. **PFI update construction.** Every pivot owns packed index/value arrays.
   `src/factorization.jl` first creates singleton vectors and then reserves space
   for all nonzeros. Profiles show both construction and growth. Allocate the
   final capacity once, preserving ownership, mixed-type conversion semantics,
   and all pivot checks; validate gains on complete iterations.
2. **Primal ratio test.** Investigate inference and boxing around optional steps
   and the returned state in `_primal_ratio` and its iteration call site. Preserve
   relaxed Harris selection, strict fallback, tie behavior, and numerical checks.
3. **Bound-flipping ratio scratch.** `_bound_flipping_ratio_test` constructs fresh
   `Int[]` lists, including fallback paths without flips. Consider workspace-owned
   storage, after checking aliasing and lifetime across retries.
4. **Refactorization reuse.** The largest per-call byte volume is here, with
   profiles pointing to `lu(sparse_basis)` and owned CSC assembly arrays. Measure
   actual refactorization frequency and larger models before ranking its total
   impact. Any symbolic/numeric reuse must respect changing sparsity and preserve
   failure/retry semantics; the present audit does not establish safe reuse.
5. **Triangular updates at greater depth.** Use the method survey to locate update
   growth, then repeat on longer update chains and larger sparse bases. Do not
   change the default method merely from these allocation counts.

Already zero-allocation kernels are lower priority for allocation work on this
Float64 configuration. This does not claim they have negligible CPU cost.
Markowitz, non-Float64 arithmetic, long runs, terminal certificates, cleanup,
and full-solve runtime comparisons remain outside this survey. Preparation
failure statuses describe the audit's ability to establish a measurable state;
they are not a replacement for the full solver's infeasibility certification.

## Reproduction and validation

```sh
julia --startup-file=no --compiled-modules=existing --project=dev dev/iteration_allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile --output=diagnostics/iteration-kernels-pfi.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/iteration_allocations.jl adlittle --basis-update=all --pricing=all --samples=3 --profile --output=diagnostics/iteration-kernels-backends.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/tests/iteration_allocation_tests.jl
```

The focused test suite passes 282 assertions: independent replayed states for all
four basis methods, original-input preservation, FTRAN/BTRAN residuals after
updates, refactorization isolation, stage selection, zero-allocation solve and
recompute controls, iteration status/step reporting, CLI validation and TOML
metadata. The test file is included in `dev/tests/runtests.jl`. Independent review
identified the clone-capacity measurement defect; final review found no blocking
issues after replay replaced cloning. The production solver suite was not rerun
for this tooling-only addition.

Raw results: [PFI fixtures](iteration-kernels-pfi.toml) and
[all basis/pricing combinations](iteration-kernels-backends.toml).
