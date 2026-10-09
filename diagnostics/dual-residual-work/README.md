# Native compensated residual data movement

Baseline production `9c67ab2`, diagnostic baseline `ce84212`. This follows
`diagnostics/dual-allocation-cost`: native correction and repeated residual
scans are more promising time targets than the exceptional BigFloat allocation
count alone.

## Investigation and bounded change

`_compensated_quality_term!` performs five accumulator-array loads and stores
per nonzero product: residual, compensation, error sum, positive scale, and
term count. For transposed CSC multiplication, all terms in one column update
the same output component. The new native Float32/Float64 specialization holds
these accumulators in local scalars and stores them once per column, preserving
exact term order, FMA, TwoSum, zero-product skipping and final Dot2Err enclosure.
No reassociation, fast-math, tolerance or precision change is introduced.

Empty and singleton columns retain the old per-term helper. This matters for
basis matrices rich in slack/identity columns. The first local-only prototype
was slower on runtime's early sparse state; the structural short-column path
removed that measured regression. The original prototype patch and measurements
are retained. Selection of the specialized path occurs inside the quality evaluator only
for transposed work. Forward calls use the unchanged generic accumulator
directly; dense/non-native transpose calls use an inlined generic fallback.

There is no new matrix scan, basis solve, coefficient copy, heap allocation,
persistent scratch field or retained cache. Work reduction scales with the
number of active terms per multi-entry transposed CSC column. Forward work is
not intentionally reduced.

## Why other apparent duplication remains

The row residual following successful `_try_native_dual_correction!` is not
unconditionally redundant. The correction validates its private trial, then
calls the stop callback and publishes a `:correction` event. Those callbacks
can mutate the matrix, basis, tolerance or published vector. The caller's
recheck observes that later state. Removing it without a stronger callback
contract would weaken existing behavior; it is retained.

Likewise, repeated finite-workspace checks surround distinct primal/dual/weight
updates and recovery boundaries. This change does not introduce a global
validity cache whose invalidation would need to cover those mutations.

## Validation protocol

One numerical Julia process, one Julia/BLAS thread, existing 8 GiB virtual-memory
limit / 6 GiB available-RAM floor / 1 GiB swap ceiling. Production precision
is unchanged; semantic coverage includes other supported precisions.
Input reading and explicit final original-feasibility checks are outside solve
timing. The full runtime comparison uses HH/native320, dual, steepest-edge,
legacy, partial pricing off, default presolve/scaling, relaxed integrality,
infinite solver time limit and 1M iteration limit. The outer diagnostic guard
is bounded. No excluded large model is solved or factorized.

- Differential tests compare every scratch field to the original per-term
  helper on Float32/64, rectangular/empty shapes, explicit zeros, subnormals,
  cancellation, overflow, infinities and NaNs.
- Paired kernel measurements use nine alternating warmed batches of ten calls on the same scratch storage;
  full quality result and all scratch fields must match. Includes sparse and
  dense CSC, ordinary dense matrices, zero-heavy vectors, empty/singleton
  columns and saved runtime/medium bases. Runtime batches vary `rhs[1]`, so those
  timed cases use snapshot-derived vectors with modified RHS, not exact
  checkpoint acceptance replays (the initial equality check uses stored RHS).
  Medium uses a random test vector;
  this is not a captured correction or a full medium timing estimate.
- Runtime order is baseline, candidate, candidate, baseline in separate guarded
  processes. The same diagnostic observer records hashes; all completed pivots
  and selected state arrays every 80 iterations must match the established baseline. Compilation,
  GC, allocation totals and original feasibility are reported separately.
- Targeted integration, wider semantic regressions, 100 external combinations
  (five models x five managers x two algorithms x two backends), and a guarded
  full project-suite attempt are recorded separately.

Scripts: `reproduce/`. Raw non-overwritten attempts:
`.superpowers/dual-residual-work/`. Final results and the independent review are recorded below.

## User-reported prior improvement

During this investigation the user reported that the preceding merged changes
reduced their full dual runtime solve from 332 s to 297 s: 35 s (10.54%). This is
external user evidence, not a timing sample from this harness. The unmerged
local-accumulator candidate described here was not included in that comparison.

## Focused results and scope

The final shared-storage benchmark (`results/final-paired-results.toml`) measures
the complete native quality evaluator against its frozen pre-change body, not
only the accumulation loop. Ratios below are baseline time / candidate time;
values greater than one favor the candidate.

| Transposed case | Ratio |
|---|---:|
| Synthetic sparse CSC, Float32/Float64 | 1.390–1.391 |
| Dense CSC, Float32/Float64 | 2.457–2.509 |
| Runtime-derived states at 1k/10k/30k/50k | 1.070 / 1.391 / 1.329 / 1.307 |
| Medium basis, random vector | 1.065 |
| Entirely zero vectors | 0.988–0.994 |

Forward control ratios are 0.992–1.015; ordinary dense-matrix transpose controls
are 1.000–1.002. All candidate batches have exactly zero bytes and allocation
events. These kernel measurements do not establish a whole-solver speedup or
uniform improvement for every input. In particular, the zero-vector control
shows a small unfavorable difference. Empty/singleton columns bypass the local
accumulators without adding any scan to classify vector density.

## Preserved unsuccessful and superseded attempts

The initial targeted harness had an incorrect relative include path and failed
before executing its intended tests; `targeted-invalid-v1.jl` preserves it.
The corrected harness subsequently passed all 1,315 checks. Early kernel
prototypes and measurements are retained to document the short-column and
forward-dispatch investigations. The original dispatch benchmark associated
different scratch storage with each arm; the final benchmark uses the same
storage and separately checks correctness with independent scratch objects.

An external-validation run of a superseded implementation was intentionally
stopped. SIGTERM did not immediately terminate its Julia process. A shell
sequence mistakenly continued after a failed termination assertion and edited
the source before that process had exited. The single-process guard rejected a
new numerical launch; the old owned process group was then terminated and its
exit verified. That entire external attempt is excluded: exit 137 and
`sources_unchanged=false` are recorded in `external-process.json`, with the
explanation in `external-intentional-stop.json`. This was a harness/control
error, not evidence of a numerical failure. The final verification starts from
fresh output directories and frozen sources.

The external regression script is loaded through a Julia `-e` expression,
which the runner's direct-file argument discovery does not see. Its SHA-256 is
therefore checked separately against baseline Git content before and after
that final job (`external-script-provenance.json`). No source or script edits
are permitted during the final sequence.

## Full runtime comparison

| Order | Build | Solve seconds | Compilation seconds | GC seconds |
|---|---|---:|---:|---:|
| 1 | Baseline | 170.693 | 0.052 | 2.897 |
| 2 | Candidate | 169.957 | 0.050 | 2.884 |
| 3 | Candidate | 172.755 | 0.049 | 2.968 |
| 4 | Baseline | 173.865 | 0.047 | 2.923 |

Baseline mean is 172.279 s; candidate mean is 171.356 s, a nominal 0.54%
reduction. This difference is smaller than within-build variation and **does
not establish a whole-solver speedup**. The focused kernel improvement is the
reason to retain the small optimization; no multi-second solver benefit is
claimed from this sample.

All four solves return OPTIMAL, objective 51,425,691.76210138, with verified
original primal feasibility, 54,591 iterations and 194 refactorizations.
Every recorded event count matches, including 11,379 correction attempts and
11,227 accepted corrections. Pivot and sampled-state fingerprints match:

- Events: `6330422d394b22e155e2ecd58fb96fd3a89035a8d86ed6b07722c348bd59ccdb`
- States: `1af4c4c85c63a500a038b6101718f969d8a0ab11fb5a978ee2ba77e1621eb743`

Whole solves allocate approximately 96.009 million objects and 13.671 GB each;
differences of a few objects/tens of kilobytes are immaterial. These cumulative
allocation totals include setup and exceptional repair allocations; they are
not retained memory. The initial warmup and process startup are outside the
solve timer. Separate process resource logs preserve their overhead.

## Final verification and review

- 1,315 targeted checks passed with normal compilation, including the 266 new
  differential checks for all accumulator fields and exceptional Float32/64
  inputs.
- 15,689 semantic checks passed with `--compile=min`, covering primal/dual,
  phase transitions, recovery, cleanup and supported precision entry paths.
- All 100 unique external combinations passed original primal feasibility and
  reference-objective checks. Their objectives and iteration counts exactly
  match the previous certified `simplex-data-movement` external report. This
  does not substitute for pivot fingerprints on those external problems.
- Four complete runtime solves and 23 paired kernel cases passed as above.
- The full normal-compilation project suite reached the 300-second guard while
  Julia was in type inference/compilation for
  `test/legacy_primal_direction_price_tests.jl:157`. The buffered log also contains **25 failed assertions and 2 test errors** in
  `primal_bound_snap_tests.jl`, `primal_candidate_retry_tests.jl` and
  `primal_retry_pricing_tests.jl`. Exit 75 therefore does not classify this
  attempt as a clean timeout. The baseline/candidate triage below identifies matching pre-existing failures;
  no complete project-suite pass is claimed. The full log and
  process report are preserved.

Every final process reports unchanged pinned sources. The audit checks exact
job identities, baseline source hashes against `9c67ab2`, common candidate
source hashes, input identities, all runtime event counts and fingerprints,
and exact external configuration coverage. `results/final-provenance.json`
archives the union of pinned file hashes and each preflight identity.
The runner used for final validation is preserved as `run-final-v1.py`; after
all numerical processes exited, `run.py` was amended to explicitly pin the
external script previously checked separately. No production code changed
between final validation and commit.

Independent review by `data_movement_review` found no unnecessary added scans,
basis solves, allocations or retained memory, and no numerical blocker in the
specialization. It verified the focused benchmark against frozen baseline
code, exact arithmetic order, generic fallbacks, runtime evidence and audit
coverage. The only added dispatch is the transposed CSC specialization; it
removes repeated accumulator-array traffic without introducing a persistent
cache. The tiny zero-vector timing penalty and inconclusive whole-solver
timing are retained in the assessment.

Reproduce the final raw-data audit from the original experimental checkout:

```sh
python3 diagnostics/dual-residual-work/reproduce/audit.py
```

`reproduce/final.py` requires a fresh final output directory and the preserved
local environments/snapshots. Do not overwrite completed attempts or launch it
alongside another numerical Julia process. Manifest and local preferences are
not committed.

## Existing full-suite failures: baseline triage

The final suite's buffered output must be read in full: it contains failed
assertions in addition to its eventual compilation timeout. An initial
status interpretation looked only at the guard/stack output and missed these
messages; this was corrected before integration.

A separate sequential guarded replay of the three affected files, using
`--compile=min`, produced **313 passes, 25 failures and 2 errors on both
unmodified master `9c67ab2` and this candidate**. The normalized failure
locations, expressions, evaluated values and exception messages match exactly
(`results/legacy-triage-audit.json`). Both runs record unchanged sources.

Most expectations require a particular snapped value, rejection or alternate
entering column for a tolerated structural-bound fixture. Two require the
specific `:refactor_residual` event, although the refactorization-count assertion
passes. The implementation already has feasible-point preservation/recovery
paths that can invalidate these historical trajectory expectations. Whether
each fixture needs updating or exposes a separate core issue requires further
investigation; this performance change does not alter those tests or declare
them resolved. In particular, reproducing a failure on baseline establishes
that it was not introduced here, not that its underlying behavior is correct.

The bounded optimization's evidence is the exact accumulator comparisons,
targeted numerical regressions, certified external runs, unchanged runtime
fingerprints and unchanged baseline failure signatures. Full-project health
remains an explicit limitation.

## Follow-up

The 25 legacy assertions and two test errors above are resolved by the
[test-fixture repair](../legacy-suite-repair/README.md). It separates mandatory
fixed-variable snapping from allowed nonfixed retention and corrects the
pivot-refresh diagnostic expectation. Production code is unchanged; the
historical failed-run evidence in this directory is preserved.
