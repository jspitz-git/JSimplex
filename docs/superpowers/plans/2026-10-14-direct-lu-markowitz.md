# Common factor export and Markowitz direct LU Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task, with fresh independent reviews at the stated boundaries. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Qualify a common native/Markowitz factor export and compare all three direct LU managers with their ordinary counterparts in short, bounded tests.

**Architecture:** An isolated ordinary source overlay exposes a private export contract and explicit direct-manager factory. Existing Markowitz extraction and triangular update kernels are reused; the old diagnostic installer is never executed. Component qualification precedes cost tests and a small public-solver integration check.

**Tech Stack:** Julia, LinearAlgebra, SparseArrays, existing JSimplex backends; Python for admission and result auditing. No new dependency.

**Spec:** ../specs/2026-10-14-direct-lu-markowitz.md

## Global Constraints

- First deliverable is an isolated Float64 experiment, not a production default.
- Other precisions retain ordinary dispatch and original arithmetic.
- No small coefficients or tolerances are changed. Outer simplex recovery and final certification remain unchanged. Direct native substitution loses UMFPACK combined-solve iterative refinement; equivalent native stability is not claimed.
- Use one Julia process at a time, Julia/BLAS threads=1, heap hint=2 GiB, VM limit=8 GiB, available RAM floor=6 GiB, swap ceiling=1 GiB. All process limits include termination.
- CI stays disabled, automation paused, HH reuse disabled; preserve user environments.
- Do not rerun or edit historical direct-LU experiments, replay drivers, frozen audits or old numerical attempts. New files and output paths only.
- No numeric launch in this planning step. Before each later execution stage bind exact sources, runtime, fixtures, driver, commands and output reservation; independently review numerical and work/memory admission. Standing short-run permission is sufficient; no repeated human approval request.

## Review Focus

1. Dense-core row pivots and sparse/dense boundary permutations: test the full exported identity, not only separate L/U shapes (Task1).
2. Failed/resized refactorization, divergent copies and mutable source buffers: old factors and exports must remain usable without alias corruption (Tasks1–2).
3. Scaling ambiguity, normalization overflow/underflow and unsupported types: explicit fallback, unchanged exceptions and retained tiny nonzeros (Tasks1–2).
4. Prepared entering spike followed by DSE FTRAN, aliasing and indexed solves: correct direction provenance and cache invalidation (Task2).
5. Attractive solve timings hiding export cost, retained backend memory or changed solver trajectories: whole lifecycle comparisons and separate public certificates (Tasks3–4).

## Source map and candidate file boundaries

Read src/factorization.jl, markowitz_factorization.jl, triangular_factorization.jl,
triangular_rows.jl, triangular_indices.jl, triangular_spikes.jl,
hypersparse_factorization.jl and huangfu_hall_factorization.jl. Existing
_hh_extract_parts(::MarkowitzBackend,::HHExtractWorkspace) and scaling helpers are
reusable extraction primitives; borrowing them does not enable HH symbolic reuse.
Historical direct.jl/README.md and tests markowitz_tests.jl,
triangular_prepared_spike_tests.jl, triangular_preparation_lifecycle_tests.jl,
triangular_stability_tests.jl are references only.

Prepare new files under diagnostics/direct-lu-markowitz/reproduce/:
`factor-export.jl`, `direct-factor.jl`, `fixtures.jl`, `correctness.jl`, `cost.jl`,
`solver-check.jl`; new `results/` paths hold each stage's immutable outputs.
The ordinary candidate overlay includes the two implementation files after
huangfu_hall_factorization.jl. Reference overlay has identical source/environment
except these additions and the explicitly bound factory routing in Task4.
Actual src/test/Project/Manifest/CI and old diagnostics remain untouched in Tasks1–4.
Future production location would be src/factor_export.jl and src/direct_lu_factorization.jl;
production promotion is a separate decision after results, not part of this plan.

### Task1: Export contract and isolated implementation

**Interfaces:** Define private `BasisLUExport` with fields
`lower::SparseMatrixCSC{Float64,Int}`, `upper` of the same type,
`rows::Vector{Int}`, `columns::Vector{Int}`, `scaling::Vector{Float64}`,
`divide_scaling::Bool`. `_export_basis_lu(backend)::Union{Nothing,BasisLUExport}`
has concrete methods for UMFPACKBackend and MarkowitzBackend{Float64}; generic
fallback returns nothing without constructing factors. Work vectors needed for
native orientation are created inside the export and included in its cost.
Empty UMFPACK state returns an owned empty export. Keep arrays private by contract.

- [ ] Prepare literal RED tests for missing export methods, then implement in the new candidate file. Expected RED is a missing contract/method, not a numerical failure of the existing solver. Execute only after Task2 admission is accepted.
- [ ] Use _hh_extract_parts(F,HHExtractWorkspace()) on the underlying native factor and _hh_scale_mode(F,L,U,p,q,s,work,auxiliary) with private vectors; avoid _umfpack_scale_mode and its full sparse absolute-value copies. Use _hh_extract_parts on Markowitz directly, without an orientation solve. Validate dimensions/permutations/CSC triangular structure/all finite coefficients/unit lower diagonal/finite nonzero upper diagonal and scaling once at export. Return nothing only for unsupported type/backend or ambiguous native orientation; propagate other errors. Malformed claimed output raises ArgumentError before publication.
- [ ] Freeze these correctness fixtures: empty; 1x1 [2]; 8x8 diagonal 2:9; mixed [I4 zeros(4,4); E C], with E[1,1]=E[2,2]=E[3,3]=E[1,4]=1/8, E[4,4]=1/2 and all other E entries zero; pure dense C; signed/permuted/scaled tridiagonal n16; singular duplicate-row matrix; explicit stored zeros. C0[i,j]=8 when i=j and (-1)^(i+j)/8 otherwise, C=C0[[4,2,3,1],:] (4x4). Assert mixed fixture has both sparse pivots and nonempty core, and core.p is nonidentity; assert nonzero sparse-to-core L21 contains unequal entries moved by that permutation (the incorrect unpermuted L21 must fail the identity oracle). Assert pure C has zero sparse pivots. Source-derived fixture discriminator: all first four columns are nonsingleton, so singleton-row pivots select4 then3; stored nonzeros25→22→20 and remaining dimensions8→7→6 trigger dense transition at k=2. The core C row swap moves the unequal 1/8 and1/2 multipliers from sparse pivot4. Require k=2 and these permutation-sensitive coefficients in the executable test. This is a prospective source-derived expectation, not runtime evidence. Refuse fixture drift, do not tune after results.
- [ ] For scaling fixture use tridiagonal diagonal4/subdiagonal-1/2/superdiagonal1/4, cyclic row permutation by3, reversed column permutation, row scales 2^((i%7)-3). Check full P*S*B*Q=L*U with exact Rational{BigInt} residual evaluation of stored Float64 values outside measured windows; bound each entry by 128*n*eps(Float64)*(abs(L)*abs(U)+abs(P*S*B*Q)) entrywise. Zero denominator requires exact zero. This is a tolerance identity, not a claim of exact LU arithmetic.
- [ ] Test backend-buffer mutation/refactor after export, two independent exports, scaling orientation in both conventions through helper-level constructed parts, invalid permutations/diagonals/NaN, and unsupported Float32/BigFloat256/Rational{BigInt}. Unsupported calls return nothing and leave input values/owners unchanged. No arbitrary-precision export admitted.
- [ ] Self-review source diff and explicit work ledger, then obtain independent review of export algebra, ownership, fallback and costs before numerical admission.

### Task2: Three managers and lifecycle correctness

**Interfaces:** `_direct_lu_factor(Factor, B::AbstractMatrix{Float64}, backend::Val{R}; normalize::Bool=true)` consumes Task1. A new `DirectLowerBackend{R}` supports existing `_backend_dimension`, `_backend_storage_count`, `_copy_backend`, `_backend_forward_solve!`, `_backend_transpose_solve!`, `sparse_solve_view` (returns nothing), and manager-specific `refactorize!` methods. R is :native or :markowitz. Keep requested normalization/backend through fallback. The wrapper has the same concrete type for successful export and ordinary fallback for a given R; optional typed ordinary backend state represents fallback, so in-place refactor publication never tries to replace a field by an incompatible type. Ordinary generic precisions use their original constructors.

- [ ] Build exactly one ordinary backend, export once, and initialize the chosen triangular manager directly from packed U and q. Do not call Factor(B) then factor B again. Avoid constructing and discarding identity U in the successful direct path; a private initializer must allocate required manager scratch/history/cache exactly once. Specify private _init_direct_manager(::Type{Factor},base,packed_upper,q) for the three manager types. FT/SS use ordinary packed indices; BG uses one newly owned UpperRowOrder shared by its UpperRowIndices, with the actual nonidentity U and initial dirty upper cache. BG copies must rebase this order. Existing production constructors remain unchanged.
- [ ] Port the historical lower-only algebra, not its global method installer. Forward lower solve is inv(L)*P*S*rhs then inv(D) if normalized; transposed lower solve is S*P'*inv(L')*inv(D)*rhs. Normalize only owned U, validating all new values before mutation. If normalization is unsafe retain unnormalized direct; if export is unavailable initialize identity-correction with the already constructed original backend. Record actual mode.
- [ ] Keep packed-U manager algorithms unchanged. Share only immutable-by-contract extracted Float64 lower data in copies; own scratch and mutable upper/permutation state, preserve existing shared-history retirement rules. Release full backend/workspace and temporary CSC U on success. Do not add per-solve validation scans, metadata caches or runtime counters.
- [ ] Prepare tests for all3 managers x both backends x normalized/unnormalized direct, compared with ordinary correction on Task1 nonsingular fixtures. Verify FTRAN/BTRAN residuals against current explicit B after each update; exact offline Float64-token residual norm bound is 128*n*eps(Float64)*max(1,norm(M,Inf)*norm(x,Inf),norm(rhs,Inf)). Do not require direct/correction bit identity or suppress exceptions.
- [ ] Eight replacements at j=1+mod(7*t,n), r=1+mod(j,n), a=copy(B[:,j]); a[r]+=1/32 for t=0:7, n>=2. Each uses genuine entering FTRAN, then distinct DSE RHS FTRAN, update, then unit-RHS BTRAN. Preserve source input matrices/RHS, exercise destination=RHS alias only where ordinary contract allows it, rejected scratch aliases, and indexed :sparse/:dense/:auto fallback. Fork a copy after update2, diverge it, refactor original after update4, check saved copy. Include failed singular and resized refactors, stale prepared spikes and tiny/nonfinite normalization rejection with unchanged original U. Through a test-local exporter injection seam (no production method overwrite), force export unavailable across direct→fallback→direct refactors; verify requested R/normalization, wrapper type, input ownership, saved copies, solutions and transactional failures at each transition. Seal the exact seam and all extra correctness calls in admission.
- [ ] Freeze exact tests/counts and guarded commands in admission. One RED process <=30s and one correctness process <=90s, including termination. RED runs only contract sensitivity tests on reference; GREEN runs full candidate checks plus focused unchanged Markowitz/triangular lifecycle tests named in admission. No full suite. Preserve raw before aggregate assertions and process logs when raw is absent; any unexpected failure stops this stage.
- [ ] Independent result review must accept correctness and absence of unnecessary work/memory before Task3. Successful component tests do not establish a public solver trajectory.

### Task3: Bounded paired lifecycle costs

**Files/interfaces:** fixtures.jl exports exact matrix, RHS and replacement schedule tokens; cost.jl uses explicit factories only. No production dispatch override. Reference is ordinary correction; candidate is normalized direct, with actual mode checked outside measured windows.

- [ ] Freeze four cost fixtures n32/96 x sparse/dense. Sparse uses the Task1 tridiagonal formula. Dense has diagonal4 and offdiagonal (-1)^(i+j)/16/n (n32/96; freeze exact resulting Float64 bits before run). Both apply cyclic row permutation by3 and reversed columns, no additional row scaling. Each step is entering FTRAN(a_t) to direction, then DSE FTRAN(i/n) in a different destination, replacement with the unchanged direction, then BTRAN(e_j). The reference basis changes by exactly B[:,j]=a_t. Freeze exact Float64 tokens for all a_t, DSE vectors and the resulting matrices B4/B8 used at refactors; compute these outside measured windows identically for both sides, with no in-window oracle matrix update or unused alternating RHS. Bind source/input hashes before launch.
- [ ] There are24 cells:4fixtures x3managers x2backends. Two serial processes, each3warm+7measured alternating reference/candidate pairs per cell, reversed starting side in process2. Each window owns a complete fresh lifecycle: construct, eight updates with2FTRAN+1BTRAN per update, refactor with B4 after update4 and B8 after update8. The second refactor exercises ordinary backend spare/output reuse; report first and second refactor costs separately. Thus at most960 lifecycles,7680updates,15360FTRAN,7680BTRAN and1920explicit refactors, plus960initial constructions across warm/measured schedules. Native orientation solves and backend internal work are additional, explicitly ledgered. Correctness probes/warmup beyond this schedule require explicit admission counts.
- [ ] Include factor/export/normalization/packed construction/scratch in windows. Input fixture preparation and result validation stay outside, identically for both sides; no repeated matrix copy to obtain a privileged candidate input. Record total and nested construction/FTRAN/BTRAN/update/refactor durations, total bytes/events/GC/compile/recompile and detached result checks. Component timing instrumentation is identical; nested timers are subsets, never added again to totals. Store final factors only until checks; post-window reachable-memory snapshots after the second refactor include pooled capacity/workspace and ordinary backend spares. Only final-state retained memory is measured; long-history and peak/native live memory remain unqualified. History ownership is tested in Task2 without retaining old factors during cost windows.
- [ ] Both processes <=90s each including termination. Record every window and partial progress immediately between cells; preserve timeout/GC/outliers. Measured compile/recompile must be zero. Do not rerun a rejected schedule, increase dimensions/limits or tune thresholds using results. GC stays part of total cost; report it rather than delete affected pairs.
- [ ] Report paired ratios/median/MAD/range and per-process results for each cell, no pooled cross-manager claim. A cell is promising only if each process median total time ratio<=0.95, at least10/14 measured pairs faster, and median total bytes AND events do not increase in either process. Record retained memory; an increase>10% versus reference disqualifies that cell from promotion recommendation. These are engineering selection rules, not a statistical proof. A failed cell remains failed; a manager/backend is promising for this bounded eight-update/two-refactor workload only if all four cells qualify. This does not cover long chains, large sparse fill, recovery-heavy trajectories or equivalent native refinement. No automatic integration even on PASS.
- [ ] Independent numerical/work/memory result review; a correct but slower path may remain an explicitly labelled experimental comparator. Do not replace the default or call it a speedup without its exact qualifying scope.

### Task4: Short public integration and disposition

**Files/interfaces:** solver-check.jl and a separately frozen candidate overlay factory fragment at src/factorization.jl::_basis_factorization(B,options). Only legacy Float64 with FT/SS/BG routes to the explicit direct factory using the option's native/Markowitz backend; PFI, HH, adaptive and all other precisions retain ordinary routing. No process-global method replacement or new public SolverOptions value. Reference/candidate use separate ordinary project processes with identical dependency environment.

- [ ] Prepare this overlay offline, exact inverse of factory fragment and two includes; independently review dispatch, refactorization policy and exception behavior. Bind the current source and tested implementation again; do not load old direct.jl installers or isolated nested full modules.
- [ ] Fixed tiny public LP: minimize -3*x1-2*x2, rows x1+x2<=4, x1<=2, x2<=3, variables>=0; expected unique optimum [2,2], objective -10. Each manager/backend uses original legacy policy, dual algorithm, pricing=:steepest_edge, presolve=false, scaling=:off, partial_pricing=false, verbose=false, refactorization_interval=2, time_limit=5s, iteration_limit=100. Tolerances remain default and are bound in admission. Run reference/candidate for all6combinations:12solves total, in two serial processes <=60s each including import/termination. No large MPS solves. This is functional integration, not timing evidence.
- [ ] Assert actual direct factory selected, no fallback on this fixture, backend preserved through exercised refactors, unchanged inputs, OPTIMAL and independent original-row/bound feasibility plus reference objective; preserve normal production certification. Log iterations/refactors without demanding identical trajectories. Add dispatch-only checks for adaptive/Float32/BigFloat/Rational/HH/PFI without extra public solves. If the fixture does not exercise a refactor, report that coverage as absent and rely on Task2 rather than changing the fixture post-run.
- [ ] Bound stages separately: RED30+correctness90+cost2x90+integration2x60 =420s maximum process wall budget over the whole future programme, not one continuous run; no stage advances after unexpected numerical failure. Cost rejection permits separately reviewed functional characterization only, never automatic production promotion.
- [ ] Publish results and independent review. Decide separately per manager/backend: promising, inconclusive, or rejected for performance; retain correctness limits. Any eventual package API/default or dynamic sparse-storage change requires a new concrete plan, not completion of this one by implication.

## Planning completion and next action

This document and the linked spec are the plan-only deliverables. Save a fresh
independent review with source references and file hashes; resolve findings before
publication. No Julia/query/import/compile/test/benchmark in the planning stage.
Next action after acceptance is Tasks1–2 offline candidate/test preparation and
independent review, followed by a separately sealed short-run admission.
