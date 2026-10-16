# Column-contiguous block U for direct BG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for the user's preserved inline workflow. Implement task-by-task only after a separate implementation request. Steps use checkbox syntax; this document authorizes no Julia.

**Goal:** Replace per-entry linked U storage with contiguous blocks and compact row incidences while preserving direct BG numerical order and satisfying whole-lifecycle allocation/memory gates.

**Architecture:** Private BlockBGFactor owns one coefficient copy in bounded column blocks and Int32 row gap-buffer handles with reciprocal positions. Local block edits repair affected handles; solve loops traverse contiguous prefixes, and growth adds bounded slabs instead of copying the coefficient arena.

**Tech Stack:** Existing Julia1.13 Float64 direct BG/native threshold_one/Markowitz default; existing Python offline evidence tooling, no new dependency.

**Spec:** docs/superpowers/specs/2026-10-16-direct-bg-block-upper.md (read fully before any task).

## Global Constraints

- Planning only now: no candidate, driver, launcher, Julia/query/parser/import/compile, new measurement or production/test/env/CI/master edit.
- B=32,additional slabA=256; Int32 encoded handles/IDs/offsets with checked limits and0sentinel; no silent fallback/widening/tuning. Row growth required+min(8,max(1,old_capacity div8)); descriptor growth max(required,K+max(K div2,8)).
- One value per coefficient, exact arithmetic/order/pivot/zero/exception/cache ownership contract; no mirror, global method overwrite, repeated solve-time packing or invariant scans.
- Standalone Float64 private BG only; same genuine lower/export/normalization and prepared two-RHS provenance. No FT/SS/HH/public/indexed interface changes.
- Old DynamicBGFactor candidate and all source/raw/reviews/scripts remain frozen and stopped. Original cost auditFALSE retained; no rerun/relabeling. Master26e2291745999f485a74f643298ca997d65c7205 unchanged.
- Future numerical admission is separate, exact and independently reviewed;300/292, conditional pure-timeout600/592 only,Julia/BLAS1,heap2GiB,VM8GiB,RAM6GiB,swap1GiB. CIoff,HHdisabled,automationpaused.
- Current foreign VSCode Julia is untouched; only new planning paths permitted, pinned STATUS/roadmap unchanged. Fresh required preflight before future pinned edits or execution.

## Review Focus

1. Nonidentity q plus swaps/rotations crossing block boundaries: stable column IDs and logical arithmetic order must remain identical (Tasks1/2).
2. Aliased destinations and entering+DSE two-RHS caches: no stale handles or changed spike provenance (Task2).
3. Integer/handle overflow and allocation failure across multiple reserve steps: no corrupt live structure, explicit capacity-versus-factor rollback distinction (Tasks1/2).
4. Imported signed/explicit zeros, cancellation, missing diagonal and intermediate Hessenberg/nonfinite values: original branch/check/order preserved (Tasks1/2).
5. Sparse row headers and fragmented/high-water slabs/gaps/descriptors: report complete costs; no hidden mirror or numeric retries after failure (Tasks1/3).

---

## File map

All future sources under NEW diagnostics/direct-bg-block-upper/reproduce/:
- block-upper.jl: representation, allocation/handle/gap/block primitives and q-aware construction.
- block-oracles.jl: test-only full invariants/materialization/work ledger helpers.
- block-upper-tests.jl: structural/allocation/overflow/index tests.
- block-bg.jl: explicit private manager methods, source-inverse maps to accepted reference.
- block-bg-tests.jl: differential lifecycle/alias/failure tests.
- fixtures.jl: byte-exact reuse or source-bound import of existing frozen fixtures, no modified tokens.
- prepare-overlay.py and source-bindings.json: ordinary isolated stage from accepted master-based adapter stage; exact inverse and complete membership.
Future new evidence directories DIRECT-BG-BLOCK-U-PREPARATION, DIRECT-BG-BLOCK-ADAPTER-PREPARATION, DIRECT-BG-BLOCK-DRIVER-PREPARATION, DIRECT-BG-BLOCK-RED, DIRECT-BG-BLOCK-GREEN, DIRECT-BG-BLOCK-COST-PREPARATION and numbered result directories. None is created or executable now by this plan.

## Task1 — OFFLINE storage candidate, structural tests and full memory ledger

**Consumes:** spec representation/constants/contracts; unchanged stopped slot and packed reference sources as read-only evidence.

**Produces:** `BGBlockUpper`; `_bgu_build(A::SparseMatrixCSC{Float64,Int},q::Vector{Int})::BGBlockUpper`; `_bgu_find(U,rid::Int,cid::Int)::Int32`; `_bgu_set!(U,rid::Int,cid::Int,value::Float64)::Nothing`; `_bgu_swap_rows!(U,j::Int)::Nothing`; `_bgu_rotate_rows!(U,first::Int,last::Int)::Nothing`; `_bgu_copy(U)::BGBlockUpper`. Internal helpers use `_bgu_` prefix. Test-only `_bgu_check(U)::Bool`, `_bgu_materialize(U)` and pure handle/capacity limit tests. No solver methods here.

- [ ] Prepare an explicit field/container ledger:16C+4R+28K+32n+656core payload,8n+24Souter pointer payload, every Vector/Memory/struct/header/backing capacity and scratch, growth coexistence and copy/refactor extras. Compute m/K0 from every original frozen fixture's exported source/evidence only when available; unknown factor fills stay unknown, not inferred from input nnz. Stop for design revision if a proven lower bound already exceeds the memory gate. Preserve the illustrative dense32/96 arithmetic as predictions, not measurements.
- [ ] Write UNEXECUTED tests named empty_and_import, nonidentity_q, handle_backrefs, gap_move_grow, split32_insert33, boundary_swap_rotate, deletion_merge_right, reserve_failure, checked_limits, explicit_zero_order, fragmented_high_water and copy_independence. Enumerate inputs/assertions before deriving RED/GREEN counts. Use tiny column counts0/1/31/32/33/64, holes, full/partial tails, maximum accepted synthetic limits and just-overflow values; no huge allocation to test overflow.
- [ ] Implement the standalone OFFLINE candidate text: exact first slab, seven descriptor arrays and capacity bins,32encoded offsets, row gaps with physical reverse positions. Add a private call-local allocator/limit seam for failure tests, never retained in live objects. Grow descriptors/directories privately, with no implicit Julia query or syntax check.
- [ ] Implement direct bulk CSC import via counts and inverse q; no generic per-entry insertion calls or packed intermediate. Add source checks for two-pass O(n+m) work and all allocations. Validate slot/row uniqueness and inverse maps in tests, not per solve.
- [ ] Implement local edits with pre-reserved resources,33entry scratch and nonthrowing commit; at most one local merge after deletion. Tests inject each allocation failure and distinguish preserved live structure from permissible unused-reserve growth. Source/target cursors reload repaired handles. Preserve exact zeros until reference removal.
- [ ] Implement gap moves/growth and reciprocal repairs, local swaps/rotations and deep copy. Tests compare logical U and both indexes after EVERY primitive; no copied mutable arrays/free bins/backrefs may alias.
- [ ] Build the separate ordinary overlay and source inverse manifest; compare every old source/env file with its accepted original, only new include/files differ. Self-review memory/work scaling; independent gpt-6-astra numerical/work/memory review. Save separate PASS closure/exact diagnostic publication only; no Julia and no runtime-pass claim.

## Task2 — OFFLINE BlockBG adapter and differential tests

**Consumes:** Task1 API, accepted DirectLowerBackend/export/normalization, packed BG row/history/prepared-cache semantics and frozen fixtures.

**Produces:** `BlockBGFactor{F}` and `_block_bg_factor(B::AbstractMatrix{Float64},backend::Val,policy::_NativePivotPolicy)`; Vector{Float64} `forward_solve!`, `transpose_solve!` (including _UnitTransposeRHS), `replace_column!`, `copy_basis_factorization`, `refactorize!`; `_block_bg_mode`, dimension/storage/finite metadata only as needed by tests. No subtype of old packed union or production routing.

- [ ] Copy exact numerical branches and policy/exception order with a helper-by-helper source inverse; storage access differences explicit. Constructor builds directly from real exported U/q. Export failure uses unchanged fallback semantics; refactor publishes a full candidate only on success.
- [ ] Write UNEXECUTED differential tests against packed DIRECT BG using all seven accepted lifecycle fixtures, both genuine backend arms and nonidentity q. At each entering FTRAN, distinct DSE FTRAN, replacement, BTRAN, copy/diverge after2 and refactor4/8 compare output bits, U logical order, maps, pivot/history values and mode. Do not compare incidental block IDs.
- [ ] Add dimension0/1/31/32/33/64 block-boundary tests, signed zero/cancellation, pure swap chains across blocks, target gap insertion/removal, missing diagonal/Hessenberg, overflowing handles and nonfinite arithmetic. Preserve exact exception order and no post-failure use until refactor.
- [ ] Add allocation failure in setup/copy/refactor with live/saved ownership snapshots, and failed update with structural/cache checks but no false full-rollback claim. Verify no copied mutable slab/row/gap/descriptors or scratch alias. Reject new scratch aliases and unsupported scalar/indexed/keyword calls before backend work using sentinels.
- [ ] Adapt FTRAN/BTRAN to contiguous block prefix loops preserving per-column/per-row arithmetic order and last-diagonal fast path with original fallback. No row index traversal, packing, scalar conversion of coefficients or full invariants inside solve. Bound O(n+nnz+blocks+history); retain two prepared spikes and stale-direction checks.
- [ ] Adapt update elimination to monotone row-gap merge, local block shifts and handle repairs; account for32element edit costs, gap movement, replacement scans and pure-rotation interval movement. Source statement of cheap updates is a hypothesis, not performance acceptance.
- [ ] Prepare exact source/stage/inverse/field/work ledgers and independently review candidate plus tests. Preserve all originals and rejected versions. Separate PASS offline closure; no Julia or promotion.

## Task3 — Separate RED/GREEN admission, then bounded comparative costs

**Consumes:** independently accepted Tasks1/2, actual enumerated test tree, source manifests and accepted frozen input tokens.

**Produces:** new prepared drivers/seal/launcher/guard/auditor plus separate independently admitted RED, GREEN and cost results. This task is never auto-started by planning or source acceptance.

- [ ] Prepare concrete RED for the new missing block/adapter contracts only, without running old tests; derive exact expected failures from the actual candidate tests. Prepare GREEN and all raw outcomes before aggregate assertions. Top-level imports/definitions precede main; bind expected loaded module keys to exact driver report (including deliberate presence/absence of Test), test malformed/extra/missing paths offline.
- [ ] Freeze exact fixture/scalar/call/allocation-probe budgets, complete source/runtime/env/stage membership, command/output reservation, boot/start/command/groups ANDsessions and resource guards. Negative parser/admission tests cover incomplete cells, wrong policies, signed-zero pair differences, compilation, integer metadata overflow, timeout-plus-error and extra attempts. Do not reuse old launchers or execute Julia before fresh exact-stage review.
- [ ] On later user request, independently admit one RED, review result, then separately one GREEN. Confirm expected failure tree and then all structural/differential checks plus exact residuals. Stop on equivalence failure; no relaxed tolerance or changed fixture. Keep every failed attempt and warning. Pure timeout alone may receive separately reviewed longer limit, never automatic.
- [ ] Prepare a NEW cost driver: packed DIRECT BG reference versus BlockBG candidate, four unchanged sparse/dense32/96 inputs x two backend arms,8updates/refactors4/8,3warm7measured alternating pairs,48warm112measured windows/process. Bind policy controls and extra probes/counts BEFORE launch; source-derived API counts distinguish from observed native entries. No ordinary or stopped-slot numerical comparator is silently added.
- [ ] Include whole setup/export/normalization/block+row construction, all solves/updates/refactors and symmetric clocks in timed windows. Outside timing record exact outputs/unchanged inputs and11checkpoints per probe lifecycle: C/R/K/S,live entries/blocks,slab/free capacity,row gap reserve, per-array and full factor graphs. A separately named source-inverse probe alone counts block moves/splits/merges,tuple and handle repairs,gap moves,row/descriptor growth,slab appends and copied bytes. No diagnostic counters or full scans added only to timed candidate.
- [ ] Record source allocation requests and all temporary coexistence (slabs/descriptors/rows/copy/refactor) separately from aggregate GC traffic and reachable graphs. Include complete headers/backing reserve and retained free blocks. Save compile/recompile,GC,outliers and paired distributions; no native peak/free or cache-miss attribution without evidence. An unchanged event count is not an allocation-byte pass.
- [ ] After fresh independent first-cost admission, run at most one300/292process. Preserve all complete pairs even on partial timeout. Per cell require time pairedmedian<=0.95, median bytes/events nonincreasing, every final AND11checkpoint graph<=1.10reference, all numerical/compile gates; first8cells all pass and>=3/7faster each before requesting independently admitted opposite-order second process. Second process repeats fixed cells;>=10/14faster combined and allfourfixtures perbackend required. Negative first gate stops this fixed design; no block-size/slab/gap tuning or selected-cell rerun.
- [ ] Independently review numerical/work/memory results. Publish original failures and precise limits. If rejected, freeze and stop. If promising, propose separate public/interface and production-integration plans; no public solver speedup or general precision claim from component results.

## Completion of this planning request

Self-review spec-to-task coverage, fields/signatures/formulas and all five Review Focus mappings. Fresh independent gpt-6-astra design/work/memory review must accept before diagnostic closure/publication. Only new plan/spec/evidence files are written; STATUS/roadmap/source/runtime stay unchanged while foreign Julia is visible. No numerical admission follows. Link the accepted plan for user review; next possible requested work is Task1 OFFLINE candidate/tests, with the preserved inline execution method.
