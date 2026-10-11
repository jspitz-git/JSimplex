# HH Markowitz exact triplet allocation plan

> **For agentic workers:** Use superpowers:executing-plans inline and sequentially.

**Goal:** Reduce measured temporary triplet growth during HH Markowitz extraction
without changing factor entries, arithmetic order, supported precision or ownership.
**Architecture:** Count exact triplet lengths from packed-vector lengths and a
nonzero-only pass over the existing dense core; allocate private I/J/V vectors
once and fill them in the original order. Retain existing sparse CSC assembly,
permutations, extraction checks and independent output buffers. No cache/API.
**Tech Stack:** Julia Test/LinearAlgebra/SparseArrays/TOML, existing resource guard.
**Spec:** ../specs/2026-10-11-simplex-core-architecture-design.md

## Constraints and decision

One numerical Julia/BLAS thread, heap2GiB,VM8GiB,availableRAM6GiB,swap1GiB.
No excluded inputs/aliases; synthetic matrices only for local gates. Preserve
failed attempts, old sources/envs and accepted measurements. No changed tolerance,
precision or dropped coefficients. Main remainsb720674 until reviewed integration.
Standing user authorization explicitly requests inline work without new approvals.
This bounded S4 implementation follows the approved architecture spec; no new
product behavior/design decision is required from the user.

Ruling: unconditional dense-triangle capacity can overallocate for a mostly-zero
core. Use exact counts instead, accepting one additional O(core_dimension^2)
zero-predicate traversal and O(sparse_pivots) length reads per refactorization.
Do not claim a speedup if this added work cancels allocation savings. No per-step
or candidate overhead outside refactorization. All new vectors are temporary;
there is no retained cache. Output CSC arrays remain independently owned.

## Review focus

- Count and fill predicates must agree for signed zero/tiny coefficients/all types.
- Empty/all-sparse/all-dense/mixed core and nontrivial core pivot order need coverage.
- Changed ordering or precision is unacceptable; compare exact CSC/permutation arrays.
- Failing/saved factor semantics and ownership remain unchanged.
- New counting traversal must be measured on dense and mostly-zero cores, not
  hidden by reporting only lower allocation traffic.

## Task 1: RED and minimal implementation

Modify src/huangfu_hall_factorization.jl::_hh_extract_parts(::MarkowitzBackend,...).
Create reproduce/hh_triplet_reference.jl (exact pre-change function) and
reproduce/hh_triplet_checks.jl; no replacement of reference bodies after measurement.

- [x] Before production edits, record a normal-mode failing allocation gate on
  dense256: candidate extraction <=80% of baseline bytes, with exact output and
  zero measured compilation. Candidate initially is unchanged production.
- [x] Add exact counts and allocate/fill triplets once. Preserve iteration/zero
  checks and CSC construction; no new symbolic factor reuse or arithmetic.
- [x] GREEN allocation gate and exact extraction equality on Float16/32/64,
  BigFloat,Rational{BigInt}; empty,sparse,dense,mixed,signed-zero/tiny and core pivot
  cases. Check output storage ownership and saved-factor residual/failure behavior.

## Task 2: cost and integration gates

Create reproduce/hh_triplet_cost.jl. Six alternating baseline/candidate pairs,
16calls each, independent warmups, same source fixture ownership. Include sparse,
dense and forced mostly-zero valid core representations at64/256; mixed core too.
Record every sample's compile/GC/bytes/events/elapsed, exact output equality.

- [x] Audit exit/pins, complete expected samples and compile0; report medians/ranges.
  Reject promotion for material unexplained regression even when bytes improve.
- [x] Run existing HH/Markowitz focused correctness and precision/lifecycle tests,
  plus guarded paired sparse/dense complete-solve trajectories if cost passes.
- [x] Fresh independent numerical/work/memory review. Only then separate the
  production commit, integrate into master, run integration checks and push.
  If rejected, preserve experiment and restore production before further work.
- [x] Update S4 report/STATUS/parent and record exact next coverage gaps. This local
  chunk does not complete whole-medium/S6 or all other backend/precision studies.

Task1 complete: RED440pass/1expected allocation failure; GREEN442pass. Task2 cost84
compile0samples and focused4366 pass; trajectory pending. See S4-TRIPLETS.md for
work counts, numerical coverage and mostly-zero-core timing tradeoff ruling.

Paired trajectory gate complete:121 assertions,8exact pairs,source/pins verified.
Final independent review pending.

Task2 complete: cost84/14audit gates,focused4366,trajectory8pairs/121assertions,
review approved without blockers or deferred minors. Production0f2c468 ->
master3220118; integrated1294/1294 with independent pins and user-file preservation,
push/remote verified. No numerical job active. Preserve raw RED and all snapshots.
Ruling: bounded same-arithmetic allocation improvement accepted with explicit
mostly-zero-core timing uncertainty; no whole-solver/medium speedup inferred.
