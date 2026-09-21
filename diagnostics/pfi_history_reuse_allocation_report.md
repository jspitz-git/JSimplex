# Reuse retired PFI eta vectors

After [CSC assembly reuse](basis_matrix_reuse_allocation_report.md), the audit
still attributed PFI pivot allocations to the owned index/value arrays of every
eta update. PFI now retains private retired arrays at successful refactorization
and reuses them for later pivots. The numerical update and solve algorithms are
unchanged. This round does not change the triangular basis methods.

## Ownership and lifetime

Active histories remain append-only. `copy_basis_factorization` shares active
eta arrays as before, marking the shared prefix in both source and copy. Only
updates appended after that prefix can be retired into a factor's private pool.
Shared arrays are never cleared or reused, even when their copies are no longer
reachable. Copies start with an empty pool; they do not receive the source's
retired buffers. Copies of copies obey the same rule.

On successful native or Markowitz refactorization, unshared eta arrays are
logically emptied and pooled; the active history and shared-prefix marker reset.
`resize!`/`empty!` retain backing capacity for later growth. Reference-valued
coefficients are cleared, so retiring a BigFloat/BigInt history does not keep
those coefficient objects alive merely for buffer reuse.

Pivot validation and inversion run before borrowing retired buffers. Mixed-type
coefficients are still converted once; sparsity is checked after conversion.
A later conversion/arithmetic exception can discard a borrowed spare buffer, but
cannot overwrite active or shared history. A failed factorization does not retire
updates, preserving the old factor and its copies.

The pool retains storage up to the history's allocation high-water mark, with
per-buffer capacity reflecting earlier density/dimensions. This reduces repeated
allocation, not necessarily retained or peak memory. The first retirement can
allocate the pool's backing vector. Copying now also creates an empty private
pool and records sharing; copying is not an allocation optimization in this round.
Direct aliases to internal eta arrays can observe retirement; callers requiring
a preserved factor must use `copy_basis_factorization`.

## Measurements

Julia 1.13.0, aarch64-linux-gnu, one Julia thread. Whole solves use Float64/native,
presolve disabled and scaling off. Each case is warmed twice and sampled three
times, with setup outside kernel measurements. All measured compilation times
are zero. Julia allocation counters do not measure all native-library allocations
or peak RSS. Timings overlapped validation and do not establish a runtime speedup.

The process-only baseline restores the old allocating `replace_column!` body
(verified against the saved pre-change method) and disables retirement. Both
modes retain the enlarged PFI struct and empty private pool, so these comparisons
isolate recycling rather than reproduce the old constructor's byte layout.
This adds two startup allocations to these PFI solve baselines compared with
the preceding report. Triangular controls do not have the new PFI fields.

After preparing and retiring sufficient owned history, batches of dense updates
need no Julia allocations. Both native and Markowitz backends give these results:

| Rows | Pivots | Allocations before → after | Bytes before → after |
| ---: | ---: | ---: | ---: |
| 64 | 1 | 4 → 0 | 1,152 → 0 |
| 64 | 20 | 80 → 0 | 23,040 → 0 |
| 512 | 1 | 6 → 0 | 8,336 → 0 |
| 512 | 20 | 120 → 0 | 166,720 → 0 |

New or insufficient-capacity pools still allocate. These zero-allocation results
apply to scalar types without arithmetic allocations, here Float64, and to
established capacity; they do not mean every PFI pivot is allocation-free.

## Iteration audit

The unchanged harness measures 48 adlittle snapshots, totaling 504 kernel rows.
All snapshot metadata, iteration statuses and completed-step counts match the
preceding audit. All 36 triangular snapshots keep their kernel allocation counts.

PFI primal preparation has already performed phase-I refactorization, allowing
retired storage to help the next pivot: all six primal next-iteration and update
rows save two or four allocations. Three are zero-allocation. The six dual
next-iteration/update rows are unchanged. Three dual refactorization rows after
five pivots add two allocations to establish the pool (for example 83 → 85 with
steepest-edge pricing); the other nine PFI reset rows are unchanged. Every other
kernel allocation count is unchanged.

Some individual primal steps allocate more bytes despite fewer objects: after
five steepest-edge steps, 4 allocations / 608 B becomes 2 / 1,248 B because a
reused small buffer grows geometrically. The zero-growth path is demonstrated
separately above; whole-solve results below include these growth costs.

## Complete solves

All 32 before/after solve pairs (afiro/adlittle, four update methods, primal/dual,
intervals 1/20) reach OPTIMAL with identical objectives, iteration counts and
refactorization counts. The 24 triangular controls retain their allocation counts.
Six PFI pairs improve both counts and bytes; the two default-interval afiro
pairs are unchanged because they offer no benefit from subsequent buffer reuse.

| Dataset | Algorithm | Interval | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: | ---: |
| afiro | dual | 1 | 1,792 → 1,734 | 414,280 → 412,696 |
| afiro | dual | 20 | 460 → 460 | 78,768 → 78,768 |
| afiro | primal | 1 | 1,942 → 1,887 | 418,000 → 413,664 |
| afiro | primal | 20 | 614 → 614 | 109,104 → 109,104 |
| adlittle | dual | 1 | 2,032 → 1,763 | 920,328 → 903,080 |
| adlittle | dual | 20 | 1,185 → 920 | 535,488 → 508,128 |
| adlittle | primal | 1 | 7,571 → 7,252 | 5,913,240 → 5,877,688 |
| adlittle | primal | 20 | 1,224 → 1,025 | 579,288 → 567,160 |

At the default interval, adlittle PFI allocation counts decrease by 22.4% dual
and 16.3% primal. Both runs perform five refactorizations. The interval-1 primal
case performs 83 resets and saves 319 allocations overall, including pool growth
and the remaining LU/refactorization costs.

## Validation

The initial regression passed four checks and failed four allocation assertions
as expected: each post-refactorization update allocated four objects / 1,152 bytes.
The expanded new file passes 3,068 assertions across both backends and five scalar
families, copies/copies of copies, shared-prefix/private-suffix retirement,
independent pools, dense-to-sparse-to-dense reuse, dimension changes including
zero, invalid inputs, conversion failures, singular reset, mixed-type underflow
and stored BigFloat precision. The existing PFI/iteration allocation files add
99 passing assertions.

Independent review found no actionable issue. Its separate seeded probe passed
189,412 ownership/solve checks across 500 mixed operations per backend, varied
pivot rows, multiple retired buffers and up to 12 live factor copies.

The complete production suite passes **202,836 assertions** in one run
(7m32.5s), including MOI tests. The 504-row iteration audit and all 32 complete
solve pairs preserve their numerical results and statuses. `git diff --check`
passes.

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'push!(LOAD_PATH, pwd()); include("test/runtests.jl")'
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/pfi_history_reuse_probe.jl before diagnostics/pfi-history-reuse-before.toml
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/pfi_history_reuse_probe.jl after diagnostics/pfi-history-reuse-after.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/iteration_allocations.jl adlittle --basis-update=all --pricing=all --samples=3 --profile --output=diagnostics/iteration-kernels-pfi-history-reuse.toml
```

Raw data: [before](pfi-history-reuse-before.toml),
[after](pfi-history-reuse-after.toml),
[iteration baseline](iteration-kernels-basis-matrix-reuse.toml),
[iteration after](iteration-kernels-pfi-history-reuse.toml).
