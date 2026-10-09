# Shared simplex feasibility work

First production change in the shared-work investigation. Baseline: `6b891d0`.
This change applies to both primal and dual simplex and is independent of the
basis manager. It does not enable indexed pricing, partial pricing or any
adaptive policy.

## Change and numerical contract

The ordinary iteration loops used the full primal-infeasibility summary solely
to ask whether its sum exceeded the primal tolerance. The summary adds only
individual violations strictly greater than that tolerance. With validated
positive, finite Float32/Float64 tolerance, the first included violation already
makes the answer false; later positive terms cannot reverse that answer.

The new predicate compares the same lower/upper violations and can stop at the
first violation. Feasible points still inspect every basic variable. It avoids
the summary's sum/count bookkeeping, including in that worst-case traversal.
It does not treat a sum of individually tolerated violations as infeasible.
Only two ordinary-loop call sites change. Summaries used for reporting,
recovery and certification retain their original implementation.

Other arithmetic types retain the original sum-based implementation. In
particular, BigFloat continues to use the original ambient-precision behavior;
there are no conversions or precision changes. NaN/Inf decision compatibility
is covered separately from the unchanged whole-workspace finiteness check.
No pivot choice, tolerance, factorization or numerical safeguard changes.

## Work and memory review

Frequency: once per ordinary primal/dual loop, before deciding whether to
continue. Original work is O(number of basics), including both bound checks and
summary bookkeeping. New hardware-float work is O(first violating basic), up to
the same O(number of basics) for feasible points. This predicate does not inspect
matrix nonzeros or the factor update chain. There are no new solves, copies,
full-array passes, caches or retained per-workspace storage. No invalidation or
aliasing protocol is added. Both old and new measured kernels allocate zero
bytes. The independent review found no unnecessary work or retained-memory cost.

## Measurement protocol

- Julia 1.13.0, aarch64, one Julia/BLAS thread, `-O1` for warmed kernels and solve
  checks; semantic regressions use `--compile=min`. Workload precompilation is
  disabled. Existing 8 GiB VM / 6 GiB free-RAM / 1 GiB swap guard.
- Kernel experiment: 4,132 and 360,982 basics, Float32/Float64, feasible input and
  first/middle/last violating basic. Nine alternating measurements per case,
  40 calls per measurement after warmup. This is a scan-only synthetic fixture;
  it never factors the large synthetic matrix. No factor graph is needed by the
  measured predicate.
- `candidate_kind=production` invokes the actual installed helper. The additional
  dual-feasibility predicate in the probe is diagnostic only and is not adopted:
  its feasible-case measurements did not establish a useful improvement.
- Visit counts are analytical loop bounds, not hardware counter measurements.
  Early-exit timings at the first entry are near the measurement/optimizer floor;
  do not interpret them as reliable nanosecond latency or a huge speedup factor.
- Paired solves use Float64, steepest-edge, legacy, full pricing, relaxed
  integrality and default presolve/scaling. All five managers solve fast0507 with
  native refactorization, interval 80, both algorithms. HH/native320 additionally
  checks the first 2,000 medium primal / 4,000 medium dual iterations and the full
  runtime dual solution. Medium prefixes do not establish behavior in later
  phases or full-medium convergence.
- Compare ordered completed pivot/flip choice-and-step payloads and aggregate
  numerical event counts (the payload hash does not include event tags),
  full selected numerical/basis state every 80 iterations and at the final
  observed workspace, final structural-primal hash, iterations/refactorizations,
  objective and original-model feasibility. Instrumented elapsed times are
  correctness-run observations, not statistically established end-to-end speedups.
- The runner pins sources, dependency/preferences files, scripts and inputs before and after each
  job, refuses an existing output directory, and runs only one numerical process.
  Julia version, architecture and thread counts are recorded; runtime binaries
  and the complete system environment are not hashed.

## Coverage and limitations

The focused predicate tests cover tolerance boundaries, all basic positions,
nonbasic exclusions, unbounded/fixed bounds, signed zero, NaN/Inf, finite
violations whose sum overflows, empty/nonempty zero-allocation calls and
BigFloat values stored at 256 bits evaluated under a 64-bit ambient precision.

No representative dense LP solve is benchmarked here. Matrix density does not
enter this predicate; the synthetic scans do not establish whole-solver speed
on dense problems.

This is a bounded improvement to one ordinary-loop check. It is not a solution
to the full medium versus Clp/HiGHS speed gap. The other proposed directions
(RHS preparation, manager update processing/storage and numerical-recovery
cost) remain separate investigations. Read-only inspection confirmed that
weight RHS preparation already avoids a redundant dense reset, auxiliary FTRAN
already skips prepared-update payload copies, and FT/SS/BG already cache active
upper columns and composed row operations. Those existing optimizations are not
claimed as new work here. Removing reconstruction solves or recovery checks
requires separate numerical evidence and is not part of this change.

Raw local attempts are preserved under `.superpowers/simplex-shared-work`.
The first scan harness attempt had a syntax error; the second attempted to
initialize an oversized Float32 synthetic factor and reached the guarded memory
limit. These are harness/setup failures, not numerical failures of an LP solve.
The corrected scan-only fixture avoids that factorization. The initial red
contract test failed because the helper was absent, as intended. None of these
attempts is counted as a completed validation run.

## Remaining investigation order

1. **RHS and column preparation:** measure unit-RHS clearing and manager handoff
   copies independently. A direct unit-RHS path must account for later residual
   checks, scratch consumers and aliasing; merely removing the dense buffer is
   not justified. The existing weight-RHS overwrite already skips clearing.
2. **Update processing and storage across managers:** distinguish PFI eta work,
   FT/SS/BG composed-row/active-upper work and HH middle-product work. One candidate
   is combining finite-direction validation with prepared-direction comparison
   in compatible native-vector paths. It must preserve scalar equality (including
   signed zero), rejected-input behavior and the generic AbstractVector fallback.
   No gain has been measured and no such change is installed here.
3. **Numerical checks:** ordinary dual pricing and the tableau-row residual check
   revisit some of the same basis coefficients. A possible combined traversal
   would have to preserve each accumulator's original arithmetic order, residual
   scaling, nonfinite handling and sparse-pricing fallback. The residual check
   itself remains necessary. Full-factor checks in staged recovery must be
   charged to recovery rather than assumed to run on every ordinary pivot.

These are follow-up measurement candidates, not verified optimizations or a
promise that all apparently duplicate work can be removed.

## Results

All ten guarded validation jobs exited zero and retained their source pins.
The 295 focused predicate tests and 15,689 semantic checks passed. The external
suite passed 305 assertions covering 100 unique combinations (five inputs,
two algorithms, two refactorizations, five managers), all with reference
objectives and original-model primal feasibility. This is not a run of the
entire project suite.

All 13 baseline/candidate cases matched for every recorded numerical field:
ten full fast0507 solves, two limited medium prefixes and one full runtime dual
solve. See the paired TOML reports for hashes, event counts and states. The audit
checks the source-file key sets, baseline against Git `6b891d0`, exactly three
changed production files and all candidate preflights against the paired source
hashes. The full runtime pair returned OPTIMAL at the same iteration count and
with the same original feasible primal vector and objective.

Warmed production-predicate medians for 360,982 basics:

| Type | Input | Original (µs) | Predicate (µs) | Reduction |
| --- | --- | ---: | ---: | ---: |
| Float32 | none | 578.79 | 401.12 | 30.7% |
| Float32 | middle | 576.61 | 195.69 | 66.1% |
| Float32 | last | 552.62 | 392.94 | 28.9% |
| Float64 | none | 558.78 | 429.84 | 23.1% |
| Float64 | middle | 559.24 | 217.61 | 61.1% |
| Float64 | last | 558.24 | 431.23 | 22.8% |

Full runtime: 54,591 iterations, 194 refactorizations, objective `51425691.76210138`.

Both versions allocate zero measured bytes in every kernel case. Raw alternating
samples and analytical visit counts are in `results/production-kernel.toml`.
Process wall time and peak RSS are in `results/validation.json`; those process
figures include compilation, loading, instrumentation and setup. They are not
ordinary-iteration benchmarks, and their difference from instrumented solve
time cannot be attributed solely to compilation. No full-medium speedup is
claimed. Final certification remains part of the unchanged full-solve checks;
its cost and recovery cost were not separately benchmarked by this experiment.

## Reproduction

The reproduction scripts retain the local paths used for this investigation.
`validate.py` is the historical orchestration: it expects the main checkout to
contain baseline `6b891d0` and an unused `.superpowers/simplex-shared-work` output.
After merging, do not run it against an updated main checkout and call that a
baseline. For a repeat, prepare a separate baseline checkout and pass that path
as the later `--project=...` argument to `run.py`; use fresh output directories.
The candidate project is this checkout. `paired.jl` accepts `fast`, `medium` or
`runtime` followed by a fresh report filename. The existing guard and Julia
wrapper paths must remain available. Run jobs sequentially.

`audit.py RAW_DIRECTORY OUTPUT_JSON` audits a complete raw validation directory.
The raw process records identify the actual baseline and candidate project
paths, independently of where the audit script is run. Committed reports are
compact evidence; full logs and preflight manifests remain in the raw directory.
No Manifest.toml or LocalPreferences.toml is committed.
