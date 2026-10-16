# Direct BG Dynamic Upper Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans with the independent reviews below. Current authorization is this plan/review ONLY, no implementation or Julia. Do not rerun accepted historical executables.

**Goal:** Test whether shared coefficient slots with ordered row/column indexes reduce the complete cost of direct BG without weakening numerical behavior.

**Architecture:** Diagnostic-only BGSlotUpper arena plus a separate DynamicBGFactor. Existing packed direct BG is the numerical/storage reference; ordinary BG remains a separately reported performance comparator. Export, normalization, backend policy and full replacement refactor stay unchanged.

**Tech Stack:** Julia Float64/Int64 and existing backend/Test code; Python offline manifests/audits, no dependency changes.

**Spec:** `../specs/2026-10-16-direct-bg-dynamic-upper.md`.

## Global constraints

- Planning now only. Future code under `diagnostics/direct-bg-dynamic-upper/reproduce/`, results under `diagnostics/simplex-core-architecture/results/DIRECT-BG-DYNAMIC-U-*`. No new source is created in this step.
- Actual master26e2291745999f485a74f643298ca997d65c7205; planning diagnostic47ec2fc41fa3d21df9569e64a3b5a3e4ec7fa184. Use accepted master-based GREEN source tree with separately pinned environment, not older diagnostic src. Preserve all old raw/review/failure files.
- Float64 direct BG only; native threshold_one/Markowitz default, normalize requested=true. No ordinary dispatch changes, FT/SS/HH/PFI/public routing, export optimization, refactor reuse, tolerance/precision/pivot changes or unsafe coefficient dropping.
- Exact spec invariants,56*C+64*n payload ledger, checked3/2 growth/free-slot reuse, no n-squared reservation or hot whole-store checks. All additional scratch/history/temporary buffers count separately.
- No Julia until later concrete driver/counts/input bits/output paths/environment and independent actual-stage admission. One process, Julia/BLAS1,heap2GiB,VM8GiB,RAM6GiB,swap1GiB;300/292, separately reviewed pure-timeout600/592 only. No hours-long runs/full suite/automatic retry.

## Review focus

1. A row swap leaves column lists sorted under the OLD map or changes solve accumulation order: Task1 order/bit-pattern tests and Task2 selected-state comparison after every step.
2. Slot reuse leaves stale incidence/iterators or causes a source row to skip fill: Task1 exact free/live checker plus adjacent-row merge insertion/deletion tests.
3. Copy/refactor releases or recycles storage still owned by a saved copy: Task2 divergent copy/failure tests, shared-prefix history and backend owners checked separately.
4. Exported explicit/signed zeros, cancellation, nonfinite or missing diagonals alter pivot/exception behavior: Task1 primitive/import tests and Task2 reference-ordered rejection cases.
5. Pointer savings hide allocation growth, solve locality loss or retained high-water capacity: Task3 complete lifecycle/peak coexistence ledger and all cost gates; no automatic promotion.

## Task1 — Offline arena implementation and structural tests

**Files:** future `slot-upper.jl`, `slot-upper-tests.jl`, `prepare-overlay.py` in new reproduce directory. Do not edit existing candidate/export/production files.

**Interfaces:** `BGSlotUpper`; `_bg_slots(U::SparseMatrixCSC{Float64,Int},q::Vector{Int})::BGSlotUpper`; `_bg_reserve!(U,required::Int)::Nothing`; `_bg_lookup(U,rid::Int,cid::Int)::Int` (0 absent, ordered row scan); `_bg_set_at!(U,slot::Int,value::Float64)::Nothing` for known existing pair; `_bg_link!(U,rid,cid,value,rowpred,rownext,colpred,colnext)::Int` for absent pair, capacity first; `_bg_unlink!(U,slot::Int)::Nothing`; `_bg_swap_rows!(U,j::Int)::Nothing`; `_bg_rotate_rows!(U,first::Int,last::Int)::Nothing`. Explicit test-only `_check_bg_slots(U)::Bool` and `_bg_selected_state(U)` return detached logical CSC/bit tokens. No exposed stale slot handles.

- [ ] Write UNEXECUTED tests first. Import empty0x0, identity3, and explicit CSC U with column pointers[1,2,4,7],rows[1,1,2,1,2,3],values[2.0,-0.0,3.0,1.0,4.0,5.0]. Assert both indexes visit exactly these6slots, preserve signed zero, and ordered logical materialization matches input bitwise. Repeat with q=[3,1,2]: column_order=q, column_position=[2,3,1], each row list sorted by original basis ID, column lists keyed by q[j], and logical materialization identical to input. Row1 stable IDs must be[1,2,3], not CSC visit order[3,1,2]. Reject duplicate/out-of-range/wrong-length q before publication. No solve here.
- [ ] Test deletion/reinsertion of pair(1,3), exact cancellation to0.0 and-0.0, head/tail/singleton deletion, fill at every row/column boundary and repeated free-list reuse with unchanged capacity. For growth at capacities0/16/24, verify exact requested capacity rule, all seven buffers committed together, invalid integer overflow rejected before publication; injected allocator failure leaves old buffer identities/maps/contents unchanged.
- [ ] Test adjacent swap and first-to-last row rotation on the above U including absent entries/explicit zero. Compare exact permutation of selected entries, reciprocal links and logical traversal order; inverse transforms restore bit patterns. Repeat swaps/rotations under q=[3,1,2] and verify both logical order and stable-ID row order. Test corruption detection for duplicate pairs, cycles, bad neighbors, missing ownership and free/live overlap. Checker is never called in hot production-like paths.
- [ ] Implement only the arena algorithms specified; no per-coefficient objects, dictionary, hidden packed-U mirror or sort on solve. Keep free-ID reuse internal. Whole-column replacement and elimination helpers are Task2, not a second independent representation.
- [ ] Build ordinary overlay from accepted stage/master source and append candidate include only, with exact inverse manifest. New RED driver later checks required symbols/contract absence without executing old tests. Preserve all source and unexecuted tests; independent numerical/work/memory review before Task2. No Julia in this preparation task.

## Task2 — Offline direct BG adapter and differential lifecycle tests

**Files:** future `dynamic-bg.jl`, `dynamic-bg-tests.jl`, `reference-bindings.json`; extend NEW overlay preparation only.

**Consumes:** Task1 BGSlotUpper and slot operations; frozen DirectLowerBackend/export/normalization, BartelsGolubStep/Update, two-slot prepared-spike contract and existing exact fixtures.

**Produces:** `DynamicBGFactor{F}` with fields exactly from spec; `_dynamic_bg_factor(B::AbstractMatrix{Float64},backend::Val,policy::_NativePivotPolicy)`; Vector{Float64} `forward_solve!`, `transpose_solve!`, `replace_column!`, `copy_basis_factorization`, `refactorize!`; `_dynamic_bg_mode`, dimension/storage/growth/finite helpers needed only by these diagnostic tests. No AbstractTriangularBasisFactorization subtype or broad interface fallback.

- [ ] Pin a source inverse for each adapted helper. Copy the accepted BG arithmetic/pivot/history/zero branches and guard order, replacing storage accesses only. Explicitly map row/column maps, lower calls, two prepared slots, composed-row history replay, upper-prefix eligibility and scratch rejection; no silent generic dispatch to packed methods. New specialized helper names are allowed, edits to old union dispatch are not.
- [ ] Construct directly from the same real backend/export/normalization output, never from a temporary packed BG. Pass the exact exported q into the q-aware builder, without renumbering basis IDs; import identity arena with identity q on genuine exporter fallback. Preserve invalid-policy pre-work rejection and runtime type through normalized/direct/fallback/empty/refactor transitions. Test-only exporter injection mirrors the old seam and is not retained in factors or used by normal solves.
- [ ] Implement `_dynamic_bg_replace!` using original spike validation/preparation, column replacement/maps, original pure-swap batching, row union merge and adjacent-row elimination. Source-order node iteration preserves stable-column elimination order and logical-row solve order. Capture next pointers before mutations; reinitialize row cursors after swaps. Exact-zero removal must not skip next node. Reserve only on fill and publish no success history on failure.
- [ ] Write differential tests using the seven frozen accepted lifecycle fixtures and both policy arms. Entering FTRAN, distinct DSE FTRAN, replacement with original entering direction, unit BTRAN; compare output bits, logical U bits, row/column maps, pivot decisions/history multipliers and mode after every successful operation. Copy/diverge after update2; refactor after4/8; resized/empty/singular and injected exporter failure preserve prior live/saved owners. History comparisons use logical values, not slot IDs. Include alias RHS, destination private-scratch rejection, changed entering buffer/signed zero and two-slot provenance. No indexed sparse support: explicit rejection before any solve/update, tested with a factor-call sentinel.
- [ ] Include explicit nonidentity-q construction/update/copy/refactor cases and compare the stable-column-ID arithmetic trace against packed direct BG; a nonidentity permutation cannot be assumed from random fixtures. Add focused n0/1/3/4 sequences for partial overlap of adjacent rows, disjoint rows, pure-swap chains, cancellation deleting current/next target, new fill requiring growth, nonfinite intermediate and zero pivot. Trace old reference operation order/exception first; match it without invoking an invalid factor afterwards. Failure tests distinguish refactor rollback from partial-update invalidation. No fabricated exact test count: freeze the actual enumerated assertion tree and API/backend call ledger in Task3 admission preparation.
- [ ] Independently review complete candidate and unexecuted tests; exact original source inverse and intentional storage differences. Runtime bitwise equivalence and numerical correctness remain UNQUALIFIED until Task3. Next task first prepares concrete admission, not automatic execution.

## Task3 — Separately prepare and admit correctness, then costs

**Files:** future `red.jl`, `green.jl`, `cost.jl`, Python seal/guard/audit/summary and exact manifests in NEW results directories. No existing executable is rerun or overwritten.

- [ ] Prepare driver/expected assertion tree, exact per-case counts/inputs/exceptions, resource/process guard, fail-closed parser and full source/runtime/environment manifests. RED checks missing new contracts, not old seven-failure adapter RED. Self-tests reject malformed/partial output and measured compilation; fresh independent actual-stage review before each Julia process. Then separately authorized RED and GREEN; result review gates costs. Any equivalence failure stops this candidate; no tolerance relaxation or post-output tuning.
- [ ] Correctness oracles: independent exact Float64 residual bound `128*n*2^-52*max(1,||M||inf*||x||inf,||b||inf)` and unchanged export identity bound; zero bounds require exact zero. Additional bitwise representation-order oracle applies to dynamic versus packed DIRECT with identical lower export. Ordinary numerical results are independent controls, not assumed bitwise equal to direct.
- [ ] Cost preparation uses unchanged frozen sparse/dense32/96 token files and eight-update/refactor4/8 schedule. Pair dynamic direct with packed direct BG, two matched backend arms,3warm7measuredpairs/cell, second process reverses order; first accepted result before second. This primary comparison is8cells/process,160windows/process (48warm112measured),320total lifecycle windows,320construct640refactor2560updates5120FTRAN2560BTRAN timed entries. Genuine controls, export orientation and correctness probes require separate explicit budgets before any launch.
- [ ] If ordinary comparison is included, prepare two separate additional paired processes dynamic versus ordinary with the SAME counts; do not pool them or silently add them to primary300s processes. Four processes maximum for this two-comparator protocol,640total lifecycle windows; each separately admitted. It is not required to run ordinary comparison after primary rejection. Bind this stop decision before launch. Never reuse old cost1/cost2 as a concurrent control.
- [ ] Measure full construction/export/normalization/arena build, updates, FTRAN/BTRAN and full refactors, GC/compile/bytes/events, reachable capacity and source-derived peak growth/copy coexistence. Nested times are subsets. No full invariant scans/diagnostic counters inside candidate alone; a separately frozen instrumented correctness path records reserve growth/link work, not a timed performance claim. Both sides have identical timing instrumentation; serialized results outside windows, no retained old factors or row list accumulation. Warm windows still include fresh factor construction; do not promise zero allocations from allocator warmup.
- [ ] Primary gates per cell/two processes: whole paired median<=0.95 EACH,>=10/14faster pairs, median bytes AND events nonincreasing EACH, every memory pair<=+10% (zero reference permits only zero). All four fixtures must pass for a backend recommendation. Measured compile/recompilezero and exact correctness always mandatory. Negative costs are accepted evidence, not numerical failure or permission to tune. Report small timings, GC/outliers and ordinary comparison separately. No guaranteed allocation reduction from asymptotic work alone.

## Task4 — Decision and explicit boundary

- [ ] Publish accepted correctness, work/memory costs and per-backend performance disposition with raw failures retained. Full-loop and reachable-memory gates take precedence over faster update-only numbers.
- [ ] If rejected, preserve this version and stop; do not silently add dense fallback, compact mirrors, smaller indices, backend reuse or a changed fixture under its admission. Any follow-up is a new design.
- [ ] If promising, propose separate tests for public/indexed interfaces and a separate production integration plan. Do not claim public solver performance, other managers/precisions or native-memory accounting from this experiment.

## Completion of this planning step

Save fresh host/source pins and prior continuation bytes, self-review against spec, fresh independent gpt-6-astra numerical/work/memory review, separate PASS closure and exact staged/committed names/blobs before diagnostic push. Actual src/test/env/CI/master unchanged. Next possible step is Task1 OFFLINE candidate/test preparation after user review, not a numerical run. Existing inline execution preference is retained; no need to ask it again.
