# Markowitz Row-Count Fusion Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Ship the exactly qualified row-count fusion with a permanent work regression.

**Architecture:** Replace the redundant `sum(length,rows)` by integer accumulation
in the existing singleton loop. Append one isolated test module to the existing
workspace-reuse test file; leave its complete current prefix intact. Existing
reset, capacity reuse, scalar arithmetic, pivot order and failure handling remain.

**Tech Stack:** Julia, Test, existing Markowitz backend and dictionary interface;
Python only for immutable admission, process guards and evidence validation.

**Spec:** ../specs/2026-10-11-simplex-core-architecture-design.md, original S4 scope.

## Global constraints

- Native problem precision is the normal computation mode; wider precision is
  an exceptional recovery/reference path, not a performance shortcut.
- Do not weaken tolerances, residual checks or certificate acceptance.
- Keep simplex candidate selection unchanged in arithmetic-preserving changes.
- One numerical Julia process, one Julia thread and one BLAS thread; heap2GiB,
  VM8GiB, availableRAM6GiB, swap1GiB, hard120seconds per admitted process.
- No big/largo/AnyMOD or aliases, new LP, HH/controller/isolation work or old rerun.
- Preserve environments, failed evidence, all frozen S4-AB artifacts and older maps.
- Automation stays paused, CI disabled and HH reuse disabled.
- Standing human short-attempt permission applies; do not request it again.

S4-AC is OFFLINE preparation: candidate test/source and this concrete plan only.
Nothing here is a Julia syntax/runtime pass or numerical launch admission. Before
Task1 execution, prepare and independently admit exact stage drivers, commands,
source/test/runtime/environment pins, output reservations and fail-closed auditors
in S4-AD. Do not silently run a plain unguarded test command. No production edits
before the actual permanent regression is observed failing for the expected reason.

## Files and interfaces

- Modify only `src/markowitz_factorization.jl`: exactly S4-AB's candidate-source.jl.
- Append only `test/markowitz_workspace_reuse_allocation_tests.jl`: exactly the
  S4-AC test-append.jl module, with the original whole-file prefix unchanged.
- No Project/Manifest/LocalPreferences/runtests/CI/dependency edits.
- New test-only `MarkowitzInitialRowCountTests.RowLengthDictionary{T}` wraps real
  Dict storage, counts length calls, and resets its count on empty!. Existing
  `_construct_markowitz` and `_reset_markowitz_workspace!` are called directly.
- Integration consumes S4-AB accepted source/cost evidence and S4-AC source/test
  candidates; produces one minimal production/test commit and verified master.

## Review focus

1. Shrunk workspaces must still clear all retained tail dictionaries and preserve
   row/column owners: new six-predicate cases plus unchanged reset-history tests.
2. Singular construction must remain a failure with the correct pivot index:
   new zero-matrix cases and existing post-failure live/saved factor solves.
3. Empty and dense bypasses, exact arithmetic and stored precision must remain
   unchanged: existing markowitz_tests and runtime_markowitz_cache_tests.
4. Pivot ties, manager reuse and allocation-free regrowth must remain unchanged:
   the entire existing workspace-reuse test prefix, not only the new suffix.
5. The count wrapper must not change production dictionary dispatch or become
   production instrumentation: only its own methods inside the new test module;
   generic side-effectful/throwing length ordering remains outside the qualified
   Dict/OrderedDict contract. Inspect the exact source inverse and test isolation.

## Task 1: Observe the permanent work regression fail

**Files:** S4-AC/test-append.jl; future S4-AD exact suffix extraction driver.
**Consumes:** unchanged actual constructor and four n/capacity fixtures.
**Produces:** preserved expected RED evidence for the actual proposed test.

- [ ] Bind the existing branch/master refs and a fresh full34groups ANDsessions
  preflight, updating that set after each admitted process. Preserve current
  continuation bytes before editing them. Reconcile AB closure/publication through
  AC's before copies, without executing old scripts.
- [ ] Prepare one exact suffix-only RED driver using ordinary checkout loading,
  no method replacement/module clone, source-bound Test results and raw-before-
  aggregate-failure evidence. The suffix is UNEXECUTED until admission succeeds.
- [ ] Run RED once through its independently admitted 120s guard and reservation.
  Expected: 20 passes, four row-read failures, zero unexpected errors, 24 tests;
  reference row reads [2]*n+[1]*(capacity-n), no solve or completed factorization.
  Preserve nonzero exit/raw and stop on any different outcome. No automatic retry.

## Task 2: Install the exact change and run focused GREEN

**Files:** the two actual files above, plus separately bound S4-AD GREEN driver.
**Consumes:** accepted RED result; exact source and whole-test candidates.
**Produces:** actual production/test verification and independent review.

- [ ] After RED closure proves no live process, apply the exact source candidate
  and full test candidate. Verify the two-file diff and unchanged original prefix.
- [ ] Seal a separate GREEN manifest binding actual changed src/test and the RED
  evidence, then obtain independent numerical admission before its one run.
- [ ] The GREEN driver runs the complete three files, once each:
  `markowitz_workspace_reuse_allocation_tests.jl`, `markowitz_tests.jl`,
  `runtime_markowitz_cache_tests.jl`, with ordinary JSimplex/Test context. Freeze
  exact include context and per-file case/call/assertion expectations in admission;
  files containing public solves must have their explicit call schedule inventoried.
  Expected: zero failed/broken/error assertions and every original test retained;
  the workspace file has 300 original +24 new tests =324 prospective assertions.
- [ ] Compare actual production source with the AB candidate and test prefix with
  AC's original. Reuse the frozen AB 12-case/240-window performance evidence;
  do not repeat/tune it. This integer-count change introduces no new production
  buffer, solve, scan or conversion. The two full dictionary resets remain.
- [ ] Obtain fresh independent numerical/work/memory review of the actual edits
  and GREEN result. Preserve any failure and diagnose under a separate admission;
  this plan supplies no retry allowance for a consumed stage.

## Task 3: Integrate and verify actual master

**Files:** only the same production/test files in the integration commit.
**Consumes:** accepted actual GREEN source/test and review; standing merge permission.
**Produces:** pushed minimal commit, separately verified master and diagnostic record.

- [ ] Commit only the exact two-file change. Integrate that commit into master
  without unrelated diagnostics or user files; preserve primary user changes.
- [ ] Bind the actual master source/test to GREEN bytes and a new master driver,
  manifest, admission and one120s reservation. Run the complete workspace test
  file once (324 prospective assertions). No old frozen driver is reused.
- [ ] Review the result, verify no live groups/sessions/Julia, then publish using
  a separate PASS closure, exact staged/committed names/blobs and fail-fast push
  with remote verification. Preserve current continuation before updating it.
- [ ] Record the production commit and actual-master evidence in STATUS/roadmap.
  Broader S4/S6 remain open; no universal/end-to-end speedup or memory-saving claim.

At most three NEW guarded processes, each120s: one expected RED, one GREEN and
one actual-master validation, sequentially and only after their own admission.
This is a prospective integration schedule, not an executed/numerically admitted
budget. RED has four tiny singular constructor attempts; GREEN/master have four
new attempts per full workspace-file execution plus the unchanged existing tests.
No additional cost benchmark or long run is required for the unchanged candidate.
