# Allocation audit: native LU input copies

This sixth round removes redundant matrix copies before native LU factorization.
All preceding allocation changes remain in both measurements, including PFI
capacity reservation and direct basis assembly. Measurements use Julia 1.13.0
on aarch64-linux-gnu with one Julia thread. Each entry is the minimum of three
warmed calls, with no compilation observed in any measured call. These are
cumulative Julia heap allocations, not peak memory or all external-library
allocations.

## Findings and changes

The post-assembly `adlittle` profile still attributed allocations to the CSC
constructor immediately before native Float64 LU. Inspection of the installed
Julia sources confirmed two redundant copies:

- `SparseMatrixCSC{Float64,Int}(B)` copies an already matching CSC matrix, and
  UMFPACK then makes its own copies of the column pointers, row indices, and
  values. Using `convert` avoids the first copy when the type already matches.
  Dense inputs and CSC inputs requiring index conversion still get converted.
- `lu(Matrix{T}(B))` creates a private dense matrix, then `lu` copies it again.
  Calling `lu!` on that private matrix removes the second copy. The caller's
  matrix remains untouched, including when factorization fails.

The checks used `SparseArrays/src/solvers/umfpack.jl` and
`LinearAlgebra/src/lu.jl` from the installed Julia 1.13.0 distribution. The
factorization still owns its data; no LU storage is reused across refactorizations.
Default pivoting, singularity checks, backend selection, and the previously
optimized PFI update storage are unchanged.

## Results

Complete `PFIFactorization` construction on sparse tridiagonal matrices with
diagonal 4 and adjacent diagonals 1, with input construction outside measurement:

| Scalar type | Rows | Before (B) | After (B) | Fewer bytes |
|---|---:|---:|---:|---:|
| Float16 | 32 | 4,800 | 2,664 | 44.5% |
| Float32 | 128 | 133,024 | 67,400 | 49.3% |
| Float64 | 512 | 582,520 | 553,568 | 5.0% |
| BigFloat | 32 | 2,218,176 | 2,208,552 | 0.4% |
| Rational{BigInt} | 32 | 6,903,616 | 6,886,200 | 0.3% |

Float64 uses sparse UMFPACK; the other rows use the existing dense backend.
Arbitrary-precision arithmetic dominates allocations in the last two cases, so
removing a matrix copy saves a much smaller fraction of their totals.

On the five fixture initial bases, full native refactorization allocated
4.1–4.4% fewer bytes and workspace initialization allocated 2.3–2.6% fewer bytes.
Whole Float64 solves without presolve showed the following changes:

| Model | Dual before (B) | Dual after (B) | Fewer bytes | Primal before (B) | Primal after (B) | Fewer bytes |
|---|---:|---:|---:|---:|---:|---:|
| afiro | 100,848 | 98,768 | 2.1% | 141,984 | 139,536 | 1.7% |
| adlittle | 498,152 | 483,608 | 2.9% | 669,616 | 650,416 | 2.9% |
| kb2 | 936,304 | 890,016 | 4.9% | 280,016 | 271,856 | 2.9% |
| sc50a | 328,992 | 320,800 | 2.5% | 250,936 | 244,936 | 2.4% |
| flugpl | 49,392 | 48,768 | 1.3% | 108,128 | 106,256 | 1.7% |

With presolve enabled, whole-solve savings were 0.1–0.6%. All 20 combinations
(five models, primal/dual, presolve on/off) remained `OPTIMAL`. Status, objective,
complete primal vector, and iteration count matched serialized pre-change
snapshots exactly using `isequal`.

Machine-readable measurements are in
[`lu-allocations-before.toml`](lu-allocations-before.toml) and
[`lu-allocations-after.toml`](lu-allocations-after.toml). Timings overlapped other
validation, so no runtime-speedup claim is made.

## Reproduction

The existing audit covers initialization, refactorization, and whole solves:

```sh
julia --startup-file=no --project=dev dev/allocations.jl afiro adlittle kb2 sc50a flugpl --samples=3 --profile=refactorize --output=lu-audit.toml
```

To reproduce the typed factorization probes in Julia with `--project=dev` from
the repository root:

```julia
include("dev/allocations.jl")
using .JSimplexAllocations, JSimplex

for (T, n) in ((Float16, 32), (Float32, 128), (Float64, 512),
               (BigFloat, 32), (Rational{BigInt}, 32))
    B = JSimplex.SparseArrays.spdiagm(
        -1 => ones(T, n - 1), 0 => fill(T(4), n), 1 => ones(T, n - 1))
    println(T, " ", measure_allocations(_ -> JSimplex.PFIFactorization(B); samples=3))
end
```

The reported runs used `--compiled-modules=existing` to support the read-only
package cache. Use identical runtime and inputs for comparisons.

## Regression coverage

Both warmed allocation budgets failed on the pre-change implementation:
Float32 construction allocated 133,024 bytes against a 90,000-byte limit, and
Float64 construction allocated 582,520 bytes against a 570,000-byte limit.

Ownership tests cover dense and sparse inputs for Float16, Float32, Float64,
BigFloat, Rational{Int}, and Rational{BigInt}. They check unchanged inputs,
forward/transpose solves after input mutation, copied factorizations after
refactorization, and preservation of a usable factorization after a singular
replacement fails.

Independent review found no issue. Its 42 comparisons across six scalar types
and dimensions 0–6 preserved the exact LU result type, factors, and pivots.
BigFloat results and stored precisions also matched when factoring a 512-bit
input at ambient precision 64 bits. Float64 dense, transpose, view, and CSC
inputs matched the previous implementation; UMFPACK's CSC arrays did not alias
the input storage.

The complete mandatory suite passed **14,414/14,414** tests, including the new
134 allocation and ownership checks. JuMP integration passed all **23** tests,
including generic numeric types. The two previously documented JET
development-suite failures remain outside this round's scope; the full optional
development suite was not rerun.
