# Native dual cleanup reconstruction

This integrates the shared-core repair from experimental commit
`40518ae38ec2aa6bcc1572e819c0e4f170c9545e`. The direct-LU, persistent-incidence
and packed-slot prototypes are not included.

## Cause and repair

Experimental FT full solves of runtime.mps exposed a cleanup failure after
63,786 iterations. Primal and dual bound infeasibilities were within tolerance,
but independent linear-system certification still rejected the state. Primal
cleanup succeeded; dual cleanup failed on both aged and freshly refactorized
bases. A native BTRAN correction removed the large residuals, but cancellation
lost coupled tiny terms in homogeneous equations. Clearing those terms could
also erase information needed by nonzero right-hand sides.

Primal cleanup already reconstructs such local terms within bounded work and
certifies every equation before publishing. An explicit orientation restriction
prevented dual cleanup from using it. The repair applies that existing
reconstruction to a sparse copy of B', then independently checks the original
matrix with the transposed residual calculation. Driver cleanup explicitly
requests reconstruction for both primal and dual solutions.

Working precision, tolerances, the single full-basis correction, reconstruction
work limits and atomic publication are unchanged. A failed or cancelled cleanup
leaves published solution state intact. Ordinary simplex iterations and adaptive
heuristics do not change. Higher precision is not introduced.

## Independent regression and integration verification

The new regression uses a 2-by-2 system independent of runtime.mps. It must
recover `[-tiny, tiny]` from costs `[0, tiny]`, with `tiny=1e-20` for Float32 or
`1e-66` for Float64. Relative comparisons use zero absolute tolerance, so
zeroing the solution cannot pass. Coverage includes all four basis managers,
unchanged costs/basis, original equations, cancellation and exceptions at every
observed boundary, disabled correction budget, checked-solve policy, a bad
factor and nonfinite data.

All 4,722 targeted native cleanup, phase-transfer, residual-policy and driver
checks pass on the integration source with `--compile=min`:

```bash
julia --startup-file=no --compile=min --project=. diagnostics/basis-direct-numerical/reproduce/regression.jl
```

All 1,007 normal-compilation reconstruction and compensated-residual checks
also pass. Allocation assertions are kept separate from `--compile=min`. Local
verification uses one Julia/BLAS thread, disabled package precompile workload,
an 8-GiB virtual-memory cap and the retained RAM/swap guard. Logs are kept under
`.superpowers/basis-core-fixes-integration/`. No manifest, preference file or
binary snapshot is committed.

All 80 external solves also pass (245 assertions): afiro, adlittle, pk1, flugpl
and fast0507, both primal/dual, all four ordinary basis managers, and both
native/Markowitz backends. Every input digest matches the retained manifest;
every solution reaches OPTIMAL with independently checked original primal
feasibility and reference-objective agreement. These integration runs use the
production managers, not the experimental direct-LU replacements.

The existing runner reproduces this matrix:

```bash
julia --startup-file=no --project=. diagnostics/basis-selective-preparation/reproduce/external.jl diagnostics/basis-selective-preparation/reproduce/external-inputs.toml NEW_OUTPUT.toml
```

The manifest references retained local inputs. Results and source fingerprints
are stored in [external.toml](results/external.toml) and
[verification.json](results/verification.json). The integration review found no
actionable issue or dependency on experimental manager code.

## Historical full-run evidence

In the preserved experimental branch, this core repair let both formerly
failing FT prototypes finish the full native-reader runtime solve with certified
OPTIMAL, 64,993 iterations, 823 refactorizations and zero original-model
restarts. Both produced the same primal-vector bits and all 819 logged progress
states. The original-model objective was 51,425,691.76209568 versus the reference
51,425,691.76210457; the original primal constraints were independently checked.
These are historical prototype results, not new full-runtime measurements on
this integration source.

The full report, capture/replay scripts, results and local snapshots remain in
`/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl`, under
`diagnostics/basis-direct-numerical/` and `.superpowers/direct-numerical/`.
Use `git show 40518ae:diagnostics/basis-direct-numerical/README.md` there for the
original reproduction protocol. Those snapshots and prototype runners require
the retained experimental environment; the standalone regression above does not.

This is not a full-project-suite pass. Historical full-suite attempts hit wall
time limits during compilation; fresh verification here uses the relevant
semantic, normal-compilation and external-model suites.
