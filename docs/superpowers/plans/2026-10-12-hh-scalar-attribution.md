# HH scalar component attribution plan

> **For agentic workers:** Use superpowers:executing-plans inline and sequentially.

**Goal:** Fill the bounded HH component-cost precision gap without repeating the
accepted Float64 runs or changing production.
**Architecture:** A separate diagnostic driver measures backend refactorization,
HH extraction and whole refactorization with independent fresh owners. It verifies
residuals, exact saved-factor preservation, dimension/pattern/failure lifecycle and
Julia-visible retained graphs outside timing. No backend selection change.
**Tech Stack:** Julia LinearAlgebra/SparseArrays/TOML/Serialization, existing guard.
**Spec:** ../specs/2026-10-11-simplex-core-architecture-design.md

## Constraints and rulings

Source matches master3220118. One Julia/BLAS1,heap2GiB,VM8GiB,availableRAM6GiB,
swap1GiB. Synthetic inputs only; no big/largo/AnyMOD or aliases. Preserve all old
runs/worktrees/envs. No production edits, changed tolerance or precision to rescue
comparisons. Standing authorization chooses inline execution without reconfirmation.

Ruling: use8/32 matrices with exactly representable1/16 coefficients: sparse
symmetric2x2 blocks versus dense identity+rank-one. These bounded fixtures avoid
uncontrolled rational coefficient growth while exposing distinct sparse/dense
inputs. They do not model arbitrary fill/growth or match prior Float64 recipes.
Measure Float16,Float32,BigFloat at its existing256-bit default,Rational{BigInt}
and Rational{Int64}; native and Markowitz. Native non-Float64 HH may use dense LU
regardless of sparse input; report actual factor type, never call it UMFPACK.

Three rotating rounds, four calls/sample per region:40cases,360samples. Warmups
and construction are outside timing; first inactive-slot allocation is included
in each fresh-owner batch. No baseline/candidate speedup claim. GC is part of
elapsed; do not add independently sampled component medians or overlapping graphs.
Object graph excludes native memory/hidden backing capacity and is not peak RSS.

## Review focus

- Scalar-safe exact snapshots/hashes; no reinterpretation of BigFloat/BigInt refs.
- Rational residuals must be exact; floating residuals use16eps(T)*max(1,norm(rhs)).
- Saved base remains exact after successful and failed refactorization.
- Sparse/dense labels describe input, not actual backend storage or fill.
- Changed pattern/dimension and empty/failure paths retain valid live/saved factors.

## Task 1: diagnostic driver and guarded evidence

Create diagnostics/simplex-core-architecture/reproduce/hh_scalar_components.jl.
Use datatype-specialized functions consuming SparseMatrixCSC{T,Int} and Val backend.
Return samples with case/type/backend/actual factor type/dimension/matrix hash,
round,region,seconds,compile_seconds,gc_seconds,bytes,allocations. Include per-case
fresh/cycled retained graphs and per-type/backend lifecycle records. Assertions
are the diagnostic's acceptance oracle; no production behavior needs a RED test.

- [x] Build driver with40cases/360samples and exact ownership/residual assertions.
- [x] Independently confirm old runner/child/driver absent; launch one guarded run.
- [x] Audit normal exit, all pins/source hashes, exact case/group keys, compilation
  zero, finite metrics, lifecycle/failure coverage and resource guard records.
  If failed, preserve raw partial report; fix only demonstrated harness defects,
  and continue missing cases without repeating already completed accepted cases.

## Task 2: review and continuation

Create S4-SCALARS.md and compact results/S4-D evidence. Report medians/ranges,
bytes/events/GC, native versus Markowitz mechanisms and retained-graph limits.

- [x] Fresh independent final numerical/work/memory review; resolve blockers.
- [x] Update STATUS/parent and this plan; commit/push diagnostics only. No new
  production merge required. Broader S4 manager/history/medium and S6 remain open.
- [x] Select the next concrete S5 handoff boundary contract using the existing
  ownership inventory and completed old-origin entry attribution; do not repeat it.

Task1 complete:360compile0samples/40cases/10lifecycles,exit0,pins verified. Initial
BigFloat Serialization hash gate rejected; separate8case canonical/mutation probe
confirms value equality without changing original cost records or repeating costs.
Final audit22checks pass with explicit hash limitation in S4-SCALARS.md. Preserve
initial audit and probe. No production changes. Fresh final review pending.

Task2 complete: fresh independent final review accepted with no blockers. One P3
preservation-hardening minor is deferred (initial audit write_text on accidental
rerun); accepted evidence is committed and auditor must not be rerun on that case.
S5-A boundary selected and concrete cleanup-entry-contract subplan saved. Source
remains master3220118; no production merge or new timing claim. Diagnostic push
is the final publication step. Full S4/S5/S6 are not complete.
