# Reuse the leaving triangular column during a pivot

A significant repeated allocation remained after the [triangular reset change](triangular_reset_allocation_report.md):
`_rotate_columns!` discarded the leaving packed column and allocated new index
and value arrays for the entering spike on every pivot.

The rotation now repacks that column's owned arrays with `_packed_column!`, then
moves the column through the existing rotation. The spike is separate scratch and
has already been computed before repacking. The helper retains the spare entry
needed by subsequent row rotations, omits stored zeros, and overwrites the whole
logical result. Buffers grow only as needed. The allocating `_packed_column`
helper retains its existing semantics.

This applies to Forrest–Tomlin, Suhl–Suhl and Bartels–Golub. It preserves full and
partial rotations, permutations, update records and all arithmetic. Factor
copies own separate upper arrays; reusing the leaving column does not alter saved
factors. PFI is unchanged.

## Measurements

Same environment as the prior audit: Julia 1.13.0, aarch64-linux-gnu, one Julia
thread, Float64/native, presolve disabled and scaling off. Each case is warmed
twice and measured three times, with setup/replay outside measurement. All rows
have zero measured compilation time. Timings overlapped validation and do not
establish a runtime speedup.

The 48-snapshot adlittle audit covers four basis methods, three pricing rules,
both algorithms and two preparation depths. All 36 triangular next-iteration
and update rows save two or four allocations. All 12 PFI controls and every other
kernel allocation count are unchanged across the 504 measured rows. Preparation
metadata, terminal/iteration statuses and completed-step counts agree exactly.

Whole iterations after five steps, steepest-edge pricing:

| Method | Algorithm | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| pfi | dual | 4 → 4 | 192 → 192 |
| pfi | primal | 4 → 4 | 608 → 608 |
| forrest_tomlin | dual | 10 → 8 | 704 → 640 |
| forrest_tomlin | primal | 8 → 4 | 544 → 160 |
| suhl_suhl | dual | 10 → 8 | 704 → 640 |
| suhl_suhl | primal | 8 → 4 | 512 → 160 |
| bartels_golub | dual | 7 → 5 | 448 → 384 |
| bartels_golub | primal | 9 → 7 | 1,040 → 1,232 |

Allocated bytes do not improve in every individual step: Bartels–Golub primal
above saves two allocations but grows backing buffers geometrically, using 192
more bytes in that step. This is visible in the raw profiles. Whole-solve results
below improve in both counts and bytes for every triangular case measured.
A focused rotation with established capacity drops from four allocations / 640
bytes to zero; complete pivots still allocate update-history storage and may
expand other buffers.

## Complete solves

The reproducible probe runs afiro and adlittle with all four methods, both
algorithms, and initial refactorization intervals 20 (default) and 1 (stress).
The baseline process restores exactly the old allocating rotation method; other
code includes all preceding optimizations. The probe does not rewrite repository
files. The restored method was checked against the saved pre-change source.

All 32 before/after pairs reach OPTIMAL with identical objective, iteration and
refactorization counts. All 24 triangular cases use fewer allocations and bytes;
the eight PFI controls keep the same allocation counts. Small byte differences
in unchanged native-library paths are not counted as an optimization.

Default-interval complete solves on adlittle:

| Method | Algorithm | Allocations before → after | Bytes before → after |
| --- | --- | ---: | ---: |
| pfi | dual | 1,206 → 1,206 | 542,224 → 541,856 |
| pfi | primal | 1,244 → 1,244 | 583,864 → 583,288 |
| forrest_tomlin | dual | 2,136 → 1,840 | 601,136 → 567,264 |
| forrest_tomlin | primal | 2,142 → 1,902 | 661,880 → 633,784 |
| suhl_suhl | dual | 2,112 → 1,812 | 601,600 → 566,176 |
| suhl_suhl | primal | 2,128 → 1,896 | 663,080 → 638,696 |
| bartels_golub | dual | 2,269 → 2,007 | 599,360 → 595,280 |
| bartels_golub | primal | 2,199 → 2,003 | 662,232 → 658,392 |

For these default adlittle solves, triangular allocation counts drop by 8.9–14.2%.
This establishes a useful repeated-work saving rather than only a helper-level
microbenchmark result.

## Storage tradeoff and remaining work

The existing upper-column buffers now retain their capacity across replacement
pivots as well as refactorization. Geometric growth can overallocate on individual
calls. A dense history can leave O(n²) backing storage even when current columns
are sparse; this is not a reduction in peak or retained memory. Removed
reference-valued entries remain collectible. Shallow references to an internal
upper column observe its new contents, while `copy_basis_factorization` remains
isolated.

The remaining prominent sites in this Float64 audit are new LU factors at
refactorization and owned update-history arrays. Native backend objects are
shared by factor copies (`_copy_backend`), so in-place LU reuse would need an
explicit ownership solution. Reusing update arrays also cannot overwrite entries
still held by saved factors. CSC basis assembly still allocates its owned result;
its practical priority should be reassessed on larger problems and actual
refactorization frequency. The small initial pricing-cache allocation is lower
priority than repeated work. This audit does not establish that all remaining
allocations are unavoidable, nor does it cover every numeric type's performance.

## Validation and reproduction

The regression initially passed 756 assertions and failed six checks as expected:
all three warmed rotations allocated four objects / 640 bytes. The expanded test
file passes **857 assertions**, covering both native and Markowitz backends,
all three triangular methods, five scalar families, repeated real pivots,
independent saved factors, empty/zero/growing packed columns, signed zeros,
NaN/infinities and stored BigFloat precision under lower ambient precision.
It is registered in `test/runtests.jl`.

Independent review found no correctness issue. Its differential probe also
matched the old implementation over 3,000 randomized rotations (12,000 checks),
including partial ranges, column uniqueness and separation from spike scratch.

The complete production suite passes **197,409 assertions** in one run
(8m27.1s), including MOI tests. All 504 audit rows and all 32 complete-solve pairs
were checked against the reported counts and unchanged numerical results.
`git diff --check` passes.

```sh
julia --startup-file=no --compiled-modules=existing --project=dev -e 'push!(LOAD_PATH, pwd()); include("test/runtests.jl")'
julia --startup-file=no --compiled-modules=existing --project=dev dev/iteration_allocations.jl adlittle --basis-update=all --pricing=all --samples=3 --profile --output=diagnostics/iteration-kernels-column-reuse.toml
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/triangular_column_reuse_solve_probe.jl before diagnostics/column-reuse-solves-before.toml
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/triangular_column_reuse_solve_probe.jl after diagnostics/column-reuse-solves-after.toml
```

Raw data: [iteration baseline](iteration-kernels-triangular-reset.toml),
[iteration after](iteration-kernels-column-reuse.toml),
[solves before](column-reuse-solves-before.toml),
[solves after](column-reuse-solves-after.toml).
