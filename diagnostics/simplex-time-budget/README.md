# Medium simplex time budget

Status: all four reference/census comparisons completed and audited; sampling
completed for the two prefixes and is unavailable for cleanup. Full generated
tables are in [RESULTS.md](RESULTS.md), with raw evidence in `results/`. Production sources are unchanged from master
`fe839aa72171d7496c9c931d9393278448c7317e`. This is a diagnostic investigation,
not a solver optimization. See the implementation plan in
`docs/superpowers/plans/2026-10-10-simplex-time-budget.md`.

## Scope

Four exact measurement slices: the first 4,000 dual iterations, the first 2,000
primal iterations, and 256 cleanup steps from each historical medium handoff.
The fresh prefixes use Float64, HH/native320, steepest-edge, legacy, full pricing,
default presolve/scaling and relaxed integrality. Cleanup retains its saved
HH/native160 options; the case name identifies the historical solve's origin,
not necessarily the algorithm executing cleanup. These are not interval pairs. The phase-I primal prefix also has artificial
columns (360,982 × 239,057, 1,014,403 nonzeros), whereas the dual auxiliary
prefix has 360,982 × 186,497, 961,843 nonzeros. Their per-step ratio is not a
controlled same-matrix kernel speed comparison.
All numerical processes run sequentially with one Julia/BLAS thread under the
existing 8 GiB VM / 6 GiB available-RAM floor / 1 GiB swap guard, with a
2G Julia heap-size hint. This hint can affect GC timing and is part of the
measurement environment, not an assumption about the user’s full-run setup.

These slices do **not** account for the user's complete seven-hour run. In the
historical record, primal phase II spans iterations 71,062–335,046 and dual phase
II 35,705–212,280. The available event snapshots are not complete checkpoints of
all pricing state. Reconstructing missing state would create a different replay
and would not close this coverage gap. No full-run or other-solver speed ratio is
inferred from the selected slices. The timings below quantify current code on
these inputs and starting states, not the cost of all old snapshots.

## Measurement boundaries

Each case has a short 32-step warmup, an unwrapped reference, a warmup after
installing diagnostic wrappers, and a census. The prefixes additionally have
an independent sampling run. Cleanup sampling was abandoned after the first
attempt stalled in profiler operation; see the preserved attempt below.
Reading/deserialization is timed separately. Solve timings include presolve,
initialization, iterations and any recovery encountered. Cleanup initialization
and its defensive copy of the supplied basis are inside the cleanup timing.
`compile_seconds` and GC are reported separately, but are included in wall time.
Process resource logs include all warmups, loading, compilation, report writing
and input preparation; the difference from solve timers is not labelled entirely
as compilation.

The reference also has a diagnostic observer: it hashes ordered pivot/step data
and full numerical states every 128 completed steps and at return. This overhead
is shared across modes and separately timed in the census. It is not production
solver work. All completed modes must have identical status, iteration count,
event counters and event/state hashes. The missing cleanup profiles are not
counted as successful comparisons. All slices intentionally stop at an
iteration limit; they are not claims of a new medium optimum or certificate.

The census wraps selected original method bodies with exception-safe counters.
Inclusive times overlap. Exclusive values subtract nested measured payloads;
their time/byte/allocation sums must equal the outer counter exactly. The
`outer_unattributed` bucket and iteration bodies retain unwrapped work and probe
bookkeeping. Function wrapping may change inlining, escape analysis and GC;
empty-probe calibration is not an exact correction. Absolute census times must
be compared against the reference before drawing cost conclusions.

The ordinary basis bucket does not include every solve: direct solves inside
numerical-recovery helpers stay in that recovery helper's exclusive time. Nor
is the whole `recompute!` bucket a pure factor solve: it also rebuilds nonbasic
contributions, primal values, dual RHS and reduced costs. The first 128-step
window includes setup and must not be interpreted as an ordinary iteration.

Sampling uses Julia Profile with a 5 ms nominal delay. It materially perturbs
this workload (the first dual sample is 1.79 times reference wall time), so its
stacks provide a qualitative cross-check, not exact baseline percentages.
The flat profile is inclusive across inlined frames; do not sum its rows.
Cleanup sampling did not complete and supplies no time percentage or stack
attribution. The prefix overhead must not be generalized to cleanup.

## Architectural findings in the measured slices

- Legacy primal reconstructs the point and reduced costs after each accepted
  step (`primal_simplex.jl`, call to `recompute!`). Reconstruction traverses
  nonbasic contributions, performs FTRAN and BTRAN, and rebuilds prices. This
  is additional to entering-direction and pricing-weight solves.
- `_finite_workspace` traverses primal values, reduced costs, costs and, for
  DSE, pricing weights. The dual prefix records 16,004 calls for 4,000 steps.
  With 547,479 working variables, four full traversals per call imply roughly
  35 billion logical scalar visits (about 280 GB of Float64 element accesses).
  These are source-derived logical counts, **not measured DRAM traffic**;
  caches, compiler transformations and early exits matter.
- The ordinary dual row and direction residual checks each execute once per
  prefix step. They are independent numerical checks, not demonstrated redundant
  work. A future optimization must prove reuse/fusion and invalidation correct.
- Most allocation events in the dual prefix are one-time presolve work:
  168,091,971 objects and 8.173 GB in the census. Sampling attributes part of
  this work to exact rational arithmetic in aggregation and bound propagation.
  A large aggregate object count does not establish allocating ordinary pivot
  loops or repeated high-precision basis recovery.
- Primal Harris can test bound snapping for multiple improving pivot contenders.
  Its full-row validation path is conditional; call counts alone must not be
  converted to full-scan counts without checking which path executed.

## Reproduction

`reproduce/sequence.py` runs four cases with `run.py`, refusing existing output
folders and another live Julia process. Reports remain under
`.superpowers/time-budget/CASE-1`. `summarize.py` exports only cases whose process
finished successfully with unchanged pins and all available matching trajectories
(three for prefixes, two for cleanup). `resume_cleanup.py` records the diagnostic
method change and preserves the original failed attempt.
Failed or incomplete attempts remain local and are not counted as completed.
The local environment, historical handoffs and wrapper/depot paths must exist;
they are not portable package test fixtures. Manifest and preferences are not
committed. Exact source, script and input hashes are retained in preflight files. Shared
external depots and the Julia installation are not byte-for-byte pinned; Julia
version, Manifest hash and launcher hash are recorded. Reproduction requires
new output directories; the scripts deliberately refuse to overwrite attempts.

## Interpretation and next implementation targets

1. **Repeated reconstruction and validation in primal.** The 2,000-step prefix
   calls `recompute!` 2,003 times and the instrumented solve gateway 10,006 times.
   Reconstruction alone, excluding nested gateway solves and refactorization,
   costs 9.902 s in the census. Sampling additionally locates substantial work
   in `_finish_legacy_primal_point!` → `_legacy_primal_reconstruction_feasible`
   → compensated equation residual. This latter check is unwrapped and remains
   in `iteration_other`; its exact time is not claimed. Preserving validated
   intermediate results or an audited incremental reconstruction would be an
   architectural change with numerical-risk testing, not just a loop edit.
2. **Repeated full scans in dual.** The finite-workspace checks cost 4.589 s;
   row and direction residual checks cost 1.801 and 2.609 s in the census.
   The latter two check different equations and are not interchangeable.
   Candidates for reuse must establish which vectors changed since validation,
   including callback access. Neither looser tolerances nor removed residual
   checks are justified by these measurements.
3. **Basis operations and whole-vector pricing/updates.** The gateway costs
   10.161 s for dual and 9.418 s for primal. These combine multiple solve roles;
   they are not all FTRAN or all BTRAN. Direct recovery solves may be accounted
   inside recovery instead. Dual full pricing/ratio selection remains material,
   but no single measured kernel explains an order-of-magnitude gap. Optimizing
   a small kernel cannot yield that gap at unchanged operation frequency.
4. **Presolve allocation and GC.** Exact aggregation/propagation is a separate
   setup target. Its allocation count is large but its duration is seconds on
   these runs, not hours. Refactorization timing also contains substantial GC
   (dual 3.753 of 4.169 s; primal 1.762 of 1.983 s), so it is incorrect to label
   the entire observed refactorization duration LU arithmetic. Allocation
   reduction and arithmetic acceleration need separate experiments.

These priorities are evidence for further experiments, not demonstrated speedups.
No production code, arithmetic precision, safeguards or tolerances were changed.
The review found repeated full-data work worth investigating, but has not proven
it all unnecessary. Diagnostic wrappers add work and can alter compilation and
allocation behavior; the dual census has 3,997 more allocation events than the
reference despite zero-allocation empty probes. Sampling adds roughly 75–79%
wall time to both prefixes. Do not interpret these instrumentation effects as
production regressions or optimizations.

## Preserved sampling failure

`cleanup-dual-1` completed its reference in 91.053 s with 256 steps. During the
subsequent Profile run, the main Julia thread stopped accumulating CPU at
4:41 while another Julia thread accumulated over ten minutes of CPU. Two
recorded observations ten seconds apart show unchanged main-thread CPU, output
and I/O and ten more CPU seconds in the helper. RSS was about 2.88 GiB, swap
zero. This is evidence of a stall associated with sampling, not a numerical
failure or a measured long simplex iteration. No stack debugger was available;
the exact internal profiler defect is unverified.

Only that verified diagnostic process group was stopped (exit137). The runner
recorded unchanged source pins; all files were retained. Cleanup was then
repeated in `cleanup-dual-2` without starting Profile, followed by the first
`cleanup-primal-1` with the same reference/census method. Original `measure.jl`
is preserved; `measure_counted.jl` differs only by omitting the sampling call
and its comparison. This is a diagnostic fallback, not a production change.

## Cleanup entry versus repeated work

For the dual-origin replay, the reference is 87.552 s (the preserved earlier
reference was 91.053 s with identical fingerprints). The census is 100.304 s.
GC accounts for 16.066 s of the reference and 27.110 s of the census; most of
this wall-time difference is GC rather than new numerical work. Both report
2,780,762 allocation events. This does not establish unbiased individual timings.

The census records 19,696 gateway calls for 256 cleanup steps. The projection
helper takes 32.223 s **inclusive**; primal entering selection takes 44.987 s
**inclusive**, including 36.580 s in nested calls. Source inspection identifies
lazy steepest-edge weight computation for invalid improving-column weights as
the solve path inside entering selection. These are major entry costs on a
restored, non-unit basis, not representative ordinary per-step solve counts.
The event counter records only two `refactor_other` and one `refactor_limit`,
but the direct method counter records 16 refactorizations: projection performs
additional direct refactorizations that do not publish those events. Likewise,
its direct column replacements are not all in `_replace_pivot_column!`.
Therefore event counters alone undercount basis work during cleanup entry.

The complete post-initialization 128-step reference window takes 10.930 s,
about 85.4 ms/step. Point preservation occurs 256 times; its helper takes 7.254 s
inclusive in the census. The selected-row native filter costs only 0.434 s
across 515 calls here. Although its source traverses all nonzeros when needed,
a row index for that particular filter is not a leading optimization target
on this evidence. Repeated point reconstruction/certification and initial weight
construction deserve separate investigation.

## Review scope and coverage

Production `src/`, `test/` and `Project.toml` are unchanged from the pinned
master. This is not a production optimization, and no new solver regression
suite is claimed. Validation covers nested/exception-safe counter accounting,
zero-allocation empty probes, completed-process/source gates, trajectory and
state equivalence, zero measured compilation, and actual saved option metadata.
Independent review checks the attribution and audit as well as diagnostic cost.

The observed repeated scans and reconstruction are concrete work, but this
investigation does not prove that any safeguard is redundant. No arithmetic
precision or tolerance was raised to improve a comparison, and no coefficient
was dropped. Instrumentation overhead and GC variation are material and retained
in the report. The absent long phase-II measurement, unavailable cleanup sample
profiles, single paired timing per slice and HH-only scope limit generalization.
Other managers share core call sites but their time proportions were not measured
here. A complete explanation of the seven-hour versus ten-minute comparison
still requires the actual long phase-II trajectory, not extrapolated prefixes.

The primal-origin cleanup reference is 81.412 s; its census is 89.817 s.
It also executes primal cleanup and preserves the point in every one of the
256 steps. The full post-initialization 128-step block is 11.443 s (89.4 ms/step).
Its census records 18,698 gateway calls, 9 refactorizations, 18.309 s inclusive
projection and 47.484 s inclusive entering selection. Both cleanup cases are
consistent with expensive entry work plus more expensive per-step point upkeep.
They do not establish that the missing long reduced-model phase II has the same
cost or behavior.

The audit confirms all four reference/census trajectory and state comparisons,
two additional successful profile comparisons, a matching repeated cleanup
reference, 256 actual cleanup steps from each saved prior counter, actual
HH/native160 snapshot options, and unchanged production source pins. The
interrupted sampling attempt is explicitly non-successful; its available
reference is retained but its missing profile and census are not fabricated.

Final independent review found no blocker to committing this diagnostic evidence.
See [REVIEW.md](REVIEW.md).
