# Small import reserve for direct BG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for the preserved inline workflow after a later implementation request. Steps use checkbox syntax; this request authorizes planning/review only.

**Goal:** Avoid early occupied-block migrations by importing short U tails with one or two reserved slots, preserving numerical behavior and bounding the complete work/memory cost.

**Architecture:** Separate BGReserveUpper/ReserveBGFactor diagnostics derived from frozen Split sources. Only a new pure helper and the initial importer change; padding is allocated directly in the original three coefficient arrays. Free allocation, row storage, numerical loops and backend policy stay fixed.

**Tech Stack:** Existing Julia1.13 Float64/Int, native threshold_one and Markowitz default; Python for offline evidence, no new dependency.

**Spec:** docs/superpowers/specs/2026-10-18-direct-bg-import-reserve.md; read in full before each task.

## Global Constraints

- Planning/review ONLY now. No implementation, Julia/query/parser/import/compile/numerics, candidate/test Julia, driver or launcher in this request.
- New paths only; old Split/Block/Dynamic candidates and all raw/checks/reviews remain FROZEN and stopped. No src/test/env/CI/STATUS/roadmap edits; master26e2291745999f485a74f643298ca997d65c7205 unchanged. CIoff,HHreuse disabled,automation paused.
- Import positive terminal count1/2/3 into capacity2/4/4; count4:32 unchanged; empty column creates no block. Interior32 unchanged. Maximum block32,slab256,Int32handles,32bins and existing row/descriptor/directory growth unchanged.
- Float64/Int private direct BG, dense vector methods; native threshold_one/Markowitz default. Exact existing arithmetic, normalization, safeguards, ownership/alias rules and prepared entering+DSE behavior retained.
- Whole cost and all intermediate graphs mandatory. No loop/row-policy/backend/precision changes, broad inbounds changes or extra permanent metadata to rescue a failed comparison.
- Every later execution requires a new user request and fresh exact independent admission;300/292 initially, pure-timeout-only separately admitted600/592,Julia/BLAS1,heap2GiB,VM8GiB,RAM6GiB,swap1GiB. This plan authorizes no execution.

## Review Focus

1. Nonidentity q separates input CSC offsets from padded physical positions; repeated short tails and columns33/34/35/36/64 must partition exactly (Task1).
2. Explicit/signed zeros and empty/identity columns must retain live bits/count, with only slack cleared to+0.0 and no numerical suppression (Tasks1/2).
3. Size arithmetic and descriptor/physical cursor bounds must be checked together; partial allocation or refactor failure must preserve inputs/oldfactor, and copy must own padded slack (Tasks1/2).
4. Early reserved insertion, later growth/merge/free reuse and row rotations must preserve handles/back-references and prepared entering direction after a distinct DSE solve (Tasks1/2).
5. Dense96 has little graph headroom; cumulative import traffic and old+new factor coexistence can offset sparse savings, and row growth/solve overhead remain (Tasks1/3).

---

## File map

Future separate diagnostics/direct-bg-import-reserve/reproduce/: `reserve-upper.jl` (storage/import), `reserve-oracles.jl` (test-only invariants), `reserve-upper-tests.jl` (structural/failure tests), `reserve-bg.jl` (adapter), `reserve-bg-tests.jl` (differential coverage), `source-bindings.json`, `adapter-source-bindings.json`, `prepare-overlay.py` (exact stage). Frozen fixture values are copied byte-exact when needed, never modified in place.

Planning evidence: diagnostics/simplex-core-architecture/results/DIRECT-BG-IMPORT-RESERVE-PLAN. Later result roots DIRECT-BG-IMPORT-RESERVE-U-PREPARATION, ADAPTER-PREPARATION, DRIVER-PREPARATION, RED, GREEN, COST-PREPARATION and numbered runs. Create only the root appropriate to the separately requested task.

## Task1 — OFFLINE importer/storage candidate and structural tests

**Consumes:** frozen diagnostics/direct-bg-split-upper/reproduce/split-upper.jl, split-oracles.jl, split-upper-tests.jl and the spec. Existing structural representation and allocation seams stay unchanged.

**Produces:** `BGReserveUpper`, `_rbu_import_capacity(t::Int)::Int`, `_rbu_build_with(A::SparseMatrixCSC{Float64,Int},q::Vector{Int},allocate,limit::Integer)::BGReserveUpper`, `_rbu_build(A::SparseMatrixCSC{Float64,Int},q::Vector{Int})::BGReserveUpper`. Existing `_sbu_*` interfaces become `_rbu_*` unchanged in arguments/returns; test-only `_rbu_check` and `_rbu_materialize` retain their prior contract with padded initial layout permitted.

- [ ] Write UNEXECUTED `import_capacity_classes`: expected1→2,2→4,3→4,4→4,31→31,32→32;0/33reject before mutation. These are expected runtime assertions, not Python-source-pass substitutes.
- [ ] Write `padded_tail_partition`: ordered columns with lengths0/1/2/3/4/31/32/33/34/35/36/64; verify count/capacity, exactlyK0 descriptors, initialC=m+Delta, R=m,free0,slackDelta,complete physical partition,rows/backhandles and zeroed padding. Include0x0 and all-empty nonzero dimension.
- [ ] Write `nonidentity_q_offsets` with multiple adjacent short tails and nonidentity q; compare bitwise logical CSC to input, stable column/row maps and source immutability. Verify each physical cursor advances by capacity, source cursor by count, including column33..36 suffixes.
- [ ] Write `explicit_signed_zero_import`: live explicit+0/-0 bits retained and counted; all new slack+0 and ids/backs0, no tuple copied twice or full slab zero/rewrite. Test oracle scans stay outside timed candidate.
- [ ] Write `import_size_limits_before_allocate`: synthetic limit allows m but rejects32*K0 (and, where applicable, paddedC), with zero allocator calls. Prove C0<=32*K0 for the class/tail geometry; a paddedC-only overflow while32*K0 fits is impossible. Test checked-size/physical-cursor boundary arithmetic without huge allocation and retain invalid CSC/q rejection order.
- [ ] Write `import_allocation_failure_each_buffer` with injected failure at every importer allocation, asserting A/q unchanged, no returned object and no outer-factor publication. No assumption that private abandoned buffers have already been physically freed.
- [ ] Write `reserved_third_entry` using an imported two-entry tail: third insertion leaves that block ID/slab/start/capacity, no block reserve/relocation/old-capacity clear; fourth also fits, fifth uses unchanged target8 path. Row reserve/gap/back-repair costs remain visible and are not incorrectly required to be zero.
- [ ] Write `delete_merge_refill_padded` and `copy_padded_independence`: after delete/free/merge/reuse and row swap/rotation all inherited invariants hold; copy retains capacity/cleared slack with disjoint mutable owners. Include full32→33 numerical block split and later refactor rebuild.
- [ ] Prepare standalone text by explicit type/helper renames; allow inverse differences only for the importer and newcapacity helper. ComputeC0/K0 during the existing pointer loop, use one final allocation per coefficient array and separate physical/input cursors. Do not change rowreserve/freelist/numerical primitives. Audit newly introduced physical offset/overflow checks.
- [ ] Port inherited structural tests individually. List each obsoleteC=m/tight-tail assertion and its exact replacement; all other assertions remain byte-inverse. Add test-only request/copy/zero counters to establish exactly3*Delta extra slack stores and no additional import buffer requests. No instrumentation in timed code.
- [ ] Produce ledger for initialP, array/backing/header cost, cumulative three-import16*(Delta0+Delta4+Delta8), source request counts, copy, old+new refactor coexistence and unchanged nonlinear row-growth/fragmentation bounds. Do not claim an O(live) lifetime bound.
- [ ] Run NEW offline source/geometry checks only; verify full inverse and all stated formulas on saved/structural inputs without Julia. Fresh independent gpt-6-astra numerical/work/memory review; separate PASS closure and exact staged names/blobs before diagnostic commit/push. Task2 remains separately requested; no runtime acceptance.

## Task2 — OFFLINE BG adapter and differential tests

**Consumes:** Task1 interfaces/ledger and frozen split-bg.jl/split-bg-tests.jl plus direct-lu-policy-adapters/reproduce/direct-factor.jl and exact original fixtures.

**Produces:** `ReserveBGFactor{F}`, `_reserve_bg_factor(B::AbstractMatrix{Float64},backend::Val,policy::_NativePivotPolicy)`, renamed exporter/refactor/copy seams and `_reserve_bg_mode`. Forward/transpose/replace/copy/refactor methods mirror Split signatures on the newtype; `_rbg_*` helpers have exact numerical inverse. No oldmethod override.

- [ ] Prepare UNEXECUTED differential tests against packed DIRECT BG for all seven frozen lifecycle fixtures and both fixed policies, including nonidentity q and empty/short/full tail cases. Exact outputs/Uorder/maps/history/modes, source and ownership checks; no rerun of stopped Split as a numerical comparator.
- [ ] Test enteringFTRAN→distinctDSE FTRAN→replacement with original entering direction across padded insertion, eventual relocation and refactors4/8. Preserve every existing supported alias rejection and real backend forwarding path.
- [ ] Test signed/explicit zero, cancellation, missing-diagonal/Hessenberg, singular/nonfinite/overflow and unsupported scalar/indexed calls with inherited safeguard/exception order. Include different dimensions at construction/refactor where the original contract supports them; do not expand supported methods.
- [ ] Test copy/diverge and exporter/import allocation failure at setup/refactor: old factor remains usable and owned until complete successful publication; failed update has no success history/validpreparedcache and retains the specified earlier edits. Count old+newfactor+backend/export temporaries instead of reporting only post-refactor graph.
- [ ] Prepare adapter via exact type/helper-only inverse; no change to numerical loops, growth policy, row storage or solve fast paths. Freeze immutable stage/source identities and test assertion inventory; no Julia parse/load/compile.
- [ ] Reconcile complete memory/work ledger with Task1; zero new per-RHS full scans/solves/conversions, added import arithmetic and slack stores only. Independent gpt-6-astra review, PASS closure, exact diagnostic publication. Task3 is separate.

## Task3 — NEW concrete drivers, separate execution admissions and cost decision

**Consumes:** accepted Tasks1/2, enumerated assertions and ledgers, exact preserved four performance fixtures.

**Produces:** new RED/GREEN then cost drivers with seal/guard/failclosed auditor and source-inverse untimed probe, only after separate requests. No old exclusive script or numerical driver is rerun.

- [ ] Prepare top-level-loaded RED/GREEN drivers and actual stage manifest; enumerate exact expected new RED failures from tests, not old10. Freeze GREEN groups/assertions/entry counts, world-age/warning rejection, raw-before-aggregate/error logs and failclosed missing-output gates. Offline tests cover wrongmodule/pin/phase, malformed manifests and reservation/log linkage.
- [ ] On later explicit RED request, fresh host/ref/runtime/env/stage/command/output reservation plus exact independent admission before one300/292attempt. Preserve expected failures/exit and independently review result. GREEN is a later separately requested/admitted run with all correctness/ownership/structural checks and zero warnings. Pure timeout gets separate fresh admission before600/592; no mutation to frozen attempts.
- [ ] After accepted GREEN and a later request, prepare the cost driver for packed DIRECT BG versus ReserveBG, same sparse32/dense32/sparse96/dense96 inputs and both policies. Eightupdates,refactors4/8,3warm7measured alternating pairs;48warm112measured. All construction/export/normalization/import,solves,updates/refactors and symmetric timers included. No prebuiltfactor or padding work outside timing.
- [ ] Prepare a separate source-inverse untimed probe with original83counters plus explicit import counts: tailclass1/2/3,Delta,live/slackwrites,coefficientrequest count/bytes,physicalcursor endpoints. Reset/cumulative semantics and every counted entry must be specified; no instrumented type in timed paths. Record full backing capacities, partition, upper/wholefactor graphs at11lifecycle checkpoints and counters at each step.
- [ ] Freeze structural sequences before any launch: imports length0..4/31..36/64 with qpermutation; reserved2→3→4→5growth; paddeddelete/free/reuse; copy/refactor ownership and allocation failure. Separate structural work from timed lifecycle. Derive actual call/clock/probe/output budgets from the final driver, do not copy old200construction count without proof.
- [ ] Report import/refactor old+newcoexistence and cumulative allocations in the budget, not just final graph. Record known constraints of summarysize/RSS/native accounting; no unsupported native-free or complete physical peak claim. Every temporary added only by diagnostics is separately enumerated.
- [ ] On later request, fresh exact firstcost admission and one300/292process. Verify every bitwise/input/exactresidual/compilezero gate and all warm/measured/GC/outlier records. All8cells require timepairedmedian<=.95,bytes AND eventsnonincrease,every final/probegraph<=1.10,>=3/7faster. Otherwise stop the fixed design; no class retuning, selectedfixture retry or second process.
- [ ] Only after all8pass and another request/admission, opposite-order second process; bothprocess gates and>=10/14faster EACHcell. Fresh independent numerical/work/memory result review, PASS closure/exact stagedandcommittedblobs/push/remoteverify. No automatic production integration; a later separate plan must address public coverage.

## Completion of this request

Review spec coverage, exact interfaces, all five Review Focus classes and work/memory limits. Obtain fresh independent gpt-6-astra review of these documents and their evidence. Preserve initial findings and before-versions if corrected. Publish only the two documents and new planning evidence after PASS closure/exact staging. Next possible requested step is Task1 offline candidate/tests; no implementation or execution begins here.
