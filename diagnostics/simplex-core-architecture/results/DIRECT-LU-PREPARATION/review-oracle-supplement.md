# Source-only supplement — unsupported-precision solve oracle

Date: 2026-10-15. Decision: **no additional finding; final offline acceptance stands**. The existing `review-final.md` and `review-final-bindings.json` were retained unchanged. No Julia execution or numerical permission is implied.

Question: could `B \\ T[1,1]` in `correctness.jl:112` reach an unsupported UMFPACK precision for the sparse Float32, BigFloat256, or Rational{BigInt} fixture, and should the oracle instead use `Matrix(B)`?

The frozen fixture at line 105 is exactly `sparse(T[2 1;0 3])`. It is square, upper triangular and not lower triangular. Source inspection of the installed Julia 1.13 standard library shows that `SparseArrays/src/linalg.jl:2333–2344` checks triangularity before selecting sparse LU and directly calls `UpperTriangular(A) \\ B` for this fixture. The later `lu(A)` at line 2349 is therefore unreachable.

`LinearAlgebra/src/triangular.jl:1995–2002` chooses the result scalar type using scalar left-division promotion. For non-BLAS types such as BigFloat and Rational{BigInt}, it allocates the corresponding typed result and calls generic `ldiv!`. The triangular dispatcher at lines 1254–1257 reaches `generic_trimatdiv!`. `SparseArrays/src/linalg.jl:1099–1115,1173–1201` supplies that generic CSC kernel, whose upper-triangular branch performs scalar divisions and multiply/subtract updates without conversion to Float64 or an UMFPACK call. Float32 also has the supported triangular route. These are source-level dispatch deductions, not observed runtime behavior.

The general concern would be valid for some nontriangular sparse inputs: `SparseArrays/src/solvers/umfpack.jl:383–389` rejects unsupported floating types, and the generic sparse LU path applies `float` before redispatch. It does not apply to this deliberately triangular oracle. Existing `test/factorization_tests.jl:114–118` uses `Matrix(B)` for a different nontriangular Float64 fixture and does not establish a requirement to change this one.

No implementation or test changes are needed for the current frozen input. A future change to this fixture's triangularity would require rechecking the oracle dispatch. The later execution admission must bind its actual runtime and standard-library source; this supplement inspected only the installed Julia `1.13.0+0.aarch64.linux.gnu` source tree without running its executable, parser, importer or numerical kernels.

Work/memory: no code changed, so this supplement adds no runtime work or retained memory. Avoiding a gratuitous Matrix conversion preserves the existing prospective oracle's sparse triangular route. This is not a speedup claim and does not alter the initial work/memory assessment.
