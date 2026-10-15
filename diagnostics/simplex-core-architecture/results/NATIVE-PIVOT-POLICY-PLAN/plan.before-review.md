# Optional native Float64 pivot policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Carry an opt-in threshold-one pivot policy safely through ordinary native backend lifecycles without changing defaults, safeguards or solve-loop work.

**Architecture:** SolverOptions stores immutable symbolic intent; native UMFPACKBackend stores a constant enum. Fresh construction applies private controls, while private spares and copies preserve the invariant. Precision transfers retain intent without changing non-Float64 arithmetic. Direct prototypes stay frozen until a later separately accepted adapter/comparison stage.

**Tech Stack:** Julia, installed SparseArrays/UMFPACK, isolated ordinary source overlay, Python saved-data checks, existing bounded process guards.

**Spec:** `docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md`.

## Global constraints

- This published step is SOURCE/DESIGN only. No Julia/query/parser/import/compile, candidate, driver or numerical execution while preparing/reviewing it.
- Master `6f68e24e8ddac42b948da8fcc2d636c010751194`, actual src/test/environment/CI, HH reuse disabled and paused automation stay unchanged. No old scripts/auditors/raw/pins/reviews/plans are rerun or rewritten.
- Default remains `:default`; new value is exactly `:threshold_one`. Only actual native Float64 uses pivot1/IRSTEP0. All other controls and all safeguards stay unchanged. No arbitrary thresholds, combined refinement, auto switching or fallback retry.
- Subsequent candidate work is OFFLINE first. Each numerical stage needs fresh boot/start_ticks/command/refs, all208groups ANDsessions plus newly created groups, no Julia, literal source/runtime/input/environment pins and fresh independent gpt-6-astra exact-stage admission. Standing human short-run permission applies; do not ask for it again.
- Numerical limits: one attempt per separately admitted stage, Julia/BLAS1, heap2GiB, VM8GiB, availableRAM>=6GiB, swap<=1GiB, <=30s RED, <=60s focused GREEN, <=45s component cost, <=60s public integration, inclusive of import/output/termination. Failure/timeout preserves evidence and stops; no automatic retry, extra warmup or longer limit.
- Original direct-LU cost1 FAILED/CONSUMED, cost2 BLOCKED. No production merge or direct-prototype promotion follows from this plan's acceptance. No large LP/full suite, new optimization target, precision increase or tolerance relaxation.

## Review focus

1. Fresh recovery, remaining-budget, phase or precision-copy path resets intent: Task1's option-copy tests and Task3's real recovery test must retain the symbol.
2. Copy shares active LU and somebody rewrites controls: Task1's control-owner and copy tests require no control mutation; Task2 verifies the backend enum is constant and spares are private.
3. Failed spare refactor corrupts the active factor or loses policy: Task1's failure cases exercise both no-spare fresh failure and populated-spare lu! failure, followed by preserved-factor solves.
4. Empty/resized transitions or returning from BigFloat silently select default: Task1's repeated-empty lifecycle and precision round-trip tests require the same selection, without native work in empty/non-Float64 cases.
5. Wrong backend, strategy claim or hidden hot-path allocation: Task1 rejects Markowitz/HH nondefault before native work; Task2 captures actual strategy, controls, fill, scratch and measured allocations, preserving symmetric-strategy and cost limitations.

## Task 1: Offline candidate and tests with independent review

**New preparation directory:** `diagnostics/simplex-core-architecture/results/NATIVE-PIVOT-PREPARATION/` containing candidate source copies, test text, an ordinary-overlay builder, exact inverse manifest, source/work ledger and independent review. No Julia execution in this task. Do not modify the frozen direct candidate.

**Candidate source map (actual originals unchanged):**
- `src/options.jl`: final Symbol field/keyword, validation and compatibility construction.
- `src/factorization.jl`: enum, constant backend field, fresh-LU helper, native/Markowitz dispatch, PFI construction and options factory.
- `src/triangular_factorization.jl`: FT/SS/BG policy-aware constructor and factory overloads; existing solve/update/refactor arithmetic unchanged.
- `src/simplex_phase_one.jl`, `src/simplex_precision.jl`, `src/solver.jl`, `src/lp_refinement_driver.jl`: append actual symbol through the six named copy/validation paths. Recovery's existing `_basis_factorization(B,ws.options)` then receives the setting without a new recovery algorithm.
- New candidate tests `test/native_pivot_policy_tests.jl` plus isolated test entry. Future permanent `test/runtests.jl` inclusion is reserved for Task3, not edited now. MOI raw attributes and HH implementation stay unchanged.

**Interfaces:**
- `SolverOptions(T; native_pivot_policy::Symbol=:default, existing_keywords...)`; field `native_pivot_policy::Symbol` is last. `_validated_options` appends that symbol with default compatibility for its old arity. Public conversion validates it.
- `_native_pivot_policy(value::Symbol)::_NativePivotPolicy`, two enum constants from the spec.
- `_native_lu(B::SparseMatrixCSC{Float64,Int}, policy::_NativePivotPolicy)::Float64UMFPACK`.
- `_factorize_basis(B::AbstractMatrix, backend::Val, policy::_NativePivotPolicy)`: native Float64 applies policy; native other precisions use existing path; Markowitz rejects nondefault before construction.
- `Manager(B::AbstractMatrix{T}, backend::Val, policy::_NativePivotPolicy)` for PFI/FT/SS/BG; old constructors forward default. `_basis_factorization(B,mode::Val,backend::Val,policy)` plus options adapter.
- `UMFPACKBackend` keeps its concrete nonparametric type and old two/four-argument default wrappers; new factory initialization supplies the fifth constant enum field. `_copy_backend` copies the enum while preserving all original ownership behavior.

- [ ] Write **options_and_copy_intent** tests before candidate implementation. Default keyword/old16-field construction give `:default`; `:bad` throws. Nondefault Markowitz and HH throw for Float16/32/64, BigFloat256 and both rational types. For PFI/FT/SS/BG native options test both symbols through `SolverOptions(T,o)`, `_phase_options`, `_remaining_options`, `_lp_auxiliary_options` and `_copy_precision_options`; assert unchanged unrelated fields, only intended budget/algorithm/scaling changes. Float64→BigFloat→Float64 retains `:threshold_one`; no factorization is needed for these tests. MOI existing `_solver_options` still returns default.
- [ ] Write **backend_owned_policy** tests using B=sparse([4.0 1;1 3]), C=sparse([5.0 1;1 4]), diagonal replacement, 3x3 identity, empty0x0 and same-pattern B with all stored values+0.0. Both policies: all20 control fields match installed defaults except declared slots; factor control vectors of independently built factors differ in identity. Default old wrappers still accept singular raw lu(check=false), with existing singular solve-view behavior. Constant policy assignment throws. No poison of shared active controls.
- [ ] Write **private_spare_copy_and_failure** tests for each of PFI/FT/SS/BG and both policies. Exercise fresh B→C (no spare), second same-pattern refactor (spare reuse), changed pattern, changed dimension, nonempty→empty→empty→B. Assert policy at every stage; fresh/no-spare/copy-spare transitions are observed, not inferred from one success. Copy with nonempty manager update history, refactor original and copy independently, verify old values/owners remain intact. In separate states, fail fresh singular construction with no spare and fail singular lu! with populated private spare; require original exception, unchanged active owners/values/dimension/policy/history, dropped failed spare, and valid F/B solves of preserved active factors. A later valid refactor after failure must retain the selected policy. No whole-native-rollback claim.
- [ ] Write **precision_and_factory_dispatch** tests. Float16/32, BigFloat256, Rational{Int}/Rational{BigInt} native constructors under either policy have the same backend type and outputs as their default path; no UMFPACK factor/control is created. Float64 reconstruction after option round-trip selects threshold-one. Default HH/Markowitz factories remain their old route; nondefault direct internal Markowitz/HH factory calls fail before factorization. Generic additional supported types retain source dispatch without a universal runtime claim.
- [ ] Prepare a RED entry that checks only missing option/enum/constructor contract markers on the unchanged reference; no factor/solver calls. Expected failures must be named. Do not report this as a solver defect or historical CI reproduction.
- [ ] Implement only the candidate changes from the Interfaces and spec. Default fresh LU remains literal `lu(B)`; threshold-one allocates a local default vector and changes exactly two slots. `_refactorize_backend` changes only fresh-LU selection; reused spare controls are untouched. Empty/copy carry the enum; original pattern, exception, publication and history rules remain.
- [ ] Verify exact whole-source inverse against the recorded baseline and enumerate every edited fragment/new method. Audit all positional SolverOptions constructions and option reconstruction calls, not only text matching a new keyword. Check no production F/B/update arithmetic, safeguards or HH source change; no new matrix scan/solve in loops. Existing singular-wrapper tests remain intact.
- [ ] Freeze candidate/tests/overlay and concrete expected test groups; obtain fresh independent gpt-6-astra numerical/work/memory review. Publish only after separate PASS closure, exact staged names/blobs and fail-fast push. This acceptance is OFFLINE; RED/GREEN/cost remain unexecuted.

## Task 2: Admit and qualify ordinary backend plumbing

**New directory:** `results/NATIVE-PIVOT-QUALIFICATION/`; concrete driver, launcher, guard, auditor, command/pins/admission, raw and result reviews must be prepared and accepted before any run. Ordinary source overlay only; no global method overwrite, old driver import or nested isolated full-module scheme.

**Interfaces:** consumes exact Task1 overlay/tests. Saves per-transition policy/control bits/owners and output tokens, actual work counters, exceptions, counts and raw-before-assert. Offline auditor uses exact stored values and the unchanged original residual bound.

- [ ] Derive exact setup/factor/refactor/copy/F/B/public-solve counts from the selected tests and driver before admission, including negative tests and post-failure solves; distinguish component entries from native internals. Bind fixed assertions and original neighbor testsets in a literal required list. No full file selected merely because it was pinned. If fixed work cannot fit the cap, stop before launch and redesign explicitly; never silently omit a gate.
- [ ] Fresh independent exact-stage admission, then ONE RED<=30s. Require the named missing-contract failures and zero native work; preserve exit/status. Only the expected RED allows a separately admitted ONE GREEN<=60s. GREEN must pass all Task1 tests plus unchanged constructor/copy/refactor/singular/hypersparse neighbors. All raw failures survive; no numerical retry.
- [ ] Prepare a separately admitted ONE cost<=45s. Reuse the four saved B4 and entering/DSE/unit RHS inputs from NATIVE-ACCURACY-PREPARATION, with policies default/threshold-one. Four fixtures × two arms × (3warm+8measured alternating matched rounds)=88windows. Each window: one native backend construction, two same-B refactors (first fresh/no-spare, second private-spare reuse), then16FTRAN/DSE/BTRAN triplets. Exact component totals88constructions+176refactors+4224solves; no public solve or extra calibration. Measure setup, each refactor and48solve region separately, and enclosing total as a superset; never sum nested timers twice. Include controls/CSC/scratch/private candidate allocation. Output vectors and fixed metadata storage are preallocated equally outside regions; quantify retained diagnostic bytes before launch.
- [ ] Store every output and actual control/strategy/refinement metadata, counts and all measured time/bytes/events/compile/recompile/GC samples; snapshot final fill/native Info and graph outside timing. Require all measured compile/recompile0, record GC and all outliers. Threshold-one must pass every unchanged `128*n*2^-52*max(1,norm(M,Inf)*norm(x,Inf),norm(b,Inf))` residual. Default's known sparse96 false outcome is diagnostic data, not suppressed or made an all-pass accuracy requirement. Compare default output with the saved C tokens and explain any nonmatch; do not retry.
- [ ] Report eight paired ratios/median/MAD/range for each region and fixture, all allocation counts, extra option/backend metadata and native fill/scratch costs. The old accuracy experiment is historical evidence, not a fresh timing reference. C/P within the new candidate measures selected-policy tradeoffs; it does not isolate overhead against the previous binary. Default call/solve source inverse establishes unchanged algorithms, not a measured universal zero-overhead claim. No new allocation API or loop scan in F/B/update is allowed; investigate material unexplained work rather than waive it. Legitimate accuracy-induced fill cost is not rejected merely for exceeding a speedup threshold.
- [ ] Fresh independent result review must reconcile current hashes, inputs, options, lifecycle owners, process groups/sessions, resource guards, every false result and work/memory interpretation. Separate PASS closure and exact publication. Passing ordinary plumbing does not qualify the direct managers, full solver or old cost2.

## Task 3: Focused public integration and promotion gate

**Candidate files:** same Task1 source, new focused tests and eventual `test/runtests.jl` inclusion; no direct-prototype source changes. Test public factory propagation before any production integration.

- [ ] Prepare independent admission for ONE<=60s focused integration, with exact predeclared counts and unchanged tests. Use the existing direct-LU plan's tiny LP: objective-3x1-2x2, x1+x2<=4, x1<=2, x2<=3, x>=0; optimum[2,2],objective-10. Four ordinary managers × two policies=8public solves, native Float64, legacy dual/steepest-edge/presolve=false/scaling=off/partial_pricing=false/refactorization_interval=2/time_limit=5/iteration_limit=100. Preserve original certificate/tolerances. Record policy at construction and exercised refactors without requiring identical trajectories or artificially adding pivots. Missing refactor coverage stays reported; Task2 provides its lifecycle coverage.
- [ ] Add one fixed tiny PFI threshold-one recovery-trial test using the existing checkpoint/recovery test setup and real `_recovery_trial`, plus copied phase/remaining/auxiliary/precision option assertions. Bind its exact constructor/solve budget before admission; verify the new private factor policy and unchanged live factor/controls. Do not infer recovery propagation merely from a constructor unit test. Failure/stop/observer tests reuse specified existing coverage where source-identical; new flag coverage and reused coverage must be distinguished.
- [ ] Independently review complete candidate diff, options compatibility, default paths, all supported-precision dispatch and computational work/memory. Only accepted GREEN/cost/public results plus a separate integration admission can authorize merge and focused master checks; no automatic full suite or original benchmark replay. Preserve all original evidence.
- [ ] After ordinary policy integration, prepare a NEW source/design adapter step for the three direct prototypes. It must retain policy in DirectLowerBackend and propagate it through copy/refactor/empty/fallback before extraction, with equal native policy on reference and candidate. Do not edit the frozen direct source or create a new numerical allowance here. Markowitz stays default. A later concrete accepted plan chooses a newly labelled comparison; oldcost2 remains blocked.

## Handoff

Next executable work is **Task1 OFFLINE candidate/tests preparation and independent
review**, using inline implementation followed by an independent reviewer as in
the existing workflow. No Julia and no production edit in that next task.
The design/plan itself changes no source, default, work budget or runtime result.
