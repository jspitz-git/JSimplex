# Dense LU reuse: measured potential

Production dense refactorization currently calls `_factorize_dense_basis`, which
allocates a private `Matrix` and pivot vector. The installed Julia 1.13 provides
`lu!(F, A)` to copy new coefficients into existing dense factors and reuse pivots.
The project already requires Julia 1.13.

This process-local probe alternates two preallocated dense LUs. It installs the
candidate only after successful `lu!`, retaining the previous active factor in
the other slot. It measures storage reuse, not a complete production implementation:
saved-copy ownership, dimension changes and candidate disposal after failure
would still need the same care as in the UMFPACK backend.

Julia 1.13.0, one BLAS thread, three samples after two warmups. Setup is outside
measurement; every measured compilation time is zero. Input matrices have a unit
diagonal and a 1/4 superdiagonal, with two rows exchanged to exercise pivoting.
Both dense and CSC inputs go through dense LU. The table uses CSC inputs, as in
basis assembly. These are Julia allocation counters, not peak retained memory.

| Type | Dimension | Allocations fresh → reuse | Bytes fresh → reuse |
| --- | ---: | ---: | ---: |
| Float32 | 64 | 5 → 0 | 17,048 → 0 |
| Float32 | 512 | 6 → 0 | 1,052,832 → 0 |
| Float32 | 1,024 | 6 → 0 | 4,202,656 → 0 |
| Rational{Int64} | 64 | 5 → 0 | 66,200 → 0 |
| BigFloat | 64 | 178,948 → 178,943 | 17,211,960 → 17,178,528 |
| Rational{BigInt} | 64 | 1,314,630 → 1,314,625 | 54,487,832 → 54,421,008 |

Float32 and machine-integer rational LU can therefore avoid all repeated
factorization allocations in these cases. BigFloat and BigInt rational arithmetic
still allocate scalar results; container reuse removes only about 0.19% and 0.12%
of byte traffic respectively in the 64-row CSC examples. Savings depend on the
matrix and scalar type. The arithmetic, pivot searches and copying new coefficients
remain; no full-solver runtime speedup is established here.

Explicit dense Float64 controls also reach zero allocations (8,396,960 bytes saved
at dimension 1,024). They do not represent the production Float64 path, which uses
the already optimized sparse UMFPACK backend. Dense reuse would primarily benefit
the other scalar types under `basis_refactorization=:native`, not Markowitz.

Two Float32 factor matrices at dimension 1,024 retain roughly 8 MiB, plus pivots
and wrappers, versus about 4 MiB for one matrix. This trades retained storage for
lower allocation traffic and GC pressure. Shared saved factors can require further
storage. Same-size reuse is straightforward; changed dimensions require explicit
handling before calling `lu!(F, A)`.

The probe passed 132 checks for solves, transposed solves, disjoint active/candidate
arrays, preservation of the old active factor, and singular-candidate failure.
An initial test RHS caused Rational{Int64} solution denominators to overflow;
the final validation uses matrix-generated RHSs whose exact solutions contain only ones.
Production source is unchanged; these checks are feasibility evidence, not a
replacement for production integration tests.

```sh
julia --startup-file=no --compiled-modules=existing --project=dev diagnostics/dense_lu_reuse_feasibility_probe.jl
```

[Raw measurements](dense-lu-reuse-feasibility.toml).
