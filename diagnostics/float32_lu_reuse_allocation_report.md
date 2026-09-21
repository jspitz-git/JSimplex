# Native Float32 dense LU storage reuse

Float32 now has a dedicated native backend with an active LU and a private spare.
Repeated same-size refactorization copies new coefficients into the spare and
calls Julia 1.13's `lu!(F, B)`, reusing both factors and pivot storage. Only a
successful candidate becomes active. PFI, Forrest–Tomlin, Suhl–Suhl and
Bartels–Golub all use this path. Float64/UMFPACK, other dense scalar types and
Markowitz retain their previous implementations.

## Ownership and capacity

Both slots have a concrete LU type. An earlier `Union{Nothing,LU}` spare caused
one 32-byte LU-wrapper allocation per reset despite reusing its arrays. A
`has_spare` flag avoids that boxing: when false, the spare field aliases the active
LU and must not be used as a candidate. Successful `lu!` returns the new LU status;
that result is installed along with the reused factors and pivots.

Copies get separate slot containers and share only the active LU read-only. Both
source and copy mark it shared. A shared active LU never becomes a reusable spare;
copying copies obeys the same rule. Existing private spares remain private to their
source. Sharing flags are conservative and are not cleared when copies are garbage
collected.

Square dimensions are checked before mutation. A candidate with a different shape
is replaced with a freshly allocated LU, rather than passing incompatible storage
to `lu!`. A failed reused candidate is discarded, leaving the active LU and update
history usable. Repeated empty resets preserve an available nonempty spare for
later growth. This is a two-slot cache, not a pool of every previously encountered
matrix dimension. There are no new concurrency or allocation-failure guarantees
for subsequent history resets.

Two 1,024-square Float32 factor matrices retain approximately 8 MiB rather than
4 MiB, plus pivot arrays and wrappers. Saved copies can retain further LUs. This
trades retained storage for less repeated allocation; it is not a peak-memory
reduction. The first additional LU, missing candidates after failures or copies,
and unmatched dimensions still allocate.

## Measurements

Julia 1.13.0, aarch64-linux-gnu, one Julia and BLAS thread, two warmups and three
samples. Setup is outside kernel measurements. Every measured compilation time
is zero. Counts and bytes are Julia allocation counters; overlapping validation
means timings do not establish a runtime speedup.

The process-only baseline rebuilds LU with `lu!(Matrix{Float32}(B))` on each reset.
Both versions retain the new ownership container, so this isolates reuse rather
than reconstructing the old immutable backend's constructor and copy costs.
The numerical fresh-LU operation is the former production operation.

All four update methods give the same warmed refactorization results on
tridiagonal CSC input, including basis-history reset:

| Dimension | Allocations before → after | Bytes before → after |
| ---: | ---: | ---: |
| 64 | 5 → 0 | 17,048 → 0 |
| 512 | 6 → 0 | 1,052,832 → 0 |
| 1,024 | 6 → 0 | 4,202,656 → 0 |

An additional warmed in-place FTRAN/BTRAN pair allocates zero bytes and objects
for all four update methods.

## Complete solves

The comparison contains 48 pairs: afiro, adlittle and a 64-row diagonal problem,
all four methods, primal/dual, configured refactorization intervals 1/20, presolve
disabled and scaling off. All pairs preserve status, objective where returned,
iteration count and refactorization count. Allocation counts improve in 35 pairs
and remain equal in 13; none increase.

All 16 diagonal cases reach OPTIMAL at objective 64 after 64 pivots. Default
interval 20 results (three actual resets for dual, four for primal):

| Method | Algorithm | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| pfi | dual | 268 → 258 | 101,568 → 67,472 |
| pfi | primal | 435 → 420 | 176,832 → 125,688 |
| forrest_tomlin | dual | 572 → 562 | 115,584 → 81,488 |
| forrest_tomlin | primal | 1,003 → 988 | 201,664 → 150,520 |
| suhl_suhl | dual | 620 → 610 | 119,072 → 84,976 |
| suhl_suhl | primal | 1,051 → 1,036 | 205,152 → 154,008 |
| bartels_golub | dual | 704 → 694 | 121,088 → 86,992 |
| bartels_golub | primal | 1,202 → 1,187 | 209,840 → 158,696 |

These default-interval diagonal solves save 24.4–33.6% of allocated bytes.
Configured interval 1 has larger savings but adaptive dual refactorization means
it does not necessarily refactorize on every iteration.

All 32 afiro/adlittle Float32 cases return NUMERICAL_ERROR in both the allocating
baseline and the new version under the unchanged default tolerances. Their
matching results check preservation of existing behavior; these are not evidence
of successful Netlib solves or a full-solve runtime improvement. Numerical
robustness and tolerance changes are outside this allocation optimization.

## Validation

The initial regression passed 16 solve checks and failed all 16 zero-allocation
budgets against the former implementation. The final new file passes 2,722
assertions covering dense/CSC inputs, changed values and pivots, caller ownership,
dimension changes including zero, successful/singular/nonfinite resets, failure
recovery, saved copies and branching update histories. FTRAN/BTRAN results are
compared against independent Float64 reference solves.

Independent review found no actionable issue. Its separate probe passed 58,716
assertions, including 1,000 randomized copy/reset/failure transitions with storage
alias checks and structured-matrix replacements. It also inspected the installed
Julia `lu!` implementation to check private input copying, pivot reuse and status
handling. Unrelated changes and concurrent mutation were excluded from review;
whole-solver measurements and the full suite are handled separately here.

The complete production suite passes **219,126 assertions** in one run (7m40.4s),
including MOI tests. `git diff --check` passes. All 48 measured solve pairs retain
their prior outcomes, including the Float32 numerical limitations described above.

## Reproduction

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'push!(LOAD_PATH, pwd()); include("test/runtests.jl")'
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/float32_lu_reuse_probe.jl before diagnostics/float32-lu-reuse-before.toml
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/float32_lu_reuse_probe.jl after diagnostics/float32-lu-reuse-after.toml
```

Raw measurements: [before](float32-lu-reuse-before.toml),
[after](float32-lu-reuse-after.toml).
