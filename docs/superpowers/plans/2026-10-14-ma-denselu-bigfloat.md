# MA native DenseLU BigFloat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task, with fresh independent reviews at the stated boundaries. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce transient BigFloat product allocation in native DenseLU forward and transpose solves without changing numerical results, owners or failure effects.

**Architecture:** A local JSimplex specialization keeps original LU/permutation/triangular control flow and replaces only multiplication intermediates with one private MA output. Ordinary subtraction/division still publish fresh scalar owners. The generic backend stays the fallback.

**Tech Stack:** Julia1.13, native LinearAlgebra LU, BigFloat/MPFR, installed MutableArithmetics1.8.1 SaQfc, existing bounded Python guards.

**Spec:** `docs/superpowers/specs/2026-10-14-ma-denselu-bigfloat-design.md`.

## Global constraints

- Current step MA-Q is documentation/source review only: no Julia/query/parser/import/compile/numerics, candidate or production/env/test/CI edits.
- Master6f68e24 and MASTER-PROFILE evidence stay frozen; beforecopies resolve only six current predecessor bindings.
- Exact BigFloat/native DenseLU only; no Markowitz/HH/DSE/cleanup omission reopening, no factorization algorithm, eta updates, safeguard or tolerance changes.
- n>=16, matching scalar rounding modes, exact supported storage; unsupported calls use unchanged whole original path before mutation.
- One private product; no mutation of published scalar leaves, fused operation, persistent state, new full scan or hidden fallback retry.
- Standing human approval permits short experiments without another permission question. It does not replace a concrete immutable numerical admission. Maximum120s/process,360s/qualification sequence; no hours, no automatic retry.
- One Julia/BLAS thread,2GiB heap hint,8GiB VM,6GiB availableRAM,1GiB swap; compiled-modules=existing. Fresh host boot/start_ticks/command/full158groups ANDsessions plus new groups; never PID-only.
- Production MA is currently NOT a direct dependency. Candidate-only environment may use already installed MA; no package install/network/Pkg.resolve in preparation. Future integration must explicitly add the direct dependency and test clean-load compatibility; do not rely on MOI's transitive dependency.

## Review focus

1. Scoped/global rounding mismatch and mixed stored/ambient precision: whole fallback or exact same output bits/precision; tests in Task2.
2. Shared LU/RHS/destination scalar leaves and retained prior outputs: no mutation of old numeric owners; tests in Task2.
3. Diagonal/zero-heavy factors whose triangular wrapper changes branch: preserve actual source path including unit divisions; tests in Task2.
4. Singular/dimension/pivot failures after partial writes: same exception and destination prefix, no restart; tests in Task2.
5. Small/empty/unsupported calls and dependency-load overhead: no scratch or hidden scans; controls in Tasks2–3.

### Task1 — MA-R: isolated offline candidate and exact reference

**Files:** create `diagnostics/simplex-core-architecture/results/MA-R/{reference.jl,candidate.jl,tests.jl,fixtures.toml,source-map.json,plan.md}`; leave actual src/test/Project/Manifest unchanged.

**Interfaces:** diagnostic module `MADenseProbe`, with
`reference_forward!(dest,backend,rhs)`, `reference_transpose!(dest,backend,rhs)`
calling original ldiv!, and `candidate_forward!`/`candidate_transpose!` same return
contract. Private eligibility `_dense_ma_eligible(dest,backend,rhs)::Bool` and
`_dense_ma_mul!(product::BigFloat,a::BigFloat,b::BigFloat)::BigFloat` (MA.operate_to!).
Local LU/triangular helpers accept the one product parameter, never own global state.
No extension of production or LinearAlgebra methods in the diagnostic module.

- [ ] Read fresh installed LU/factorization/triangular/mpfr/MA source and master pins. Refuse drift without an explicit new source reconciliation; do not regenerate old evidence.
- [ ] Copy the original complete backend reference exactly. Record inverse replacements for local helper names/qualification and each selected product expression. Preserve all original subtraction/division/assignment/control-flow order, including initial `oA \ B[i]` operations before multiplication where applicable. Pin `istriu`, `uppertriangular`, `lowertriangular`, `uplo_char`, `isunit_char`, `_wrapperop`, `_unwrap_at` and the reached `_ldiv!` normalization definitions.
- [ ] Mirror square three-argument ldiv!, pivot loops and the full normalized triangular path. Source-map every branch to installed lines; do not precompute all istriu results or hoist scans across mutations. Implement local equivalents of pivot loops; private stdlib normalization calls in the prototype must be named/pinned and are not a compatibility promise.
- [ ] Implement the O(1) n16/shape/storage/rounding predicate. Scalar alias checks are unnecessary for scratch because product is fresh and never published; all original container alias behavior must still be preserved. No blanket deep-copy of inputs, ownership scan or matrix-finiteness scan.
- [ ] Add direct MA usage to a diagnostic-only environment using the installed pinned package; keep reference/candidate imports identical. Save unexecuted source and tests, exact source inverse and work ledger. Review candidate independently before any Julia. If equivalence needs global replacement or hidden retries, stop this route rather than expanding it.

### Task2 — MA-S: correctness and bounded component cost qualification

**Files:** create new `results/MA-S/{driver.jl,launcher.py,audit.py,pins.json,admission.md}` only after Task1 acceptance. Copy generic guards into this new directory; never execute old stored scripts. Future exact commands use the pinned existing wrapper and private environment, with stage index1/2/3 and exclusive run output path. Driver/command/raw schema and complete calls must be frozen in admission before launch.

**Interfaces:** consumes the four MADenseProbe entry points and immutable fixture file. Produces one preserved RED record, correctness records, all paired cost windows, independent review and acceptance decision.

- [ ] Prepare a failing route-contract test: original module lacks `_dense_ma_eligible` and candidate entry points; baseline correctness still passes. RED must explicitly mean missing optimization-route coverage, not an original numerical defect. Run RED once under the same admitted guarded sequence, record expected failure, never turn a generic launch/import error into RED success.
- [ ] Define nonsymmetric dyadic matrices deterministically. For n>=2: diagonal `n+2+i/16`; dense off-diagonal `(-1)^(i+j)*(1+mod(3i+5j,7))/64`; zero-heavy retains only `abs(i-j)==1` plus `(i,j)==(n,1)` off-diagonals. RHS `(-1)^i*(1+i/16)`. Use n0 empty and n1 diagonal. LU factor creation outside solve-cost windows, same factors read-only on both sides; independent input copies where required.
- [ ] Correctness grid: bits128/256/512 × n0/1/2/8/15/16/32/64 × dense/zero-heavy × F/B. For n16 and bits256 additionally identity, nontrivial row permutation of a nonsymmetric matrix, cancellation, positive/negative zeros, Inf/NaN operands, zero pivots first/middle/last, invalid pivot index, wrong dimensions, rhs view, destination===rhs, distinct containers sharing BigFloat leaves, copied PFI backend, and retained outputs across second calls. Prepare explicit exceptional fixtures in MA-R from private copies of the n16 factor: zero diagonal at1/8/16, ipiv[8]=17, RHS length15, destination length17; never mutate the shared measured factor. For remaining cancellation/nonfinite/alias cases freeze exact literal operands, owner graphs and expected routes in MA-R; MA-S may only bind these accepted fixtures, not select replacements after runtime. Reference-capture class/prefix during the admitted correctness run; never retune a failed fixture. Exact arithmetic changes from zero/nonfinite inputs must not be elided.
- [ ] At n16 test stored precision128/512 under ambient256 and stored256 under ambient128/512. Test globally matching RoundNearest/Down/Up/ToZero, and nested scoped mismatch with restored global/ambient state. Gatefalse tests require original helper delegation and zero product-scratch creation, using diagnostic-only instrumentation. Compare finite exact Rational{BigInt} tokens plus precision/signbit; NaN classification/sign and signed infinities separately. Preserve factor bits/ipiv, RHS bits and retained leaf identities/values. Compare exception type/message and destination post-unwind tokens; no tests mask a partial write.
- [ ] Cost schedule fixed now:36targets = bits128/256/512 × n16/32/64 × dense/zero-heavy × F/B. Controls16 = n0/1/2/8/15 at256 dense × F/B (10), scoped RoundUp/global RoundNearest at n32 × F/B (2), Float64/native and Rational/native n32 dense × F/B (4). These52cases use three independent serial processes, each3warm+7measured alternating reference/candidate pairs,4whole backend calls/window:12480cost calls maximum. First process alone executes correctness/RED; freeze their exact counts in admission. Maximum3×120s including termination; stop on first unexpected failure. All setup/scratch and routing inside full-call window; factor construction/reset and output checks outside, reset identical for both sides. Separate first-call compile/import time. No profiler inside cost windows.
- [ ] Require all correctness flags and measured compile/recompile0. Retain GC/outliers. Targets: median bytes/events strictly lower in every process, pooled paired-time median<=0.95, each process median<1, at least15/21 measured pairs faster, independently for every target. Controls: no scratch on fallback, no additional vector scans/solves; bytes/events no increase, time median increase<=max(5% of reference,0.2microseconds/call), each process<=max(10%,0.4microseconds/call). These prospective noise budgets are not significance claims. All52cases must pass; otherwise preserve the outcome and reject this exact route for promotion. No threshold change/rerun/tuning under consumed schedule.
- [ ] Independently review numerical equivalence, whole F/B costs, cold dependency cost and work/memory. Product counts from source do not substitute for allocation measurements or complete backend call accounting. Publish failure as failure; a lack of improvement does not imply all MA strategies impossible.

### Task3 — conditional production integration and public validation

**Files:** only after Task2 passes, proposed changes `src/dense_bigfloat_ma.jl`, two BigFloat-specific backend overloads in `src/factorization.jl`, one import/include in `src/JSimplex.jl`, direct MA entry in `Project.toml`, `test/dense_bigfloat_ma_tests.jl` and its `test/runtests.jl` include. No user Manifest/LocalPreferences edits. All existing generic/native Float32/64/Q methods unchanged.

**Interfaces:** proposed production overloads retain `_backend_forward_solve!` and
`_backend_transpose_solve!` signatures with exact BigFloat storage. New private
helpers remain local; no exported API or backend layout change. Planned direct
MA UUID d8a4904e-b15c-11e9-3269-09a3773c0cb0,compat ="=1.8.1" initially; widen only after separate version review and tests.
The initial supported Julia implementation is the pinned1.13 source; Julia compat
alone does not establish that private stdlib helpers or source-derived loops match
future versions. Freeze a supported Julia range and admission source checks before
production integration; an unsupported version uses the generic route.

- [ ] Prepare separate RED/GREEN/master integration admission; exact candidate diff and tests, immutable per-stage source and environment pins, short guards. Standing numerical permission remains, but do not automatically launch from this plan-only request.
- [ ] Permanent tests use representative Task2 ownership, rounding, exceptional and boundary fixtures, plus unchanged `test/factorization_tests.jl`, `test/refactorization_factor_tests.jl`, `test/refactorization_failure_tests.jl`. No growing tracing arrays, production hit counters or extra permanent solver corpus.
- [ ] Check local helper compatibility with supported Julia/MA versions. Preserve stdlib-derived license attribution. Unsupported library API shape must fail admission or retain original route; never silently use a different arithmetic sequence. Clean isolated dependency environment load is a separate explicit test; no blanket Pkg update or changing user env to hide issues.
- [ ] Qualify actual PFI integration at zero/one/three updates, copy/refactor and forward/transpose alias boundaries. Existing eta arithmetic unchanged; all new work included. Freeze exact fixtures/call budget before launch.
- [ ] New bounded public reference/candidate comparison on afiro and sc50a BigFloat256, no profiler, verbose=false identically on both sides; three interleaved warm pairs then7measured pairs per model. Compare statuses, exact endpoints/precision, objective, iterations/refactors, input preservation and allocations. Freeze source/env/process schedule in its own admission; do not rerun MASTER-PROFILE. Require median time reduction>=5% and bytes/events reduction for both, no measured compile/recompile. These new settings are not directly comparable timings with the old verbose profile.
- [ ] If any integration/cost gate fails, preserve raw and do not merge. If all pass, fresh independent production work/memory review, separate PASS closure/exact staged blobs, merge/push under standing permission and verify actual master with a small admitted check. Full-suite/large-HH claim remains open; CI stays disabled.

## This plan's completion

MA-Q completes when design, plan, source-bound evidence and independent review are
accepted and published. It does not implement MA-R/S or declare performance gains.
Next concrete step is Task1 offline preparation; the broader plan remains open.
