# Independent native pivot policy SOURCE/DESIGN review

Decision: **not accepted yet**. One P2 contract-scope finding requires a small documentation amendment. The proposed managed-backend implementation is otherwise coherent. This review accepts no candidate, production change, Julia invocation, numerical allowance, or runtime behavior.

## Finding F1 — explicitly delimit auxiliary raw-LU safeguards

The specification says the selection affects an actual Float64 native UMFPACK factor (lines44–45) and broadly promises recovery/phase/cleanup/retry propagation (line113). The implementation map and tests cover factors owned by `UMFPACKBackend`, but the public solver also constructs fresh Float64 sparse LU factors outside that backend factory:

- `src/dual_simplex.jl:102`, `_try_refine_dual_prices!`;
- `src/dual_simplex.jl:176`, `_small_dual_refinement_factor`, called at line192 by `_stabilize_small_dual_pivot!`;
- `src/dual_simplex.jl:949`, `_try_refine_dual_direction!`;
- `src/dual_simplex.jl:1012`, `_try_refine_dual_pivot!`.

Each uses the current sparse basis and plain `lu(B)` on the native Float64 route. `basis_matrix` assembles a `SparseMatrixCSC{T,Int}` (`src/simplex.jl:260,278`), so these are real UMFPACK factors, not generic dense or high-precision-only paths. None passes through the planned option adapter. A threshold-one managed factor can therefore coexist with default-policy auxiliary factors in one solve. The current text never states that boundary, and the planned factory/recovery tests cannot establish a broader guarantee.

Required resolution: explicitly restrict this option to managed `UMFPACKBackend` basis lifecycles, list these four unchanged auxiliary safeguards as excluded, and state the mixed-policy consequence for full-solver claims. Pin/read the relevant source and keep those safeguards source-identical. This is a scope correction, not a request to propagate the flag into auxiliary algorithms, alter safeguards, or reopen stopped work. Apply consistent wording to spec, plan and continuation text. The alternative of changing those algorithms would require a separate design and is not recommended for this amendment.

## Source/API and lifecycle assessment

`SolverOptions{T,M,R}` currently has16fields. Appending a Symbol without adding a type parameter, preserving the explicit old16-argument constructor, and forwarding that symbol through validation/conversion, phase, remaining budget, auxiliary LP and precision-copy paths is consistent with the current source. Low-level historical positional construction is intentionally not recast as validated public parsing. Public conversion must validate new values/combinations; candidate review must verify the actual overloads and dispatch.

The proposed private enum and constant field preserve the concrete `UMFPACKBackend` type used by PFI dispatch and singular-wrapper tests. Legacy two/four-argument wrappers can default their reconstruction policy while the policy-aware factory supplies all five fields. The proposed default-only generic manager fallback keeps HH unchanged and rejects nondefault before factorization. Float32 keeps its specialized backend; other supported non-Float64 scalars keep generic dense LU. Retaining intent in options is sufficient to reactivate it on a later Float64 reconstruction; no non-Float64 factor needs a new policy field.

The installed wrapper creates a default vector with IRSTEP0 (lines1039–1048), copies that vector into the factor (lines241–252), and sizes scratch from the selected refinement value. Its `lu!` path retains `F.control` (lines445–484). Fresh threshold-one construction may therefore own a local default vector, set two slots, and call the existing LU once. Default must remain literal `lu(B)`. Existing private-spare reuse already preserves controls and needs no rewrite or scan. The recommended `SparseArrays.LibSuiteSparse` constants plus one are usable; the wrapper also imports those constants and defines its `JL_` indices. AUTO/SYMMETRIC limitations are stated correctly.

`_copy_backend` already marks the original shared and gives the copy a separate slot container with a shared active factor and no spare. Copying the enum preserves this invariant. Empty transitions need only retain the enum. Fresh factorization publishes after success; reused-spare failure drops the mutated candidate and rethrows before active publication. Manager histories reset only after successful backend return. The planned failure, copy-with-history, repeated-empty, pattern/dimension and precision tests cover these distinctions. No whole-native rollback claim is made.

The named `_recovery_trial` rebuild uses `ws.options` and is a valid propagation target. The concrete successful fixture is `test/basis_recovery_tests.jl`, testset “Basis checkpoints own working data and preserve consumed work,” Float64 arm (line25 onward). Naming it directly in Task3 would make the future admission more precise; it is not a separate blocker because Task3 already requires an exact fixture/budget before launch.

The frozen direct candidate constructs an ordinary factor afresh and retains backend/normalization only. Deferring a new adapter with its own retained enum, equal reference/candidate policy and direct/fallback/copy/failure coverage is appropriate. No frozen direct file should be edited here, and oldcost2 remains blocked.

## Computational work, allocations and memory

**No unnecessary NEW production work or memory is introduced by this documentation-only stage.** For the proposed implementation, I found no avoidable work or retained-memory addition in the stated managed-backend design:

- Setup and fresh reconstruction add constant Symbol validation/translation and one enum initialization. Each options/backend copy carries constant metadata; object alignment may exceed the enum payload. No additional matrix conversion, full-vector/matrix scan, factorization or solve is prescribed.
- Fresh threshold-one construction obtains one installed default-control vector and the wrapper performs its existing control copy, just as default LU obtains/copies controls. Two constant slot stores and dispatch are added. Actual allocation effects must be measured, not inferred from this source equivalence.
- Private refactorization retains the existing O(n+nnz) pattern checks and LU work, with no new control allocation, control scan or extra scratch. Empty/copy transitions introduce no native factor solely to retain metadata and no extra native owner or growing cache.
- FTRAN, BTRAN, per-candidate and update loops receive no policy lookup, scan, copy or arithmetic change. Added metadata does not scale with n, nnz or update-chain length. Recovery reconstruction pays the same one-time plumbing as setup.
- Changed pivots can change fill, native work and later numerical trajectories. The previous +15U entries/+48native bytes are observations, not bounds. The proposed paired sparse/dense measurement separates setup, two refactor paths, solves, compilation and diagnostic retention. Its within-candidate policy comparison does not prove zero overhead against the old binary.

The proposed cost accounting is internally consistent:88backend constructions+176refactor entries+4224solve entries. Under the stipulated fresh/no-spare then private-spare sequence, native internals are176fresh LU and88lu! attempts, not264fresh LU. The future literal ledger must include negative tests and recovery work separately. No benchmark was needed or run for this documentation review.

## Integrity and checker outcome

A new independent Python read/hash checker verified all39required paths, all35source-evidence hashes, all514baseline production/test/environment hashes, all source anchor locations and historical C/P/R summary counts. No old script, numerical auditor, Julia parser/query/import/compiler, factorization or solve was executed. Historical false results and consumed budgets remain unchanged.

The saved checker has37checks:36true and one **checker-only false**. `separate_admissions_no_runtime_authorization` searches case-sensitively for `oldcost1FAILED` in the continuation, whose actual text is `Oldcost1FAILED`. The continuation does preserve the failed/consumed cost1 and blocked cost2 boundaries. This erroneous substring assertion is not a second document finding. Both the original checker and its false output are deliberately preserved; a corrected independent check belongs to the amendment review, not an overwrite of this evidence.

`review.json` binds the exact39required input files, their required-list file, this review text, and both checker files (43bindings). Additional source observations and baseline-manifest identity are bound in `reviewer-check.json`. Current-ref/process preflight, continuation mapping and publication closure remain the parent's separate work. Preserve this initial rejected review and checker before any amendment.
