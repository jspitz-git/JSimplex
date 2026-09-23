# Simplex Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Implement all proposed algorithm changes for more robust and faster primal and dual simplex, committing each verified feature separately.

**Architecture:** Establish diagnostics and shared numerical contracts, then improve pivoting, recovery, incremental primal updates, and pricing. Hypersparse kernels, phase I, and adaptive precision build on the same interfaces. Enable changes incrementally and compare them against both the parent revision and the original solver.

**Tech Stack:** Julia 1.13, SparseArrays/UMFPACK, native Markowitz and basis updates, Test, and MOI; GLPK and BenchmarkTools remain development-only.

**Spec:** [Modernization specification](../specs/2026-09-22-simplex-modernization-design.md).

## Global Constraints

- Julia 1.13; preserve support for Float32, Float64, BigFloat, and rational types.
- Production dependencies remain LinearAlgebra, Logging, MathOptInterface, OrderedCollections, and SparseArrays; this plan adds no dependencies.
- Work in .worktrees/simplex-modernization on branch feature/simplex-modernization, starting from commit d93cfd3.
- Each verified feature gets its own commit, including tests, documentation, and a validation report.
- Preserve Solution{T}, existing statuses, explicit LP relaxation, and validation against the original model.
- Share the time limit and completed-step budget across phases, repairs, retries, algorithm switches, and precision increases.
- Do not weaken user tolerances or certification to make a benchmark pass.
- Exact rational arithmetic uses neither floating-point perturbations nor automatic conversion to floating-point arithmetic.
- Working perturbations must not modify the input model and must be removed before certification.
- Algorithm changes need not preserve bitwise intermediate results or the pivot path.
- Write all material intended for the remote repository in English, including documentation, code comments, reports, and commit messages.
- Use /home/jspitz/NetLib, /home/jspitz/MIPLib, and /home/jspitz/mps as the external test collections; solve MIPLib cases only as explicit LP relaxations.
- Exclude big.mps, largo.mps, and AnyMod.mps (stored locally as AnyMOD.mps) from complete simplex solves; use them only for explicitly bounded stress tests.

## Review Focus

- A deadline or logger exception between proposing and applying a pivot must not leave partial state changes: F04, F06, F07.
- Lower/upper/fixed/free variables, zero widths, and width overflow in BFRT must not invalidate status proofs: F03, F08, F12–F13.
- BigFloat values stored at higher precision than the ambient context and rational arithmetic without eps must retain their values: F02, F22–F24.
- Sparse right-hand sides can produce dense solutions, and cancellation can change support: F16–F19 test both solve directions and mode changes.
- Postsolve, restoring costs/bounds, and converting higher-precision output require fresh certification of the original LP: F07, F13, F21, F23–F25.
- The stress-only exclusion must survive explicit file selection, aliases, compression, and capitalization: F01, F25.

## Worktree and preparation status

The dedicated worktree was created from d93cfd3:

~~~bash
cd /home/jspitz/JSimplex.jl/.worktrees/simplex-modernization
git branch --show-current
git status --short
~~~

The expected branch is feature/simplex-modernization. Implement changes here.
Do not use the existing presolve or primal-simplex worktrees, or create a
nested worktree on resumption. The planning commit precedes F01; feature
checkboxes below track actual implementation.

Preparation reproduced the isolated `Pkg.test()` failure: test imports were
missing from `test/Project.toml`. Commit `a52e194` declares the three standard
libraries used directly by tests. The standard launcher then passed
224,921/224,921 checks without numerical changes. See the
[preflight report](../../../diagnostics/simplex-modernization/preflight_test_environment.md)
and the earlier [baseline record](../../../diagnostics/simplex-modernization/planning_baseline.md).

Verify pathof(JSimplex) before development so tests load this worktree:

~~~bash
JULIA_DEPOT_PATH=/tmp/jsimplex-modernization-depot:/home/jspitz/.julia JULIA_PKG_OFFLINE=true julia --startup-file=no --project=. -e 'using JSimplex; @assert startswith(realpath(pathof(JSimplex)), realpath(pwd())); println(pathof(JSimplex))'
~~~

Use the available local dependency cache. The main checkout's dev/Manifest.toml
can be copied into this worktree's ignored dev/Manifest.toml because JSimplex
has the relative source path ".."; still verify pathof(JSimplex).
Dependency manifests and incidental dependency changes do not belong in
algorithm commits.

## Test data and execution modes

Use [the test corpus plan](2026-09-22-simplex-test-corpus.md) for the three
external roots, compression handling, fixed selections, and stress budgets.
Use local NetLib and MIPLib cases for algorithm comparisons, plus eligible
models under /home/jspitz/mps. Retain small repository fixtures for the
mandatory offline suite. Solve MIPLib only as explicit LP relaxations.

Use a 360-second solver budget for complete `runtime.mps` comparisons: the
user expects this model to need at least five minutes. Retain earlier shorter
runs as censored screening observations. For `medium.mps` and difficult large
runs, request 24 GiB rather than the harness's 4 GiB screening default; the
worker still clips the allowance to the host's reported memory.

big.mps, largo.mps, and AnyMod.mps (actual spelling AnyMOD.mps) are excluded
from complete simplex solves. They belong to a separate opt-in stress suite
for bounded parsing, memory behavior, and component tests. Do not attempt
a full-sized basis factorization or unrestricted solve on these models.
Stress outcomes do not enter solved-LP coverage or speed scores.

## Stages and commits

The table gives the recommended sequential implementation order. Dependencies
permit moving whole stages; they are not an instruction to delegate
implementation in parallel.

| Status | Feature | Dependencies | Separate commit |
| --- | --- | --- | --- |
| [x] | F01 Reproducible diagnostics and benchmarks | baseline | `feat: add simplex numerical benchmark harness` |
| [x] | F02 Shared numerical policy and residuals | F01 | `feat: add shared simplex numerical quality checks` |
| [x] | F03 Stable Harris BFRT | F02 | `feat: stabilize dual bound flipping ratio test` |
| [x] | F04 Pivot validation and reselection | F03 | `feat: retry numerically unsafe simplex pivots` |
| [x] | F05 Shared iterative solve refinement | F02, F04 | `feat: share iterative refinement across simplex methods` |
| [x] | F06 Basis checkpoints and repair | F05 | `feat: recover simplex from verified basis checkpoints` |
| [x] | F07 Feasibility recovery and primal/dual handoff | F06 | `feat: add bounded simplex feasibility recovery` |
| [x] | F08 Incremental primal bound flips | F07 | `feat: update primal bound flips incrementally` |
| [x] | F09 Incremental primal pivots | F08 | `feat: update primal pivots incrementally` |
| [x] | F10 Shared adaptive refactorization | F09 | `feat: schedule basis refactorization by quality and cost` |
| [x] | F11 Stagnation detection | F07 | `feat: detect scaled simplex stagnation` |
| [x] | F12 Adaptive dual cost perturbations | F11 | `feat: adapt dual cost perturbations to stagnation` |
| [x] | F13 Reversible primal bound perturbations | F09, F12 | `feat: recover degenerate primal paths with bound perturbations` |
| [x] | F14 Automatic pricing and weight recovery | F11, F13 | `feat: adapt simplex pricing using reliable edge weights` |
| [x] | F15 Partial pricing | F14 | `feat: add partial simplex pricing with full-scan certification` |
| [x] | F16 Indexed vectors and sparse pricing | F15 | `feat: add indexed simplex vectors and sparse pricing` |
| [x] | F17 Hypersparse base LU solves | F16 | `feat: solve sparse basis factors by reachability` |
| [x] | F18 Hypersparse basis updates | F17 | `feat: propagate sparse support through basis updates` |
| [ ] | F19 Adaptive sparse pipeline and fill-in | F10, F18 | `feat: integrate adaptive hypersparse simplex kernels` |
| [ ] | F20 Better initial bases | F07 | `feat: construct guarded simplex crash bases` |
| [ ] | F21 Phase I modernization | F09, F13, F20 | `feat: reuse recovered bases in simplex phase one` |
| [ ] | F22 Basis transfer across precisions | F07, F21 | `feat: transfer simplex state across working precisions` |
| [ ] | F23 Higher-precision solves and pivoting | F05, F19, F22 | `feat: boost simplex working precision on numerical failure` |
| [ ] | F24 LP iterative refinement | F23 | `feat: refine LP solutions through scaled correction problems` |
| [ ] | F25 Integration and default selection | F01–F24 | `feat: enable verified adaptive simplex defaults` |

Detailed plans:

1. [Measurements and numerical contracts, F01–F02](2026-09-22-simplex-01-foundation.md).
2. [Pivoting and recovery, F03–F07](2026-09-22-simplex-02-stability.md).
3. [Incremental primal and refactorization, F08–F10](2026-09-22-simplex-03-primal.md).
4. [Degeneracy and pricing, F11–F15](2026-09-22-simplex-04-pricing.md).
5. [Hypersparse kernels, F16–F19](2026-09-22-simplex-05-hypersparse.md).
6. [Initial bases and phase I, F20–F21](2026-09-22-simplex-06-initialization.md).
7. [Adaptive precision and completion, F22–F25](2026-09-22-simplex-07-precision.md).

## Verification and commit protocol

Each task includes a concrete test case and required behavior. New interface
examples specify proposed contracts; they are not already available APIs.
Task text defines the variables used in algorithm pseudocode.
Register new production test files in test/runtests.jl and development tests
in dev/tests/runtests.jl. Large external LPs stay outside mandatory offline
tests.

For each Fxx:

- [ ] Write the reproducer and behavioral test; run the targeted suite and confirm that the failure reflects the missing feature.
- [ ] Implement the feature, fallback, and documentation; propagate API changes to MOI and option conversions in the same change.
- [ ] Run targeted tests and the full production suite below. Fix new failures rather than replacing expectations with the new output.
- [ ] Run the relevant numerical benchmark without concurrent tests, recording limits and failures; run development checks for API or type-stability changes.
- [ ] Review the diff, scratch ownership, perturbation restoration, deadlines, and statuses. Add commands and results to diagnostics/simplex-modernization/Fxx.md.
- [ ] Stage only the feature's files, tests, report, and updated plan. Create its listed commit before starting the next feature.

The following full-suite command passed during preparation:

~~~bash
JULIA_DEPOT_PATH=/tmp/jsimplex-modernization-depot:/home/jspitz/.julia JULIA_PKG_OFFLINE=true julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/runtests.jl")'
git diff --check
~~~

After resolving the recorded invocation difference, also validate the standard
Pkg.test() entry point with the same depot/offline environment.

~~~bash
JULIA_DEPOT_PATH=/tmp/jsimplex-modernization-depot:/home/jspitz/.julia JULIA_PKG_OFFLINE=true julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
~~~

Loading the package alone does not constitute a full test run.

Example targeted invocation; use the test file specified by the current task:

~~~bash
JULIA_DEPOT_PATH=/tmp/jsimplex-modernization-depot:/home/jspitz/.julia JULIA_PKG_OFFLINE=true julia --startup-file=no --project=. -e 'using Test, JSimplex; include("test/dual_simplex_tests.jl")'
~~~

Development and independent-reference checks after preparing the dev environment:

~~~bash
JULIA_DEPOT_PATH=/tmp/jsimplex-modernization-depot:/home/jspitz/.julia JULIA_PKG_OFFLINE=true julia --startup-file=no --project=dev dev/tests/runtests.jl
JULIA_DEPOT_PATH=/tmp/jsimplex-modernization-depot:/home/jspitz/.julia JULIA_PKG_OFFLINE=true julia --startup-file=no --project=dev dev/run_suite.jl --tag=numerical --compare-glpk
~~~

Preserve existing bitwise-path tests for the legacy implementation. For adaptive
paths, add behavioral invariants and independent oracles. Do not remove
regressions or raise allocation limits indiscriminately. Document necessary
new workspace storage and measure it separately from recurring pivot costs.

Each Fxx report records the parent hash, hashes of tested sources and datasets,
settings, precision, test counts, status/certification, times, iterations,
refactorization reasons, repairs, memory, and opt-in/default decision. Keep
reports and comments in English. Do not embed a commit's own resulting hash
inside that same commit; derive it from history or record it later.

## Milestone gates

- After F07: reproduce a late numerical failure and recover at least one case; introduce no false certified status. **Recovery milestone unmet:** F07 is implemented and verified but remains opt-in. Extended runtime and greenbea runs do not establish new solved coverage; see the [F07 report](../../../diagnostics/simplex-modernization/F07.md).
- After F10: demonstrate cheaper primal iterations and measure complete primal solves, including numerical quality after long update chains. **Cost milestone unmet:** F08/F09 reduce basis-solve work, but the combined adaptive path has not established cheaper complete primal solves. F10 passes complete suites and preserves quick solved coverage; all runtime comparisons reach 360-second limits. Keep adaptive opt-in; see the [F10 report](../../../diagnostics/simplex-modernization/F10.md).
- After F15: validate degeneracy beyond pk1 and ablate perturbations/pricing; do not hide stagnation by increasing iteration limits. **Verification complete, performance mixed:** F12–F15 retain independent ablations; degen2 and markshare_4_0 reach consistent optima, while scsd8 remains unsolved. Partial pricing reduces scan work but does not establish a broad speedup. Legacy remains the public default; see the [F15 report](../../../diagnostics/simplex-modernization/F15.md).
- After F19: demonstrate hypersparse benefits on sparse solve results and correct dense fallbacks; include factor extraction, graph, fill-in, and conversion costs. Oversized models remain bounded component probes.
- After F21: report phase-I time/iterations separately and verify artificial removal and postsolve.
- After F24: test and ablate precision boosting separately from LP correction and linear-system refinement.
- After F25: run the quick and frozen holdout corpora, plus eligible complete runs of runtime.mps, medium.mps, and NetLib greenbea, to termination or preset limits. Report unfinished runs explicitly. Report the three oversized stress models separately.

If a milestone fails, fix the issue or keep the feature opt-in and document
its limits. Creating all modules alone does not complete the objective.
Changing defaults requires the specification's evidence; an unsuccessful
rollout must not be committed as successful.

## Handoff

The user authorized sequential implementation in this worktree, with one
commit per verified feature. Preparation and F01–F15 are complete; F16 is next.
See the [F15 validation report](../../../diagnostics/simplex-modernization/F15.md).
On resumption, use the feature checkboxes and commit history, then read the
specification and the next incomplete stage. Keep implementation sequential
because the stages share numerical contracts.
