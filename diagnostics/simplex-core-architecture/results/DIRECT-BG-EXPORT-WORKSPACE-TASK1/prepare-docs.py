from pathlib import Path
R=Path.cwd();C=R/'diagnostics/direct-bg-export-workspace/reproduce';E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-WORKSPACE-TASK1'
(C/'work-memory-ledger.md').write_text('''# Task1 source work, memory and ownership ledger

UNEXECUTED candidate and tests, Float64/Int only. This is not runtime, parse, dispatch, allocation-event or speedup acceptance. No wrapper/Task2, driver/Task3 or actual src/test/env changes.

## Scope and source binding

The complete75-file historical ordinary stage and604 installed dependency/runtime paths from the cost1-300 seal are rehashed by the new source check. Their hashes are read-time provenance; no runtime is loaded. The stage root already includes frozen factor-export.jl and direct-factor.jl; future root additions are workspace.jl, export.jl, import.jl in that order after those definitions and before module end. No existing methods are overwritten. Tests are separate modules; include workspace-tests.jl then import-tests.jl outside JSimplex, call their entry functions only under a later concrete admission. Relative fixture include resolves the unchanged direct-lu-policy-adapters/reproduce/fixtures.jl. Source manifest explicitly records historical versus live triangular_factorization.jl difference. No current-master composition is implied.

## Private scratch

BGExportWorkspace has two union fields (BitVector or nothing; four-vector tuple or nothing) and two Int fields. It retains no matrix/backend/output/owner/callback. Policy base charge512 is not a physical header bound. Seen payload8*cld(n,64), orientation32*n; exact-length arrays only. P0=16*(l+u)+8*(n+1); retention limit min(1MiB,P0÷16). Seen preferred; orientation eligibility includes room for seen even if called alone. No allocation of an empty workspace; complete orientation attached only after four acquisitions. Actual charged amount includes only attached arrays. The tuple/workspace/header and allocator overhead remain additional measured graph obligations.

Seen scratch: one BitVector request on a miss, zero on a hit. Allocation falses initializes bits on a miss as original; original p and q validation still each reset seen and visit n permutation entries. _bgx_prepare! is O(1) with no array/graph scan. Checked budget arithmetic occurs once in seen acquisition and once in reached nonunit orientation (two calls per such export, not one). A miss creates at most one mutable workspace per export, unless a later fallback releases it. Mismatched dimensions or reduced eligibility release old arrays; no shrink copying, sizehint or retained high-water capacity. Invalid inputs/exception drop all scratch. A temporary seen may remain live while result metadata is constructed; no native-free claim.

Orientation: all-unit return has no helper acquisition and zero solve. Frozen exporter previously allocated its work/auxiliary before calling the helper even for all-unit scaling; their removal on this path is an explicit source delta. Nonunit early path uses work/auxiliary only: at most2 array requests,16*n payload, one real conditional ldiv!. After its finite/nonzero guard, two more arrays: total4 requests,32*n. Allocation-failure counts stop at the failed request. Existing full group uses0 requests, with the same solve/loops/FMA/64*n*eps threshold. No decision cached. The exact numerical helper body is restored by the inverse checker; only acquisition, exception cleanup and equivalent nothing-return cleanup differ. Temporary partial pairs are never attached. Markowitz uses seen only and original extraction ignores HHExtractWorkspace.

## Export retained work

Existing triangle validations cost O(n+l+u), original p/q O(n), scaling O(n). Raw native extraction still creates fresh HHExtractWorkspace and CSC outputs, including CSR-to-CSC assembly. Markowitz still creates six triplet arrays, folds core row order and constructs two CSC matrices. All existing conversions, native workspace, symbolic/numeric factorization and conditional orientation solve remain. The result BasisLUExport is the original immutable type with fresh owned arrays and original sharing contract. _bgx_checked_basis_lu creates one temporary result object for the native validation step just as reference; no extra invariant pass. Export failure/nothing drops scratch, not numerical active state; Task2 must supply the outer busy/publication ownership contract.

## Import successful normalization

Cold _bgx_import_upper requests D[n], two Int order maps[n], an outer packed-column vector[n], then n Int index arrays totaling u entries and n Float64 value arrays totaling u entries. Aggregate scalar-array payload8*n(D)+16*n(order)+16*u(indices+values), plus outer column records, shared immutable UpperRowOrder/UpperRowIndices wrappers and array/allocator headers. D is absent for normalize=false. These outputs match reference representation and remain freshly owned. No cached output/second active slot is added.

D requires n original U[col,col] lookups (sparse lookup cost, not falsely constant), same finite/nonzero guards. Output order maps each get n stores. CSC column traversal copies exactly u row indices. Accepted normalization performs u divisions and original finite/underflow predicates and u final-value stores. Reference has u temporary stores+u CSC copyback stores+u final packed stores. Removed: one u Float64 array request/8*u payload and2*u value stores, not an assertion of exact GC-event decrease. Raw U colptr/rowval/nzval stay read-only. Candidate still allocates a fresh D and all final packed structures. No numerical safeguards removed.

The candidate checks normalization state per slot (isnothing(D), rejected) and copies indices in that traversal; reference has a normalization loop then copy operations. This adds bounded O(u) scalar branch work while removing two O(u) store passes; net time unproved. No per-entry diagnostic callback/counter is present. Exact source loops establish store counts; future admitted instrumentation must use a separate inverse-bound clone outside timing if runtime store counts are required. This Task1 does not claim executed counts.

## Rejection and exceptions

Diagonal ineligibility stops D checks at first invalid diagonal, then raw import u value stores; its D allocation may become garbage. Division rejection at slot k performs k divisions and k-1 normalized stores, stops further division, completes the remaining index/array construction, then overwrites all u values from raw U exactly once. Total k-1+u stores, at most2*u-1, no second output allocation or retry solve. Some values remain uninitialized privately until raw fill; they are never returned on incomplete allocation. Output allocation happens earlier/interleaved compared to reference; OOM position is not claimed identical. Every local allocation can throw the same injected sentinel and raw input remains unchanged. Structural malformed CSC must be rejected at the original exporter boundary, not rescanned in importer.

## Lifecycle peak and deferred work

For C=1+r exports/imports: avoided successful-normalization temporary payload8*sum(u_t), no backend reconstruction saving claimed. Peak includes A_old+A_new+E_t+W_t+garbage awaiting GC; E_t includes whole backend/raw extraction/CSC/triplets. Copies, history H, prepared caches, wrapper and surviving scratch must be counted in Task2. Wrapper/active-factor atomic publication and copy policy are NOT implemented by Task1. No added solves or scans in existing FTRAN/BTRAN/update methods, which are unchanged. Other precisions and native retention remain unqualified.

## Tests and future execution budget

Two test modules, seven named testsets, only explicit run_workspace_tests()/run_import_tests() entry points. Synthetic OrientationSolve owns its dispatch and never overwrites a backend method. Every _bgx_scale_mode call still exercises the real candidate helper; solve boundary stubs cover thrown/zero/nonfinite outputs, not actual backend failure proof. Four failure injections, full cache acquisition/reuse, all-unit and nonretained success are separate. Genuine integration test loops seven unchanged fixtures times two selected policies:14 fresh factorization entries,14 candidate exports and14 reference exports; native orientation internal work conditional, Markowitz extraction additional. No refactors/full solves/public LPs in this Task1 fixture loop. Exact export_identity performs rational matrix work outside future timing; do not treat14 factorization entries as complete backend work.

Test allocations/snapshots are cold: fixed-size requests logs per allocator (bounded by the enumerated call loops), detached CSC/bit and packed snapshots, rational oracle matrices, synthetic n64 stored-zero triangles and n2 triangle, no diagnostic data in candidate hot loops. Candidate tests enumerate failure position over actual first-pass allocation request list; exact prospective assertion/call counts must be frozen in Task3 after static inventory, before any run. No guessed RED count and no numerical allowance.
''')
(E/'REPORT.md').write_text('''# Direct BG export workspace Task1 offline preparation

Prepared separate workspace/export/import source and structural tests under diagnostics/direct-bg-export-workspace/reproduce. No Julia, parser, import, compilation or numerics executed; no actual src/test/env/CI/master changes. Accepted parent plan/spec and amendment review remain frozen. Task1 only; Task2 wrapper/lifecycle and Task3 driver/admission remain separate.

The source uses bounded exact-size private scratch, staged orientation acquisition and fused normalization into fresh packed U. Original raw extraction and triangle/permutation validation methods are reused unchanged, with no production method overwrite. Mutable scalar concerns do not arise in this Float64-only candidate; no generalization to BigFloat or Rational is made.

Work/memory conclusions and limitations are in work-memory-ledger.md. Potential saving is8*nnz(U) temporary payload and2*nnz(U) stores on successful normalization, not measured speedup. Retained cache can raise graph size; whole future graph gates remain required. No complete native allocation/work budget is claimed.

Tests were saved before the candidate. Their Julia RED/GREEN is intentionally UNEXECUTED under the user's request. New offline inverse/hash/source checks establish source relationships only. The unchanged seven fixtures, both policies, malformed exports, signed zero, normalization fallback, budget/shrink, scratch poisoning and local allocation/solve-failure boundaries are represented. Active-factor failure publication/copy integration belongs to Task2.

Ruling: preserve the accepted inline workflow, but the explicit no-Julia request supersedes skill baseline/runtime TDD and task-done execution. No old script is run, no temporary skill workspace deleted, and no implementation beyond Task1 is authorized.
Ruling: source-derived u-store checks remain offline; no per-entry runtime audit hook is added to this performance candidate. Future Task3 may build a separately inverse-bound instrumented clone for detached checks. Wrong source-count assumptions would invalidate the ledger, not justify claiming executed counts.
''')
(E/'progress.md').write_text('''# SDD ledger — plan: docs/superpowers/plans/2026-10-18-direct-bg-export-workspace.md

Task1: in progress, offline candidate/test preparation only. BASE6ab0f14111aea8ec9043679541241dd8fe3e1920.
Pre-flight Task1->Task2: BGExportWorkspace and owner.workspace protocol consumed by future BGExportFactor; allocation keyword propagated, no wrapper now.
Pre-flight Task2->Task3: future actual wrapper type/stage and count inventory not created; no driver or launch now.
Ruling: reuse current linked diagnostic worktree; no install/build/baseline Julia because explicitly forbidden.
Ruling: use this tracked results ledger instead of running skill shell setup/task-done tools that would imply runtime completion or modify preserved plan artifacts. Existing historical ordinary stage is read-only evidence, not this task's writable workspace.
Tests prepared first. Candidate sources then prepared. Source/hash/inverse checks and independent review pending. Julia syntax/loadability, numerical correctness and allocations remain UNEXECUTED.
''')
print('Created report/ledger; no Julia')
