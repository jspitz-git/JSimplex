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
- [ ] Run a failing regression using `A = [-7e-8 -0.01; 0 -0.009]`, first column fixed at 1, nonnegative rows, and an improving second column. After one pivot, require primal infeasibility at most `1e-7` with no refactorization. Repeat with a free entering variable and a third row `[0 1]`, which detects damage to another basic variable.
- [ ] In legacy ratio selection, validate the actual signed step of negative-ratio candidates against entering and basic bounds before accepting them. Keep nonnegative step semantics and adaptive behavior unchanged; reject an unsafe strict fallback too.
- [ ] Test lower/upper bounds, both entering directions, all update backends, and safe tolerated negative steps. Run existing primal and numerical regression tests.
- [ ] Repeat runtime with the user's settings and PFI, record any subsequent independent failure, and commit the verified repair.

## 2. Diagnose legacy stability refactorizations

Files: existing `src/dual_simplex.jl`, `src/simplex_recovery.jl`, and factorization code only where measurements demonstrate a defect; focused regression tests alongside the owning subsystem.

- [ ] Capture the first residual-triggered refresh and subsequent update ages on runtime with the user's factor settings and dual simplex.
- [ ] Compare updated and fresh directions against the original basis using existing accurate residual machinery. Distinguish a bad solve from an overly restrictive acceptance test.
- [ ] For each established cause, write and observe a failing small regression, implement the smallest native-precision repair, and rerun its owning tests before a separate commit. Do not tune adaptive mode or loosen user tolerances.

## 3. Verify the final branch

- [ ] Run sequential external checks from NetLib, MIPLib LP relaxations, and the user's mps directory. Include runtime and medium completion attempts and fast0507 performance/correctness checks.
- [ ] Run the full production suite, development/JET checks, and GLPK checks on the final source tree. The unchanged base already passed 254083 production and 1208 development checks; preserve those baseline records rather than repeating them.
- [ ] Record commands, source hashes, statuses, certified residuals, elapsed times, refactorization causes, and memory evidence in an English diagnostic report. State time limits and remaining failures explicitly.
- [ ] Review the complete diff and commit verified artifacts. Leave this worktree and logs intact; merging/pushing this new branch requires a later user request.

## Evidence-driven follow-up

The bound-snap guard is committed as `12cdd13`. It preserves feasibility on runtime but exposes another early termination: the best priced entering column can have no safe ratio while another column has one. Add a legacy candidate retry using the existing exclusion vector, without basis snapshots or an automatic refactor. Cancellation must clear exclusions; exhaustion must never report optimality. An eight-candidate cap proved insufficient on the actual saved runtime basis (the ninth candidate is valid), so search the finite candidate set subject to the caller's time/cancellation guard.

Also test the initial phase-I tolerance cutoff: ignoring a small initial bound violation can leave an improving column blocked even when a zero-cost column would first restore exact feasibility. Use a small independently solvable model before changing that cutoff, and retain adaptive phase-I behavior.
