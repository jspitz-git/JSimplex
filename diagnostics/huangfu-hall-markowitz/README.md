# Huangfu–Hall with Markowitz refactorization

Select `basis_update=:huangfu_hall, basis_refactorization=:markowitz` in
`SolverOptions`, or set the same two MOI raw attributes in either order.
All supported HH scalar types are accepted. Native Float64 still requires
64-bit indices; Markowitz does not add that restriction.

The existing Markowitz backend supplies sparse elimination factors and the
trailing dense LU. HH extracts independent CSC L/U factors in the task scalar.
The trailing LU row permutation is composed with the outer row order and applied
to the lower-left sparse block. Upper sparse rows retain their column coordinates.
The dense matrix is not reconstructed or refactorized during extraction.

Backend choice is a factor type parameter, so an empty reset, copy, failed
refactorization or working-precision transfer cannot silently switch backends.
Backend construction uses its existing private output-slot reuse. Extracted
active factors and saved copies never alias mutable backend arrays. Ordinary HH
updates, reach-based unit-transpose preparation, bounded scalar pools and the
native UMFPACK path are unchanged. Explicit hypersparse policies continue using
HH's dense solve kernels and preserve stored BigFloat precision.

## Verification

`test/huangfu_hall_markowitz_tests.jl` first failed for all six tested scalar
types because the combination was rejected. Its initial implementation passed
828 component checks: sparse-only, dense-only and mixed factorizations, nontrivial
core and outer permutations, prepared/unprepared updates, forward/transpose
aliases, copied factors, singular refactorization rollback and dimension changes.
Existing public/MOI, precision-transfer and BigFloat hypersparse tests now also
exercise Markowitz. Exact equation assertions are used for rational types.

Use the normal Julia compiler for `test/huangfu_hall_tests.jl` allocation checks;
semantic tests can use `--compile=min`. Run one Julia/BLAS thread at a time with
the existing memory guard and the 8 GiB numerical virtual-memory ceiling.
`LocalPreferences.toml` remains configured with `precompile_workload=false`.
No precompile workload expansion is part of this change: the existing workload
already covers native HH and the shared Markowitz backend.

The external runner reuses the pinned afiro, adlittle, pk1, flugpl and fast0507
inputs and the public HH harness utilities. Every solve must reach OPTIMAL,
match the reference objective and certify feasibility in the original model.
The runtime selection solves only dual runtime.mps with its pinned input digest,
a 900-second solver limit, steepest-edge pricing, legacy strategy, no partial
pricing and an 80-update interval. Reports retain failures before the runner
exits unsuccessfully; a timeout is not classified as convergence.

```sh
julia -g0 -O2 --project=. diagnostics/huangfu-hall-markowitz/reproduce/external.jl markowitz small OUTPUT
julia -g0 -O2 --project=. diagnostics/huangfu-hall-markowitz/reproduce/external.jl markowitz runtime OUTPUT
```

The split runner passed 2,510 semantic checks with `--compile=min` and 1,833
checks with normal `-g0 -O2` compilation, including the original HH allocation
regressions and complete Markowitz allocation testsets. Two earlier attempts to
compile all public scalar combinations together reached the 300-second guard
inside LLVM. An initial mixed interpreter run reported three allocation failures;
all three pass under normal compilation. The split runner preserves the original
assertions and selects whole testsets, without weakening allocation limits.

```sh
julia --compile=min --project=. diagnostics/huangfu-hall-markowitz/reproduce/targeted.jl semantic
julia -g0 -O2 --project=. diagnostics/huangfu-hall-markowitz/reproduce/targeted.jl compiled
```

The earlier full
suite's baseline failures and compilation limit are documented in the
[scalar-extension record](../huangfu-hall-precision/README.md); this change does
not alter unrelated primal tests or solver heuristics.
