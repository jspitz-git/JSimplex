# Residual and certificate follow-up probes

Diagnostic-only investigation from `c962506`. No production or test code is
changed. The purpose is to rank further work without changing arithmetic,
tolerances, safeguards, pricing, candidate selection or basis managers.

## Protocol and scope

All jobs use the existing `diagnostics/dual-residual-work/reproduce/run.py`
source-pinning runner, Julia 1.13.0 aarch64, one Julia/BLAS thread, 8 GiB VM,
6 GiB available-RAM floor and 1 GiB swap ceiling. Raw attempts are retained in
`.superpowers/residual-followup-probes`. Each diagnostic has a 600 s outer
guard. The full runtime solve retains infinite solver time and 1M iterations.
Only HH/native320 is solved here. The inspected residual and certificate paths
are shared core code, but these results are not a timing comparison across
managers or proof of benefit for all precisions.

The reproduction scripts make process-local copies or instrumentation of
existing functions. No candidate is installed in the package. Microbenchmarks
warm each arm, alternate order on shared input/storage, assert zero compilation
in timed batches, consume outputs and record allocation bytes. They compare
exact results before timing. Synthetic sparse/dense and zero-heavy controls
include Float32 and Float64. Saved runtime BTRAN vectors are used unchanged;
the medium basis control uses an explicitly labeled random vector.

## Rejected scalar changes

1. Skipping the division when the row residual is exactly zero and its tolerance
   is positive does not help. In runtime states at 10k, 30k and 50k, respectively,
   90.1%, 72.9% and 69.1% of columns have zero residual. Baseline/candidate timing
   ratios are 0.937, 0.943 and 0.931: the candidate is slower despite those zeros.
   Both versions allocate zero bytes. Keep the original loop.
2. Replacing `ldexp`-spelled native underflow thresholds with equal constant
   expressions is neutral/noisy (ratios 0.982–1.034). The original generated LLVM
   already contains the constant thresholds. Float32/64 boundary/nonfinite and
   random comparisons agree, but no production change is justified. This probe
   is in ordinary gradual-underflow mode; it does not establish equivalence of
   the helper rewrite in other floating environments.

See `results/probe1.toml`, `results/thresholds2.toml`, and retained LLVM output.

## Full runtime attribution

`census1` solves runtime to OPTIMAL in 54,591 iterations / 194 refactorizations,
objective 51,425,691.76210138, with verified original feasibility. Event and
selected-state hashes match the established reference:

- events: `6330422d394b22e155e2ecd58fb96fd3a89035a8d86ed6b07722c348bd59ccdb`
- selected states: `1af4c4c85c63a500a038b6101718f969d8a0ab11fb5a978ee2ba77e1621eb743`

| Component | Calls | Inclusive seconds |
|---|---:|---:|
| Borrowed basis matrix, including validation and assembly | 11,430 | 4.008 |
| Basis validation, including calls outside matrix assembly | 12,836 | 0.868 |
| CSC basis assembly | 11,435 | 3.272 |
| Native compensated forward quality | 1,717 | 1.985 |
| Native compensated transposed quality | 10,877 | 7.031 |
| Native dual correction, including nested operations | 11,225 | 21.914 |

Total instrumented solve time is 168.899 s, including 0.047 s compilation and
2.903 s GC. These are nested costs: do not sum the table. Timers subtract nested
bodies for exclusive time but leave timer-hook overhead in the parent. The
solver observer also hashes pivots and selected arrays. This is attribution,
not a before/after solver speed claim.

Direct traversal of the original matrix could avoid part of the 3.272 s basis
copying cost, about 1.94% of this instrumented solve. Even the impossible ideal
of eliminating all assembly *and* all validation would remove only 2.45%.
Validation must remain. A persistent basis cache is therefore still lower
priority; it requires invalidation for basis/matrix mutations and additional
ownership discipline. This follow-up splits costs that the earlier inventory
reported together; it does not reverse that inventory's rejection of an
unsupported global cache.

## Late medium certificate attribution

`certificate-census.jl` continues the existing primal-origin and dual-origin
original-LP handoffs for exactly 32 cleanup iterations, then warms and measures
ten certifications of the final actual workspace. Both cleanup paths use the
primal algorithm. These bounded continuations are deliberately ITERATION_LIMIT,
not new complete medium solves. Their elapsed time includes compilation and
initialization and is separate from the warmed certificate sample.

| Handoff origin | Final iteration | Certificate ms/call | Allocated MB/call | Native filters / 10 certificates | Exact fallback calls |
|---|---:|---:|---:|---:|---:|
| primal | 335,078 | 21.380 | 18.784 | 20 | 0 |
| dual | 212,312 | 21.885 | 18.784 | 20 | 0 |

Both final points pass the current certificate. Per-call attribution is about
8.04–8.07 ms for the initial row enclosure, 5.90–5.98 ms for model-bound checks
exclusive of the native filter, 3.06–3.25 ms for stored-activity consistency
exclusive of the filter, and 3.05–3.20 ms for both native filters combined.
The remaining time includes point/variable checks and timing overhead. Neither
sample measures certification frequency throughout an entire solve, and neither
is a before/after optimization trial. The two origins are different endpoints,
not timing repetitions of one endpoint.

The continuations took 72.574 s (18.835 s compilation) and 65.836 s (zero measured
compilation), respectively. These include cleanup initialization and 32 steps;
do not extrapolate them to the whole multi-hour solve. The historical handoffs
and endpoint sampling also differ from earlier 128/512-step investigations.

## Prioritized next experiments

1. **Reuse native-filter and row-selection scratch.** Each fallback allocates a
   full row-to-slot map, three selected-row accumulator arrays, an uncertainty
   mask and result indices. Reuse owned buffers while reinitializing every
   relevant element. Keep exact fallback unchanged. This applies to certificates
   regardless of the basis manager. The measured 18.784 MB is the whole
   certificate allocation, not an attribution of all bytes to these arrays.
2. **Avoid the full temporary activity-bound array and reduce bound-check data
   movement.** `_legacy_primal_row_consistent` materializes
   `Bound.(@view(primal[n+1:end]))` on fallback. A read-only indexed representation
   could construct the identical Bound on demand without retaining a full
   array. The model-feasibility path also rescans row intervals to collect
   uncertain rows after a failed whole-vector check. Any fusion must preserve
   finite checks, error behavior and independent decisions.
3. **Share native activity aggregates within one certificate, if a paired probe
   supports it.** The two filters do repeat matrix traversal, but together cost
   only about 3.1 ms here. Avoid claiming that sharing eliminates most of the
   21–22 ms certificate cost. Different row sets, bounds and exact fallbacks must
   remain correctly handled. A local lifetime avoids cross-iteration invalidation.
4. **Treat implicit basis traversal as a smaller separate improvement.** It may
   remove coefficient copies in native correction while keeping validation and
   summation order. Its measured ceiling on this runtime is modest; do not
   introduce a global cache to pursue it without an additional paired probe.

No implementation or whole-solver speedup is claimed for these proposals.

## Work and memory review

No production work, allocations, retained memory, scans or solves are added by
this diagnostic-only change. The rejected row branch adds a test per basis
column with a measured regression. The threshold rewrite eliminates no runtime
work in inspected compiled code. Basis assembly is already buffer-reusing;
removing coefficient copies must not remove validation or alter accumulation
order. Certificate scratch reuse would reduce repeated allocations while
retaining O(rows + ambiguous rows) storage per workspace; that tradeoff must be
measured, bounded, and checked across phase transitions and aliases.

A shared native row sum within a single certificate could serve independent
model-bound and stored-activity decisions. Any future implementation must keep
each bound check, finite-coefficient checks, exact fallback, term order and
outward rounding. No cross-iteration cached verdict is proposed.

## Preserved unsuccessful launch

`thresholds1` never launched Julia: the single-process assertion rejected it
while `census1` was active. An unprivileged sandbox process listing had omitted
the host Julia process. The existing guard prevented concurrent numerical
execution. `thresholds2` is the completed retry; the refused launch is not a
completed measurement. No source was edited during a pinned run.

## Final audit

Four jobs completed with exit zero and unchanged pinned sources; the refused
launch is recorded separately. Full logs contain no test failure/error markers.
The production and test trees remain identical to `c962506`. Compact reports,
process records, log files, generated LLVM and an integrity summary are stored
in `results/`. Independent review found no blockers and explicitly reviewed
computational work and memory; see `results/review.md`. No full project test
suite was rerun because no production/test code was modified.
