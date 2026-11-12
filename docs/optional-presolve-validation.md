# Optional presolve integration validation

Validation was performed on ARM64 with Julia 1.13.0, one Julia/BLAS thread,
against master `85778e3b3f999cf91def2ad04fee257b1b1527e3`. Numerical jobs ran
serially while holding all 97 suite locks. No runtime, medium or largo LP solve
was started for this integration.

## Functional coverage

* Optional option/MOI/copy tests: 9981 assertions. Defaults, all flag combinations,
  previous positional constructors, recovery/phase/precision/refinement copies,
  unchanged tolerances, unsupported scalar rejection and MOI lifecycle.
* Primal phase-II witness tests: 162 assertions, Float32/64/BigFloat, including a
  real artificial variable, requested/unrequested witnesses, identity mismatch,
  all three flags and unchanged iteration/refactorization counts.
* Core integration: 921 assertions covering disabled identity/fixed setup cost,
  actual reductions, owned metadata, all 8 combinations, min/max, primal/dual,
  scaling, original-model certification, stop/decline and empty histories.
* Real populated base-history composition: 476 assertions; signed multiple
  merging: 54. Both include original cleanup and original optimality checks.
* Mixed 256-bit stored/96-bit ambient transformation and restoration: 17 assertions,
  using a known exact reduced witness independently checked before restoration.
* Missing-dual fallback through the actual public caller: 15 assertions. Original
  recovery must run and certify; no unchecked optional hint can publish OPTIMAL.
* Unequal-cost capacity dominance: 60 assertions, both objective senses and all
  three floating types, with the donor selection and original certificate checked.

The new tests are included in `test/runtests.jl`. This was targeted integration
validation; the complete repository test suite was not run.

## Preserved negative evidence and limits

Two initial small Float32 **no-presolve references** ended in NUMERICAL_ERROR at
unchanged default tolerances. Their complete model data are retained locally in
`diagnostics/optional-presolve-integration/results/development-failures.json`,
with the original failure logs. They were not retried. Revised positive fixtures
use different input with a representable optimum; they do not loosen tolerance.

A stored 256/ambient 96 BigFloat no-presolve reference also failed. Its precise
internal reject message was not captured by the original assertion, so no exact
cause is claimed. The replacement mixed-precision test checks transformation,
owned data, primal feasibility and the original dual witness directly, without
another simplex solve. Existing original-objective evaluation conservatively
declines that narrower-ambient case; this guard remains unchanged. Successful
mixed-precision simplex execution on that reference is **not** established.

Initial zero-allocation test expectations were corrected after measuring a fixed
144-byte immutable-result box. The returned result is identical to the base and
no optional index/cache/history is constructed; the cost does not grow between
2 and 64 columns, across Float32/64/BigFloat. A recovery-test callback initially
attempted to mutate an immutable progress context; only the test was corrected
to replace it with a context sharing its original fields. These development
failures and logs were retained.

## Computational-work review

The independent read-only review found no remaining material unnecessary scans,
basis solves, model copies or retained intermediate models. It identified two
issues that were fixed before integration: duplicate proportional grouping when
merging was a no-op, and losing the requested primal phase-II witness, which
otherwise forced another complete original solve.

Grouping is now shared until the CSC changes; scalar exact caches can survive a
merge, but support groups cannot. The enabled setup budgets and cache limits
remain those of the verified prototypes. Postsolve retains maps, shapes and
owned scalar undo data, not intermediate models, caches or factors.

Enabled primal witness export reuses an existing certificate dual, with no
additional BTRAN. The mapped original primal/witness is independently checked
to preserve the internal certificate contract. Those extra final scans and
allocation are intentional, occur only for requested optional witnesses, and
are followed by the existing original-model cleanup/certificate boundary.

## Existing regressions and default-off comparison

The affected existing options, presolve, postsolve/basis, primal certificate,
primal simplex and MOI suites produced 1481 passes and one failure. The failure
is a stale exact `MOI.RawStatusString` expectation in `test/moi/result_tests.jl:320`.
A separate execution against the original master snapshot confirmed identical
NUMERICAL_ERROR, zero results and the same prefixed message before and after
integration. That unrelated test and production message were left unchanged.

Four afiro/sc50a primal/dual HH/native240/Devex solves with all optional flags off
matched original master in objective bits, full primal SHA, status, iterations
and refactorizations. All-three-enabled solves also returned OPTIMAL and passed
original primal feasibility and objective comparison. These small standard
models supplement the constructed cases that prove actual optional reductions.

| Model / algorithm | Iterations / refactors | Original bytes | Off bytes | Original ms | Off ms |
|---|---:|---:|---:|---:|---:|
| afiro dual |9 /1|748952|758680|0.9885|0.8343|
| afiro primal |8 /1|733984|739824|0.6075|0.6000|
| sc50a dual |36 /1|2045496|2046328|1.2745|1.2496|
| sc50a primal |35 /1|2058624|2053152|1.2830|1.2878|

Measured calls were warmed, with zero reported compilation and GC. Each timing
is only one very short sample and establishes no speedup or regression. Options
storage increased from 128 to 136 bytes. This is not a cold-start/package
compilation benchmark, nor a large-model whole-solve performance claim.

## Focused enabled-work measurements

For simultaneous merge/dominance when merging finds no equal-cost pair, sharing
grouping reduces support/signature passes from 2 to 1. Outputs and work statistics
matched. Five warmed samples per case, medians:

| Rejected-capacity setup | Separate grouping ms / allocated bytes | Shared grouping ms / allocated bytes |
|---|---:|---:|
| Sparse 128x512, 1024 nnz, 16 groups |141.187 /156223080|117.319 /155490696|
| Dense 32x64, 2048 nnz, 1 group |21.151 /36409832|18.669 /35603480|

Sparse GC medians were 59.783/33.297 ms; dense GC was zero. These are temporary
allocated bytes, not retained memory. The time difference includes GC and has
limited sampling; the demonstrated work saving is one grouping pass. This is
presolve setup, not solver iteration timing.

The extra mapped-primal/witness checks were measured separately, with 128 rows
and columns: sparse 128 nnz: 4.6 microseconds, dense 16384 nnz: 225 microseconds, both
8720 allocated bytes and zero new basis solves (nine warmed samples, medians).
The checks are final certification work; accepted simplex iterations gain no
extra scans. Higher-precision certification costs were not benchmarked here.

Local raw reports, source/reference hashes and failure evidence are under
`diagnostics/optional-presolve-integration/results/`. Functional tests are
tracked in `test/optional_*tests.jl`; the full standard runner includes them.
