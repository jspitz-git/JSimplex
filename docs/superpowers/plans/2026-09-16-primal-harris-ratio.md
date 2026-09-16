# Primal Harris Ratio Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Select stable primal pivots within the feasibility tolerance while retaining bound flips.

**Architecture:** Keep `_primal_ratio` as the single ratio decision point. Its first pass records the strict minimum ratio and the earliest relaxed limit; its second pass chooses the largest eligible pivot. Check aggregate predicted primal infeasibility before accepting a relaxed step.

**Tech Stack:** Julia 1.13, JSimplex workspace and basis types, `Test`.

**Spec:** `docs/superpowers/specs/2026-09-16-primal-harris-ratio.md`

## Global Constraints

- Work in `.worktrees/primal-simplex` on `feature/primal-simplex`.
- Commit this feature separately after the full Julia test suite passes.
- Keep exact rational and all floating scalar types supported.

---

### Task 1: Harris pivot and feasibility guard

**Files:**
- Modify: `src/primal_simplex.jl`, function `_primal_ratio`
- Test: `test/primal_simplex_tests.jl`
- Modify: `README.md`, primal algorithm description

**Interfaces:**
- Consumes: `_primal_ratio(workspace, entering, direction, tableau_column)` and the current `(step, leaving_row, leaving_state)` return contract.
- Produces: The same return contract, with a stronger eligible pivot when total predicted violation remains within tolerance.

- [x] **Step 1: Write failing tests.** Add testsets that call `_primal_ratio` on a two-row case with breakpoints `1` and `1 + 5e-8`, expecting the second row's larger pivot; on a three-row case where the relaxed step creates total violation above `1e-7`, expecting the strict first row; on a bounded entering variable, expecting `(1.0, 0, BASIC)`; and on tied `Rational{BigInt}` breakpoints, expecting the larger pivot.
- [x] **Step 2: Run the primal tests.** Use `JULIA_DEPOT_PATH=/tmp/jsimplex-primal-depot:/home/jspitz/.julia JULIA_PKG_OFFLINE=true julia --project=. -e 'using Test, JSimplex; include("test/primal_simplex_tests.jl")'`. Confirm the Harris pivot tests fail due to the old strict ratio behavior.
- [x] **Step 3: Implement the ratio test.** Preserve the strict minimum and entering bound as fallback. Compute each relaxed breakpoint as the raw strict breakpoint plus `primal_tolerance / abs(movement)`. Select the eligible row with largest `abs(tableau_column[row])`, then predict bound violations at its strict step. Keep the relaxed choice only if their sum is within tolerance.
- [x] **Step 4: Verify and document.** Run the targeted primal tests and `Pkg.test()` with the same depot and offline environment. Update README to describe Harris selection, then run `git diff --check`.
- [x] **Step 5: Commit.** Stage only the ratio implementation, tests, documentation, spec, and this plan; commit as `Add Harris primal ratio test`.
