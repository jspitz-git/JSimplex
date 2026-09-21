# Reuse UMFPACK LU through two private slots

Native Float64 refactorization now alternates between an active LU and a private
candidate. `lu!` reuses the candidate's Julia arrays and workspace. Symbolic
analysis is reused only when dimensions, column pointers and row indices match
the candidate exactly; otherwise `reuse_symbolic=false` rebuilds it. All four
basis update methods use this backend.

The active LU changes only after successful factorization. A failed `lu!` drops
the possibly damaged candidate and leaves the active LU and update history
usable. Nonsquare input is rejected before mutation. Empty bases retain private
storage for later growth. There is no new guarantee for allocation failure during
later basis-history resets or for concurrent use of a mutable factorization.

Saved factors receive a separate backend container and share only the active LU,
read-only. Both containers mark that LU shared, so neither can recycle it. Private
candidates are never shared, including when copying a copy. This conservative
ownership flag does not attempt to detect when saved copies become unreachable.
Two slots need warming; a copy or failed candidate can require a fresh LU again.

This reduces allocation traffic, not necessarily retained memory: an independent
factor can retain two complete LUs, and saved copies can retain additional older
factors. UMFPACK still constructs a new native numeric factorization inside `lu!`.
Dense LU and Markowitz backends are unchanged.

## Measurement

Julia 1.13.0, aarch64-linux-gnu, one Julia thread. Cases are warmed twice and
sampled three times; kernel setup is replayed outside measurement. Compilation
time is zero in every probe row. Counts and bytes use Julia allocation counters,
not peak RSS or complete native-library memory accounting. Timings overlapped
validation and do not establish a runtime speedup.

The process-only baseline replaces refactorization with fresh `lu` while keeping
the new ownership container in both modes. It installs the result only after
success and discards the spare. This isolates LU reuse without adding an artificial
wrapper allocation to each baseline reset; it is not a byte-exact recreation of
the former immutable backend or its copying costs. Whole-solve baseline counts
are two higher than in the preceding report because of the ownership containers.

## Repeated refactorization

The input is a tridiagonal matrix with diagonal 4 and off-diagonals -1. The
same-pattern case doubles stored values; the changed-pattern case adds one corner
entry. Each sample starts with two private slots containing the original pattern,
so changed-pattern measurements really rebuild symbolic analysis every time.
All four update methods give the same figures:

| Dimension | Pattern | Allocations before → after | Bytes before → after |
| ---: | --- | ---: | ---: |
| 64 | same | 81 → 32 | 84,128 → 54,400 |
| 512 | same | 86 → 32 | 549,336 → 331,088 |
| 4,096 | same | 86 → 32 | 4,272,936 → 2,544,560 |
| 64 | changed | 81 → 64 | 88,336 → 91,424 |
| 512 | changed | 86 → 64 | 579,352 → 592,816 |
| 4,096 | changed | 86 → 64 | 4,510,504 → 4,628,384 |

Same-pattern allocation counts fall by 60.5–62.8%. Changed-pattern counts fall by
21.0–25.6%, but allocated bytes increase by 2.3–3.5% in these examples. Thus a
lower object count does not imply lower byte traffic for every refactorization.

## Complete solves and iteration audit

All 32 before/after pairs (afiro/adlittle, four update methods, primal/dual,
refactorization intervals 1/20, presolve disabled, scaling off) reach OPTIMAL with
identical objectives, iteration counts and refactorization counts. Allocation
counts improve in 24 cases; the eight default-interval afiro cases, which have
only one reset and cannot benefit from a warmed spare, are unchanged.

Default-interval adlittle:

| Method | Algorithm | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| pfi | dual | 922 → 867 | 508,240 → 503,024 |
| pfi | primal | 1,027 → 955 | 567,576 → 567,192 |
| forrest_tomlin | dual | 1,558 → 1,503 | 550,208 → 545,536 |
| forrest_tomlin | primal | 1,657 → 1,585 | 620,248 → 619,864 |
| suhl_suhl | dual | 1,548 → 1,493 | 551,152 → 546,480 |
| suhl_suhl | primal | 1,663 → 1,591 | 626,872 → 626,488 |
| bartels_golub | dual | 1,830 → 1,775 | 568,608 → 564,304 |
| bartels_golub | primal | 1,838 → 1,766 | 634,872 → 634,376 |

These full-solve counts decrease by 3.0–7.0%; byte savings are much smaller.
The new iteration audit preserves all 48 snapshot metadata records and all 504
stage labels/statuses/completed-step counts against the preceding audit. All 24
primal refactorization rows improve from 81 to 62 allocations, with lower bytes;
their phase-I preparation has already made a reusable candidate available. The
other 480 kernel allocation counts are unchanged, including early dual resets.

## Validation

The initial regression against fresh LU passed eight solve checks and failed all
four allocation budgets. The final budget requires repeated same-pattern resets
to allocate at most half as many objects as fresh LU.

The new test file passes 2,432 assertions across all four update methods. Coverage
includes changed values, equal-nnz changes to column pointers or row indices,
input ownership, dimensions including zero, singular candidates with and without
shared active LUs, recovery, branching saved copies and mixed pivot/reset sequences.
FTRAN and BTRAN are compared with independently assembled basis solves.

Independent review found no actionable issue. Its randomized probe passed 15,140
assertions across 180 mixed operations per method, seven live branches, dimensions
0–12, successful/singular resets, pivots, copies and explicit active/spare ownership
checks. Installed Julia's `lu!` implementation was inspected for input copying,
dimension changes and failure semantics.

The complete production suite passes **216,386 assertions** in one run (8m03.9s),
including MOI tests. `git diff --check` passes. The complete-solve comparison and
iteration audit preserve numerical results and statuses as described above.

## Other uses of swapping

Dual high-precision refinement currently saves and restores reduced costs by
copying whole vectors in `_try_refine_dual_pivot!` and `_try_refine_dual_prices!`.
The newly computed price vector could become the candidate, with the old vector
retained for rollback and references swapped on acceptance/rejection. Before
implementing this, audit borrowed references and measure how often these repair
paths run. This round does not change them.
The subsequent [feasibility investigation](dual_price_swap_feasibility_report.md)
checks ownership, failure paths, allocation savings and repair frequency.

The same active/candidate approach is possible for dense LU, and potentially for
Markowitz after adding reusable workspace. Ordinary pricing and ratio-test scratch
is better reused directly when no previous valid state needs to survive a failed
candidate; adding a second buffer there alone would not remove more allocations.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'push!(LOAD_PATH, pwd()); include("test/runtests.jl")'
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/umfpack_reuse_probe.jl before diagnostics/umfpack-reuse-before.toml
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/umfpack_reuse_probe.jl after diagnostics/umfpack-reuse-after.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/iteration_allocations.jl adlittle --basis-update=all --pricing=all --samples=3 --profile --output=diagnostics/iteration-kernels-umfpack-reuse.toml
```

Raw data: [before](umfpack-reuse-before.toml), [after](umfpack-reuse-after.toml),
[iteration baseline](iteration-kernels-triangular-history-reuse.toml),
[iteration after](iteration-kernels-umfpack-reuse.toml).
