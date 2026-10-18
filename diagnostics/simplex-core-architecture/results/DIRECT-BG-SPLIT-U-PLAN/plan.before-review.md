# Demand-sized free blocks for direct BG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for the preserved inline workflow, only after a later implementation request. Steps use checkbox syntax; this planning request authorizes no candidate or Julia.

**Goal:** Avoid assigning an entire32-position free extent to a short U block while preserving BG numerics and measuring all metadata/movement costs.

**Architecture:** Separate BGSplitUpper/SplitBGFactor candidate uses the existing contiguous-block layout. Free allocation rounds demand to1/2/4/8/16/32 and splits a larger donor once, returning its suffix to capacity bins. Initial import, row storage, numerical loops and backend behavior stay fixed.

**Tech Stack:** Existing Julia1.13 Float64/Int private direct BG, native threshold_one and Markowitz default; Python offline tooling, no dependency change.

**Spec:** docs/superpowers/specs/2026-10-18-direct-bg-split-free-blocks.md (read completely).

## Global Constraints

- Planning/review ONLY now. No implementation, Julia/query/parser/import/compile, numerical call, new fixture, driver/launcher or old-check execution.
- NEW design/source paths only. Both old block and dynamic candidates and every result/check/review stay frozen/stopped. Master26e2291745999f485a74f643298ca997d65c7205 unchanged; no src/test/env/CI/STATUS/roadmap change. CIoff,HHdisabled,automationpaused.
- Maximum block32,slab256,Int32handle encoding,32bins,row growth required+min(8,max(1,old div8)),K growth max(required,K+max(K div2,8)) fixed. New allocation target is next class1/2/4/8/16/32 before bin search.
- No coalescing, packing mirror, new solve fast path, row-policy/backend/pivot/tolerance/precision change. Same safeguards and source numerical order.
- Separate fresh exact independent numerical/work/memory admission before every later run;300/292,pure-timeout600/592 only,Julia/BLAS1,heap2GiB,VM8GiB,RAM6GiB,swap1GiB,full groups ANDsessions/boot/start/command. No automation or automatic retry.

## Review Focus

1. Arbitrary imported tails and remainder capacities3/5/28/31: exact partition, bin membership and target rounding (Task1).
2. Descriptor growth/Int32overflow or allocation failure after a fresh slab but before split: no lost extents or corrupted live handles (Task1).
3. Repeated small allocation/deletion/merge/refill and exhausted suitable bins despite enough total free space: account for metadata/fragmentation and avoid false amortized/live-memory bounds (Tasks1/3).
4. Nonidentity q, row swaps/rotations and entering+DSE prepared cache across relocation: original output order/ownership/exception semantics (Task2).
5. Dense columns repeatedly growing through classes and tiny sparse columns dominated by metadata: all lifecycle work and checkpoint memory included, no sample/fixture selection (Tasks2/3).

---

## File map (future implementation only)

New diagnostics/direct-bg-split-upper/reproduce/: `split-upper.jl` owns representation/allocator/primitives; `split-oracles.jl` test-only complete partition/handle/work checks; `split-upper-tests.jl` structural/allocation tests; `split-bg.jl` private BG adapter; `split-bg-tests.jl` differential tests; `source-bindings.json` and `prepare-overlay.py` bind exact source inverses and isolated stage. Original fixed fixtures imported byte-exact, no changed matrix/options.

New result directories: DIRECT-BG-SPLIT-U-PREPARATION, DIRECT-BG-SPLIT-ADAPTER-PREPARATION, DIRECT-BG-SPLIT-DRIVER-PREPARATION, DIRECT-BG-SPLIT-RED, DIRECT-BG-SPLIT-GREEN, DIRECT-BG-SPLIT-COST-PREPARATION and numbered attempts. Current planning evidence alone uses DIRECT-BG-SPLIT-U-PLAN. New scripts receive explicit one-shot outputs; old scripts never rerun.

## Task1 — OFFLINE storage candidate, structural tests and full ledger

**Consumes:** frozen block-upper.jl as text/reference, spec allocation/failure/partition policy.

**Produces:** `BGSplitUpper` with unchanged field layout; `_sbu_target(required::Int)::Int`; `_sbu_reserve_block!(U::BGSplitUpper,required::Int,allocate,limit::Integer)::Int`. Inherited APIs renamed `_sbu_build(A::SparseMatrixCSC{Float64,Int},q::Vector{Int})::BGSplitUpper`, `_sbu_find(U,rid::Int,cid::Int)::Int32`, `_sbu_set!(U,rid::Int,cid::Int,value::Float64)::Nothing`, `_sbu_swap_rows!(U,j::Int)::Nothing`, `_sbu_rotate_rows!(U,first::Int,last::Int)::Nothing`, `_sbu_copy(U)::BGSplitUpper`. Test-only `_sbu_check(U)::Bool` and `_sbu_materialize(U)`.

- [ ] Enumerate UNEXECUTED tests before implementation: `target_classes` asserts1→1,2→2,3→4,4→4,5→8,16→16,17→32,32→32 and0/33rejection; `donor32_split4` asserts same donor ID,4prefix/28suffix,unchanged C/R/live/active handles and used+1; `exact_fit_no_split` asserts no extra descriptor. Expected offline tree is explicit; no Julia-pass claim.
- [ ] Add `repeated_four_requests`: one free32extent yields eight4extents, seven remainder descriptors, no coefficient allocation when metadata reserve suffices. `nonpower_bins`: free3 is skipped for target4,free5 splits4+1,free31 splits16+15. `partition_holes` includes arbitrary initial tail offsets/nonidentity q, active/free neighbor extents and no orphan/overlap.
- [ ] Add `descriptor_failure_each_array`, `append_then_split_failure`, `handle_offset_limits`: inject each seven-array allocation failure, directory/append failure and synthetic just-over-limit without huge allocation. Assert original live owners/values/order/handles and complete post-failure partition; permit explicitly changed unused reserve. Test failure before split commit and every exact-fit/no-fit path.
- [ ] Add `relocation_keep_handle`, `copy_independence`, `fragmented_exhaustion`, `delete_merge_refill`, `monotone_fill_to32`, `split33_boundary` and inherited structural cases. Check all invariants after every primitive; descriptor count<=C,spare K not referenced,free cells cleared,one outstanding reserve then take. Repeatedfill tests count actual metadata growth/copy/clearing, not just moved live tuples.
- [ ] Prepare separate candidate text with exact helper/type renames. Change only target/free reservation logic and required test oracle additions; preserve all numeric/storage primitives otherwise byte-inverse. Split metadata only after all fallible reserve/checks, using one new positive descriptor and original bins. No persistent reservation object, free descriptor stack or extra struct fields.
- [ ] Create explicit source inverse and memory/work ledger: P formula plus actual backing/header/outer pointer cost,used/C/K bounds,one-split versus geometric growth costs,fragmentation/coexistence,old+new copy/refactor graphs. Compute bounded sequence predictions without executing Julia. Expected: no unsupported live-memory or guaranteed speedup claim; no omitted headers/temporary metadata.
- [ ] Offline source checks and independent numerical/work/memory review of candidate+tests; separate PASS closure/exact diagnostic staging. Expected: no unresolved findings; no runtime assertion or numerical allowance. Commit only new accepted preparation artifacts.

## Task2 — OFFLINE private adapter and differential tests

**Consumes:** Task1 interfaces and accepted original direct lower/export/normalization/packed BG source, fixed fixtures and prepared-cache contract.

**Produces:** `SplitBGFactor{F}`, `_split_bg_factor(B::AbstractMatrix{Float64},backend::Val,policy::_NativePivotPolicy)`; explicit Vector{Float64} forward_solve!,transpose_solve! (including _UnitTransposeRHS),replace_column!,copy_basis_factorization,refactorize!; `_split_bg_mode`. All distinct types, no overwritten original methods.

- [ ] Copy/rename frozen block-bg.jl to a separate adapter with exact numerical inverse and only storage-type/helper changes. No solve-loop or diagonal-lookup optimization. Assert full3-way text lineage to accepted packed numerical branches; factory keeps original backend/policy/export/fallback behavior.
- [ ] Prepare differential tests versus packed DIRECT BG for all seven existing lifecycle fixtures,both backends and nonidentity q: enteringFTRAN,distinctDSE FTRAN,replacement,BTRAN,copy/diverge2,refactors4/8; compare output bits,U order/maps/history/mode and independent ownership. Old measured block candidate is not run as a fresh comparator.
- [ ] Add allocator-sensitive differential cases: empty/short/exact-tail columns,2→4→8→16→32growth,33split across block boundary,free-suffix reuse,alternating fill/delete/merge and row rotations across differently sized extents. Preserve signed/explicit zeros,cancellation,Hessenberg/missing diagonal,overflow/nonfinite and exact exception order.
- [ ] Add allocation failure in setup/copy/refactor and failed update: publish only complete new refactor,retain live old factor on refactor failure,allow update's earlier committed changes,require invalid caches/no success history. Reject unsupported scalar/indexed/destination-scratch aliases before backend work. Validate entering direction remains valid after distinct DSE solve.
- [ ] Count factory/scan/copy/solve work, retained partitions and all temporary coexistence in the cold and hot paths. Explicitly distinguish fewer new slabs from potentially more descriptor partitions/relocations/clears; verify no new per-RHS full scan/allocation/cache.
- [ ] Prepare exact stage/source/runtime-text inventories and independent candidate/test review, then PASS offline closure and new diagnostic commit. Expected: no Julia/parse/import/compile, no performance acceptance and no actual source/test changes.

## Task3 — NEW drivers, separate RED/GREEN and bounded cost decisions

**Consumes:** accepted Tasks1/2; actual enumerated tests, fixed fixture tokens and full work/memory ledgers.

**Produces:** new concrete drivers,seal/launcher/guard/auditor/admission manifests and separately accepted results only upon subsequent user requests.

- [ ] Prepare RED for missing NEW allocator/adapter contracts; derive exact failure count from tests (do not reuse old8). Prepare GREEN complete inherited+new structure/differential cases, top-level definitions before main and exact loaded-module schema. Expected offline checks reject malformed/missing/extra paths and world-age/warning outcomes; no Julia yet.
- [ ] Pin complete stage/source/runtime/env/command/output reservation,actual assertion/call/probe budgets and fresh boot/start/command/full groups ANDsessions/resources. Review exact run independently before each later RED and GREEN. Expected RED only declared failures,then separately GREEN all correctness gates; retain all failures, no test/tolerance relaxation. Pure timeout only may receive separately admitted longer run.
- [ ] After accepted GREEN and a later request, prepare new packed DIRECT BG versus SplitBG cost driver. Same four32/96sparse/dense fixtures/two backends,8updates,refactors4/8,3warm7measured alternating pairs,48warm112measured windows. Whole setup/export/normalization/storage/solve/update/refactor and identical clock overhead inside timing; graphs/counters/residuals outside. Derive exact clock count and output membership from new source, not assumptions.
- [ ] Add separately typed source-inverse probe counters: target/bin inspections,exact-fit/split counts and remainder capacities,new descriptor IDs,descriptor growth/new/copied/coexisting bytes,slab/directory/row growth,extent relocations/live tuple copies/old-capacity clears,retained active slack/free capacities and all original update movements. No counter code in timed candidate. Counters are source operations, not native-entry or physical-allocation proof.
- [ ] Freeze separate structural probe schedules for repeated4requests,monotone growth and fragmented refill before numerical admission; distinguish their allocations from timed lifecycle totals. Record11checkpoint complete partition/capacity/backing/whole graphs per lifecycle. No new counters/full scans only on timed candidate. Expected auditor detects omitted remainder/metadata costs and falsely passing final-only memory.
- [ ] On fresh request/admission, one cost300/292process. Independently verify bitwise outputs,unchanged inputs,exact residual128*n*2^-52bound,measuredcompilezero,all samples/GC/outliers. Per EACH of8cells require paired time median<=.95,bytes AND events nonincrease,each final AND checkpoint graph<=1.10,>=3/7faster. Any false gate stops new fixed design: no tune or selected subset.
- [ ] Only after all8pass and separate request/admission may opposite-order second process run. Both process gates and>=10/14faster EACHcell required. Independent numerical/work/memory result review, PASS diagnostic closure/exact names+blobs before publication. Expected: precise scoped component decision, no automatic public/production promotion.

## Completion of this planning request

Self-review specification coverage, signatures and all five Review Focus mappings. Obtain fresh independent gpt-6-astra planning/work/memory review; preserve any initial findings and corrections. Publish only new spec/plan/planning evidence after PASS closure and exact staging. No candidate/Julia/numerical admission. Next possible user-requested work is Task1 offline candidate and structural tests, using the preserved inline execution preference.
