# Simplex Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Establish measurements, replay, and a shared numerical contract before changing pivot paths.

**Architecture:** Internal diagnostics remain separate from public results. Policy enables ablations and retains the legacy path for comparison. The corpus runner separates complete solve benchmarks from bounded stress probes.

**Tech Stack:** Julia 1.13, Test, SparseArrays, existing JSimplex backends, and MOI.

**Spec:** [Specification](../specs/2026-09-22-simplex-modernization-design.md). Also read the [main plan](2026-09-22-simplex-modernization.md) for validation/commit commands and the [test corpus plan](2026-09-22-simplex-test-corpus.md) for collection and stress rules.

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

- F01: retain timeouts, missing inputs, compression failures, and late numerical failures in reports.
- F01: explicit selection must not bypass oversized-model exclusions; keep stress results out of solve scores.
- F02: zero denominators, overflow, and mixed stored BigFloat precision.
- F02: preserve public options through conversion and MOI reset.

---

### F01: Reproducible diagnostics and benchmark corpus

**Files:** Create: src/simplex_diagnostics.jl, dev/simplex_benchmarks.jl, dev/simplex_cases.toml, test/simplex_diagnostics_tests.jl, dev/tests/simplex_benchmark_tests.jl. Modify: src/simplex.jl, src/dual_simplex.jl, src/primal_simplex.jl, src/JSimplex.jl, both runtests.jl files.
**Interfaces:** SimplexDiagnostics() owns integer counters and a ring buffer containing the latest 64 events. record_event!(d, reason::Symbol)::Nothing; event_count(d, reason)::Int. The benchmark entry point benchmark_main(args)::Int returns a nonzero code on input/validation errors. Diagnostics remain internal; public SolveStatistics stays compatible.

- [ ] Test bounded history and counters that continue increasing after the buffer fills:

~~~julia
d = JSimplex.SimplexDiagnostics()
for _ in 1:100
    JSimplex.record_event!(d, :refactor_residual)
end
@test JSimplex.event_count(d, :refactor_residual) == 100
@test length(d.events) == 64
~~~

- [ ] Implement events for phases, completed pivots/flips, proposed/rejected pivots, refactorization reasons, corrections, pricing, perturbations, and certification. Later tasks add their call sites. No I/O or allocated strings in normal iterations. Kernel timing is opt-in; reports distinguish measurement overhead from normal execution.
- [ ] Implement the runner commands below. Record variant, source/dataset hashes, scalar type/precision, options, BLAS settings, status, errors in original units, phase/total times, counters, and memory. --source loads the selected checkout/snapshot in a separate process, without relying on the main checkout.
- [ ] Discover NetLib/MIPLib/local cases from the three roots in the corpus plan. Add the eight specified quick cases, NetLib greenbea, and eligible local runtime/medium cases. Stream .mps.gz with resource bounds and explicit LP relaxation. Keep repository fixtures for offline regression coverage.
- [ ] Implement a separate opt-in stress execution mode for big.mps, largo.mps, and AnyMOD.mps. Enforce canonical-path/name classification before launching work, including --file. No unrestricted solve or full-sized basis factorization. Implement the corpus plan's watchdog, memory/read caps, and separate stress outcomes.
- [ ] Test CLI parsing, missing inputs, mismatched hashes, corrupt gzip, timeout, and numerical failure. Add selection tests for capitalization, aliases, compressed forms, and rejection of full solves on stress-only models. Freeze a content-deduplicated holdout and deterministic generated cases before tuning.
- [ ] Export state at the first serious repair: basis, states, working costs/bounds, options, precision, original/working model hashes, and counters. Support replay with a rebuilt factorization, explicitly noting that it does not reproduce update-chain drift. For drift replay, retain the initial state and pivot/flip/refactorization sequence.
- [ ] Measure the baseline, run new tests and the full suite, and commit: feat: add simplex numerical benchmark harness.

Implement these commands in F01; they are not currently available:

~~~bash
julia --project=dev dev/simplex_benchmarks.jl --source=. --suite=quick --algorithm=both --samples=7 --time-limit=60 --iteration-limit=100000 --output=/tmp/simplex-quick.toml
julia --project=dev dev/simplex_benchmarks.jl --source=. --file=/home/jspitz/MIPLib/pk1.mps.gz --algorithm=both --samples=7 --time-limit=60 --iteration-limit=100000 --output=/tmp/simplex-pk1.toml
julia --project=dev dev/simplex_benchmarks.jl --source=. --file=/home/jspitz/mps/runtime.mps --algorithm=both --samples=3 --time-limit=1800 --iteration-limit=1000000 --output=/tmp/simplex-runtime.toml
julia --project=dev dev/simplex_benchmarks.jl --source=. --file=/home/jspitz/mps/medium.mps --algorithm=both --samples=3 --time-limit=1800 --iteration-limit=1000000 --output=/tmp/simplex-medium.toml
julia --project=dev dev/simplex_benchmarks.jl --source=. --suite=stress --mode=stress --time-limit=60 --memory-limit-mib=4096 --read-limit-mib=256 --output=/tmp/simplex-stress.toml
~~~

Also implement --suite=holdout, --replay=PATH, --policy=PATH, and the root,
compression, and stress-operation controls specified by the corpus plan.
TOML policy selects only implemented internal switches; unknown keys are
errors. Each complete solve starts from the original input rather than a
previously solved basis. Large baseline runs belong to F01 execution, not
to preparation of this plan.

### F02: Shared numerical policy and componentwise residuals

**Files:** Create: src/simplex_numerics.jl, test/simplex_numerics_tests.jl. Modify: src/options.jl, src/simplex.jl, src/solver.jl, src/JSimplex.jl, src/moi/optimizer.jl, src/moi/attributes.jl, test/options_tests.jl, MOI tests, README.
**Interfaces:** NumericalPolicy(::Type{T}; kwargs...) constructs concrete NumericalPolicy{T}. Boolean switches are stable_ratio, recovery, incremental_primal, adaptive_refactor, adaptive_stalling, adaptive_pricing, partial_pricing, hypersparse, crash, phase_one, precision_boosting, and lp_refinement. Unimplemented modules initially remain false; their tasks expose and enable them only in the adaptive profile.
SolveQuality{T} contains absolute_error::T, relative_error::Union{Nothing,T}, finite::Bool, reliable::Bool.
solve_quality!(scratch, B, x, rhs, policy; transposed=false)::SolveQuality{T}.
_componentwise_backward_error(r, scale) is a floating-point helper; rational arithmetic checks residuals exactly.

- [ ] Add zero-denominator and normalization tests:

~~~julia
@test JSimplex._componentwise_backward_error([0.0], [0.0]) == 0.0
@test isinf(JSimplex._componentwise_backward_error([1.0], [0.0]))
@test JSimplex._componentwise_backward_error([1e-10], [2.0]) ≈ 5e-11
@test SolverOptions(simplex_strategy=:adaptive).simplex_strategy == :adaptive
@test_throws ArgumentError SolverOptions(simplex_strategy=:unknown)
~~~

- [ ] Implement r=b-B*x, or r=b-B'*x, and scale abs(b)+abs(B)*abs(x) without unsafe overflow. If the scale cannot be evaluated reliably, return unreliable rather than zero divided by Inf. Derive the initial floating backward-error limit from 256eps(T); if k*eps(T)>=1, increase precision or reject rather than allowing infinite tolerance. Scale componentwise sums and use higher precision where necessary.
- [ ] Separate solve tolerance, pivot error, and primal/dual tolerances. NumericalPolicy also contains max_refinements=3, max_pivot_candidates=8, max_recovery_rounds=2, stagnation_window=64, max_precision_bits=512, and max_lp_refinements=8. These are initial experimental policy limits, not replacements for user tolerances.
- [ ] Propagate simplex_strategy through all constructors, conversions, _remaining_options, and MOI; default to :legacy. Test that Float64→Float32 conversion preserves the option and MOI reset restores its default.
- [ ] Test scaled versions of the same system, an almost singular B with a small residual, transpose solves, Float32, exact Rational{BigInt}, and 512-bit stored BigFloat inputs under a 64-bit ambient context. New APIs must not mutate B/rhs or overwrite live tableau scratch.
- [ ] Run targeted numerical/options/MOI tests and the full suite. Check unchanged legacy behavior on the F01 quick suite, then commit: feat: add shared simplex numerical quality checks.
