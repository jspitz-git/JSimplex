# Rational Primal Support Admission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans`
> to execute this source/design task sequentially. No Julia execution is allowed.

**Goal:** Decide whether the ordinary `update_primals!` consumer can use already
valid support for exactly `Rational{BigInt}` without changing arithmetic effects,
ownership, failure behavior, or adding a full admission scan.

**Architecture:** Inspect the unchanged helper, caller, support metadata and
installed scalar arithmetic. Reuse existing scratch metadata; define a concrete
read-only eligibility decision and dense fallback on paper, or reject it.
The exact type restriction is prospective, not an accepted implementation.

**Tech Stack:** Julia source text, installed Base source text, Python for bounded
source integrity checks; no imports, compilation, numerical calls or cache edits.

**Spec:** `docs/superpowers/specs/2026-10-11-simplex-core-architecture-design.md`,
original S3 value-update requirement; `diagnostics/simplex-core-architecture/S3-VALUE-UPDATE-SUPPORT-CONTRACT.md`.

## Global constraints

Preserve all numerical safeguards, tolerances, scalar policies and existing
operation order for executed entries. No small-coefficient pruning. No actual
src/test/env/CI changes, candidate/driver/launcher or numerical permission in G.
Keep every frozen artifact and failed record. Never rerun S3-F or older scripts.
No DSE/HH/isolation/import/controller-budget or cleanup-omission reopening.
Preserve user files and use the existing diagnostic worktree. Before changing
pinned continuation files, verify fresh boot/start-ticks/command and full groups
AND sessions, preserve their prior bytes and map their existing bindings.

## Review focus

- Rational{BigInt} finite/exception behavior and mutable numerator/denominator
  ownership: skipping arithmetic must not silently retain observable aliases.
- Direct-helper overlapping arrays, repeated basic indices, or entering index
  already basic: retain ordered behavior or leave these on the dense fallback.
- Invalid, detached, mismatched, cancelled-entry or absent support: no support
  rebuild, sorting, cache construction or full-vector admission scan hidden here.
- Observer/recovery writes between producer and consumer: prove the proposed
  eligibility restrictions from the actual call path, not metadata names alone.
- Full/dense support and arbitrary other scalar types: preserve the original
  dense path and account for every new check on its execution frequency.

## Task 1: One bounded source/design decision (S3-G)

**Files:** Read `src/{dual_simplex,hypersparse_pipeline,hypersparse_pipeline_types,indexed_vector,numeric,simplex_numerics}.jl`, the workspace ownership definitions located from their declarations, and installed Base rational/BigInt arithmetic actually used by the recorded runtime. Create `diagnostics/simplex-core-architecture/S3-RATIONAL-PRIMAL-SUPPORT-ADMISSION.md`, its independent review, and new `results/S3-G` evidence. Modify only STATUS and the original roadmap after preserving their current versions.

**Interfaces:** Consumes `update_primals!(workspace::SimplexWorkspace{T}, tableau_column::Vector{T}, entering_index::Int, leaving_row::Int, primal_step::T)` and the six-buffer `HypersparseWorkspace`. Produces a written eligibility table, failure/ownership analysis and exact work ledger. No Julia interface is implemented.

- [ ] Read F report/review and current continuation; verify only bindings needed
  for this new decision. Record current host/refs without repeating old audits.
- [ ] Follow multiplication/subtraction by exact zero in the installed scalar
  source. State finite versus nonfinite behavior, object identity and mutation
  obligations. Do not equate rational value equality with owned BigInt identity.
- [ ] Trace primal/direction/basis ownership and supported callback writes to
  this boundary. For each of the five review-focus classes, give a concrete
  source-backed accept/fallback/reject outcome and a prospective test oracle.
- [ ] Specify the eligibility predicate in evaluation order, with exact fields
  and checks, and the iteration/entering-addition behavior. Keep arbitrary
  Rational types and floats dense. If O(1) admission cannot establish required
  ownership/order without new cache metadata or an O(m) scan, stop this route;
  do not invent another equivalent inventory stage.
- [ ] Count added checks on eligible and fallback calls, indexed visits including
  cancelled entries, retained owners and invalidation obligations. Separate
  O(s) element work from BigInt bit complexity. No inferred speedup.
- [ ] Independently review the complete source/design decision with fresh
  gpt-6-astra, explicitly including unnecessary work/memory and numerical
  semantics. Resolve findings while preserving any rejected evidence.
- [ ] Publish only after separate PASS closure and exact staged names/blobs are
  verified; fail fast before commit/push. Verify committed blobs and both remote
  refs. No production integration.

If accepted, the next deliverable is a concrete offline source/test preparation
plan with explicit boundaries, not a launch. Any later numerical experiment
requires separate accepted admission and a new explicit human allowance.
