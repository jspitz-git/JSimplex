# Sequential Basis Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce triangular basis overhead through five separately reviewable, sequential experiments.

**Architecture:** Stack one feature branch/worktree per proposal on the last verified predecessor. Preserve existing defaults unless validation supports changing them; larger numerical changes use explicit opt-in paths first.

**Tech Stack:** Julia, native sparse LU, Markowitz LU, existing basis replay and external LP diagnostics.

**Spec:** `docs/superpowers/specs/2026-09-28-basis-optimization-series.md`

## Global Constraints

- Use problem precision; higher precision remains a recovery mechanism.
- Do not change the adaptive simplex strategy.
- One numerical process at a time, one Julia/BLAS thread, bounded time/memory.
- Do not solve/factorize big.mps, largo.mps or AnyMod.mps, including aliases.
- English repository artifacts; separate worktree and verified commits per proposal.
- Keep public APIs compatible and retain provenance safeguards.

## Review Focus

- Auxiliary solves overwriting or evicting a prepared entering column.
- Failed updates/refactorizations and copied factors retaining stale metadata.
- Empty matrices, identity tails, signed zero and exceptional arithmetic.
- Generic precision and backend fallback paths accidentally using Float64 assumptions.
- Sparse kernels paying more for graph construction than they save in solves.

## 1. Selective update preparation

Worktree `.worktrees/basis-selective-preparation`, branch `perf/basis-selective-preparation`.
Files: `src/triangular_factorization.jl`, `src/triangular_spikes.jl`,
`src/hypersparse_pipeline.jl`, `src/{primal_simplex,dual_simplex,solver}.jl`,
`test/triangular_selective_preparation_tests.jl`.
Interface: internal `_ordinary_forward_solve!(destination,factor,rhs)` skips
preparation; public `forward_solve!` retains its behavior. Pipeline keyword
`prepare_update::Bool=false` is explicitly true at entering-column sites.
Adaptive pipeline behavior remains unchanged in this stage.

- [x] Add failing tests proving auxiliary solves do not evict a prepared direction,
      same-buffer overwrites invalidate provenance, and update residuals remain small.
- [x] Add the shared internal solve implementation and explicit call-site intent.
- [x] Run prepared-spike, triangular and pipeline regression suites, the project
      test entry point, paired histories, and external primal/dual LP corpus.
- [x] Record measurements/limits and commit the verified feature.

## 2. Incremental auxiliary lists

Worktree `.worktrees/basis-incremental-metadata`, branch `perf/basis-incremental-metadata`.
Files: `src/triangular_rows.jl`, `src/triangular_factorization.jl`, relevant tests.
Interface: retain `_dense_upper_columns(factor)` sorted logical column output;
retain `_triangular_row_columns!` incidence interface. Track the earliest changed
column rather than rescanning a known unchanged prefix; clear only touched rows.

- [x] Add tests for rotated identity/nonidentity columns, disjoint touched tails,
      copied/refactorized factors and failed replacements.
- [x] Implement affected-region maintenance with conservative invalidation.
- [x] Validate exact replay outputs and compare total update/solve costs for all
      three managers, including early medium and runtime histories.
- [x] Record results and commit.

## 3. Fused solve stages

Worktree `.worktrees/basis-fused-solves`, branch `perf/basis-fused-solves`.
Files: `src/triangular_rows.jl`, `src/triangular_factorization.jl`, solve tests.
Interface: existing public solve signatures and buffer ownership remain intact.
Fuse row permutations with the next solve stage or hand off existing scratch
buffers. Evaluate diagonal-position caching separately from buffer fusion.

- [x] Pin aliased input, factor scratch, empty/identity factors, exceptional values
      and Float32/generic solve behavior against independent matrix solutions.
- [x] Implement buffer handoff and permutation fusion, preserving arithmetic order
      where practical; reject extra metadata if maintenance outweighs solve savings.
- [x] Run focused/project tests, paired histories and independent external solves.
- [x] Record each accepted/rejected optimization and commit accepted changes.

## 4. Legacy hypersparse kernel

Worktree `.worktrees/basis-legacy-hypersparse`, branch `perf/basis-legacy-hypersparse`.
Files: `src/hypersparse_updates.jl`, `src/hypersparse_pipeline.jl`, options and tests.
Interface: explicit legacy kernel selection independent of adaptive strategy;
retain dense fallback for unsupported types, dense support and exceptional inputs.
Finalize option naming after inspecting existing option validation and graph APIs.

- [x] Measure sparse graph construction and identify a reusable packed-factor
      traversal; do not enable a kernel that rebuilds all U after each exchange.
- [x] Add sparse/dense equivalence, graph invalidation and original LP certificate tests.
- [x] Implement opt-in BTRAN first, then FTRAN where total measured cost improves.
- [x] Measure own trajectories versus dense mode and PFI; commit with limitations.

Task 4 disposition: completed as a tested diagnostic opt-in, not a new public
option/default. Both hybrid variants regress runtime replay bundles; independent
LP trajectory tests pass. See diagnostics/basis-legacy-hypersparse/README.md.

## 5. Direct LU updates

Worktree `.worktrees/basis-direct-lu`, branch `perf/basis-direct-lu`.
Files: new direct-LU factor module, factorization dispatch, tests and diagnostics.
Interface: existing basis solve/update/copy/refactorize contracts with explicit
experimental selection; existing managers remain available for comparison.

- [ ] Inspect backend factor extraction, permutations/scaling and ownership;
      write the exact factor identity and update equations before implementation.
- [ ] Implement a bounded prototype with independent matrix residual tests for
      successive replacements, pivot failures, copy/refactorize and transposed solves.
- [ ] Integrate opt-in operation with compatible backend/type fallback, then
      test increasingly long histories and independent runtime/medium solves.
- [ ] Compare total cost and stability with correction-factor managers and PFI;
      commit only verified functionality and document unsuccessful experiments.

## Execution and acceptance

The later architectural steps require detailed local designs based on the
preceding measurements; expand each section before changing its production code.
This is an execution dependency, not a request for renewed user approval.
Each feature gets a final independent code review and a committed report. A speed
claim must identify workload, warmup, baseline, source revision and full versus
fixed-history timing. A numerically unsafe or slower candidate is documented and
rejected instead of becoming a new default.

## Implementation notes from source inspection

Task 2 can conservatively retain an unchanged upper prefix: all three replacements
rotate/change rows and columns only at or after the leaving column's current
position. An `upper_dirty_from` bound must take the minimum across invalidations,
including unsuccessful replacements. A separately owned list of populated
incidence rows can replace `foreach(empty!, rows)` for FT/SS. Copy constructors
start with empty incidence; refactorization clears it before resetting the cache.

Task 3 can compose three existing mappings while gathering/scattering one vector:
compiled row-operation coordinates, logical upper coordinates, and original
basis column order. BG's stable upper coordinates are a fourth mapping; copied
factors rebase those coordinates, so equality of row maps must never be assumed.
The ordered last entry of a packed triangular column can supply the diagonal
without a binary search, with the missing-diagonal case preserved explicitly.

For Task 4, first evaluate a hybrid: keep the already optimized correction-factor
operations dense, but use reachability for the immutable base LU. This avoids any
updated-U graph construction and leaves the adaptive pipeline untouched. Measure
conversion and base-graph construction in total costs. Full sparse correction
traversal is justified only if that baseline leaves substantial profitable work.

For Task 5, the existing update kernels can potentially operate on the original
LU upper factor by replacing the base backend with a lower-only backend. For
`P*S*B*E = L*U`, use `B0 = inv(S)*transpose(P)*L`, initial packed upper `U`, and
initial column order from `E`; existing updates then maintain
`B = B0*inv(R)*U*transpose(Q)`. Native scaling direction must be verified using
the existing UMFPACK scale-mode check. Native Float64 is the first prototype;
unsupported backend/type combinations retain the existing correction-factor
implementation. Losing native combined-LU solve refinement and starting from a
potentially dense upper factor are explicit stability/performance risks to test.

Task 3 detailed design: keep the compiled elimination order, but gather from its
physical coordinates directly into upper-solve coordinates. Save prepared spikes
in logical coordinates before solving, then scatter once into basis order. BTRAN
composes stable-upper and compiled-row maps in one gather before reverse row
operations. If destination aliases spike scratch, copy the completed source to
work before invoking the backend. Generic fallback retains existing operations.
Use the sorted last diagonal entry when present, retaining lookup for malformed
or missing diagonal columns. No separately maintained diagonal cache is needed.

Task 4 detailed trial design: an explicitly loaded diagnostic backend wraps native
Float64 LU with one lazily constructed immutable sparse view. Dense correction U
and row operations remain unchanged. BTRAN-only and BTRAN+FTRAN are separate
trials. Count input support before building the view, retain dense fallback for
high density/nonfinite input, and catch only sparse arithmetic overflow. Include
support conversion, graph construction, copying and fallback in total costs.
Copies own traversal scratch; refactorization creates fresh backend/view state
transactionally. No adaptive policy is changed. Public integration is conditional
on whole-bundle and own-trajectory results; reject a slower trial with raw evidence.
