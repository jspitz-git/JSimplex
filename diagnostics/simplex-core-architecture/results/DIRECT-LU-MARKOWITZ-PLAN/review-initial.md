# Independent initial review: common factor export and Markowitz direct LU plan

Review scope: documents and source inspection only. No Julia process, import, probe, compilation, test, benchmark, historical driver, or production edit was performed. This review does not admit a numerical run.

Reviewed checkout HEAD: `9ea533ebcba2d5611a839b8e4bb03b59c2b1c371`. The documents identify master baseline `6f68e24e8ddac42b948da8fcc2d636c010751194`; this review did not execute either baseline.

Reviewed SHA-256 values:

- `docs/superpowers/specs/2026-10-14-direct-lu-markowitz.md`: `d6b1c266a03dd3905713ee1cb1b08f6cb603f562e7770382916e9c90d55f8d1b`
- `docs/superpowers/plans/2026-10-14-direct-lu-markowitz.md`: `1c52f8458927e702ff2928e7051f350a649fa066bcf93a2d4e171ffd0c825837`

**Readiness verdict: changes requested before accepting this plan for execution preparation.** The core algebra and source reuse are feasible, but the four findings below should be resolved in the documents. After that, offline implementation/test preparation can proceed; the separately frozen implementation and run admission still require their stated independent reviews.

## Findings

### P2 — The designated mixed fixture cannot test the sparse/core lower-block permutation

Plan line 65 designates `blockdiag(I4,C)` as the mixed sparse/dense fixture and asserts nonidentity `core.p`. Its sparse-to-core lower block is zero. Permuting those zero rows cannot reveal an omitted or incorrect permutation of the lower-left block. Pure dense C has no sparse lower-left block either. The tridiagonal fixture has no assertion guaranteeing both a nonidentity core permutation and nonzero, permutation-sensitive cross-boundary lower coefficients. Thus the key source operation may remain untested even when the full exported identity passes the named boundary fixture.

The relevant implementation is `src/huangfu_hall_factorization.jl:205–218` and `:236–240`: core row pivots change both the outer row permutation and the rows of sparse lower coefficients. In particular, `row=k+core_positions[row-k]` must be distinguished from leaving the coefficient in its old row. Plan line 25 explicitly prioritizes this boundary.

**Change:** freeze a small coupled block fixture, with nonzero lower-left coupling that changes under the core row permutation. Assert `0 < sparse_pivots < n`, nonidentity core permutation, and nonzero permutation-sensitive cross-boundary coefficients. Require the full exported identity on this fixture, and include it in the direct-manager solve tests. Preserve the existing block-diagonal fixture if useful, but do not count it as coverage of this coefficient relocation. This is an offline fixture correction, not permission to tune a fixture after a failed run.

### P2 — The cost schedule specifies incompatible first-FTRAN right-hand sides

Task2, plan line 78, requires genuine entering FTRAN for `a = B[:,j]` with `a[r] += 1/32`, followed by a distinct DSE FTRAN. Task3 line 86 instead freezes an alternating `+/-1` RHS, then line 87 budgets exactly two FTRAN calls per update. There is no stated role for that fixed RHS consistent with the inherited genuine entering-column schedule and the separate `i/n` DSE RHS.

`src/triangular_factorization.jl:847–871` consumes a tableau direction for the actual entering column. `src/triangular_spikes.jl:1–4` and `:79–95` preserve the entering partial solve by exact output-buffer provenance. Substituting a solve of the alternating vector changes the represented replacement; adding it as a third solve exceeds the frozen counts. This ambiguity affects both correctness and measured work.

**Change:** specify the ordered calls explicitly: `direction = FTRAN(current_factor, a_t)`, auxiliary DSE FTRAN with the frozen `i/n` vector in a separate destination, replacement using the unchanged `direction`, then BTRAN of the frozen unit RHS. Remove the unused alternating RHS or assign it a separately counted, explicitly admitted role. State that the explicit reference basis is updated with that same `a_t`, and that the refactor after update four uses the resulting current basis.

### P2 — Fresh construction plus one refactor excludes the reference backend's reusable-refactor regime

Task3 line 87 restarts each window with a fresh factor and performs exactly one refactor. In `src/factorization.jl:323–338`, a new UMFPACK backend has no spare: its first refactor calls fresh `lu`; subsequent refactors can call `lu!` on the previous spare and may reuse symbolic state when the pattern matches. In `src/markowitz_factorization.jl:561–574`, the first refactor similarly establishes the spare output that subsequent refactors recycle. Markowitz workspace dictionaries can already be reused on the first refactor, but the prior output/core pools are a separate reuse opportunity.

The proposed successful direct path deliberately releases the backend/workspace and constructs a new candidate each time (plan lines 74–76; spec lines 53–57). That is a reasonable initial ownership choice, but repeated warmup of freshly constructed lifecycles does not warm the missing spare-state path. The comparison can systematically miss a cost difference relevant to repeated refactorization while labelling a manager/backend broadly promising across all four cells (plan line 90).

**Change:** either include a precisely bounded second-refactor segment for each side, report first and subsequent refactor costs separately, and recompute all event/process counts before admission; or explicitly restrict selection language to fresh construction plus first-refactor workloads and mark reusable-refactor performance unmeasured. Do not call the resulting selection broadly representative of lifecycle/refactor cost without that qualification. No extra run or larger budget is requested by this review.

### P2 — The plan omits the native refinement limitation while broadly promising unchanged safeguards

The historical README explicitly states that direct CSC lower substitution removes native combined-solve iterative refinement (`diagnostics/basis-direct-lu/README.md:11–15`). The ordinary native path delegates to UMFPACK through `ldiv!` (`src/factorization.jl:120–137`), whereas the proposed direct backend performs the lower substitution itself and the manager solves packed U (plan line 75; historical `reproduce/direct.jl:20–75`). The exported identity and correct normalization algebra do not establish equivalent stability.

Spec line 46 and plan line 17 broadly say numerical recovery/safeguards are not removed without distinguishing preserved outer simplex recovery and certification from this known change inside the native solve. The small diagonal-dominant fixtures and tiny LP do not resolve that limitation. This is a missing numerical qualification, not a finding that the proposed algebra is wrong or that the historical results failed.

**Change:** explicitly record the absence of native combined-solve refinement for successful native direct mode, distinguish it from retained solver-level recovery/certification and ordinary fallback, and carry that limitation into the final disposition. Either admit a bounded newly frozen scaled/cancellation-sensitive component fixture, or state that this sensitivity remains unqualified in the first short experiment. Do not claim equivalent native stability from the listed checks.

## Additional implementation/admission recommendations

1. **Choose the exact native helper path now.** Plan lines 35–37 and 64 say extraction/scaling helpers but leave two materially different historical implementations available. Prefer `_hh_extract_parts(F, HHExtractWorkspace())` and `_hh_scale_mode(F,L,U,p,q,s,work,auxiliary)` as the specified pair, with singular/error checks retained. The historical `_umfpack_scale_mode` allocates `abs.(L)`, `abs.(U)`, permuted vectors and multiplication temporaries (`src/hypersparse_factorization.jl:17–49`); the HH helper uses caller work and two temporary vectors, with four coefficient traversals and a possible native solve (`src/huangfu_hall_factorization.jl:156–199`). Both verify orientation; only the latter avoids these unnecessary matrix copies. Do not use `_hh_extract_base`, which additionally constructs an upper-row index not consumed by the direct backend (`:261–289`). Keep the documented arithmetic/platform validation obligations of the selected existing helper.

2. **Bind public LP options explicitly.** Defaults are `presolve=true`, `scaling=:auto`, and steepest-edge pricing (`src/options.jl:149–156`). Singleton presolve can remove the two individual upper-bound rows (`src/presolve_rows.jl:90–139`); the source inspection does not prove this entire LP is eliminated. To make the test's route and basis dimensions deliberate, specify `presolve=false`, `scaling=:off`, and the intended pricing in both sides. `:none` is invalid: accepted scaling symbols are `:auto`, `:on`, `:off` (`src/options.jl:227–228`). Retain the direct-factory selection assertion and the existing permission to report absent refactor coverage rather than altering a fixture after results.

3. **Make private initialization details reviewable.** FT/SS packed columns use `Vector{Int}` indices; BG columns share an owned `UpperRowOrder` through `UpperRowIndices` (`src/triangular_factorization.jl:18–45`, `:409–499`; `src/triangular_indices.jl:1–25`). A generic initializer must produce the correct field types and initialize a dirty upper cache for nonidentity U. Existing `TriangularRowCache` defaults do that (`src/triangular_factorization.jl:368–386`). Constructing identity U and overwriting it would violate the plan's work objective. Retain this as an explicit source-review check.

4. **Exercise actual fallback transitions.** Include deterministic export-unavailable factory/refactor tests, covering direct to ordinary fallback to direct and preservation of backend/normalization requests. Helper-only orientation checks do not alone prove the manager's concrete fallback type and transactional publication. This can use test-controlled extraction failure without changing production behavior or tolerances; count it in the later sealed correctness admission.

## Algebra, ownership, dispatch, and schedule assessment

The stated algebra is correct: `P*S*B*Q=L*U` gives `B0=inv(S)*P'*L`; after moving `D=diag(U)` into B0, forward lower solve applies `inv(D)*inv(L)*P*S`, and transpose lower solve applies `S*P'*inv(L')*inv(D)`. The plan's operation order matches this. Signed nonzero diagonals are valid for D. Transactional normalization rejection on nonfinite results or loss of a nonzero to underflow matches the historical code, and ordinary fallback on unavailable export is distinct from unnormalized direct mode.

Reusing Markowitz extraction is appropriate: it owns new triplet/CSC output, copies permutations, and folds core pivots instead of retaining a mutable dense core. Float64 coefficients permit read-only sharing across copied lower backends. Existing manager copies own U/permutations/scratch and mark shared update prefixes; the plan correctly requires keeping those retirement rules (`src/triangular_factorization.jl:1248–1280`). Candidate construction before publication can preserve old factors on singular/refactor failure. A stable direct backend wrapper must represent both success and fallback for in-place field replacement; the later code review must verify that concrete contract.

The factory boundary is feasible. Current option dispatch is `_basis_factorization(B, ::SolverOptions{T,M,R})` delegating to `Val(M), Val(R)` (`src/factorization.jl:428–432`), and all three ordinary manager constructors already accept a refactorization backend. A narrowly gated ordinary overlay can route only legacy Float64 FT/SS/BG while retaining all other paths. Include placement after HH has access to the referenced types/helpers (`src/JSimplex.jl:20–29`). No runtime installer is necessary.

The existing Task3 arithmetic is internally correct before any finding-driven schedule change: 2 processes x 24 cells x 10 pairs x 2 sides = 960 lifecycles, 7,680 updates, 15,360 FTRAN, 7,680 BTRAN, 960 explicit refactors and 960 initial constructions. Orientation solves are additional as stated. The stage ceilings sum to 420 seconds. Source inspection cannot establish that compilation and all correctness work fit the 90-second process ceiling; exact test counts, runtime/import behavior and guarded termination remain obligations of the later admission. Timeouts must remain outcomes, not reasons for unreviewed reruns.

## Explicit computational work and memory assessment

**No production-code change exists to benchmark here. I found no unavoidable new hot-path full-factor scan demanded by the design, but found an unresolved avoidable-cost choice in the native helper selection and a material comparison gap in reusable-refactor coverage. I cannot certify absence of unnecessary work or retention in an implementation that has not been written.**

At setup/refactor, native export must account for CSR-to-CSC extraction, permutation/scaling buffers, validation, an optional orientation solve and coefficient traversals, normalization's temporary values and diagonal, and CSC-to-packed-U conversion. Markowitz export performs two dense-core scans, O(core_dimension^2), sparse-factor traversal, triplet assembly and CSC conversion, O(nnz(L)+nnz(U)+n) output storage with transient coexistence of backend, triplets and factors (`src/huangfu_hall_factorization.jl:208–255`). These are real costs even when output is sparse. One backend factorization, no discarded identity U, no unused HH row index and release of temporary U/backend/workspace are sound requirements. Using the older orientation helper's extra full sparse copies would be avoidable.

Each direct FTRAN/BTRAN performs O(nnz(L)+n) lower substitution/scaling plus the unchanged upper/update-chain work. Normalization may add vector passes; the historical identity-L specialization fuses coordinate transfer with D scaling. Existing prepared-spike copies/checks and update history traversal remain costs and must not be described as newly zero-work. No export or full-factor validation belongs in each solve or replacement. No new recovery or final-certification scans are proposed, and preserved solver checks should stay outside any claimed component-kernel savings.

Retained direct storage should contain L, row/scaling/D arrays, owned packed U, permutation maps, solve scratch and existing manager history/caches, without the original full LU/core/workspace or temporary CSC U. Copies may share only the stated read-only lower data; retained update pools and spare capacities must appear in matched reachable-memory reports. Reachable Julia memory omits native allocations, as the plan acknowledges; it cannot support a claim about total native peak/live memory. Fresh direct refactorization trades reusable backend state for lower retention, so both costs need explicit reporting.

The proposed separate allocation events/bytes, compilation, GC, component timing and per-process paired results are appropriate for this bounded comparison. Sparse and dense inputs are represented, but dimensions 32/96 and four-update segments between reset/end do not qualify long update chains, large sparse fill, recovery-heavy trajectories or repeated backend reuse. Any promising outcome must retain those scope limits; fewer iterations or a small solve-only timing cannot establish a speedup.
