# Direct BG export/import specialization implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for the preserved inline workflow, with a fresh independent reviewer at each boundary. Steps use checkbox syntax. This turn prepares and reviews the plan only.

**Goal:** Remove avoidable call-boundary object materialization in the existing BG export/import workspace candidate without changing numeric work, ownership or storage policy.

**Architecture:** A separate namespace retains the existing types/fields and keyword test seams. Their bodies move into positional, explicitly parametric cores; thin facades and the importer core are inline candidates. No alternate algorithm or new arena.

**Tech Stack:** Julia Float64/Int, SparseArrays, existing native UMFPACK and Markowitz; new offline Python checks. No added dependencies.

**Spec:** docs/superpowers/specs/2026-10-19-direct-bg-export-specialization.md

## Global constraints

- Planning only now: no candidate/driver/Julia/query/parser/import/compile/numerics. Preserve production/test/env/CI/master/STATUS/roadmap and all frozen artifacts.
- Entry39beb6ff4a9f287dbbfc4c2a3b821d47ce374d0d; master26e2291745999f485a74f643298ca997d65c7205. Fresh boot/start_ticks/command/full256groups ANDsessions/noJulia before new pinned work; append every subsequent group/session.
- Float64/Int packed DIRECT BG; native threshold_one / Markowitz default. No tolerance/pivot/precision/arithmetic/order change.
- P0=16*(l+u)+8*(n+1), B=min(1048576,fld(P0,16)); charge512+8*cld(n,64), optionally32*n. Exact-size reuse and all old budget/exception/publication/copy contracts unchanged.
- Positional core specialization is a hypothesis. No zero-allocation, native-free, timing or inference proof is granted by this plan. Preserve harness effects and old negative/anomalous observations.
- Later numerical stages require exact reviewed sources/driver/admission and fresh guards; standing human authorization for short runs is preserved and not requested repeatedly. This planning deliverable itself executes none.

## Review focus

1. Arbitrary callable hooks must be invoked exactly once, in the existing order, with identical exceptions; Task1 equivalence/failure tests.
2. Native nonunit scaling, empty/all-unit paths and Markowitz core permutations must retain safeguards and valid output ownership; Task1 existing orientation/export tests.
3. Failed/reentrant refactor and saved copies must retain active state while cache may be dropped; Task1 full publication matrix.
4. Budget edges, shape changes and partial normalization rejection must keep old allocations, raw bits and bounded retention; Task1 existing tests plus old/new request-sequence equality.
5. Specialization may move allocations into harness or compilation; Task2 symmetric whole-result capture and Task3 complete phases/graphs/startup reporting, without claiming count reduction from an asymmetric observer.

## Task1 — Separate OFFLINE candidate and tests

**Create later:** diagnostics/direct-bg-export-specialized/reproduce/{workspace.jl,export.jl,import.jl,factor.jl,workspace-tests.jl,import-tests.jl,lifecycle-tests.jl,boundary-tests.jl,source-inverse.json,work-memory-ledger.md,overlay-manifest.json}.

**Consumes:** the four frozen workspace candidate files; structural tests and the actual accepted GREEN2 lifecycle test source selected by its sealed manifest (including the sole `sum(...;init=0)` fix). Bind the actual executed test path and hash; do not silently use the older unfixed candidate test. Reference packed DIRECT stage and fixtures remain byte-identical.

**Produces:** renamed BGSpecializedExportWorkspace/BGSpecializedExportFactor{I}/_BGXSBuildOwner and `_bgxs_*` facades, retaining every old callable signature/keyword/forwarded operation modulo explicit rename. Add only these positional cores:

| Core | Positional arguments and specialization |
| --- | --- |
| `_bgxs_scratch_core!` | `(owner::O,role::Symbol,n::Int,l::Int,u::Int,allocate::A) where {O,A}` |
| `_bgxs_checked_basis_lu_core` | `(L::SparseMatrixCSC{Float64,Int},U::SparseMatrixCSC{Float64,Int},p::Vector{Int},q::Vector{Int},scaling::Vector{Float64},divide::Bool,owner::O,allocate::A) where {O,A}` |
| `_bgxs_scale_mode_core` | `(F::FT,L::LT,U::UT,p::PT,q::QT,scaling::ST,owner::O,n::Int,l::Int,u::Int,allocate::A) where {FT,LT,UT,PT,QT,ST,O,A}`; preserve existing synthetic/genuine input support |
| `_bgxs_export_core` | `(backend::B,owner::O,allocate::A) where {B<:UMFPACKBackend,O,A}`, corresponding `B<:MarkowitzBackend{Float64}` overload, and generic unsupported fallback |
| `_bgxs_import_upper_core` | `(U::SparseMatrixCSC{Float64,Int},normalize::Bool,allocate::A) where A`; same tuple result |
| `_bgxs_build_core` | `(B::M,backend::Val{R},policy::_NativePivotPolicy,normalize::Bool,owner::O,factorize::FZ,export_parts::EX,import_upper::IM,allocate::AL,make_inner::MK) where {M<:AbstractMatrix{Float64},R,O,FZ,EX,IM,AL,MK}` |
| `_bgxs_refactor_core!` | `(f::BGSpecializedExportFactor{I},B::M,factorize::FZ,export_parts::EX,import_upper::IM,allocate::AL,make_inner::MK,check_inner::CK) where {I,M<:AbstractMatrix{Float64},FZ,EX,IM,AL,MK,CK}` |

- [ ] Prepare the renamed existing tests first. Add `boundary_request_equivalence`: run old and new helpers against equal independent inputs/owners with each side's own recording allocator; assert identical ordered `(element_type,length)` requests, arithmetic output bits/mode, retained identities within each side, and exception identity on the same injected kth allocation. Test owners must be side-specific; no mixing distinct workspace types.
- [ ] Add `boundary_hook_order`: record factorize/export/import/make_inner/check_inner calls in a fixed test-only log; expected sequence is the original one on success and each failure prefix. Use the same closures/callable structs and keyword interfaces on both sides, including a captured sentinel. Assert no duplicated calls and no success publication on failure.
- [ ] Add `boundary_hot_and_hook_agree`: default facades and explicit default hooks give equal outputs/modes, same per-side buffer-request schedule and selected graph ownership. Cover both backends, empty/singleton, normalization on/off and rejected division. Structural work tests are not allocation-event measurements.
- [ ] Produce four candidate files by the namespace rename, body extraction and thin wrappers above. Keep each original body exact modulo rename; existing calls inside the body continue through the renamed keyword facades, which forward to the typed core. Apply `@inline` only to those seven helper facades (including backend overloads) and `_bgxs_import_upper_core`. No duplicated numeric bodies, helper omission, return holder, changed allocation order or broad annotations.
- [ ] Preserve wrapper forwarded solves/update/copy/query methods and type/field layout modulo rename. Keep normal and injected operations on the same core route. Create ordinary isolated stage containing original packed reference, old workspace candidate and new namespace without global method overwrite. Bind actual sources/modules and exact include inverse.
- [ ] Create full-file inverse reconstruction: flatten the thin facade/core split and reverse the namespace rename, recovering the four original files byte-for-byte after explicitly recorded annotation/header transformations. Record new wrappers separately; no blanket diff exemption for whole files.
- [ ] Ledger: zero additional algorithmic scans/solves/copies/conversions/array requests/retained fields; unchanged source counts for fallback/early exits/success. List changed compiler-method boundaries, default hook types and potential code-size/compilation cost. Retain old+new+backend/export peak and shared-copy obligations. Do not convert policy charges into graph-byte claims.
- [ ] Run only new offline checks. Fresh independent numerical/work/memory review, separate PASS closure and exact diagnostic-only publication. No Julia in Task1.

## Task2 — Concrete correctness and allocation-gate preparation, then admitted execution

**Create later:** results/DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER with new top-level-loaded drivers, manifests, expected tests, pure auditor, seal/guard/launcher. No old script execution or changes.

- [ ] Bind exact accepted GREEN2 source/test coverage and all new Task1 tests. Preserve old assertions; derive the new assertion inventory from actual source. Do not reuse7935 as a guessed total after adding tests or changing setup.
- [ ] Define RED as the allocation nonincrease predicates for the previous workspace candidate against packed DIRECT reference on the three native cells with recorded +5/+9/+1, using the same whole-lifecycle arithmetic and symmetric capture as GREEN. Correctness is expected to pass; do not manufacture mathematical or missing-marker failures. Freeze exactly three expected failing allocation predicates only if independent review of the concrete driver/source supports that expectation; otherwise stop before launch and document why. No fixture/gate retuning to force RED.
- [ ] GREEN substitutes only the new namespace under the same three allocation predicates and runs the full adapted structural/differential/failure suite. Use at least3warm and7observed pairs, preserve all event/byte samples, and require median events and bytes nonincrease, unchanged inputs/outputs and measured compile/recompile0. The RED cost process is a newly admitted regression experiment, never a rerun of the frozen old driver.
- [ ] Fix all allocations, timer-result materialization and returned-factor capture symmetrically outside/inside their documented boundaries. Keep six nested clocks and complete result visibility consistent on both sides; expose any harness count differences rather than crediting them as kernel savings. No automatic Profile.Allocs or IR query: any claim about disappearance of exact boxed sites needs its own explicitly budgeted observation.
- [ ] Inventory all actual fixture setups, warm/observed lifecycles, copies, hook failures, backend entries, output vectors and scratch before admission. Structural tests and setup work are additional to observed windows; counters on outer APIs are not complete native work.
- [ ] Prepare failclosed malformed-output/hash/stage/module/world-age/reservation/timeout tests offline. New runtime admission requires fresh refs/boot/fullgroups ANDsessions/noJulia, actual wrapper chain, exact pins and independent review. Initial300/292s; only a verified pure timeout permits separately admitted identical600/592s. Julia/BLAS1, heap2GiB, VM8GiB, availableRAM>=6GiB, swap<=1GiB, compiled-modules=existing. Preserve every failure and never overwrite/rerun accepted outputs.
- [ ] After subsequent execution authorization, admit RED and GREEN separately, review saved results independently, publish exact closure. If GREEN allocation predicates fail, stop this fixed candidate; do not perform time-cost qualification or silently add inlining/annotations.

## Task3 — Same complete paired cost qualification with the new candidate

**Create later:** results/DIRECT-BG-EXPORT-SPECIALIZATION-COST. Read old COST-PREPARATION/{ADMISSION.md,MEMORY-WORK.md,cost.jl,inputs.json,inputs.toml,analysis.py}; copy/adapt into new files and stages without executing frozen scripts. No third timed arm: old workspace timings stay historical context.

- [ ] Preserve the four frozen fixtures, both backends/policies,3warm+7measured alternating pairs,8updates/refactors4/8 and original residual tolerance128*n*eps(Float64)*max(1,||M||inf||x||inf,||rhs||inf). Replace only the timed candidate namespace and adapt separately instrumented untimed probe clones with exact body inverse.
- [ ] Preserve full existing schedule:160 timed lifecycle windows,16 policy-preflight constructors/32refactors,24 probe constructors/48refactors/192updates,4 transition constructors/12refactors/4copies, one synthetic early orientation and three importer controls. Total204constructors/412refactors/1472updates/2944FTRAN/1472BTRAN/4copies; up to308 native orientation solves, plus internal backend work. Preserve11 probe checkpoints and sampled private-build coexistence graph. No hidden extra preflight solves or full profiler passes.
- [ ] Preserve output/residual/bitwise/input/mode/policy/loaded-path gates and every raw sample/GC/outlier. No candidate-specific artificial retention to influence compiler escape; changes needed for symmetric capture must be decided and bound before launch and applied to both sides. Report cold process/compilation separately, with zero compilation required in measured windows; source-level specialization is not a zero-cost guarantee.
- [ ] ALL8 first-process cells require median whole-time ratio<=0.95, median bytes/events nonincrease, every warm/measured/probe factor graph<=1.10 reference, measured compile/recompile0, at least3/7 faster, and all correctness gates. Stop fixed design on any failure. Passing only allocation gates is not overall acceptance.
- [ ] Fresh concrete preparation/admission reviews precede each guarded process. Only all8pass permits a separately admitted reversed-order process; both process gates and at least10/14 faster required. Preserve standing short-run authorization, pure-timeout policy and all resource guards. No launch in this plan-preparation step.
- [ ] Independent result review and exact publication. Any ordinary-BG/public/production comparison remains a separate future plan; this candidate is not integrated automatically.

## Current deliverable

Self-review and fresh independent gpt-6-astra review of this specification, plan, evidence bindings and work/memory obligations. Preserve rejected drafts if amendments are required. Separate PASS closure/exact publication; no STATUS/roadmap edit. The next concrete deliverable is Task1 offline candidate/tests, not a new memory arena or a rerun of the rejected cost candidate.
