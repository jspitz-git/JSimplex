# Fresh runtime.mps verification through both readers and simplex methods

Production base: `b8955ac` on `codex/adaptive-degeneracy`.
Production SHA-256:
`40d6fa0140556827f9e353987417296ef513e64c0618ea4afa3fcc8bddcb3718`.
No production changes are made during these runs.

## Configuration

Each case starts from `/home/jspitz/mps/runtime.mps`, SHA-256
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`.
The native MPS model has 43,021 rows, 47,148 columns and 277,210 stored
coefficients. The JuMP reader is translated through JSimplex's MOI adapter;
row/column names align its ordering with the native model, and the runner
requires exact equality of the matrix, objective, bounds and domains.

The profile matches the preceding isolated adaptive experiments and external
corpus: Float64, steepest-edge, PFI, native refactorization, interval 80,
presolve and automatic scaling, with integrality relaxed. Adaptive stalling,
pricing, primal/dual perturbations and internal phase-I construction are on;
all other numerical switches are off. Existing diagnostic overrides disable
weak-pivot preference and the outer original-LP retry. These are **isolated
profile runs**, not the default complete adaptive profile or legacy strategy.
Production export and postsolve are exercised from a fresh MPS load; no saved
workspace is used to start any case.

Each solver gets 7,200 seconds and 1,000,000 iterations, with a 7,500-second
outer guard. Cases run serially with Julia 1.13.0/aarch64, one Julia/BLAS thread,
`precompile_workload=false`, an 8 GiB virtual-memory ceiling, a 6 GiB available
RAM floor and a 1 GiB swap ceiling. Only the owned process group can be stopped.
Common paths warm up on afiro before runtime is loaded. Times include remaining
compilation and diagnostic observation, so this is not a speed benchmark.

A successful solve must pass the original-point certificate in both reader
and native ordering. Its objective is compared to the earlier certified dual
reference `51425691.762103125` from
`diagnostics/native-primal-completion/results/runtime-dual.toml`, at `rtol=1e-9`
and `atol=1e-7`. This is an existing JSimplex reference, not a new independent
HiGHS solve. Sampled working objectives and infeasibilities are observations,
not original-model solution certificates.

## Harness correction

The initial native/dual solve stopped at iteration 23,538, but its result writer
then raised an ambiguous-name error for unqualified `OPTIMAL` exported by both
JuMP and JSimplex. That attempt has no complete result report. The initial log
is retained as `native-dual-harness-error.log`; its exact runner copy is local.
The writer now uses `JSimplex.OPTIMAL`. A JuMP/dual afiro smoke test completed at
its checked optimum and successfully wrote its report and detached snapshot.
The native/dual case was then repeated from MPS to obtain a complete result.
No solver method or numerical setting changed for this harness correction.

## Reproduction

Under the existing memory guard, run each of the four reader/method pairs:

```sh
julia --project=.superpowers/adaptive-degeneracy/broad-validation/env \
  diagnostics/adaptive-degeneracy/reproduce/runtime_reader_full.jl \
  native dual 7200 OUTPUT_PREFIX
```

Replace `native` with `jump` and `dual` with `primal` for the other cases.
Use a unique output prefix: the runner refuses to overwrite a result report.
The runner reuses the committed broad-corpus policy, model-equivalence,
coverage and snapshot helpers. Its observer records phases, pricing transitions
and samples every 1,000 pivots. Local detached final workspaces are diagnostic
states, not exact resumable checkpoints of the outer driver.

## Native reader / dual simplex

The complete repetition returns `NUMERICAL_ERROR`, `dual feasibility lost`, at
23,538 iterations and 295 refactorizations, after 73.915926173 solver seconds.
The final observed working point has primal infeasibility about 9,405.44 and
one dual violation of `1.0000024985856726e-7`, slightly above `1e-7`. Its working
objective is approximately 41,950,966.08; this is not a returned solution.
No time or memory guard fires. One outer original-LP retry is intercepted by
the established isolation override; no retry is actually performed.

The completed run reproduces every observed non-time field of the initial
harness-error attempt exactly. This supports a reproducible solver failure
independent of the report-writer fix. The final detached workspace is retained
locally for a separate diagnosis; no solver correction is attempted during the
four-way verification.

## JuMP reader / dual simplex

JuMP produces an exactly equivalent original model, with all 43,021 rows
reordered and no reordered columns. Dual simplex returns `NUMERICAL_ERROR`,
`dual feasibility lost`, at 6,417 iterations and 81 refactorizations, after
18.094907553 solver seconds. The final working point has primal infeasibility
about 45,930.98 and one dual violation of `1.000000000000001e-7`. No optimum or
original primal solution is returned. No resource guard fires; the isolation
override intercepts one original-LP retry.

Both reader orders therefore expose a dual-feasibility failure very close to
the tolerance boundary under this isolated adaptive profile, at different
iterations. These observations do not yet identify its cause or establish the
behavior with adaptive pricing/perturbations disabled.

## Native reader / primal simplex

The fresh native primal solve returns verified `OPTIMAL` at **106,252 iterations**
and **1,341 refactorizations**, in **820.262893256 solver seconds**. The returned
objective is **51425691.762104236**. Original and reader-model primal certificates
pass, and the relative difference from the earlier dual reference is
`2.1587196416864492e-14`. No original-LP retry or resource guard is used.

Phase I exports successfully at iteration 82,000. Phase II then finishes on
the reduced problem, followed by original-model cleanup. The coupled phase
component is proposed and certified once. The returned status, iterations,
refactorizations and objective exactly match the earlier successful native
primal full run in `results/phase-components/runtime.toml`; every shared
1,000-pivot objective sample also matches exactly. Elapsed times are diagnostic,
not a paired speed measurement.

## JuMP reader / primal simplex

The fresh JuMP primal solve returns `NUMERICAL_ERROR`, `artificial removal
could not be completed`, at **86,607 iterations** and **1,080 refactorizations**,
in **635.440605479 solver seconds**. At iteration 86,000 the observed auxiliary
objective is about 0.26526318. Phase-I export is attempted once; a coupled
component is proposed once but is not certified. No phase-II start is observed.
The component input and final observed workspace are retained locally.

The final observed reduced workspace has 28,453 rows and 31,615 columns, zero
reported primal infeasibility, and dual infeasibility about 1.504e9. This is an
unsuccessful transition state, not a returned original-model solution. Its
working objective must not be interpreted as an optimum. The isolation override
intercepts one original-LP retry; no resource guard fires. The exact failing
certificate and its cause still require diagnosis.

## Independent returned-point verification

`reproduce/runtime_reader_verify.jl` runs in a separate guarded Julia process,
reads the native MPS afresh, and computes all original row activities, bound
violations and the objective with `Rational{BigInt}`. These exact operations
use the Float64 input coefficients and returned point; this is an independent
arithmetic check, not an exact-decimal interpretation of the MPS and not a
higher-precision solver iteration. Only the native primal run returns an
`OPTIMAL` point and is eligible for this check.

The maximum original row violation is **9.101841364717531e-9** (row 43,021),
and the maximum column violation is **3.3237683368766608e-12** (column 6,188).
Both are below the configured **1e-7** primal tolerance. The fresh native
certificate also passes. The exactly accumulated objective rounds to
**51425691.76210425**, consistent with the reported **51425691.762104236**.
This verifies primal feasibility and objective evaluation; optimality is
supported by the solver status and agreement with the earlier certified dual
reference, not by a new exact dual certificate.

Reproduce this check using the ordinary worktree project and the same memory
guard (300-second outer limit):

```sh
julia --project=. diagnostics/adaptive-degeneracy/reproduce/runtime_reader_verify.jl \
  .superpowers/adaptive-degeneracy/runtime-reader-full/native-dual \
  .superpowers/adaptive-degeneracy/runtime-reader-full/jump-dual \
  .superpowers/adaptive-degeneracy/runtime-reader-full/native-primal \
  .superpowers/adaptive-degeneracy/runtime-reader-full/jump-primal \
  diagnostics/adaptive-degeneracy/results/runtime-reader-full/exact-verification.toml
```

## Completed matrix

| Reader | Method | Status | Iterations | Refactorizations | Solver seconds |
| --- | --- | --- | ---: | ---: | ---: |
| Native | Primal | OPTIMAL | 106252 | 1341 | 820.263 |
| JuMP | Primal | NUMERICAL_ERROR | 86607 | 1080 | 635.441 |
| Native | Dual | NUMERICAL_ERROR | 23538 | 295 | 73.916 |
| JuMP | Dual | NUMERICAL_ERROR | 6417 | 81 | 18.095 |

All four final runs terminate before their time and iteration limits, without
memory-guard intervention. This is **one successful configuration out of four**,
not general convergence of runtime.mps across reader orders and algorithms.
The dual tolerance-boundary failures and the JuMP phase-I export failure are
separate diagnostic targets. No causal claim about the preceding kernel change
is established by these runs. No production correction is made here.

## Artifacts

Committed text reports and logs are in `results/runtime-reader-full/`, together
with the exact verification, native-primal historical comparison and repeated
native-dual trajectory comparison. `manifest.json` records SHA-256 and sizes of
these outputs, reproduction scripts, policy helpers and local binary captures.
Local artifacts live under `.superpowers/adaptive-degeneracy/runtime-reader-full/`
in `/home/jspitz/.codex/worktrees/adaptive-degeneracy/JSimplex.jl`; they are not
committed. The manifest also records the guard and launcher used. Preserve these
local states for subsequent diagnosis. No Manifest.toml or LocalPreferences.toml
is included in this change.
