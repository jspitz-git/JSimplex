# HH native component attribution plan

> **For agentic workers:** Use superpowers:executing-plans inline and sequentially.

**Goal:** Separate native Float64 HH backend, immutable extraction and private
scratch costs before selecting another production reuse change.
**Architecture:** A diagnostic-only driver exercises deterministic well-conditioned
sparse and dense CSC bases, timing backend-only, extraction-only and whole-refactor
batches independently. It records live/checkpoint/private Julia object graphs and
verifies saved factors across dimension/pattern changes and failed refactors.
**Tech Stack:** Julia LinearAlgebra/SparseArrays/TOML/SHA, existing Python guard.
**Spec:** ../specs/2026-10-11-simplex-core-architecture-design.md

## Constraints and interpretation

One numerical Julia/BLAS thread, heap2GiB, VM8GiB, availableRAM6GiB, swap1GiB;
no excluded models or aliases, no changed tolerances/production files. All fixtures
are synthetic. Preserve attempts. Current production matches masterb720674.
Native Float64 only in this first slice; Markowitz and other precisions remain
explicit follow-up coverage. This is component attribution, not a speed comparison.
Do not sum independent component timings or subtract GC to infer arithmetic speed.
Base.summarysize measures reachable Julia objects, not external UMFPACK allocations
or hidden backing capacity; process RSS/VM comes from guard samples. Shared base
storage must be deduplicated when reporting the live plus checkpoint graph.

## Review focus

- Saved copies share immutable base, own scratch, and contain no mutable backend.
- Extraction output cannot alias private CSR scratch; failure preserves live base.
- Same dimension does not authorize symbolic reuse; exercise a changed sparsity pattern.
- Warm samples require compile0; every recorded sample is preserved, six fixed rounds.
- Synthetic small matrices cannot explain all cumulative medium allocations.

## Task 1: component and ownership diagnostic

Create diagnostics/simplex-core-architecture/reproduce/hh_component_attribution.jl.
Interface main(output): emits TOML with fixtures, per-region samples, ownership
checks and Julia-visible retention. No production API is added. Reuse existing
HH internal component entry points without replacing their method bodies.

- [x] Generate deterministic sparse/dense CSC matrices at dimensions64/256; sparse
  fixtures have two different off-diagonal patterns. Strict diagonal dominance.
- [x] Warm each case/region; measure six rotating rounds of16 calls, recording
  elapsed/compile/GC/bytes/allocation events, matrix SHA and factor nonzeros.
  Backend-only calls retain the last backend; extraction retains the last base;
  whole-refactor retains the live factor. Their lifetimes differ explicitly.
- [x] Outside timing check FTRAN/BTRAN residuals and saved-base fingerprints after
  refactorization, same-size pattern changes,256->64->256 and singular failure.
  Record private scratch/base/backend/copy and deduplicated combined graph sizes.
- [x] Run guard600s with fresh pinned source/test/environment/driver/launcher;
  require exit0, independent pins and complete expected sample count with compile0.
- [x] Report component medians/ranges and retention limits; choose a next hypothesis
  only if these data distinguish avoidable work from required factor ownership.
  Commit the report, update STATUS. No production optimization acceptance follows.

Ruling: S4 attribution precedes S5 construction changes because both completed
S0 origins show large refactor allocation traffic; the existing S4-A dimension
fix and accepted long references are not remeasured. A diagnostic has no RED
production regression: residual, ownership, count and compile assertions are its
gates. Follow-up production changes still require RED/GREEN and independent
numerical/work/memory review.

Attempt native-components-1: exit1/pins independently unchanged,18 timing records
written before a report failure: graph() inferred Dict{String,Int64}, then the
case label insertion failed. No accepted complete attribution. Preserve report,
process and log; change only this report dictionary to Dict{String,Any}. The
original whole-script failure is RED; rerun the script to verify serialization
and all remaining ownership/lifecycle gates. No production numerical failure.

Task 1 complete: native-components-2 exit0,72 records, all compile0, all13 audit
gates, independent pins, residual/ownership/pattern/dimension/failure checks pass.
Fresh independent gpt-6-astra review has no blocker or unnecessary production
work/memory finding. See S4-COMPONENTS.md for full results and retention limits.
Ruling: lifecycle graph sizes describe the live factor plus a fresh shared-base
checkpoint; they exclude the old checkpoint still held by lifecycle(). Do not
interpret the shrink graph as total retained memory. No new run is needed for
this reporting clarification. The next Markowitz slice is a separate experiment;
this accepted native slice must not be repeated unchanged.
