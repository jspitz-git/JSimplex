# Allocation-free BG transposed solves

This ports the production fix and regressions from experimental commit
`39f3ad205ecdd1b9e5c8ef60265421575163a9f0` onto master `084a749`.

A warmed public Bartels-Golub `transpose_solve!` allocated 32 bytes on Julia
1.13.0 aarch64. Full-sampling allocation profiling identified an `UpperRowOrder`
wrapper. The shared finishing call merged `nothing` and `UpperRowOrder` into a
union and boxed that immutable wrapper. Calling the same helper inside each
branch preserves the concrete type and removes the allocation.

Arithmetic, traversal order, row/column maps, alias handling, precision and
recovery remain unchanged. This is independent of the retained-capacity policy
and does not incorporate the experimental packed-slot or direct-LU prototypes.

## Integration verification

On the integration source, all 432 new allocation/equation checks and all 13,957
existing factorization/reset/reuse checks pass under normal compilation. Five
warmed public BTRAN calls allocate `[0, 0, 0, 0, 0]` bytes, and full sampling finds
zero allocations. All 1,296 exact-equality comparisons with master `084a749`
pass under `--compile=min`. The previously failing BG allocation assertion now
passes without changing its zero-byte limit.

Runs used Julia 1.13.0 aarch64, one Julia/BLAS thread, disabled package precompile
workload, the existing 8-GiB virtual-memory wrapper, and RAM/swap guard.

## Reproduction

Run one Julia process at a time, with one Julia/BLAS thread. Use normal
compilation for allocation assertions and `--compile=min` for the independent
exact-arithmetic comparison:

```bash
julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/triangular_transpose_allocation_tests.jl")'
julia --startup-file=no --project=. diagnostics/bg-transpose-allocation/reproduce/probe.jl
julia --startup-file=no --project=. diagnostics/basis-bounded-capacity/reproduce/allocations.jl
julia --startup-file=no --compile=min --project=. diagnostics/bg-transpose-allocation/reproduce/identity.jl
```

The comparison loads the exact pre-fix public method from master `084a749`;
that commit must be available locally. It checks FT/SS/BG, both backends,
Float32/Float64/BigFloat/Rational{BigInt}, empty and nonempty factors, repeated
updates, and all three alias modes.

Historical diagnostics remain in the preserved `codex/basis-update-chain-bench`
worktree under `diagnostics/bg-transpose-allocation/` and
`.superpowers/bg-transpose-allocation/`. Its original report is available with
`git show 39f3ad2:diagnostics/bg-transpose-allocation/README.md` there.
Integration logs are retained locally in `.superpowers/basis-core-fixes-integration/`.
No full-solve speedup is claimed for this per-call allocation fix.
