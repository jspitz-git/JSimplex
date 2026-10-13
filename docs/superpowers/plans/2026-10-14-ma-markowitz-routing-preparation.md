# MA-H: prepare one routing-only Markowitz MA variant

> Use superpowers:executing-plans; execute sequentially. This plan authorizes
> OFFLINE preparation and independent review only, not Julia or integration.

**Goal:** Prepare one separate candidate that confines the MA upper helper to
exact target scalar types with positive sparse pivot count.
**Architecture:** one forward call-site condition, original inline fallback,
byte-identical previously qualified MA helpers, no persistent scratch.
**Tech Stack:** Julia source text; Python byte comparison and structural checks.
**Spec:** [MA-G decision](../../../diagnostics/simplex-core-architecture/MA-MARKOWITZ-CONTROL-REGRESSIONS.md),
[MA-D ownership contract](2026-10-13-ma-markowitz-upper-preparation.md).

## Constraints and review focus

MA-F remains NOT ACCEPTED for production benefit. All MA-E/F and older scripts,
raw data, candidates and failures are frozen. No rerun or retuning of those files.
Do not change actual src/test/Project/env/CI/master. No Julia query, parser, import,
compile or numerical run. Standing short-run permission exists, but a later new
numerical attempt still needs its own exact immutable independent admission.
Do not alter tolerances, precision, ordered arithmetic, safeguards, fixtures,
thresholds or choose a subset based on the failed controls. No HH/DSE/controller/
import/isolation/cleanup/support-only route reopening. Automation stays paused.

Review exact scalar dispatch, empty-range semantics, source ownership, exception
order and new work per full solve. A type condition may compile away; never claim
that as verified without evidence. No extra O(n) eligibility scan or metadata
cache is allowed. All original helper qualification obligations remain applicable.

## Task 1: preserve and bind inputs

- [ ] Fresh host refs/boot/start_ticks/command and all90 PGIDs AND sessions/noJulia;
      preserve MA-G-bound current STATUS and roadmap bytes before changing them.
- [ ] Create results/MA-H only. Bind the MA-E reference/candidate factor source,
      candidate tests, MA-F-repair driver/kernels and MA-G decision/review.
      Do not import/run old Python audit modules. Copy exact needed source text.
- [ ] Record a complete explicit intended-file list and byte hashes.

## Task 2: one isolated candidate, no execution

- [ ] Create results/MA-H/candidate-markowitz.jl from the frozen MA-E candidate.
      Replace ONLY the single full-forward `_markowitz_upper_solve!` call with:
      a condition `(T === BigFloat || T === Rational{BigInt}) && sparse_pivots > 0`,
      the existing call on true, and the original reference inline upper loop
      on false. Keep exact descending order and independently owned scalar
      publication. Do not edit any helper, constructor, lower solve, dense solve,
      transpose solve, copy/refactor method, import or dependency.
- [ ] Prove an exact inverse back to MA-E candidate, and a second exact inverse
      back to reference after removing the existing helper block. Preserve the
      original loop byte-for-byte modulo explicitly reversible indentation.
- [ ] Structural RED on MA-E: the restricted full-forward route is absent;
      structural GREEN on MA-H: exactly one route and exact inline fallback.
      Label these Python/source checks, not executed Julia regression tests.
- [ ] Work ledger: at most two exact-type identity tests and one integer comparison
      per full solve; short circuit count test for non-targets; no new scans,
      solves/copies/conversions/caches. Existing helper eligibility/scratch work
      unchanged for nonempty targets. No compiled-code elimination claim.

## Task 3: prepare prospective tests and numerical admission specification

- [ ] Copy unchanged MA-E semantic tests as UNEXECUTED new text, then prepare
      separate route regressions without global method overwrite or hot-path
      instrumentation. Source-exact inverse assertions must prove fallback loop
      placement; runtime value/alias checks alone cannot prove the call was absent.
      Cover Float32/64, generic fallback, both target types with zero and positive
      sparse pivots, scoped rounding mismatch, signed zero/nonfinite and exceptions.
      Preserve all original 381 runtime assertions; list any extra assertions and
      counts before admission. No weakening or substitution of existing assertions.
- [ ] Prepare a concrete subsequent SHORT qualification/cost plan with immutable
      manifests, fail-closed audit, serial guarded processes, explicit resource and
      whole-attempt limits. Keep the existing eight fixtures/six scalar settings,
      all48 cases, three warm/seven measured pairs, four repetitions/window and
      target median<=0.95 with>=6/7 faster; every control median<=1.05. Original
      MA-F results remain a separate rejected-performance record.
- [ ] Declare baseline and measurement roles before launch: original reference
      versus new routing candidate for production acceptance. Full-forward is the
      gate; the old direct upper/reset helper measurement does NOT exercise the
      new call-site condition and must be labelled unchanged-helper diagnostic.
      No claim that a direct-helper result proves bypass success. A three-way causal
      MA-E rerun is NOT part of this plan. No adaptive retries/window extensions.
- [ ] Bind repaired scoped-Test context to the installed Test source before any
      future RED. Freeze expected failures, extra test counts and all call budgets
      in the later admission; no launch is permitted from this preparation plan.
      Report all times/bytes/events/compile/GC and retain outliers and failures.
      If control gates fail again, stop without promotion or automatic tuning.

## Task 4: independent review and publication

- [ ] Fresh independent gpt-6-astra review of exact candidate inverse, prospective
      tests/admission, numerical ownership and unnecessary computational/memory
      cost. Resolve findings preserving original rejected artifacts.
- [ ] Separate PASS closure and exact complete staged names/blobs before failfast
      diagnostic commit/push; verify committed blobs and both remote refs.
      Update STATUS/roadmap with explicit old-binding mappings. No master change.
