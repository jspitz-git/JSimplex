# Separate legacy dual numerical recovery from progress heuristics

Base solver revision: `570e9eeba212b6f577b0e67aec1d349d73938b8e`.
The preceding diagnostic commit is `7e5da5c` and changes no solver code.

## Contract and scope

Numerical correctness must not depend on enabling an adaptive strategy.
The core checks and repairs numerical state; adaptive policies decide how to
change the optimization trajectory in response to slow progress. This change
removes three legacy dual heuristics already superseded by optional adaptive
policies:

- Switching steepest-edge pricing to Dantzig after 256 zero dual steps.
- Perturbing working costs after 1,024 zero dual steps.
- Growing the effective refactorization interval above the configured value
  after productive cycles.

Zero dual steps can improve primal feasibility. Their count alone neither
proves stagnation nor diagnoses an inaccurate basis solve. A healthy cycle also
does not authorize overriding the configured legacy update ceiling.

Residual checks, native corrections, numerical retries, ratio-test repairs,
invalid-weight recovery through a fresh Devex reference, and final original-LP
certification remain active. Repeated inaccurate updated solves still shorten
the refactorization interval. Clean cycles recover a shortened interval toward
the configured value, never above it. Bounded working-cost repairs needed for
dual feasibility in the ratio test remain distinct from cost perturbations
triggered solely by a zero-step count. Original-cost cleanup is unchanged.

The existing adaptive stagnation, perturbation and refactorization mechanisms
are unchanged. This is a bounded removal of legacy heuristics, not a redesign or
validation of the entire adaptive profile. Optional numerical implementations
still need their own evidence before promotion to the common core. No new
precision promotion or routine higher-precision arithmetic is introduced.

The workspace layout and its diagnostic counters are retained so existing
local snapshots remain readable. Historical reports describe the source
revision on which their experiments ran; their earlier heuristic results are
not overwritten by this change.

## Validation method

Run one numerical process at a time with Julia 1.13.0 on aarch64, one Julia
thread and one BLAS thread. The existing wrapper limits virtual memory to 8 GiB;
the guard terminates only its owned process group below 6 GiB available RAM or
above 1 GiB swap. Local precompile preferences are preserved.

`test/dual_core_policy_tests.jl` exercises real pivots. Before the production
change, its 256 checks included 62 expected failures: pricing/cost mutations
despite improving feasibility and update chains exceeding the configured
ceiling. The implementation is checked alongside numerical-recovery tests,
including deliberately corrupted factors. Adaptive mechanism tests verify
that removing the legacy triggers does not disable their separate consumers.

The `pk1` regression now explicitly selects Dantzig with a 2,000-iteration
budget. This preserves an optimality check without pretending that fixed
steepest-edge has acquired an anti-degeneracy guarantee. The model report
separately records the bounded fixed-steepest-edge behavior instead of hiding
that performance consequence.

From the checkout, through the guarded Julia wrapper:

```sh
julia --project=. diagnostics/dual-core-policy/reproduce/models.jl pk1 OUTPUT.toml
julia --project=. diagnostics/dual-core-policy/reproduce/models.jl medium OUTPUT.toml
julia --project=. diagnostics/dual-core-policy/reproduce/models.jl external OUTPUT.toml
```

Each command needs a fresh output path. `medium` uses the recorded input hash,
PFI, native factorization, steepest-edge, legacy strategy, interval 80, relaxed
integrality, a 300-second solver limit and a 1,000,000-step cap. `pk1` compares
fixed steepest-edge and explicit Dantzig for all four managers. The external
mode covers the other four inputs of the existing selective-preparation
manifest with all four managers and native dual simplex. `pk1` is kept in its
own bounded report because losing its legacy fallback can affect termination.

Endpoint equation checks describe the last observed working workspace, not a
certificate of original-input feasibility. Optimal results receive a separate
original-model primal feasibility check. A time or iteration limit is never
reported as a solved LP.

## Observed results

The targeted dual/core/numerical-recovery set passes 1,905 checks. The broader
semantic set passes 8,486 checks, including primal stability regressions and
adaptive stagnation/perturbation/refactorization consumers. These are 10,391
executed checks, not a claim about the complete project suite. Both sets run
with `--compile=min`; their output is preserved in `results/`.

With interval 80, all four managers reach the 2,000-iteration cap on `pk1`
with fixed steepest-edge pricing. All four solve it with explicit Dantzig in
607 iterations, objective zero, and a successful original-primal certificate.
The last working points also pass the stored-row equation check in all eight
runs. Thus this change deliberately gives up the earlier implicit rescue of
fixed steepest-edge; it does not claim to cure that degeneracy.

The 300-second `medium.mps` run ends `TIME_LIMIT` after 24,561 pivots, still in
the auxiliary-bound phase. Observed pricing stays steepest-edge and the largest
effective refactorization interval is 80. The last working point has primal
infeasibility sum `158828.61111161724`, zero dual infeasibility, and zero
compensated absolute equation residual; the independent stored-row check
passes. The event report contains one dual phase and one auxiliary phase, with
no perturbation, correction, repair, or precision-boost event. This does not
establish convergence, later handoff behavior, or stability of an unobserved
million-iteration continuation. Timings are not a controlled performance
comparison with earlier diagnostic runs.

All 16 additional external runs (afiro, adlittle, flugpl and fast0507, each with
PFI, Forrest–Tomlin, Suhl–Suhl and Bartels–Golub) return `OPTIMAL`, match their
manifest reference objectives, and pass original-primal certification. The
independent `reproduce/check-results.py` verifies these reference comparisons,
all eight `pk1` records, the medium endpoint checks, and the common solver
source hash. Its output is `results/model-validation.json`.

A read-only independent review found no blocking implementation issue. It
confirmed that numerical recovery and adaptive consumers remain separate;
stale README descriptions identified by that review were corrected. Review of
the model harness also emphasized that successful script execution alone is
not a passed optimization test, hence the independent reference checks above.

The standard `julia --project=. test/runtests.jl` entry point was also attempted
with normal compilation. The 240-second wall-time guard stopped it (exit 75)
in LLVM machine-code scheduling while including
`test/primal_initial_tolerance_tests.jl:3`. No test assertion failure was
recorded before interruption. That file passes in the completed semantic set
with `--compile=min`. The full suite is therefore **not completed**, and no
full-suite success is claimed. See `results/full-suite.log`.
