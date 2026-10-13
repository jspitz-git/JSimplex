# Independent S2-B source/design review

Decision: **REJECTED as written for S2-B design acceptance and S2-C preparation under the present contract.** One Important ownership finding needs a bounded design amendment and fresh review. The source-only evidence and the choice to investigate audit-input storage are otherwise accepted. This decision grants no Julia parsing, import, execution, numerical allowance, production change, or performance qualification.

Reviewed at HEAD `c44472e7a43533fb9ec337eba86189aabbe6ac61`, master `d02416c108f06fcd41d58e0a1980b70a51fef9ef`. Scope: S2-PRICE-AUDIT-STORAGE.md, the 2026-10-13 S2-C preparation plan, and S2-B/source-check.py/json, supported by current production/test source and the pinned installed Base source. Existing files were preserved; this review and reviewer-check.json were created exclusively. No repository script was imported or executed. No Julia, Julia parser, native numerical work, old experiment, or historical rehash chain was run.

## Critical findings

None.

## Important findings

### I1. Forwarding dataids alone does not protect an empty scratch parent that gets resized

The design requires both parent dataids to preserve the existing alias guard and specifically requires empty-parent and direct scratch-alias coverage (S2-PRICE-AUDIT-STORAGE.md:45-64; preparation plan:47-58). However, installed `abstractarray.jl:1588` implements `mightalias` with `!isempty(A) && !isempty(B)` before comparing dataids. In `solve_quality!`, the checked arrays include `scratch.compensation` and `scratch.error_sum` (`src/simplex_numerics.jl:379-383`), which start empty (`:123-126`). Compensated evaluation resizes and fills them (`:220-223`).

If either empty wrapper parent is the same vector as one of those initially empty scratch buffers, the alias check returns false without consulting the correctly forwarded identity. Resizing changes the borrowed concatenation's length and, when the first parent grows, shifts its indexing boundary during the synchronous evaluation. There need not be concurrent mutation or a callback.

A concrete source-derived fixture for later preparation is `A = spzeros(Float64,0,1)`, so `_PriceAuditMatrix(A)` is the 1-by-1 identity; an empty `dual` shared with `scratch.compensation`; `predicted = [1.0]`; `rhs = [1.0]`; and a fixed valid tight solve tolerance such as `eps(Float64)`. Initially the wrapper length is one and the ordinary residual is zero. The three-term roundoff bound exceeds tolerance/4 (`src/simplex_numerics.jl:395-400`), so the compensated route resizes `dual` to one and fills it with zero. Its first input access then routes to that zero rather than to `predicted[1]` (`src/primal_updates.jl:175-189`). The existing dimension validation is not repeated after resize. The vcat control retains its independent `[1.0]` input. This is static reasoning, not an executed reproduction or a qualified expected numerical result.

The normal `_primal_price_prediction_reliable` caller creates fresh scratch after preparing its input (`src/primal_updates.jl:215-220`), so this finding does **not** establish a current production failure or corruption in the intended normal call. It does invalidate the broader alias-preservation argument and the unconditional parent-alias test contract in the submitted design.

Required amendment: specify wrapper-aware alias protection that rejects shared parent storage before any scratch resize, including initially empty compensation/error_sum parents, without changing arithmetic, adding full input scans, or overwriting existing global methods. A narrowly dispatched method for the new wrapper is a possible design direction, but its dispatch, symmetry, empty/disjoint behavior and storage identity handling require review. Keep the planned direct-alias tests and add this initially-empty/resized-buffer case, with both parents and both expandable buffers covered. An explicit alternative ownership contract could also be reviewed, but merely forwarding dataids or weakening the tests does not satisfy the present contract. No runtime test is authorized by this finding.

## Minor findings

### M1. The upper bound alone does not restrict the factory to the two concrete hardware types

The planned type bound `T<:Union{Float32,Float64}` (preparation plan:45-52) also permits a union element type. A `Vector{Union{Float32,Float64}}` should follow the promised generic vcat fallback, not the hardware-only adapter path. Make the factory restriction explicit with exact Float32/Float64 methods or an exact-type guard, and prepare a mixed/union-element fallback assertion. The plan already states the intended restriction; this is an implementation precision point, not another blocker.

### M2. Freeze comparison semantics for nonfinite and signed-zero fixtures

Preparation plan:59-64 calls for equality of all quality fields and scratch arrays across nonfinite and signed-zero cases. Ordinary `==` treats NaNs and signed zero differently from the intended unchanged-value check. Specify `isequal` or appropriate bit/field assertions in the offline tests, alongside concrete expected reliability/finite results. Do not use approximate equality to conceal sign or nonfinite differences.

## Source claims, arithmetic and fallback assessment

The report correctly identifies the two prediction copies and independent reconstruction (`src/primal_updates.jl:52-69`), followed by the basic-price-zero check, concatenation, fresh quality scratch and residual evaluation (`:215-220`). The proposed storage change does not resurrect the rejected S2-A controller or skip reconstruction. Waiting for S6-AQ evidence does not prevent this distinct source/design work.

With m rows, n structural columns and N=n+m, `_PriceAuditMatrix` has N rows and m+N columns (`src/primal_updates.jl:159-173`). Its ordinary and compensated specializations visit nnz(A)+m+N ordered matrix terms (`:175-211`). Replacing only the values container leaves those loops, signs, conversions and arithmetic order intact, provided the borrowed values remain stable and method dispatch behaves as intended. `solve_quality!` accepts `AbstractVector{T}` and retains finite-input rejection, exact arithmetic, compensated evaluation and wider residual fallback (`src/simplex_numerics.jl:373-405`). The specialized CSC/transposed/vector route at `:168` does not apply to `_PriceAuditMatrix`, regardless of the values container.

The generic vcat fallback is appropriate for BigFloat, exact rationals and unsupported storage; no basis working precision or tolerance change is proposed. BigFloat stored-precision handling remains at `src/simplex_numerics.jl:344-362`. Existing cancellation, overflow-scale, tiny-residual, exact, transposed and lower-ambient-BigFloat examples are relevant test-source inputs (`test/primal_update_tests.jl:491-557`); corrected-audit publication is covered at `:559-575`. Reading these bodies is not a test run.

## Computational work and memory assessment

**No unnecessary new production work or retained memory was found in this documentation/source-check packet.** All 513 tracked src/test/.github files match master. No benchmark is required for this source-only change, and none was run.

For the proposed future candidate, the affected frequency is each reached price audit: normal incremental transactional calls occur at multiples of 20 (`src/simplex_pivot.jl:225-235`), with another incremental route at `src/primal_simplex.jl:720-725` and direct calls in tests/API usage. Earlier value/basis checks can prevent reaching it. It is not a claimed saving on every native iteration, candidate, refactorization, or final certificate.

The candidate would remove one m+N-slot concatenation/copy and introduce a constant-size two-reference wrapper. It adds indexing/routing work to the existing input finiteness scan and residual accesses, not a new full traversal. Let K=nnz(A)+m+N. `_accumulate_quality_term!` reads x once for the product and potentially again for the unsafe-range test (`src/simplex_numerics.jl:293-301`): up to 2K routed accesses per ordinary/wide pass, plus K per compensated pass and m+N input finiteness visits when all inputs reach that scan. These are source-level upper counts, not measured loads or timings; compiler elimination and short-circuit paths remain unmeasured. Dense A stored as CSC makes K grow as mn; sparse cases scale with stored nonzeros. There is no direct dependence on factor-update-chain length introduced by the container.

No basis solve, factorization, prediction copy, residual scratch allocation or policy check is removed. The initial quality scratch still owns four row-length arrays and two initially empty arrays (`src/simplex_numerics.jl:114-126`), with additional compensated/wide work on existing fallback routes. The wrapper retains both borrowed owners for its lifetime; no persistent field/cache is proposed and no GC/native-free claim follows. A constant-size ownership check needed to repair I1 is justified for correctness and must be included in later allocation/time measurements.

The proposed complete-price-audit, fixed-input sparse/dense, interleaved measurement gate is appropriate and expressly future work (preparation plan:78-88). Require its concrete later admission to distinguish compilation/initialization, ordinary audit, fallback/recovery and cleanup, state call/work counts and all samples, and define material-regression treatment before launch. Three warm pairs alone would not establish a speedup or a whole-solver benefit. Current coverage supplies no timing, allocation, inferred-dispatch, runtime alias or arithmetic-equivalence evidence.

## Evidence integrity and next decision

Independent stdin Python used only standard-library file/hash operations and read-only git commands; it did not execute the repository's source-check.py. All **531** read-time pins matched, reading **3,967,804 bytes**, with no errors. All **513** tracked src/test/.github files were independently compared byte-for-byte to master with zero differences. The comparison key set matches the packet. The packet records **40/40** true AP closure bindings; closure.json itself was rehashed as one of the 531 pins. Those older AP artifacts were not recursively rehashed again in this bounded review.

The source-check script's literal tests support only text structure (`source-check.py:18-27`), as its output scope acknowledges (`:30`). In particular, its no-Julia flag is a text/file-presence assertion, not independent proof of process history. The review itself launched no Julia. The source-check.json SHA-256 is `178b0d02832682f03defe02b50e74a4cbd1870e2fd4ff65b1d64ff1d57534088`; independent verification details are in reviewer-check.json.

Accept the evidence and narrow storage investigation; amend I1 in a preserved successor design/plan and obtain review before accepting S2-C under that contract. Preserve this rejected packet and its pins. S6-AQ remains conditional; all S2-A/S6-J/whole-AF and broader reconstruction/controller gates remain in force. No numerical or production allowance is implied.
