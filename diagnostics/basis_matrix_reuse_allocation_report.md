# Reuse CSC assembly storage during refactorization

The [previous audit](triangular_column_reuse_allocation_report.md) identified
owned CSC basis assembly as one of the remaining allocations at refactorization.
`recompute!(workspace; refactorize=true)` now assembles into private workspace
storage, retaining column pointers, row indices and values across calls. It also
retains the initial slack basis after creating the initial factorization, so a
workspace does not need a second set of assembly arrays on its first reset.
Auxiliary workspaces start with an empty cache and populate it on demand.

The public `basis_matrix` function continues to return an independent result.
Both entry points share the same CSC assembly loop, including stored zeros and
negative slack columns. Validation runs before modifying the cache. The borrowed
matrix must not be retained across another assembly on the same workspace.

Native UMFPACK copies its input CSC arrays, dense LU creates its own matrix, and
Markowitz creates its own factor data. Reusing assembly arrays therefore does not
change either current or saved factorizations. Singular factorization still
leaves the old factor usable. This does not reuse or mutate an existing LU.

Shrinking the logical row/value lengths uses `resize!`, preserving their backing
capacity for later growth. Memory retained by the cache scales with the largest
assembled basis (plus geometric growth), not the most recent number of entries.
A workspace now keeps one CSC assembly buffer alive; lower cumulative allocation
is not a claim of lower retained or peak memory. Existing refinement and basis
restoration paths that call the public allocating function remain unchanged.

## Measurements

Julia 1.13.0, aarch64-linux-gnu, one Julia thread, Float64/native; presolve disabled
and scaling off for complete solves. Each case is warmed twice and measured three
times. Setup is outside kernel measurements. These are Julia allocation counters,
not external-library memory or peak RSS. Concurrent verification makes the recorded
timings unsuitable for runtime-speed claims. All measured compilation times are
zero.

The process-only baseline restores the old `recompute!` and initialization methods;
those restored definitions were checked against the saved pre-change source.
It retains the added nullable field in `SimplexScratch`, so initialization byte
counts are not a byte-exact reproduction of the old struct layout. Both modes use
the same larger struct; comparisons isolate assembly-buffer reuse.

For established capacity, a tridiagonal basis with diagonal 4 and off-diagonals
−1 shows the following allocation reduction. All four basis-update methods give
the same assembly results:

| Rows | Assembly allocations before → after | Assembly bytes before → after |
| ---: | ---: | ---: |
| 64 | 6 → 0 | 3,904 → 0 |
| 512 | 9 → 0 | 28,952 → 0 |
| 4,096 | 9 → 0 | 229,656 → 0 |

Refactorization including refresh drops from 89 to 83 allocations at 64 rows,
and from 97 to 88 at 512 and 4,096 rows. LU creation remains the dominant cost.
Small differences between whole-refactorization bytes and the assembly-only
saving come from native-library paths; they are not additional optimizations.

The unchanged iteration-audit harness measures 48 adlittle snapshots (four
methods, three pricing rules, two algorithms, two preparation depths), totaling
504 kernel rows. Every one of the 48 refactorization rows removes six allocations;
all other kernel allocation counts are unchanged. Snapshot metadata, iteration
statuses and completed-step counts match. After five steps with steepest-edge
pricing, dual refactorization drops from 89 to 83 allocations and primal from 87
to 81 for every method. The public `basis_matrix` audit remains unchanged because
its independent-result contract is preserved.

## Complete solves

All 32 before/after pairs (afiro/adlittle, four basis methods, primal/dual,
refactorization intervals 1/20) reach OPTIMAL with identical objectives, iteration
counts and refactorization counts. Every pair has fewer allocations. Allocated
bytes decrease in 28 pairs; the four default-interval afiro dual cases increase
by 128–144 bytes while removing three allocations. Those cases perform only one
refactorization, so initial buffer growth and retention do not amortize across
multiple resets.

Default-interval adlittle solves, each with five refactorizations:

| Method | Algorithm | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| pfi | dual | 1,206 → 1,183 | 542,208 → 535,392 |
| pfi | primal | 1,244 → 1,222 | 583,816 → 579,192 |
| forrest_tomlin | dual | 1,840 → 1,817 | 567,232 → 561,712 |
| forrest_tomlin | primal | 1,902 → 1,880 | 634,264 → 629,720 |
| suhl_suhl | dual | 1,812 → 1,789 | 566,080 → 560,624 |
| suhl_suhl | primal | 1,896 → 1,874 | 639,256 → 634,712 |
| bartels_golub | dual | 2,007 → 1,984 | 595,536 → 590,704 |
| bartels_golub | primal | 2,003 → 1,981 | 658,872 → 654,232 |

For adlittle primal with interval 1 (83 refactorizations), all methods save 490
allocations and about 269 kB over the complete solve. PFI drops from 8,059 to
7,569 allocations. This change therefore applies to both PFI and triangular
methods, with the largest cumulative benefit when refactorization is frequent.

## Validation and reproduction

The initial allocation regression passed eight assertions and failed eight as
expected: refactorization plus assembly needed eight allocations beyond a direct
factor reset. The new test file now passes 2,311 assertions, including all four
update methods, both backends and five scalar families, saved factors, destructive
scratch overwrites after LU creation, independent public matrices, auxiliary
workspaces, singular/invalid bases, recovery, stored zeros, empty columns/rows,
stored BigFloat precision and zero-allocation sparse-to-dense regrowth.
The neighboring assembly/workspace files add 146 passing assertions.

Independent review found no correctness issue. Its additional adversarial probe
passed 64 checks across both backends and all four methods for Float32/Float64:
clearing the cached arrays and corrupting column pointers left current and saved
solves intact, and the next recomputation restored valid storage.

The complete production suite passes **199,720 assertions** in one run
(7m33.8s), including MOI tests. The 504-row iteration audit and all 32 complete-solve
pairs preserve the numerical results and statuses described above.
`git diff --check` passes.

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'push!(LOAD_PATH, pwd()); include("test/runtests.jl")'
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/basis_matrix_reuse_probe.jl before diagnostics/basis-matrix-reuse-before.toml
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/basis_matrix_reuse_probe.jl after diagnostics/basis-matrix-reuse-after.toml
julia --startup-file=no --compiled-modules=existing --project=dev dev/iteration_allocations.jl adlittle --basis-update=all --pricing=all --samples=3 --profile --output=diagnostics/iteration-kernels-basis-matrix-reuse.toml
```

Raw data: [before](basis-matrix-reuse-before.toml),
[after](basis-matrix-reuse-after.toml),
[iteration baseline](iteration-kernels-column-reuse.toml),
[iteration after](iteration-kernels-basis-matrix-reuse.toml).
