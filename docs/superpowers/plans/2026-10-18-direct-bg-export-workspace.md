# Direct BG private export/import workspace implementation plan

> **For agentic workers:** Use superpowers:executing-plans for the preserved inline workflow, with a fresh independent reviewer at each boundary. Do not start implementation in this planning turn.

**Goal:** Reduce temporary export/import allocation and copying for packed direct BG through bounded private scratch and fused normalization into owned final U.

**Architecture:** A distinct BGExportFactor wraps the unchanged packed BG manager. A bounded, private validation/orientation cache survives refactors; replacement factors remain private until complete. Fused import removes the normalization values temporary and CSC overwrite. Backend reuse and dynamic U are outside scope.

**Tech Stack:** Julia Float64/Int, SparseArrays native UMFPACK and Markowitz, existing packed BG; Python for new offline checks only. No dependencies added.

**Spec:** docs/superpowers/specs/2026-10-18-direct-bg-export-workspace.md

## Global constraints

- Planning only now; no candidate, Julia/query/parser/import/compile/numerics, driver or launcher.
- Diagnostic entry992fbda03d0467f466bbf3be79a2c6993f1aede6; master26e2291745999f485a74f643298ca997d65c7205. Preserve src/test/env/CI/STATUS/roadmap and all frozen evidence.
- Standalone Float64/Int packed DIRECT BG; native threshold_one and Markowitz default. No changed pivot strategy, tolerance, arithmetic order, solver safeguards, HH reuse, hypersparse or other managers.
- Budget P0=16*(l+u)+8*(n+1), B=min(1048576,fld(P0,16)); charge512+8*cld(n,64) for seen and optionally32*n for all four orientation vectors. Checked arithmetic; exact-size reuse. This is a policy charge, not an actual graph bound.
- Old factor remains intact until complete publication; workspace private and dropped after failure; copy has no cache. No retained backend or spare full output.
- Preserve inline implementation and independent reviews; each task and numerical admission requires its own later request. Frozen old scripts must never be rerun or modified.

## Review focus

1. Saved copies and failed refactor must retain active owner identities and values while private scratch is reused or poisoned. Tasks1/2 cover every allocation/publication boundary.
2. Normalization rejection after partial output must restore exact raw bits, including signed zero, without a second solve/factorization or changed safeguard. Task1 covers first/middle/last eligible off-diagonal rejection; diagonal ineligibility is a separate importer case.
3. Native nonunit scaling and Markowitz core permutations must preserve the exact validated factor/scaling identity; all-unit/empty/fallback must not keep stale cache. Tasks1/2 cover these paths.
4. Large-to-small dimension/nnz transitions, budget edges and cache sharing must not retain high-water arrays or exceed charged bounds. Tasks1/2 exercise below/exact/above thresholds and copy isolation.
5. Complete lifecycle comparison must include workspace/wrapper memory, setup/import/factorization and failed/copy coexistence, not just reduced allocation requests. Task3 binds complete schedules and graphs.

## Task1 — OFFLINE workspace, export/import kernels and structural tests

**Create later:** diagnostics/direct-bg-export-workspace/reproduce/workspace.jl, export.jl, import.jl, workspace-tests.jl, import-tests.jl and source-inverse.json/work-memory-ledger.md. Do not touch src or frozen candidates.

**Consumes:** frozen cost-stage factor-export.jl/direct-factor.jl and src/huangfu_hall_factorization.jl algorithms; seven original fixtures. First bind the full stage (including installed dependencies) and record explicitly the different live versus historical triangular_factorization.jl hashes.

**Produces:** BGExportWorkspace; `_bgx_allocate(::Type{T},n::Int)` allocation seam; `_bgx_scratch!(owner,role::Symbol,n::Int,l::Int,u::Int)`; `_bgx_export(backend,owner)`; `_bgx_import_upper(U::SparseMatrixCSC{Float64,Int},normalize::Bool)` returning `(packed_upper, Union{Nothing,Vector{Float64}})`. Owner is a mutable holder with a workspace field; Task2 supplies BGExportFactor. Test-only owner uses the same field contract. Helpers prefix `_bgx_`; no replacement of original methods.

- [ ] Write unexecuted `scratch_budget_boundaries`: no retained object below512; seen-first/all-or-none orientation retention with staged acquisition; exact charge<=B; both sides of threshold and1MiB cap; checked overflow; unsupported role rejection before mutation. Derive finite source-size test inputs, not impossible allocated arrays.
- [ ] Write `scratch_reuse_and_shrink`: identical compatible owner identities on repeated acquisition, dimension change fresh exact lengths, smaller current budget releases excess even at same n, no lingering references, allocation failure in each of four-vector group allocations never attaches a partial group. Use synthetic allocate hooks, no global allocator replacement.
- [ ] Prepare renamed exporter preserving raw extraction and validation order, with a private `_bgx_scale_mode` clone appending owner/n/l/u and the diagnostic allocator, preserving original guard/solve order. On cache miss acquire work/auxiliary first; acquire permuted/transformed only after original ldiv! and finite/nonzero auxiliary guard. Retain all four only after all allocations succeed; early exit retains no partial pair. Add `orientation_staged_early_exit` synthetic controls for thrown solve, nonfinite/all-zero auxiliary, allocation failure at each position and full reuse; assert2 requests/16*n payload on cold early exit,4/32*n when complete,0 on reuse/all-unit, no allocation of the later pair before the guard. Distinguish synthetic from genuine backend tests. `unit_scaling_no_orientation` must assert no orientation requests; Markowitz must request none. Validate p then q with original zero resets. Unsupported export/fallback releases cache.
- [ ] Write `fused_import_bits_and_counts`: exact output versus original normalize+packed recipe, normalize=false, empty, singleton, explicit signed zeros, nonidentity q applied at manager composition. For successful normalized U with u slots assert exactly u normalization-result stores, no normalization temporary/CSC write, u index copies and unchanged raw U. Assert original D and normalized mode.
- [ ] Write `normalization_rejection_first_middle_last_offdiagonal`: first/middle/last eligible off-diagonal slots (validated first/last literal CSC slots are diagonal D/D=1 and cannot reject); nonfinite division and nonzero-to-zero rejection, diagonal ineligibility, preserve raw U and exact raw-mode final packed values. Assert stop at original rejected slot, no extra basis solve, at most u fallback overwrite stores and no second output allocation. Include destination allocation failure at each packed buffer and D.
- [ ] Write `validated_export_invariants`: malformed lengths/pointers/order/triangularity, nonfinite coefficients, missing/zero diagonal, duplicate/out-of-range p/q, invalid scaling; original exceptions/order before importing. Reuse the original coupled Markowitz nonidentity-core test and its wrong-row negative witness. Keep source export ownership tests.
- [ ] Implement only the separately authorized offline candidate text later. Produce full-file inverse classifications: unchanged raw extraction, exact orientation arithmetic, original validation, selected fused importer deltas, explicit allocation-order difference. Do not claim unexecuted syntax or numerical correctness.
- [ ] Complete ledger for all vectors/objects, output and scratch ownership, retained versus transient payload, successful/fallback stores, staged native orientation2/4/0 array requests and16*n/32*n/0 payload with conditional solve, copy and old+new+backend/export coexistence. Bind new tests and fixture constants; enumerate prospective assertions, no guessed RED count.
- [ ] Run only NEW offline source/inverse/ledger checks; fresh independent numerical/work/memory review, separate PASS closure and exact staged/committed publication. No Julia. Task2 separate.

## Task2 — OFFLINE wrapper lifecycle and differential tests

**Create later:** factor.jl, lifecycle-tests.jl, overlay-manifest.json, composition-ledger.md under the same new candidate directory.

**Consumes:** Task1 interfaces and original `_init_direct_manager(BartelsGolubFactorization,base,upper,q)`, DirectLowerBackend, packed BG solve/update/copy functions and original fixtures.

**Produces:** BGExportFactor{I}(inner,workspace,busy), `_bgx_factor`, `_bgx_refactor_with!`, `_bgx_copy` with spec signatures; public-shaped forwarding only for the supported diagnostic type and complete cold driver query methods.

- [ ] Enumerate every required dispatch from the concrete prospective driver and original lifecycle tests; no missing mode/dimension/finite/growth/storage/prepared methods. Wrapper methods must forward to inner without new solves/vector scans/copies; arbitrary production dispatch is unchanged.
- [ ] Build cold constructor/refactor directly from original factorization, Task1 export/import and original inner-manager initializer. Do not create then discard a reference manager. Preserve original normalized/direct/fallback semantics and backend type policy.
- [ ] Write `private_publish_failure_matrix`: inject failure at factorization, extraction, validation, each scratch allocation, normalization/import allocation, manager creation and type check. Compare active inner identity/values/owners, saved copies, history/cache, source inputs; identical original exception, no success publication. Successful publish occurs once after all fallible work. Busy/reentrant same-owner call rejects before scratch mutation and finally releases busy.
- [ ] Write `copy_refactor_diverge`: copy creates no scratch; immutable lower metadata sharing is exactly original, mutable upper/work/cache ownership independent; refactor source and copy separately then poison scratch to prove no output aliases. Failed preparation may discard cache, not active state.
- [ ] Write `repeated_shape_lifecycle`: all seven frozen fixtures, both policies, construction then eight updates/refactors4/8, source input bit preservation, FTRAN/BTRAN exact paired outputs/residuals. Include ordinary dense RHS and unit-BTRAN metadata; entering FTRAN then distinct DSE FTRAN then replace original entering direction. Preserve supported alias rejections and unsupported indexed/scalar calls.
- [ ] Write `dimension_fallback_transition`: empty/singleton/grow/shrink, changing factor nnz at fixed n, valid export to fallback and back, normalize=false and division rejection. Verify cache retention rule at each boundary and no repeated factorization for fallback. Synthetic exporter fixtures are separate from genuine backend integration.
- [ ] Complete full factor graph/coexistence ledger, wrapper size and scratch states; enumerate source work and future driver-only diagnostic storage. Freeze exact stage and dependency paths. New offline checks plus independent review and publication only; no Julia, no actual src/test change.

## Task3 — Separate concrete drivers, execution gates and performance decision

**Create later:** new diagnostic results directory for RED/GREEN admission and another for cost; names/manifests fixed before launch. No implementation or numerical allowance in this plan.

- [ ] Prepare top-level-loaded RED/GREEN drivers with exact stage, module/world-age checks, assertion inventory and expected NEW RED failures. RED should expose missing reuse/fused import without changing old code. Derive counts from tests; no old8/10 count reuse.
- [ ] Prepare failclosed seal/guard/auditor and offline refusal tests: wrong stage/path/hash/phase, warning, malformed/missing output, reused reservation, incomplete output/counter schedule. Raw diagnostic results before aggregate assertions where possible; terminal logs mandatory on early failure.
- [ ] Later explicit RED and GREEN requests each require fresh host boot/start_ticks/command/full historical groups ANDsessions, exact refs/runtime/env/stage/output reservation and fresh independent concrete admission. Initial300/292, pure-timeout separate600/592; Julia/BLAS1, heap2GiB, VM8GiB, RAM>=6GiB, swap<=1GiB. Preserve all failures without retries disguised as the same run.
- [ ] Prepare a new paired cost driver: packed DIRECT BG reference versus BGExportFactor, four original fixtures times two policies,3warm7measured alternating pairs, eightupdates/refactors4/8. Bind exact inputs, output/residual schedule, all API/clock counts. Include constructor, extraction, cache sizing, import, solves and refactors inside symmetric timing. Source-inverse counters and graph snapshots outside.
- [ ] Add separately enumerated bounded controls for cold/nonretained orientation early exit and normalize=false, early/late normalization rejection, cold copy/no-cache, same-shape reuse and large-to-small retention. Include their setup and numerical work in admission. No growth of timed windows or arbitrary new LPs.
- [ ] All8 first cells require paired median time<=.95reference, median bytes AND eventsnonincrease, every final/probe factor graph<=1.10reference, compile/recompilezero, all bitwise/input/exact-residual checks and>=3/7faster. Record11lifecycle checkpoints with wrapper/cache and old+new coexistence budget. Preserve GC/outliers; phase medians are subsets, not additive total reconstructions.
- [ ] On failure stop this fixed design; no output-driven cache-budget/fixture/normalization retuning. On all8pass, only a separately requested/admitted reversed-order process may follow; both process gates and>=10/14faster required. Independent result review, separate PASS closure/exact publication.
- [ ] A later separate ordinary-BG comparison is mandatory before any production proposal. It must measure the actual candidate against ordinary BG with matched policies/work, not multiply historical ratios. Public integration, longer histories, all precisions and native retention are unqualified by this component plan.

## Completion of planning

Self-review scope, interfaces, every failure class and ledger. Obtain fresh independent gpt-6-astra review with an explicit computational work/memory finding, preserve any rejected review and before-documents, then separate PASS closure/exact publication. Keep old continuation documents unchanged. Final user handoff links the accepted plan/review and identifies Task1 as a possible later offline step, without starting it.
