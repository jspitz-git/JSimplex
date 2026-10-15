# Native Float64 accuracy policy comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine whether stronger pivot acceptance or bounded native refinement addresses the saved DSE accuracy failure, and quantify each mechanism's construction, solve, allocation and memory cost before considering integration.

**Architecture:** A separate diagnostic driver calls the installed Float64/Int64 UMFPACK interface with private constructor controls. Three fixed arms share identical frozen matrices and RHSs. Production defaults, solver dispatch, all three direct-LU prototypes and historical evidence remain unchanged; component success cannot qualify a manager lifecycle or resume the failed benchmark.

**Tech Stack:** Julia's installed SparseArrays/UMFPACK; Python exact rational offline oracle; existing guarded ordinary loader with `--compiled-modules=existing`.

**Spec:** `diagnostics/simplex-core-architecture/DIRECT-LU-PIVOT-GROWTH-DIAGNOSIS.md`, independently accepted at `c1901995ac6e7eee26a7c4b9cc6897c3e6b43a12`; original direct-LU comparison in `docs/superpowers/plans/2026-10-14-direct-lu-markowitz.md` remains incomplete.

## Global constraints

- This document is SOURCE/DESIGN preparation, not exact-stage numerical admission. No Julia, candidate or launcher execution while writing/reviewing it.
- No actual src/test/env/CI/master changes; master is `6f68e24e8ddac42b948da8fcc2d636c010751194`. Automation stays paused; HH reuse disabled.
- Original cost1 FAILED/CONSUMED, cost2 BLOCKED; diagnostic probe consumed. Never rerun or rewrite old drivers, auditors, raw data, false gates or frozen plans.
- This is a new explicitly labelled accuracy-policy experiment, not tuning or requalification of the old direct-LU benchmark. No new LP, large model, full solver, precision increase, tolerance relaxation or small-coefficient dropping.
- Future run: ONE attempt, <=45 seconds inclusive of import/compilation/output, Julia/BLAS1, heap2GiB, VM8GiB, availableRAM>=6GiB, swap<=1GiB. Timeout/failure preserves evidence and stops; no automatic retry or budget extension.
- Standing human permission for short numerical attempts applies only after concrete preparation and independent exact-stage admission. Do not ask again merely for the same short-run permission.

## Review focus

1. Controls shared with a caller or another arm: own constructor vector, do not mutate live factor controls; verify all 20 fields and caller-input immutability (Task1 ownership tests).
2. Fresh construction after a copied/shared backend silently resets policy: explicitly test fresh policy construction and document the currently unsupported production propagation seam (Task1 lifecycle tests).
3. Reusing shallow `copy(F)` as a refactor candidate corrupts shared CSC owners: forbid it; test a separately constructed private candidate and preservation after singular failure (Task1 lifecycle tests).
4. Refinement moves costs into workspace growth or hidden correction solves: initialize with the requested policy, capture workspace sizes and per-call attempted/taken refinement metadata, include constructor controls/scratch in costs (Task1 cost schema).
5. Residual failure, different solution bits, singularity or compile contamination: preserve raw results, never select tolerances/parameters after outputs; separate faithful diagnostic completion from accuracy and cost acceptance (Tasks1–2).

## Fixed arms and interpretation

| Arm | Constructor pivot tolerance | Constructor IRSTEP | Purpose |
| --- | ---: | ---: | --- |
| C | 0.1 | 0 | Current native reference |
| P | 1.0 | 0 | Pivot threshold 1.0 (strategy-dependent) |
| R | 0.1 | 2 | At most two native refinement attempts |

Obtain a fresh `SparseArrays.UMFPACK.get_umfpack_control(Float64,Int)` vector for every fresh construction, set ONLY the two named slots, and pass it to `lu(B; control=ctrl, check=true)`. Use installed constants plus one for Julia indexing, not unexplained numeric slots. `q=nothing`, strategy, scaling and DROPTOL remain the installed defaults; record all control bits and verify their equality across arms except the named slots. C must equal the installed default control vector, including IRSTEP0.

These are three predeclared alternatives, not a parameter sweep. P tests the direct growth mechanism, with possible fill/factorization penalties.
Call it full partial-pivot acceptance ONLY for a captured UNSYMMETRIC strategy.
AUTO may select SYMMETRIC, where unchanged SYM_PIVOT_TOLERANCE=0.001 permits
weaker diagonal pivots. Do not force the strategy or change that third control;
record STRATEGY_USED and SYM_PIVOT_TOLERANCE for every fixture/arm/window after
construction, outside timing, and in final snapshots. Report results by actual
strategy; the prior sparse96 strategy does not establish other cases. R keeps pivoting fixed but can pay on every solve and retains additional scratch. No combined P+R arm, intermediate threshold, adaptive switching or fallback retry in this experiment. None is presumed successful or fast.

The installed wrapper allocates real W length n without refinement, 5n with it, plus Wi length n in both cases. R therefore has an expected additional 4n Float64 elements (32n bytes of element payload per workspace, excluding headers), not zero retained-memory cost. `copy(F)` duplicates workspace/control/Info/lock but shares numeric, symbolic and CSC arrays. Production `_copy_backend` shares the entire active F instead; production fresh `_refactorize_backend` calls plain `lu` and would lose a nondefault policy. This plan does not claim to solve that integration problem.

## Task 1: Prepare one isolated component driver and exact admission

**Files (new only):** `diagnostics/simplex-core-architecture/results/NATIVE-ACCURACY-PREPARATION/{driver.jl,inputs.json,inputs.toml,analysis.py,config.json,control.py,guard.py,supervisor.py,launch.py,audit.py,required-paths.json,preparation-pins.json,review.md,review.json}`. Add separately named preparation checks, failure fixtures and manifests where needed; enumerate every created file before review. No writes to frozen previous directories.

**Interfaces:**
- Driver-local `policy_controls(arm::Symbol)::Vector{Float64}` accepts only `:C`, `:P`, `:R`; invalid symbols throw before any native call.
- `fresh_factor(B::SparseMatrixCSC{Float64,Int}, arm::Symbol)` returns `(factor, supplied_controls)` using the constructor rule above. It never modifies JSimplex methods or global controls.
- `run_accuracy_probe(output::String, inputs::String)` writes fixed raw schema before aggregate assertion. The auditor consumes saved bits, counts, invocation and sealed pins; it never loads Julia or replays a solver.

- [ ] Freeze exact existing `sparse32`, `dense32`, `sparse96`, `dense96` B4 and step5 entering/DSE/unit RHS tokens from `DIRECT-LU-COST-PREPARATION/inputs.json`. Include sparse32 B0 and step1 RHSs for lifecycle checks. Derive a singular matrix by retaining sparse32 B4's CSC indices and replacing every nzval with +0.0; retain original B4 separately. No random input or new LP. Independently check the subset inverse/token hashes offline.
- [ ] Implement the three controls and explicit `lu`/`ldiv!`/`lu!` component calls without including old executable scripts. Import ONLY `SparseArrays`, `LinearAlgebra` and `TOML` in the standalone driver, with ordinary `--project=/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl`. Do not import JSimplex, create an overlay, overwrite methods, clone an isolated solver module, call an HH helper or use a factor-export adapter. Native FTRAN uses `ldiv!(x,F,b)`, BTRAN `ldiv!(x,transpose(F),b)`, each with disjoint owned destination/RHS. Do not call a helper that silently adds orientation solves.
- [ ] Add exact ownership predicates: supplied controls and factor.control have different owners but equal values immediately after construction; after poisoning only the supplied vector, factor controls remain unchanged; arm factors/CSC/workspaces are independent. Freeze all owned-input snapshots and assert values/owners unchanged at teardown. Do not poison timed controls or shared factor fields.
- [ ] Prepare the fixed sparse32 lifecycle sequence separately from measurement, once per arm:
  1. Construct F from B0 with policy, create S=`copy(F)`. Check independent control/workspace/Info/lock and shared native/CSC roles. Solve entering FTRAN and unit BTRAN once on each of F and S (2F+2B).
  2. Construct private T independently from B0 with the same policy. Refactor T to B4 with `reuse_symbolic=false`; solve step5 DSE FTRAN and unit BTRAN (1F+1B). Repeat `lu!(T,B4;reuse_symbolic=true)` and those two solves (1F+1B). Check all controls and expected workspace lengths after each transition.
  3. Construct independent V freshly from B4 with policy and solve the same two RHSs (1F+1B). This pins fresh-constructor policy, not production manager propagation.
  4. Refactor ONLY private T to singular B4-zero with `reuse_symbolic=true,check=true`, expect `SingularException`; discard T after recording the exception/status. Do not solve T or substitute another attempt. Compare original F/S values and owners; solve entering FTRAN and unit BTRAN again on each (2F+2B).
  Thus per arm: 3 fresh LU, 3 lu! attempts (one expected failure), 1 shallow copy, 7F+7B. Across three arms: 9 fresh LU,9 lu!,3 copies,21F+21B. These are component entry counts, not all native internal operations.
- [ ] Reject nonsquare/mismatched dimensions or aliasing in driver preconditions before entering a scheduled call; verify those rejection predicates offline with synthetic auditor records. Empty, rectangular, other scalar and real-manager recovery behavior remain excluded and must not be claimed runtime-tested. Production baseline hashes prove unchanged code, not new coverage.
- [ ] Prepare the fixed cost schedule below and raw schema, including correctness outcomes even when false. Preserve original exception/status/exit information. An unexpected lifecycle exception or source/control/ownership/count mismatch rejects execution integrity; a predeclared residual FALSE does not suppress later scheduled cells, but rejects that arm's accuracy.
- [ ] Prepare fail-closed launcher/auditor and offline rejection tests: missing/truncated raw, false inputs, altered controls, wrong stage/source/counts, aliased owners, invalid metadata bounds, terminal deadline violation, changed pins, reused reservation and absent process closure. Bind exact wrapper/runtime/stdlib and native-library source paths, ordinary Project/Manifest/LocalPreferences files, input/driver/auditor/command paths and relevant environment variables. The command uses the ordinary project above and ONLY the three stdlibs; no JSimplex import or overlay is permitted. Pin loading inputs without claiming an observed complete import-work or native-loader closure.
- [ ] Obtain fresh independent gpt-6-astra review of numerical semantics, exact call and storage ledger, control/copy semantics, guards and raw-before-assert handling. Do not launch during preparation. Publish preparation only after separate PASS closure and exact staged names/blobs.

### Fixed cost schedule and work/memory ledger

Four fixtures × three arms × (3 warm + 8 measured rounds) = 132 cells/windows.
Each window performs exactly one fresh construction, then 16 identical triplets
(entering FTRAN, DSE FTRAN, unit BTRAN): 48 solves =32F+16B.
Totals:132 fresh LU,4224F+2112B. Including lifecycle:141 fresh LU,9 lu! attempts,
3 shallow copies,4245F+2133B =6378 solve entries; no other factorization/solve.
Each arm contributes2126 solve entries; native refinement correction work is
additional inside these entries. No workspace, simplex pivot, certificate or
full solver execution. No unlisted warmup or calibration loop.

Round order rotates C/P/R, P/R/C, R/C/P, offset by fixture index. Store the exact
schedule before launch. Use one construction `@timed` region including default
control creation, two assignments, input conversion if any, and scratch setup.
The supplied B is already exact Float64/Int CSC, so no hidden conversion may be
assumed without checking the method. Use a separate solve `@timed` region for the
16 triplets. A window's factor survives from construction through solves only.
Do not subtract the regions into a claimed pure native kernel cost.

Preallocate all 48 destination vectors per window outside both timed regions,
write each solve directly to its own Vector, and retain every output for exact
offline validation (no output-copy loop inside solve timing). Across cost windows
this is6336 vectors/405504 Float64 entries/3244032 bytes of element payload,
plus headers and lifecycle outputs. This retained diagnostic memory is NOT
solver memory or a neutral cache/GC effect. Allocate fixed result storage before
windows; never grow arrays in timed loops. No per-solve matrix/factor snapshots.

After each native solve, copy four scalar Info fields into fixed preallocated
storage: STATUS, IR_TAKEN, IR_ATTEMPTED, SOLVE_FLOPS. This read/store overhead is
included equally in each solve region and must be disclosed. Freeze installed
indices during preparation. For successful R calls require integer
0<=taken<=attempted<=2; record backtracking and attempted work, not only retained
corrections. For C/P require zero attempts. The upstream documented relationship
is one initial system solve plus one per attempted refinement; metadata is not
an instrumented full native work trace. O(m+nnz) residual evaluation and possible
correction solves are legitimate extra R work, not free precision improvement.

Capture per-region time, GC time, allocation bytes/events, compile/recompile;
record all samples and any contamination. Require measured compile/recompile=0
for interpretable cost, but retain nonzero data and stop without extra warmup or
retry. Report GC separately; do not silently remove samples. No forced per-window
GC. Report process RSS/HWM/resource samples separately from reachable Julia graph
and native Info memory estimates; neither establishes native allocation/free
balance. Report the extra R scratch explicitly even if GC allocation counters
look similar. Constructor vectors and the factor-owned control copy both count.

After the last solve window of each fixture/arm, capture ONE factor snapshot
using the already understood direct UMFPACK get_numeric interface:12 snapshots.
Inventory L/U/p/q/Rs/control/Info and do_recip, no orientation solve, before driver
admission. Compute max|U|/max|scaled B| and exact factor identity offline. Capture
fill nnzL/nnzU, workspace lengths, selected native memory/operation Info fields
and graph size outside timing. Pin which Info fields survive solves. No retired
factor owners held just for identity checking in timed cells; lifecycle owners
remain scoped to their separate test and are released before cost windows.
Dropping roots is not proof that native storage has been freed.

## Task 2: Seal and execute the single bounded experiment

**Files:** new `results/NATIVE-ACCURACY-QUALIFICATION/` for exact-stage review,
reservation, invocation, original/portable raw, postchecks and result review.
Preparation must fix all paths before admission; no launch with placeholders.

- [ ] Fresh refs, boot/start_ticks/command, full206historical groups AND sessions plus any new groups, no Julia, and RAM/swap guards. Preserve current continuation bytes before modification. Seal actual runtime/project/source/input/driver/auditor/guard hashes and literal command. Independently accept that exact manifest; standing permission is not a substitute for admission.
- [ ] Run ONCE, <=45s inclusive, guarded single process. Save every scheduled output, count and false result. Stop on structural/exception/deadline failure; never tune inputs, tolerance, policy or loop counts after observing outcomes.
- [ ] Offline exact arithmetic for every saved solve: `||M*x-b||inf <= 128*n*2^-52*max(1,||M||inf*||x||inf,||b||inf)`, M=B for FTRAN and transpose(B) for BTRAN. This is the unchanged original bound. Compare independent arms by residual, not required cross-arm bit equality; within-arm repeated bit differences are recorded and investigated, not erased.
- [ ] Report C's fresh sparse96 B4 DSE match/nonmatch against the old saved failure. Nonreproduction is a diagnostic result, not an allowance to retry; no new residual oracle fitted to outcomes. All successful lifecycle outputs must satisfy the same bound, with their actual B/RHS pairing.
- [ ] Verify process closure, raw/source/pins, inputs and all explicit budgets; then fresh independent result review. Separate integrity, per-arm accuracy, interpretable cost and remedy acceptance. P or R must pass ALL scheduled accuracy/ownership/lifecycle gates before being considered a remedy. A failure anywhere rejects that arm; both can fail.
- [ ] Report paired construction and solve medians, ranges and MAD for8matched rounds/fixture, bytes/events and workspace/fill/memory differences. Small constructor windows may be too noisy; state that uncertainty without another run. Do not require both regions to improve: an accuracy remedy may cost more. No speedup claim, unchanged-allocation inference or universal recommendation from this component experiment.
- [ ] Preserve failures, publish exact evidence with separate PASS closure and reviewed continuation. No old benchmark rerun, automatic second attempt or production merge.

## Task 3: Decide whether any production policy deserves a separate design

- [ ] If neither P nor R qualifies, stop this mechanism comparison; do not add more thresholds/refinement limits automatically.
- [ ] If only one qualifies, present its measured construction/solve/fill/scratch tradeoff. If both qualify, report the break-even number of F/B triplets from paired construction and solve costs only where denominators are resolved by the observed spread; otherwise leave it indeterminate. Do not infer a real simplex workload mix.
- [ ] Any production proposal must explicitly store an immutable policy at backend construction and propagate it through fresh candidate, spare reuse, copy, empty transitions, failed refactor and recovery. Never mutate controls of a shared active factor. Specify source-level hot-path work and all supported precisions, then test manager integration separately. No concrete production type/option is introduced by this experiment.
- [ ] Only a later accepted integration design may determine how to resume a NEW version of the three-prototype/Markowitz comparison with honestly labelled reference policy. Old cost1 remains failed and unchanged; current component results cannot promote prototypes or satisfy the full solver/S6 gate.

## Preparation handoff

The next executable task after acceptance of this plan is Task1 OFFLINE driver,
auditor and launcher preparation with independent review. It creates no running
Julia process. Task2 requires its own fresh exact admission. This plan does not
implement a remedy, select a production default or reopen stopped HH/isolation
work. No extra confirmation of the standing short-run permission is needed.
