# Reuse retired triangular update histories

The [preceding audit](pfi_history_reuse_allocation_report.md) still found repeated
history-vector allocations in Forrest–Tomlin, Suhl–Suhl and Bartels–Golub pivots.
All three methods now keep private retired histories and reuse their arrays:
indices/multipliers for Forrest–Tomlin and Suhl–Suhl, transformation steps for
Bartels–Golub. This extends the PFI ownership approach without changing PFI in
this round.

## Ownership and capacity

Each factor records the prefix of its active history shared with saved copies.
`copy_basis_factorization` marks that prefix in source and copy, and gives the
copy an empty private pool. Upper columns remain independently copied as before.
Successful refactorization retires only the unshared suffix; shared arrays are
neither cleared nor pooled, even if the saved copies have become unreachable.
Copies of copies follow the same rule.

Retirement clears logical vector lengths while retaining backing capacity.
Later updates borrow those arrays, with normal growth if capacity is insufficient.
Reference-valued coefficients are removed from retired arrays; the pool retains
the storage rather than the old coefficient objects. A copied factor never
receives the source's already retired buffers.

The existing numerical update loops are unchanged except for obtaining their
arrays from the pool. Validation still precedes borrowing, and failed LU
factorization does not retire the active history. This does not introduce a new
transactional guarantee for numerical errors during an already-started triangular
pivot. Saved factors remain isolated by their copied upper columns and protected
shared histories.

Pools retain history capacity after resets and can hold arrays sized for earlier
denser updates or larger dimensions. This is a cumulative-allocation optimization,
not a promise of lower retained or peak memory. The first retirement may allocate
pool storage, and copying now creates an empty pool and records sharing. Direct
aliases to private update arrays can observe retirement; preserved factors should
be obtained through `copy_basis_factorization`.

## Measurement method

Julia 1.13.0, aarch64-linux-gnu, one Julia thread. Whole solves use Float64/native,
presolve disabled and scaling off. Cases are warmed twice and sampled three times;
mutable kernel setup runs outside measurement. Measured compilation time is zero
in every row. These are Julia allocation counters, not peak RSS or complete
native-library memory accounting. Timings overlapped validation and do not
establish a runtime speedup.

The process-only baseline makes the history-buffer helpers allocate new arrays
and disables retirement. Restoring those allocation calls in the three update
bodies was checked against the saved pre-change source; the numerical code agrees
exactly. Both modes retain the added struct fields and empty pools. Accordingly,
the comparison isolates recycling and is not a byte-exact recreation of the old
constructor layout (these triangular solve baselines have two additional startup
allocations compared with the preceding report). PFI controls are unchanged.

## Repeated pivots

A batch cycles through pivot rows using a tableau column with pivot 1 and a
neighbor coefficient 1/4. Three setup cycles establish capacity and exercise
nonempty multiplier/step histories. Both native and Markowitz backends give the
same results:

| Method | Rows | Pivots | Allocations before → after | Bytes before → after |
| --- | ---: | ---: | ---: | ---: |
| forrest_tomlin | 4 | 16 | 62 → 0 | 2,464 → 0 |
| suhl_suhl | 4 | 16 | 44 → 0 | 1,600 → 0 |
| bartels_golub | 4 | 16 | 32 → 0 | 2,560 → 0 |
| forrest_tomlin | 64 | 64 | 254 → 0 | 10,144 → 0 |
| suhl_suhl | 64 | 64 | 252 → 0 | 10,048 → 0 |
| bartels_golub | 64 | 64 | 128 → 0 | 10,240 → 0 |

This does not make every pivot allocation-free. A separate 32-pivot same-row
regression on an eight-row basis retains four allocations / 800 B for
Forrest–Tomlin and Suhl–Suhl, and two / 192 B for Bartels–Golub. Profiling attributes
these residual allocations to growing packed upper-column buffers, not history.
Before reuse, those batches needed 68 / 2,848 B and 35 / 1,344 B respectively.
A one-row case has no such remaining growth and allocates zero after warmup.

## Iteration audit

All 48 adlittle snapshots and 504 kernel rows retain preparation metadata,
iteration statuses and completed-step counts. Every PFI kernel allocation count
is unchanged. All 18 triangular primal next-iteration/update cases save two to
six allocations and allocated bytes. Their phase-I preparation has already
retired usable histories. The 18 dual next-iteration/update cases are unchanged
at these early preparation depths.

Nine triangular dual reset rows after five pivots add two allocations for initial
pool growth; the other 27 triangular reset rows are unchanged. Every other kernel
allocation count is unchanged. After five steps with steepest-edge pricing:

| Method | Algorithm | Next iteration allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| forrest_tomlin | dual | 8 → 8 | 640 → 640 |
| forrest_tomlin | primal | 4 → 0 | 160 → 0 |
| suhl_suhl | dual | 8 → 8 | 640 → 640 |
| suhl_suhl | primal | 4 → 0 | 160 → 0 |
| bartels_golub | dual | 5 → 5 | 384 → 384 |
| bartels_golub | primal | 7 → 5 | 1,232 → 1,072 |

The full-solve comparison below includes later refactorization cycles and initial
pool costs rather than inferring total savings from these individual snapshots.

## Complete solves

All 32 before/after pairs (afiro/adlittle, four update methods, primal/dual,
refactorization intervals 1/20) reach OPTIMAL with identical objectives, iteration
counts and refactorization counts. All eight PFI controls keep their allocation
counts. Eighteen triangular cases improve both counts and bytes; the six
default-interval afiro cases, with one reset each, are unchanged.

Default-interval adlittle, with five refactorizations per solve:

| Method | Algorithm | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| forrest_tomlin | dual | 1,819 → 1,556 | 561,680 → 550,560 |
| forrest_tomlin | primal | 1,882 → 1,655 | 630,072 → 619,976 |
| suhl_suhl | dual | 1,791 → 1,546 | 560,608 → 551,536 |
| suhl_suhl | primal | 1,876 → 1,661 | 634,888 → 626,744 |
| bartels_golub | dual | 1,986 → 1,828 | 590,528 → 568,704 |
| bartels_golub | primal | 1,983 → 1,836 | 654,616 → 634,488 |

Allocation counts decrease by 7.4–14.5% in these default adlittle cases. Complete
solve totals include pool creation, buffer growth, copying and LU costs.

## Validation

With the allocating helpers restored, the adjusted initial regression passes 24
numerical checks and fails all 24 allocation budgets. The budget allows existing
upper-column growth in multirow pivots; a separate varied-row regression requires
zero allocations with nonempty histories and checks FTRAN/BTRAN against an
independently assembled basis.

The new file passes 11,106 assertions across all three methods, both backends and
five scalar families. Coverage includes branching copies and copies of copies,
shared prefixes/private suffixes, private pools, dimension changes including zero,
validation errors, singular resets and recovery, mixed-type underflow, stored
BigFloat factors, partial rotations and varied pivot rows.

Independent review found no actionable issue. Its randomized probe passed
113,076 assertions over 1,920 operations across all methods, both backends,
Float64/Rational{BigInt}, up to six live copy branches, varying dimensions and
pivots, and successful/singular resets. It checked solves, shared-prefix bounds,
empty retired arrays and disjoint storage between private pools and active
histories. Concurrency and recovery from allocation failure are outside this
change's guarantees, as for the existing mutable factorization workspaces.

The complete production suite passes **213,942 assertions** in one run
(8m01.9s), including MOI tests. All 504 iteration-audit rows and 32 complete-solve
pairs preserve numerical results and statuses as described above.
`git diff --check` passes.

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'push!(LOAD_PATH, pwd()); include("test/runtests.jl")'
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/triangular_history_reuse_probe.jl before diagnostics/triangular-history-reuse-before.toml
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/triangular_history_reuse_probe.jl after diagnostics/triangular-history-reuse-after.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/iteration_allocations.jl adlittle --basis-update=all --pricing=all --samples=3 --profile --output=diagnostics/iteration-kernels-triangular-history-reuse.toml
```

Raw data: [before](triangular-history-reuse-before.toml),
[after](triangular-history-reuse-after.toml),
[iteration baseline](iteration-kernels-pfi-history-reuse.toml),
[iteration after](iteration-kernels-triangular-history-reuse.toml).
