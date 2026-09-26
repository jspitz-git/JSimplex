# Legacy Simplex Stability Implementation Plan

> Implementation proceeds sequentially using superpowers:executing-plans. Each independently verified repair receives an English commit.

**Goal:** Repair reproducible legacy simplex numerical failures and excessive stability-triggered refactorizations without weakening feasibility tolerances.

**Architecture:** Diagnose the first incorrect state transition before changing recovery policies. Keep arithmetic at problem precision, preserve adaptive behavior, and prefer a valid pivot over trying to repair an invalid basis by refactorization.

**Tech stack:** Julia, native sparse factorization, existing simplex diagnostics and tests.

**Scope:** User reproduction is runtime.mps with primal steepest-edge pricing, Bartels–Golub updates, native refactorization, interval 80, legacy strategy, and relaxed integrality. Use the same settings for dual diagnosis. Completion attempts allow at least 360 seconds. Never fully solve big.mps, largo.mps, or AnyMod.mps. Keep sequential jobs within the 24 GiB WSL budget.

## 1. Prevent infeasible primal bound snaps

Files: `src/primal_simplex.jl`, `test/primal_bound_snap_tests.jl`, `test/runtests.jl`.

- [x] Capture the last feasible runtime state and compare the predicted pivot with full recomputation and a fresh factorization.
- [x] Establish the cause: a tolerated negative leaving value is rounded to a zero ratio, but its exact bound assignment implies a negative entering step. A fresh factorization preserves the resulting infeasibility. Another Harris candidate permits a safe zero step.
- [x] Run a failing regression using `A = [-7e-8 -0.01; 0 -0.009]`, first column fixed at 1, nonnegative rows, and an improving second column. After one pivot, require primal infeasibility at most `1e-7` with no refactorization. Repeat with a free entering variable and a third row `[0 1]`, which detects damage to another basic variable.
- [x] In legacy ratio selection, validate the actual signed step of negative-ratio candidates against entering and basic bounds before accepting them. Keep nonnegative step semantics and adaptive behavior unchanged; reject an unsafe strict fallback too.
- [x] Test lower/upper bounds, both entering directions, all update backends, and safe tolerated negative steps. Run existing primal and numerical regression tests.
- [x] Repeat runtime with the user's settings and PFI, record any subsequent independent failure, and commit the verified repair.

## 2. Diagnose legacy stability refactorizations

Files: existing `src/dual_simplex.jl`, `src/simplex_recovery.jl`, and factorization code only where measurements demonstrate a defect; focused regression tests alongside the owning subsystem.

- [x] Capture the first residual-triggered refresh and subsequent update ages on runtime with the user's factor settings and dual simplex.
- [x] Compare updated and fresh directions against the original basis using existing accurate residual machinery. Distinguish a bad solve from an overly restrictive acceptance test.
- [x] For each established cause, write and observe a failing small regression, implement the smallest native-precision repair, and rerun its owning tests before a separate commit. Do not tune adaptive mode or loosen user tolerances.

## 3. Verify the final branch

- [x] Run sequential external checks from NetLib, MIPLib LP relaxations, and the user's mps directory. Include runtime and medium completion attempts and fast0507 performance/correctness checks.
- [x] Run production, development/JET, and GLPK checks on the final source tree. The monolithic production run timed out after 301 files; all 312 files are covered across the documented continuation, including a successful replay of the one omitted shared logger fixture. Development passes 1208/1208 and GLPK 6/6. The unchanged base already passed 254083 production and 1208 development checks; preserve those baseline records rather than repeating them.
- [x] Record commands, source hashes, statuses, certified residuals, elapsed times, refactorization causes, and memory evidence in an English diagnostic report. State time limits and remaining failures explicitly.
- [x] Review the complete diff and commit verified artifacts. Leave this worktree and logs intact; merging/pushing this new branch requires a later user request.

## Evidence-driven follow-up

The bound-snap guard is committed as `12cdd13`. It preserves feasibility on runtime but exposes another early termination: the best priced entering column can have no safe ratio while another column has one. Add a legacy candidate retry using the existing exclusion vector, without basis snapshots or an automatic refactor. Cancellation must clear exclusions; exhaustion must never report optimality. An eight-candidate cap proved insufficient on the actual saved runtime basis (the ninth candidate is valid), so search the finite candidate set subject to the caller's time/cancellation guard.

Also test the initial phase-I tolerance cutoff: ignoring a small initial bound violation can leave an improving column blocked even when a zero-cost column would first restore exact feasibility. Use a small independently solvable model before changing that cutoff, and retain adaptive phase-I behavior.

## Native dual correction

The first eight saved legacy BG80 repairs all pass the original residual threshold after one compensated Float64 correction using the existing factor. Add `src/legacy_dual_correction.jl` before the legacy refactor fallback: bound correction attempts, preserve the destination on failure, reprice a corrected transpose solve, and require a corrected forward pivot to agree with the ratio-test row. Hardware floating storage stays in Float32/Float64. Explicit validated recovery and adaptive strategy retain their existing paths. The expanded correction and existing dual tests pass 1723/1723; retain stronger fault injection for tests that specifically exercise mandatory refactorization.

## Corrected cycles and consistent primal zero steps

Native dual correction must not count as a clean cycle when considering interval growth. Mark accepted corrections until the next factorization; preserve the existing recovery toward the configured interval and leave explicit adaptive-refactor policies alone. The correction and interval-policy regressions pass 313/313.

Candidate rejection alone removes early primal failure but causes excessive retries. Preserve a leaving row activity's outward value when it lies within the original model bound tolerance, so a clipped zero ratio remains an actual zero step after recomputation. Do not alter bounds, tolerances, phase-I artificial-variable thresholds, or final original-model certification. Limit this behavior to Float32/Float64 legacy primal full recomputation after an iteration. Initial reconstruction and structural/artificial nonbasic variables retain their canonical bound assignments. Keep unsafe-snap and retry regressions using structural basic variables, where exact bound assignment remains necessary.

## Certify primal points and reject inaccurate transpose rows

Fresh reconstruction can lose feasibility on an ill-conditioned basis even while the predicted point remains independently feasible. Preserve that point only after certifying original bounds and consistency with stored row activities. Keep cancellation/exception rollback and bypass adaptive/explicit refinement/incremental policies. Committed as `95a41ee` after the related 487-check suite and expanded 166-check focused suite.

A later runtime failure exposes a spurious pivot of 0.87 where fresh FTRAN gives approximately zero. Forward residual acceptance and FTRAN/BTRAN pivot agreement both miss it; the transpose-row residual fails decisively. Validate that row before a legacy primal basis mutation, reuse it for steepest-edge/devex updates, try native correction first, then permit at most one refresh of the unchanged basis before candidate rejection. Preserve independently certified primal values across that refresh. Verify a small singular-pivot regression and correction-without-refactor regression before repeating runtime and the final gates.

## 4. Investigate compilation slowdown after stability verification

The user reports a severalfold compilation slowdown on the second computer as
well. Complete the current stability verification and external measurements
first, then investigate this separately and sequentially.

- [ ] Compare representative cold compilation workloads against the previous
  branch, separating compilation from warmed solver execution.
- [ ] Use the saved inference/subtype stack samples and a bounded reproducer or
  revision comparison to identify the responsible change; do not infer a cause
  from elapsed time alone.
- [ ] Record confirmed causes and measured costs. If a bounded repair is
  established, verify its numerical behavior and compilation improvement before
  a separate English commit.
