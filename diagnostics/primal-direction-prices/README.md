# Legacy primal direction-price consistency

This sequential worktree builds on 99f6494. The preceding correlated-pivot and
per-bound snap fixes are described in ../primal-runtime-stability/README.md.
The changes here concern selected reduced prices; they do not establish that
runtime.mps converges.

## Reproduced inconsistency

The saved Suhl–Suhl phase-I state alternates two bases after a fresh native
factorization and rebuilt DSE weights. Before accepted exchanges, the cached
price is -43.8501894, while the selected FTRAN direction implies -8.65157184 or
-6.25253906. These observations use basic costs from before the exchange.
Snapshot scratch alone is insufficient evidence: another solve can overwrite it.

The native Float32/Float64 legacy path now compares the selected cached price
with c_j - c_B' B^-1 a_j before the ratio test. The allowance includes the active
price tolerance, native accumulation error and relative agreement tolerance.
Phase I retains its zero price tolerance, including genuinely tiny costs.
Unsupported arithmetic modes or unrepresentable probes defer to existing checks.
The probe neither widens arithmetic nor publishes modified costs or directions.
This is a consistency check, not an independent exact reduced-cost certificate.
Disagreement uses the existing bounded candidate rejection and native refresh.
Adaptive and generic arithmetic paths retain their behavior.

The check must precede the ratio test. A first, later placement broke the captured
cycle but subsequently reported an uncertified unbounded ray. Regressions also
showed that a false price could cause an unnecessary bound flip. The early check
covers both cases.

## Evidence and limits

- Corrupted selected-price regression: 48 failing assertions before the check.
- False unbounded/flip regression: 56 failing assertions before early placement.
- Focused tests: 1,498 assertions, including 336 new checks across Float32/Float64
  and all four managers, tiny prices and cancellation. Two review-suggested
  cases cover multi-term rounding differences and exactly one price-triggered
  refresh of a basis with update history (112 additional assertions).
- Broader semantic tests: 2,698 assertions using compile=min. This is not a full
  project-suite pass; compilation limits from the preceding investigation remain.
- Captured SS reference continuation: 64 steps, no repeated complete basis/state,
  no numerical-error termination. It still performs 64 refactorizations and makes
  no material phase-I objective progress. This is not an exact pricing-cache replay.
- Fresh PFI: TIME_LIMIT after 300 seconds, 7,533 iterations and 2,288
  refactorizations, no original-model restart or numerical-error termination.
  Phase-I objective remains approximately 605,519.5025. Its stagnation persists.

- Native residual/allocation tests: 125 assertions with normal compilation.
- External corpus: 80 optimal LP relaxations, each checked for original primal
  feasibility and reference objective agreement; 245 assertions. Both algorithms,
  all four managers, native and Markowitz backends.

Fresh FT and SS also reach their 300-second limits without numerical failure or
original-model restart. FT completes 6,220 iterations / 1,253 refactorizations;
SS completes 3,930 / 546. Neither makes material phase-I progress. In particular,
SS rejects 51,396 candidates: eliminating an inconsistent accepted step does not
guarantee an effective replacement pivot.

BG likewise reaches TIME_LIMIT after 300 seconds, 6,499 iterations and 932
refactorizations, without restart or numerical error. No manager completes phase I.

| Manager | Limit (s) | Iterations | Refactorizations |
| --- | ---: | ---: | ---: |
| PFI | 300 | 7,533 | 2,288 |
| Forrest–Tomlin | 300 | 6,220 | 1,253 |
| Suhl–Suhl | 300 | 3,930 | 546 |
| Bartels–Golub | 300 | 6,499 | 932 |

These limits verify the absence of the early failure only over the tested horizon.
They do not establish convergence or absence of other cycles. Timings include
rare-path compilation and are not controlled performance comparisons.

An independent read-only review found no concrete production defect or blocking
issue. Its two minor coverage suggestions are covered by the additional tests
above. The latest verification totals 4,566 assertions, including the 80 external
solves; captured continuation steps are observations, not additional assertions.

The remaining phase-I stagnation requires further algorithm work. These checks
prevent demonstrated inconsistent steps; adding more rejection alone is not a
convergence strategy.

## Reproduction

The input, options and source hashes are recorded in the result TOML files.
The input is /home/jspitz/mps/runtime.mps, SHA-256
`d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68`.
Use the capture and reference-continuation scripts in
../primal-runtime-stability/reproduce/. Snapshot binaries remain local.
External cases and expected objectives use
../basis-selective-preparation/reproduce/external-inputs.toml.

All numerical runs are sequential, with one Julia/BLAS thread, an 8 GiB virtual
memory limit, a wall watchdog, and an owned-process watchdog requiring 6 GiB
available RAM and at most 1 GiB swap use. Local precompile workloads remain off;
these are untracked environment preferences, not package default changes.
A separate Julia process briefly exceeded 13 GiB RSS during the first trial;
the watchdog stopped only the owned warmup, before a fresh runtime result existed.
The other process subsequently disappeared without intervention.
