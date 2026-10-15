# Final independent native pivot policy SOURCE/DESIGN review

**Accepted for the stated SOURCE/DESIGN scope, with no remaining findings.** Initial finding F1 is resolved. This accepts the amended design and plan as the basis for Task1 OFFLINE candidate/test preparation and independent review. It does not accept an implementation, numerical launch, production merge, or direct-prototype comparison.

## Amendment resolution

The spec now limits the option to managed Float64 `UMFPACKBackend` basis factors and expressly excludes the four existing raw auxiliary LU safeguards in `src/dual_simplex.jl`: `_try_refine_dual_prices!` at line102, `_small_dual_refinement_factor` at line176, `_try_refine_dual_direction!` at line949, and `_try_refine_dual_pivot!` at line1012. It states that threshold-one managed basis factors may coexist with default auxiliary factors, retains their existing high-precision safeguard arithmetic, and requires the entire source file to remain byte-identical. The plan and continuation state the same boundary. The file's complete hash matches the original baseline; no auxiliary numerical algorithm was changed.

Managed recovery remains in scope: `_recovery_trial` constructs through `_basis_factorization(B,ws.options)`. Task3 now identifies the exact Float64 fixture in `test/basis_recovery_tests.jl`, testset “Basis checkpoints own working data and preserve consumed work,” and one guarded `_recovery_trial` call. Preserving live factor/controls while allowing the existing consumed refactor counter to advance matches the current source. Exact constructor/solve counts remain a prerequisite of the future numerical admission, not an authorization supplied by this review.

The cost ledger now explicitly distinguishes88backend constructions+176refactor entries+4224solve entries from the implied176fresh native LU+88lu! attempts. These counts follow from88windows, each containing one construction, one no-spare refactor, one private-spare refactor and48solves. They are entry counts, not a complete native operation trace.

The continuation now links to this final accepted review. Its prior link to the initial rejected review is preserved through a separate, exact one-replacement mapping; no initial evidence was overwritten.

## Design assessment retained

The original review's nonblocking conclusions remain valid. A final immutable Symbol in `SolverOptions{T,M,R}`, a constant UInt8 enum in the concrete native backend, explicit old16-field and old two/four-argument compatibility wrappers, and propagation through the six option-copy/validation paths are consistent with the inspected source. Actual overloads, inference and compatibility still require candidate review and admitted tests.

Fresh threshold-one construction uses one private default control vector and the installed wrapper's existing copy; default construction remains literal `lu(B)`. Private spare reuse retains its existing controls. Copies preserve the enum, share only the active factor and keep spare ownership private. Empty transitions retain metadata without constructing a native factor. Existing publication order and failed-spare dropping preserve active owners and manager histories. No active-control mutation or repeated control-vector scan is required.

Non-Float64 precisions retain their existing Float32 or generic dense backend and arithmetic, while options retain intent for a later Float64 reconstruction. Nondefault Markowitz/HH remains rejected; default dispatch and existing MOI option behavior remain unchanged. The documented AUTO/SYMMETRIC limitation prevents treating threshold-one as a universal full-partial-pivot guarantee. Frozen direct prototypes and oldcost2 remain outside this work; a future adapter and comparison require their own design/admission.

## Computational work, allocations and retained memory

**I found no unnecessary NEW production computational work, allocations or retained memory introduced by this documentation-only stage.** All514baseline source/test/environment hashes match. No runtime measurement is needed to validate a documentation amendment.

For the prospective managed-backend implementation, the plan prescribes only constant metadata and construction/copy/recovery dispatch: one Symbol per options object, one enum per native backend, two slot stores on fresh threshold-one control creation, and existing wrapper control copying. Alignment and actual allocation effects must be counted later. No additional full-vector/matrix scan, matrix conversion, factorization, basis solve, native owner or growing cache is prescribed. Existing O(n+nnz) private-spare pattern work is retained. FTRAN/BTRAN, candidate and update loops gain no policy lookup or scan; metadata does not scale with problem dimension, nonzeros or update-chain length. The auxiliary safeguard amendment adds no work because it expressly preserves those source paths.

Selected pivots can change fill, native work and numerical trajectories; the prior +15U/+48reported native bytes are not bounds. The planned sparse/dense measurements separate fresh setup, no-spare and reused-spare refactors, solves, compilation, GC and diagnostic retention. They measure within-candidate policy tradeoffs, not a universal zero-overhead or end-to-end speedup claim. Candidate correctness/work review and concrete numerical budgets remain separate gates.

## Independent verification and preserved history

The new `reviewer-check-final.py` completed **39/39 checks**. It independently verified:

-51fixed required current paths plus3explicit link-amendment inputs;
-35original source-evidence bindings through the exact two applicable original-to-before mappings;
-43initial review bindings and39initial checker bindings through exactly the three declared original-to-before mappings;
-13first-amendment bindings through the one declared continuation-link mapping, and all4current link-amendment bindings;
-all514baseline hashes, the unchanged full dual source, the exact recovery fixture and source factory, and original accuracy/failure counts.

The initial rejected review and37-check result (36true, one false) remain intact. That original false was the documented case-sensitive `oldcost1FAILED` versus `Oldcost1FAILED` checker error, not a document failure. The new check verifies the actual text and the preserved historical failure; it does not rewrite or rerun the initial checker. The original F1 rejection is resolved by the separately recorded amendment, not erased.

`review-final.json` binds all51required files, the3additional link-amendment files, the fixed required list, both new checker files and this text: **58bindings**. No historical script/auditor, Julia query/parser/import/compiler, factorization, solve or benchmark was executed. Parent final preflight, continuation mapping, PASS closure and exact publication remain separate steps. Standing short-run permission does not substitute for later exact-stage admission.
