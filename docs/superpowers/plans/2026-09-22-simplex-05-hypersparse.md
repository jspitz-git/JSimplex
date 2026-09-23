# Hypersparse Simplex Kernels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Exploit the sparsity of working vectors during pricing, solves, and basis updates.

**Architecture:** Indexed vectors track their support. Backend adapters expose factor graphs and preserve a dense fallback. The entire pipeline switches according to measured cost and density.

**Tech Stack:** Julia 1.13, Test, SparseArrays, existing JSimplex backends, and MOI.

**Spec:** [specification](../specs/2026-09-22-simplex-modernization-design.md). Also read the [main plan](2026-09-22-simplex-modernization.md), especially the verification commands and commit protocol.

## Global Constraints

- Julia 1.13; preserve support for Float32, Float64, BigFloat, and rational types.
- Production dependencies remain LinearAlgebra, Logging, MathOptInterface, OrderedCollections, and SparseArrays; this plan adds no dependencies.
- Work in .worktrees/simplex-modernization on branch feature/simplex-modernization, starting from commit d93cfd3.
- Each verified feature gets its own commit, including tests, documentation, and a validation report.
- Preserve Solution{T}, existing statuses, explicit LP relaxation, and validation against the original model.
- Share the time limit and completed-step budget across phases, repairs, retries, algorithm switches, and precision increases.
- Do not weaken user tolerances or certification to make a benchmark pass.
- Exact rational arithmetic uses neither floating-point perturbations nor automatic conversion to floating-point arithmetic.
- Working perturbations must not modify the input model and must be removed before certification.
- Algorithm changes need not preserve bitwise intermediate results or the pivot path.
- Write all material intended for the remote repository in English, including documentation, code comments, reports, and commit messages.
- Use /home/jspitz/NetLib, /home/jspitz/MIPLib, and /home/jspitz/mps as the external test collections; solve MIPLib cases only as explicit LP relaxations.
- Exclude big.mps, largo.mps, and AnyMod.mps (stored locally as AnyMOD.mps) from complete simplex solves; use them only for explicitly bounded stress tests.

## Review Focus

- F16: value cancellation, explicit zeros, aliases, and row-index invalidation.
- F17: LU permutations and scaling, the transposed system, and a dense trailing core.
- F18–F19: a sparse RHS with a dense result and the opposite transition; all adaptation costs.

---

### F16: Indexed Vectors and Sparse Pricing

**Files:** Create: src/indexed_vector.jl, src/sparse_pricing.jl, test/indexed_vector_tests.jl, test/sparse_pricing_tests.jl. Modify: src/simplex.jl, src/dual_simplex.jl, src/primal_simplex.jl, src/JSimplex.jl.
**Interfaces:** IndexedVector{T}(n) owns values::Vector{T}, indices::Vector{Int}, membership, and generation. add_entry!(v, i, value), clear!(v), compact_support!(v), dense_values(v). RowAccess is immutable row indexing for the working A. sparse_price!(out, ws, rho, row_access) matches rhoᵀ[A,-I].

- [x] Pin down cancellation and reinsertion:

~~~julia
v = JSimplex.IndexedVector{Float64}(4)
JSimplex.add_entry!(v, 3, 2.0)
JSimplex.add_entry!(v, 3, -2.0)
JSimplex.compact_support!(v)
@test isempty(v.indices)
JSimplex.add_entry!(v, 3, 1.0)
@test v.indices == [3]
@test JSimplex.dense_values(v) == [0.0, 0.0, 1.0, 0.0]
~~~

- [x] The first version omits exact zeros only; do not drop small values by tolerance. Handle duplicate contributions, signed zero, empty support, and overflow. The dense buffer is owned, and support is not borrowed from another concurrently live solve.
- [x] Row-based pricing accumulates contributions only from nonzero rho entries; the slack part is -rho. The test A=[1 2;3 4], rho=[0,2] must produce [6,8,0,-2]. The CSC baseline is an independent reference; compare floating-point results against a residual bound and exact results by equality.
- [x] Build RowAccess once for an immutable working model, then invalidate it after a presolve transformation, phase change, dimension change, or precision transfer. Do not use a global cache keyed by A identity.
- [x] Add opt-in stress tests over the external corpora for bounded parsing, RowAccess construction, sparse pricing, memory, and cancellation-heavy support handling. For `big.mps`, `largo.mps`, and `AnyMOD.mps`, stop after bounded component checks and never invoke full-sized factorization or a complete simplex solve.
- [x] Run targeted tests for every type, the full suite, and measurements for sparse and dense rho, including index-construction cost on a short solve. Commit: feat: add indexed simplex vectors and sparse pricing.

### F17: Hypersparse Basis LU Solves

**Files:** Create: src/hypersparse_factorization.jl, test/hypersparse_factorization_tests.jl. Modify: src/factorization.jl, src/markowitz_factorization.jl, src/JSimplex.jl.
**Interfaces:** SparseSolveView adapters for basis LUs own the factors/graphs and the permutations/scaling of the given backend. sparse_solve_view(backend) returns an adapter or nothing. hypersparse_forward_solve!(dest::IndexedVector, view, rhs::IndexedVector) and hypersparse_transpose_solve! have the same mathematical contract as the existing solves.

- [x] Test reachability on a lower triangular matrix:

~~~julia
L = JSimplex.sparse([1.0 0 0 0; 2 1 0 0; 0 0 1 0; 0 0 3 1])
# The new reachability_order(L, [1]; transposed=false) visits only 1 and 2.
@test Set(JSimplex.reachability_order(L, [1]; transposed=false)) == Set([1, 2])
~~~

- [x] Implement a directed graph of nonzero dependencies, DFS/topological ordering of the reachable portion, and numerical substitution. reachability_order is a new helper for this task; in production it returns a borrowed preallocated buffer, and a test must not retain its alias across another call.
- [x] Start with a Markowitz adapter over the existing lower/upper/diagonal/row_order/column_order; when the trailing core is reached, use its dense LU and continue by reachability. Do not assume the entire factor is sparse.
- [x] Add a UMFPACK adapter with one-time extraction of publicly available factors, permutations, and row scaling during refactorization. First verify the reconstruction identity of the specific Julia backend with a test, then implement both forward and transpose mappings. Do not use internal UMFPACK pointers. If the adapter is unavailable or not worthwhile, use the original backend.
- [x] Test B=[0 2 0;1 0 3;4 0 5], both systems, unit and dense RHS, row/column permutations and scaling, an empty basis, and singularity. Compare with direct B\rhs and B'\rhs, and additionally use higher precision on small cases.
- [x] In the separate opt-in stress suite, exercise bounded factor-component extraction, reachability, sparse and dense RHS transitions, and memory limits on decompressed and explicitly LP-relaxed external instances. The three excluded files receive bounded component checks only, with no full-sized basis factorization or complete solve.
- [x] Run targeted backend tests and the full suite; measure graph construction/extraction/fresh LU and repeated solves. Commit: feat: solve sparse basis factors by reachability.

### F18: Support Propagation Through Basis Updates

**Files:** Modify: src/hypersparse_factorization.jl, src/factorization.jl, src/triangular_factorization.jl. Create: test/hypersparse_update_tests.jl.
**Interfaces:** Overload forward_solve!/transpose_solve! for IndexedVector and the existing PFIFactorization/AbstractTriangularBasisFactorization. Update operations must return the correct support; the external F17 contract remains unchanged.

- [x] On an identity basis with n=4, create a PFI column replacement with [1,2,0,0]. A solve with RHS=e₁ must have support {1,2}; with RHS=e₃, only {3}. After a second replacement that causes cancellation, compact_support! must remove the vanished entry.
- [x] PFI: propagate support through eta vectors in the exact order; for transpose solves, the pivot entry depends on the intersection of the support with the entire eta, so tracking only the old pivot is insufficient. Verify the reversed history order.
- [x] Triangular updates respect the existing algebraic order:

~~~text
forward:   B₀ solve → R row updates → U solve → Q permutation
transpose: Q transpose permutation → Uᵀ solve → reversed Rᵀ updates → B₀ᵀ solve
~~~

- [x] Forrest–Tomlin, Suhl–Suhl, and Bartels–Golub have distinct operations; give each tests against an explicitly updated B after every step. Include row swaps for Bartels–Golub, and cancellation and creation of a nonzero entry for packed U. As density grows, materialize the dense branch without losing values.
- [x] Test checkpoint restoration, graph reset on refactorization, copies of a shared factor, and source/destination aliasing. Run targeted random sequences with fixed seeds and an exact rational reference at small n.
- [x] Add opt-in, bounded stress sequences from external LP components to exercise update-chain support growth, cancellation, refactor reset, and memory accounting. For `big.mps`, `largo.mps`, and `AnyMOD.mps`, restrict execution to bounded component sequences and do not construct a full-sized basis factorization or continue into a complete solve.
- [x] Run the full suite and the F01 sparse benchmark for every update method; commit: feat: propagate sparse support through basis updates.

### F19: Complete Sparse Pipeline and Adaptive Fill-In

**Files:** Modify: src/simplex.jl, src/dual_simplex.jl, src/primal_simplex.jl, src/sparse_pricing.jl, src/hypersparse_factorization.jl, src/refactorization_policy.jl. Create: test/hypersparse_pipeline_tests.jl.
**Interfaces:** KernelModeState owns the selected sparse/dense mode and per-operation densities/costs. choose_kernel_mode!(state; support_size, dimension, sparse_cost, dense_cost)::Symbol. F10 receives the actual stored-entry count and factor growth.

- [ ] Test hysteresis and the absence of division by zero:

~~~text
dimension=0 → empty fast path
sparse occupancy 1/1000 and cheaper sparse samples → :sparse
occupancy 800/1000 for consecutive samples → :dense
single occupancy fluctuation → retain previous mode
~~~

- [ ] Connect CHUZR/CHUZC, BTRAN, pricing, FTRAN, the BFRT aggregate RHS, weights, and updates so that each stage does not rematerialize the entire vector. A dense fallback must be available independently for every operation.
- [ ] Use initial occupancy thresholds of 0.1 for switching to sparse and 0.2 for switching to dense only as experimental defaults; cost measurements may change them. Require two consecutive indications to suppress oscillation. Record the selected policy in the report.
- [ ] F10 incorporates fill-in, multiplier growth, and solve cost; refactorize on poor numerical quality regardless of speed. Residual checks are not disabled for hypersparsity.
- [ ] End-to-end tests: a block-sparse system, sparse A with dense B⁻¹a, a small dense problem, a support change after a flip, degeneracy, and precision-transfer fallback. Verify certification and bounded memory.
- [ ] Add a separate opt-in external-corpus stress suite with fixed time and memory bounds, including dense/sparse mode transitions and interrupted component pipelines. Even when selected explicitly through `--file`, never submit `big.mps`, `largo.mps`, or `AnyMOD.mps` to full-sized basis factorization or an end-to-end simplex solve; report their bounded component results separately and exclude them from solved-LP coverage and speed scores.
- [ ] Run the full suite, sparse_large/holdout, and complete runs of eligible large LPs; report extraction, graph, conversion, and factor-storage costs. Commit: feat: integrate adaptive hypersparse simplex kernels.
