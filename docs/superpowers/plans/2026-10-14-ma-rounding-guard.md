# MA BigFloat rounding guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans task-by-task, with fresh independent reviews at the stated boundaries. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove additional scoped-rounding guard allocations without changing eligibility, arithmetic, ownership or fallback behavior.

**Architecture:** A local Bool helper exposes the existing persistent dictionary lookup to call-site inlining; only the final eligibility expression changes. Independent offline review precedes separately admitted short validation.

**Tech Stack:** Pinned Julia1.13.0 Base scoped values/MPFR, existing MA-R diagnostic module and MA-S-2 corrected outer invokelatest loading boundary, Python guards.

**Spec:** `docs/superpowers/specs/2026-10-14-ma-rounding-guard-design.md`.

## Global constraints

- MA-T is plan-only. Do not implement a candidate, driver or run Julia in this step.
- Read MA-S-FALLBACK report/review and preserved source; no old script rerun or raw mutation. MA-S-2 remains rejected48/52 and its allowance consumed.
- Same exact type/storage/shape/n16 eligibility and scoped/global equality; no threshold tuning, narrower equal-mode eligibility, cache, Base method overwrite, tolerance or precision change.
- No production/src/test/env/CI/master change; no integration until a separate complete admission addresses every remaining control, including Rational. This plan does not renew the old52case schedule.
- Standing human short-run permission remains. It does not replace accepted immutable admission. Future sequence ceiling: two serial processes, each90seconds inclusive,180seconds total, one attempt; stop on unexpected failure. No hours or automatic retry.
- Julia/BLAS1, heap2GiB, VM8GiB, availableRAM>=6GiB, swap<=1GiB, compiled-modules=existing. Fresh host refs/boot/start_ticks/command/full166groups ANDsessions plus new groups before launch or pinned continuation edits. Preserve beforecopies and exact mapping.
- Use already installed diagnostic dependencies only. No Pkg update, environment mutation, global mode races or restoration bypass. User Manifest/LocalPreferences remain untouched.

## Review focus

1. Equal scoped/global mode remains eligible; all five supported public modes covered by Task2 mode matrix.
2. Unrelated precision scopes and missing keys do not cause false rejection; Task2 missing-key/context cases.
3. Nested/inherited task contexts, yield and throw restoration use fresh task state; Task2 transition tests without concurrent global writes.
4. Fallback exceptions, aliases, old scalar leaves and partial destination writes stay unchanged; Task2 reference comparisons.
5. Private API/compiler drift and hidden allocation/code growth: Task1 inverse/source gates and Task2 independent guard/whole-call cost gates; unsupported runtime refused before prototype load.

### Task1 — MA-U: separate offline guard candidate and tests

**Files:** create `diagnostics/simplex-core-architecture/results/MA-U/{candidate.jl,guard-tests.jl,source-map.json,work-ledger.md,review.md}`. Copy immutable MA-R reference/tests/fixtures by explicit source bindings as needed; never overwrite them.

**Interfaces:** keep MADenseProbe candidate_forward!/candidate_transpose! and
`_dense_ma_eligible(dest,backend,rhs)::Bool`; add
`_dense_ma_rounding_matches()::Bool`. No exported or production method.

- [ ] Verify fresh relevant source hashes against MA-T/source.json and the preserved MA-R candidate; refuse drift. Preserve all earlier continuation maps.
- [ ] Prepare a source-exact inverse: stripping the one helper and replacing its single call with the original rounding_raw equality must reproduce MA-R/candidate.jl byte-for-byte. All12MA product sites and every other helper remain untouched.
- [ ] Add the helper with this precise algorithm: read `Core.current_scope()::Union{Base.ScopedValues.Scope,Nothing}`; return true if nothing. Bind the installed CURRENT_ROUNDING_MODE key. Evaluate `v = Base.@inline Base.KeyValue.get(scope.values, key)`. Return true if v===nothing; otherwise return `(only(v)::Base.MPFR.MPFRRoundingMode) == Base.MPFR.ROUNDING_MODE[]`. No custom tree traversal, @assume_effects, global caching or broad inline annotation.
- [ ] Write unexecuted tests for Task2 using original equality as oracle. Keep original reference solve, arithmetic tests and input tokens. Instrument only a separate copy for route/scratch counters; cost uses uninstrumented source. Count all calls in the forthcoming driver, including wrappers, setup, exceptional calls and tasks.
- [ ] Independently review numerical/exception equivalence, source inverse, private API constraints and work/memory. Source constructor counts are not runtime allocation proof. Stop on failure; no switch to a different strategy under this plan.

### Task2 — MA-V: separate bounded correctness/allocation admission

**Files:** after Task1 acceptance, create `results/MA-V/{driver.jl,launcher.py,audit.py,admission.md,pins.json}` with new exclusive output paths/reservation. Never execute MA-S-2's frozen launcher or tests as a script. Source-bound reuse in a new driver is explicit new work.

**Interfaces:** original equality, new helper, original reference F/B, new uninstrumented candidate F/B, and the frozen old MA-R candidate F/B in a separate diagnostic module for RED only; fixed raw records for predicate results, route/scratch counts, numeric tokens, input/owner preservation, exceptions, compile, GC, bytes/events and times.

- [ ] Freeze exact commands, source/runtime/environment/driver hashes, raw schema, full case and call counts before independent admission. Use corrected outer Base.invokelatest dispatch only where MA-S-LOAD established it; never inside measured windows. No numerical start until this concrete admission is independently accepted. A fresh full-runtime inventory is specific to that launch, not retroactive MA-T pins.
- [ ] Predicate oracle: global modes Nearest/Down/Up/ToZero/FromZero crossed with six scope states absent or each of those five modes, at ambient128/256/512. Compare each result to original equality and the explicit expected Bool (absent or same mode). Repeat with unrelated scoped storage sizes0/8/64, constructed outside measurement. An active precision scope is not an absent task scope. Include a dedicated no-scope task case if attainable without private state mutation; otherwise record unavailable and restrict that runtime coverage, keeping its source proof explicit.
- [ ] Transition oracle: same task absent -> outerUp -> innerDown -> restoredUp -> absent, original globalNearest; throw inside inner scope and check restoration. Two child tasks created under Up and Down respectively, each yield then resume; compare against original equality before/after yield with fixed globalNearest. Keep tasks serial/cooperative, join them, hold no task/scope cache, and check no leaked global/precision changes. Test consecutive calls after serialized global mode changes.
- [ ] Whole-call correctness: original reference vs new candidate, F/B at n16/32, dense/zero-heavy fixed MA-R matrices, ambient128/256/512 and the same five-global by six-scope matrix. Add n0/1/2/8/15, Float64/Rational, RHS view, dest===rhs, shared scalar leaves, retained outputs, singular pivot, invalid pivot and wrong lengths using unchanged MA-R definitions. Do not refactor or invent numerical fixtures to make the guard pass. Compare exact finite tokens/precision/sign, NaN/Inf classes, factor/RHS/retained leaf values/identities, exception type/message and post-unwind destination prefix. Routing equals old predicate; mismatches have zero scratch and exactly one original whole-call delegation before mutation. Equal modes must not silently fall back.
- [ ] Freeze a genuine prospective RED oracle for the **old guard's performance**, not numerical correctness. First process ONLY: two dense n32 F/B cases, ambient256/globalNearest/scopedUp; direct original reference vs frozen old MA-R candidate,3warm+7measured alternating pairs,4calls/window. Exactly160additional old-arm backend calls, with the same reset/scope/timer discipline as the new whole-call cases. Both old and new modules load before measurement; bind their exact reference/candidate files and outer loading boundaries. Numerical preservation and measured compile/recompile0 must pass. RED is expected only when, in EACH direction, old-candidate side-median bytes OR events exceed the direct-reference side median across the seven measured windows. Save exact deltas, retain all GC/outliers, and never treat load/import errors as RED. This predicts an optimization-coverage failure, not an original numerical defect. If either direction unexpectedly lacks an allocation regression, stop this qualification sequence and preserve that result; no new-candidate success or causal claim, threshold change or extra repetition. Original recorded MA-S-FALLBACK results remain untouched.
- [ ] Micro-cost: old equality vs new helper for six contexts (no rounding key; unrelated8keys/no rounding key; explicitNearest; explicitUp; nestedUp/Down; explicitUp+64unrelatedkeys), globalNearest/ambient256. Two processes; each3warm+7measured alternating pairs,256predicate calls/window, Bool checksum observed outside timer to prevent dead-code removal. Freeze exact non-hoistable runtime input/call boundary and inspect generated code OUTSIDE cost windows in the admission: repeated checks must really execute; no precomputed Bool, invariant loop collapse, arbitrary invokelatest or dispatch overhead masking. Same boundary and accumulation on both sides. This is a necessary gate in driver review, not permission for an unbounded compiler investigation.
- [ ] Whole-call cost: original reference vs new candidate, ambient256, dense n32 F/B under absent/explicitNearest/explicitUp/nestedUp-Down (8cases), plus zero-heavy n32 F/B explicitUp (2cases), plus dense n15 F/B explicitUp (2cases). Total12cases, each process3warm+7measured alternating pairs,4backend calls/window. Exactly1920reference/new cost backend calls PLUS160reference/old RED calls =2080cost backend calls, and61440micro predicate calls over two processes; correctness/setup calls separately enumerated in admission. Scope/context/factor/reset setup outside windows identically; guard and all product scratch inside whole calls. No profiler in timed windows. Keep every GC/outlier; measured compile/recompile must be zero. Report cold import/setup/compile separately, including inline code growth confined to predicate.
- [ ] Freeze reducers before launch, separately for EACH whole-call case (never pool directions, sizes, layouts or rounding contexts). Divide each window time by4 to obtain per-call seconds. R_pc and C_pc are side medians of the seven measured reference and candidate per-call times for case c/process p; R_c and C_c are side medians of all14 per-call samples of that side across both processes. Define per-process ratio C_pc/R_pc and pooled ratio C_c/R_c (positive reference times required). Bytes/events are side medians of the seven raw window totals in EACH case/process; never substitute median paired differences. Raw paired deltas/ratios remain reported separately. These new reducers do not rewrite MA-S-2's frozen reducers or gates.
- [ ] Acceptance: all semantics/owner/exception/route checks and the expected old-arm RED pass. Every micro context/process new-helper measured window has zero allocation bytes/events (timer scaffolding independently characterized; never subtract an unexplained baseline). For EVERY mismatch or n15 whole-call case, candidate-minus-reference side-median bytes/events must each be<=0 in EACH process, C_c-R_c<=max(0.05*R_c,0.2e-6seconds), and C_pc-R_pc<=max(0.10*R_pc,0.4e-6seconds) in EACH process. For EVERY absent/equal-mode n32 case, candidate side-median bytes AND events must each be strictly lower in EACH process, C_c/R_c<1, and C_pc/R_pc<1 in EACH process. Retain every sample, including GC/outliers; no numerical gate may be traded for cost. These are prospective engineering budgets, not statistical significance claims. New absolute times are not compared with old process times as a speedup proof.
- [ ] Independent result review states attribution limits: even a successful change does not identify the two old heap objects. Success establishes this guard strategy locally; failure preserves raw and stops without rerun/tuning. No automatic complete DenseLU qualification or production promotion. Rational no-increase rejection and other original52case obligations remain open.

### Task3 — decision and handoff, not integration

**Files:** new MA-V result report/review and continuation records only.

- [ ] Record whether the new guard meets all prospective gates, and distinguish local guard savings from full solver performance. If accepted, a separately reviewed future complete-candidate admission is needed; it must explicitly resolve remaining Rational control evidence without rewriting MA-S-2's false gates or deleting cases.
- [ ] Preserve exact previous STATUS/roadmap bytes before updates, map only matching bindings, independently review, run separate PASS closure, stage exact names/blobs, failfast commit/push/remote verification. No automatic production edit or master merge.

## Completion of this plan request

MA-T ends with design/plan/source bindings and independent review accepted and
published. Next actionable step is MA-U offline preparation, not MA-V launch.
No runtime zero-allocation or speedup claim is made at MA-T completion.

## Independent review amendment

Initial review found two Important specification gaps: the omitted old-candidate
RED arm and ambiguous time reducers. Its report/JSON and before-review plan are
preserved in MA-T. The corrected plan adds160explicit RED backend calls (2080total
cost calls) and pins per-case/per-process side-median formulas. No numerical result,
old gate, original candidate or source was changed. source.json's original plan
hash maps only to plan.before-review; review-fix.json records exact mappings.
