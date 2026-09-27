# Compilation investigation

This directory records sequential compilation measurements after the legacy
stability validation. The adopted change simplifies hardware-only method signatures; arithmetic and
supported numerical policy behavior are unchanged. Discarded overrides remain
diagnostic evidence only.
See `report.md` for findings and limitations and `measurements.json` for data.

## Reproduction

Use Julia 1.13.0, the same installed dependencies (MathOptInterface 1.54.0), one
Julia thread and one BLAS thread. Each command starts a fresh Julia process;
package caches are retained. Run commands sequentially. The recorded environment
uses a 24 GiB virtual address-space limit. Compilation allocations are cumulative,
not peak resident memory. Do not use these small workloads to estimate large-LP
solve performance.

From a checked-out revision, with this directory supplied as `artifacts`:

```bash
export JULIA_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
julia --startup-file=no --project=. "$artifacts/cold-solve-compatible.jl" primal cold.toml
julia --startup-file=no --project=. --trace-compile=recovery.trace --trace-compile-timing "$artifacts/recovery-compile.jl" recovery.toml
julia --startup-file=no --project=. "$artifacts/callback-compile.jl" callbacks.toml
```

The recovery and callback workloads require the modernized internal APIs. The
compatible cold script omits the `simplex_strategy` keyword only on older
revisions that do not expose it; their default is the original simplex path.
The original `cold-solve.jl` explicitly selects legacy strategy and was used for
the three newer revisions. Both cold scripts otherwise use identical settings.
All AFIRO samples assert optimal status, the independently known objective, and
original-input primal feasibility. All observed samples take nine pivots and
one refactorization. Recovery runs include the unchanged existing 30-check test
file, including precision ceilings, shared budgets, cancellation, and original
callback exception identity.

`@timed @eval` includes first-call compilation in AFIRO timings. Recovery uses
`@timed include(...)` around the original test file. Trace timings include
instrumentation and describe compilation requests, including their compilation
dependencies; they are not exclusive costs of a method body. Cold measurements
are single observations per revision with two warm repetitions, not statistical
estimates. The callback workload deliberately changes only the observer type;
it is separate from the user's ordinary public solve without an observer.

Full local traces and harness logs are preserved in
`.superpowers/compilation/` in the stability worktree. The committed JSON includes
trace hashes and the largest trace entries. Historical source snapshots are
read-only experiment inputs; their manifests use the same dependency versions.

## Source variants

The signature experiment applies `simple-signatures.patch` (use
`git apply --unidiff-zero`) to production source
`d5472bc` (the documentation-only `72c8c1f` has the same production source). It
is the adopted compiler repair. The original-source BigFloat assertion trial
uses `recovery-type-experiment.jl` and was deliberately interrupted; it is not
a production modification. Both interruptions are explicitly recorded with
nonzero exit status and stack logs. Do not treat them as passed tests.

On the adopted branch, run the targeted numerical validation with:

```bash
julia --startup-file=no --project=. "$artifacts/validate-guards.jl"
```

The external 64-solve corpus uses the same input preparation and independent
references as [`../reproduce/README.md`](../reproduce/README.md). Its new results
are included in this directory's measurements, separately from the earlier
stability revision.
