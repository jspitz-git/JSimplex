# Dual allocation count and selection costs

Baseline: `9c67ab2e3f28af338ed5d8a061d6c661a759b6db`. Diagnostic-only changes.
Configuration: Float64, HH/native320, dual, steepest-edge, legacy,
partial pricing disabled, default presolve/scaling, relaxed integrality.
Julia 1.13.0 aarch64, one Julia/BLAS thread. All numerical processes ran
sequentially through the existing 8 GiB VM / available RAM >=6 GiB /
swap <=1 GiB guard. The solver's time limit was infinite; the external guard
bounded diagnostic jobs. `runtime.mps` completed; medium is a 4,000-iteration
prefix, not a convergence or medium full-performance result.

## Measurement boundaries

- Plain solves time `solve` after input reading and afiro warmup. They include
  presolve, setup, iterations, recovery, postsolve and internal certification.
  The separate original-feasibility assertion is outside the timed interval.
- `Profile.Allocs` samples a second full solve with probability 0.0001.
  Its enclosing scope also includes the external feasibility assertion and
  report construction. Sample counts classify allocation origins; byte
  estimates of rare large buffers are not reliable. Sampled solve wall time
  is not plain solver timing. GC allocation counters and sampled event counts
  are different measurements: do not normalize sampled estimates to force
  agreement with the exact total.
- The census wraps original function bodies in diagnostic `try/finally`
  counters. Inclusive times contain nested calls; exclusive times subtract
  their measured payload. Do not add overlapping inclusive rows. Recursive dual-iteration calls also
  overlap with the same label, so their inclusive sum can exceed solve totals. Counters
  can change compilation/inlining and execution cost. Empty-probe calibration
  estimates instrumentation overhead; it is not an exact correction.
- Observer work (hashes, windows and selection-snapshot serialization) has its
  own bucket. The first census captures snapshots; the repeated runtime does
  not. Observer overhead is not ordinary dual arithmetic. Tiny boxed logging
  or diagnostic objects can still appear outside the principal kernels.
- Per-phase labels are the **last diagnostic event phase**, with cleanup origin
  retained across primal/dual notifications. They are not exact lifecycle
  budgets: auxiliary return and cleanup initialization lack all necessary
  event boundaries. Use kernel totals for quantitative conclusions.
- Selector replay uses the same saved basis states and steepest-edge weights.
  Dantzig, Devex and steepest-edge are evaluated in rotated order. Devex and
  steepest-edge share the weighted scoring kernel; this comparison excludes
  different weight maintenance and changed solver trajectories. The snapshot
  workspace has no valid current factorization and is only used for selection.

## Reproduction and evidence

Raw attempts remain under `.superpowers/dual-allocation-cost/` in the
`simplex-shared-work` checkout. `run.py` pins source, environment, scripts and
inputs, rejects another live Julia process, and records guard/process status.
Reports and compact audited evidence are under `results/`.

The first allocation attempt completed a valid plain solve, then failed before
sampling: Julia 1.13 requires `Profile.Allocs.start(;sample_rate=...)` despite a
positional example in its docstring. `allocations-invalid-v1.jl` and the failed
attempt are preserved. This was a diagnostic API error, not a solver failure.

No production function, safeguard, tolerance, arithmetic precision, candidate
selection or basis-update rule was changed. Review of computational work and
memory found no production-cost change. Diagnostic instrumentation deliberately
adds work and is never installed in the package.

## Runtime findings

Two plain solves took 162.21 and 165.12 s, with 95,735,849 and 95,735,847
allocation events, 13.662 GB allocated, and 2.85–2.88 s in GC. These are
cumulative allocations, not retained memory or peak RSS. Both returned OPTIMAL
at 54,591 iterations and 194 refactorizations, objective 51,425,691.76210138,
and passed the original-model primal-feasibility check. This current baseline
is not the user's earlier 52,097-iteration build; the counts are not an exact
reproduction of the earlier version.

The two instrumented solves took 172.66 and 174.75 s. They have identical
pivot and state SHA-256 fingerprints to the prior final baseline measurement
in `diagnostics/simplex-data-movement/results/runtime-final.toml`:

- events: `6330422d394b22e155e2ecd58fb96fd3a89035a8d86ed6b07722c348bd59ccdb`
- states: `1af4c4c85c63a500a038b6101718f969d8a0ab11fb5a978ee2ba77e1621eb743`

### Small allocations

Only **four** `_stabilize_small_dual_pivot!` calls entered the expensive path.
They allocated **approximately 59.147 million objects / 3.408 GB** in each census, about 62% of
the plain allocation-event total. They took **3.04–4.10 s**, including GC.
The other 53,385 invocations returned from the cheap guard.

The four repairs call `_refined_dual_prices` twice each (256 and 512 bits).
They convert matrix coefficients to BigFloat, refine a transposed basis solve,
and compute all reduced costs. Arithmetic and scoped precision lookup create
many small backing buffers/tuples. This is an exceptional numerical certificate,
not a per-iteration precision conversion. The basis factor itself remains in
Float64. Eliminating these allocations cannot explain or cure a multi-hour
slowdown by itself.

Of 8,035 allocation samples, 7,993 had size <=128 bytes. Small-pivot stacks
accounted for 5,873 samples; presolve for 2,041; other stacks for 121. Presolve
uses exact `Rational{BigInt}` transformations; it is another large source of
small objects, shared by primal and dual rather than specific to dual steps.
Sample estimates are not exact event shares; the counters above establish
the exceptional repair cost directly.

The ordinary leaving selector, tableau pricing, Harris test, weight maintenance,
and actual bound-flip application allocated **zero** objects in both censuses.
BFRT allocated only **12 objects / 1,442,488 bytes**, for buffer growth. HH basis
updates, recomputation and postsolve have other allocation costs; this is not
an assertion that the whole dual iteration is allocation-free.

### Selection and flipping costs

These are aggregate instrumented **inclusive** times over the full runtime
trajectory; the Harris row is nested inside ratio selection.

| Operation | Calls | Time (two runs) | Allocation events |
|---|---:|---:|---:|
| Leaving-variable selection | 53,438 | 4.10–4.19 s | 0 |
| Tableau pricing | 66,564 | 7.74–7.83 s | 0 |
| Ratio selection, including BFRT/Harris | 53,451 | 10.23–10.35 s | 12 |
| Harris fallback alone (included above) | 18,018 | 3.07–3.12 s | 0 |
| Nonempty bound-flip application | 10,098 | 4.50–4.55 s | 0 |
| Weight maintenance with nested checks/solves | 53,389 | 7.00–7.15 s | 0 |

BFRT's own exclusive work takes 7.13–7.19 s, beyond the nested Harris calls.
The 10,098 flip batches change 19,468 variable bounds. Their aggregate basis
solves take 3.84–3.88 s of the 4.50–4.55 s application total. Empty flip calls
(43,291) take about 0.009 s in total.

Do not call the weight row a pure steepest-edge result: despite the configured
`:steepest_edge`, only 5,752 calls execute `update_dse!`. The legacy numerical
weight-consistency safeguard can move to Devex; later weighted maintenance is
not a full DSE solve per pivot. `update_dse!` itself totals 0.53–0.55 s here.
Across all contexts the tagged `weight_ftran` count is 7,285 (0.96–0.98 s),
including initialization/recovery callers. Those rows overlap the weight row.
The plain/census run suppresses log messages, so the exact switching iteration
and reason are not retained; do not infer them from configured options.

### Larger costs and priorities

In the same census, ordinary FTRAN and BTRAN wrappers take 21.4 and 24.3 s.
Row residuals take 15.6 s (76,232 calls), direction residuals 13.0 s (53,942),
and finite-workspace scans 6.5–6.7 s (214,772). Native correction takes about
24.0 s inclusive, 21.2 s exclusive (11,225 calls). Some of these are nested:
**do not sum their inclusive values as independent solver percentages**.

The evidence supports examining repeated native scans/correction work and
basis-solve data movement before prioritizing the exceptional BigFloat object
count. A future change must preserve certificate strength and numerical
trajectory where promised. Possible investigation targets are redundant scan
reuse with explicit invalidation, reduced correction work, or reusable wide
scratch preserving both independent certificates—not removing safeguards or
simply narrowing their precision.

## Medium prefix cross-check

A separate 4,000-iteration dual prefix reached its intended ITERATION_LIMIT
in 63.97 s, with 12 refactorizations and no compilation in the timed solve.
It allocated 168.49 million objects / 11.382 GB overall, but the instrumented
dual-iteration scope accounted for only 0.393 million objects, including
0.375 million observer objects. There were **no expensive small-pivot repairs**.
The first 1,000-iteration window includes setup and accounts for 168.46 million
objects; later 1,000-iteration windows have only about 7,650 allocation events.
Thus a large overall allocation count is not evidence of an allocating
ordinary iteration, even on this larger problem. This census does not separately
time presolve, so the entire setup residual must not be labelled presolve.

Leaving selection took 1.55 s, tableau pricing 2.98 s, BFRT 3.35 s and Harris
was never called in this prefix. All 4,000 steps used a nonempty flip batch:
5.40 s inclusive (2.58 s in the aggregate basis solve). All 4,000 weight updates
used DSE: 5.39 s including finite checks, with `update_dse!` itself 4.02 s and
its basis solves 2.58 s. This demonstrates why a fixed ratio from runtime's
mixed DSE/Devex path cannot predict medium's full-run pricing cost. These
instrumented inclusive timings also contain nested observer/probe work.

No full medium solve or final certificate is claimed by this prefix.

## Fixed-state selector replay

Nine rotated samples of 20 calls per rule, after warming the timed batch
(second replay, with a third replay validating unrounded whole-batch counters):

| Stored state | Dantzig | Devex scoring | Steepest-edge scoring |
|---|---:|---:|---:|
| runtime iteration 1,000 | 27.28 us | 29.67 us | 29.14 us |
| runtime iteration 10,000 | 47.00 us | 55.92 us | 52.97 us |
| runtime iteration 30,000 | 66.30 us | 69.44 us | 70.34 us |
| medium iteration 1,000 | 330.60 us | 350.61 us | 352.31 us |

All 108 whole batches in the third replay have exactly zero allocated bytes,
zero allocation events and zero compilation time
(the script asserts the latter). Devex and steepest-edge use identical saved
weights and the same kernel; their timing differences are measurement noise,
not evidence of distinct scoring algorithms. Their selected rows agree on
every snapshot. Dantzig selects different rows on all three runtime snapshots.
A cheaper scoring pass therefore does not establish a faster complete solve.
The medium snapshot has 360,982 basis rows versus runtime's 28,453, so raw
per-call cost must not be extrapolated between these models.

The first replay attempt detected residual compilation in its timed loop and
stopped before reporting samples. The corrected script warms the exact typed
batch function. All attempts and earlier scripts are preserved. The third replay records whole
batch counters to rule out rounding in the per-call byte report.

## Reproduce

From this experimental checkout (no other Julia process running):

```sh
python3 diagnostics/dual-allocation-cost/reproduce/run.py /tmp/dual-alloc-new 1200 -O2 diagnostics/dual-allocation-cost/reproduce/allocations.jl /home/jspitz/mps/runtime.mps /tmp/dual-alloc-new/runtime
python3 diagnostics/dual-allocation-cost/reproduce/run.py /tmp/dual-census-new 2100 -O2 diagnostics/dual-allocation-cost/reproduce/census.jl /tmp/dual-census-new/cost
python3 diagnostics/dual-allocation-cost/reproduce/run.py /tmp/dual-replay-new 600 -O2 diagnostics/dual-allocation-cost/reproduce/selection-replay.jl /tmp/dual-census-new /tmp/dual-replay-new/results.toml
```

Output directories must be new. The runner currently uses the locally preserved
Julia wrapper/guard and environments documented in its source; these paths must
exist. Raw snapshot binaries and the local manifest/preferences are not committed.

## Verification and review

`python3 diagnostics/dual-allocation-cost/reproduce/audit.py` checks the archived
runtime fingerprints, exact repair-count bounds, allocation-free measured
kernels, intended medium prefix termination, all 108 whole selector batches,
expected successful/failed process outcomes and unchanged production sources.
The maximum RSS of the census process (including medium) was 3,196,528 KiB
(about 3.05 GiB), below the configured guard; all successful attempts report
unchanged pinned sources. Compilation and the two harness failures are retained
separately rather than represented as solver regressions.

Independent review by `data_movement_review` verified quantitative tables,
allocation-stack grouping, source provenance and fingerprints. Review and
execution prompted corrections to HH option preservation, observer/cleanup attribution,
residual compilation in replay, integer rounding of byte counters and recursive
inclusive-cost interpretation. No production computational-work, allocation or
retained-memory increase is introduced by this diagnostic-only change. No
whole-project regression suite was rerun because production and tests are
unchanged; the numerical evidence here is the full runtime trajectories and
bounded medium prefix described above.
