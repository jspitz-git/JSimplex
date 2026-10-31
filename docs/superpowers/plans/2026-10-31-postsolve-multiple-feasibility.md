# Multiple-bound postsolve feasibility repair

**Goal:** Repair the PC-doma 8-BLAS-thread capture without changing tolerances,
arithmetic precision, or final original-model certification.

**Design:** Retain the existing zero-cost dual feasibility solve. Admit any
positive initial violation count and bound its local iteration budget by that
count, 32, and the remaining global iteration budget. Keep one-pivot behavior
for one violation. Costs, options, perturbation state, stopping behavior,
pricing invalidation, final recomputation and fallback remain unchanged.
An unrestricted dual solve could duplicate expensive fallback work; repeating
the helper would redundantly allocate zero costs and recompute the full state.
One bounded solve reuses its existing workspace throughout the attempt.

**Files:** src/solver.jl, test/postsolve_multiple_feasibility_tests.jl,
test/runtests.jl, diagnostics/runtime-primal-regression/ verification/evidence.

- [x] Add failing independent-bound fixtures: multiple lower/upper violations,
      remaining budget, bounded failure, cancellation, restoration, nonfinite state.
- [x] Extend the admission guard and budget; run existing and new focused tests.
- [x] Replay the saved handoff through production cleanup on PC-doma at 8 BLAS
      threads, with original settings and hashes; verify feasible entry and OPTIMAL.
- [x] Review correctness, execution frequency and memory. Measure cold recovery
      separately from setup/compilation on sparse and dense fixtures; no speedup
      inference from changed iteration counts. Run relevant related test files.
- [x] Save a reviewable patch and verification evidence. No tolerance/precision changes.

Verified: 425 focused checks and 2,731 optimized related checks (overlapping
counts), one/six-violation diagnostic fidelity, independent review without
findings. PC-doma's exact handoff needed two repair pivots, entered primal
cleanup with zero infeasibility, and reached OPTIMAL after 1,180 total additional
iterations. Evidence: diagnostics/runtime-primal-regression/results/failure2-8blas-fixed/verification.json.

Scope: continuation of the user's explicitly requested repair in the existing
workspace; preserve unrelated .vscode and prior diagnostic changes. No new
full-MPS solve is needed to verify a saved postsolve handoff. The previous full
suite evidence remains historical; report the scope of the fresh checks.
