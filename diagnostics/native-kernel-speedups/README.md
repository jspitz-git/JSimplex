# Arithmetic-preserving simplex kernel speedups

Baseline: production `9f9c2a0`; motivated by the guarded profiling recorded in
experimental commit `d02623f`. Candidate branch: `codex/native-kernel-speedups`.

## Changes and invariants

- Share the native activity enclosure and primal-column copy between model-bound
  and equation-consistency checks within a single primal point certificate.
  No cache survives the call or crosses trial points. Both checks and their
  exact fallbacks remain independent. Original bounds still apply unless an
  owned active bound perturbation supplies the working bounds.
- Check residual vector dimensions before modifying scratch, and retain explicit
  basis-index validation. Remove repeated array bounds checks inside the two
  dual residual kernels; preserve every product, sum, scale and tolerance.
- Check reduced-cost vector shape/indexing before ordered CSC subtraction loops.
  Retain the original arithmetic and zeroing of basic reduced costs.

No pricing switch, incremental state reconstruction, tolerance change, reduced
checking frequency, precision escalation, factorization change or fast-math is
introduced. Steepest-edge weighting itself remains unchanged. All sparse loops
rely on valid CSC storage, as do the existing unchecked pricing kernels.

## Validation protocol

Run only one Julia process, one Julia/BLAS thread, using the established 8 GiB VM,
6 GiB available-RAM and 1 GiB swap guard. LocalPreferences keeps precompile workload
disabled. Every paired job pins the effective project (including the separate
master baseline), sources, environment, harness, memory guard, warmup fixtures,
workloads and saved handoff. No source changes occur within a job.

1. Observe the allocation regression fail before certificate reuse. Observe
   malformed-vector validation regressions fail before loop changes.
2. Run targeted certificate, perturbation, cancellation, native-tableau and pivot
   consistency regressions. Test dimension and offset-index rejection before
   mutation. Check Float32/Float64/BigFloat/Rational reduced-cost behavior.
3. Alternate baseline/candidate kernels in seven batches in one process. Preserve
   frozen baseline arithmetic in `baseline-kernels.jl`. Compare exact results and
   mutated scratch, including signed zero and nonfinite direction/RHS cases.
4. Run semantic regressions and 100 external combinations: five approved inputs,
   primal/dual, five managers and native/Markowitz refactorization.
5. Run baseline and candidate separately with the same workload and equal iteration
   budgets: full runtime dual HH/native320; first 2,000 medium primal iterations
   HH/native320; 640 cleanup iterations from the same saved medium HH/native160
   handoff. All have infinite solver time limits and bounded outer guards.
6. Compare statuses, iteration counts, numerical event counts and hashes of every
   completed pivot's basis, primal values, reduced costs and pricing weights.
   Full runtime additionally requires original feasibility and reference optimum.
7. Attempt the full project test entry point with its own 600-second guard. Treat
   compilation/resource/time failures separately from numerical test failures.

Performance jobs use normal compilation with `-O1` (semantic tests separately
use `--compile=min`). Timings include the same observer hashing in both arms and are single paired
observations, not repeated end-to-end speed estimates. Compilation and cumulative
allocation are recorded separately. Iteration-limited medium runs are not optima.

## Preserved preliminary attempts

`certificate-red` failed the allocation requirement, with semantic checks passing.
`certificate-green` passed its executed checks but then referenced a nonexistent
`primal_row_memory_tests.jl`; this harness mistake is retained and is not counted
as a successful job. `kernel-green` reran the intended available regression files.
`dimensions-red` failed all 12 new shape/pre-mutation checks as expected. Further
indexing and provenance safeguards were identified by independent review before
paired runs; the numerical child already in flight was allowed to finish.

## Completed kernel measurements

Seven alternating batches, 2,048 rows / 4,096 columns, normal `-O1` compilation:

| Float64 kernel | Candidate / baseline median time | Baseline bytes/call | Candidate bytes/call |
| --- | ---: | ---: | ---: |
| Point certificate | 0.527 | 180,832 | 115,080 |
| Tableau-row residual | 0.818 | 0 | 0 |
| Direction residual | 0.814 | 0 | 0 |
| Reduced costs | 0.572 | 0 | 0 |
| Direction weight (unchanged control) | 1.011 | 0 | 0 |

Float32 median ratios are 0.526 / 0.813 / 0.816 / 0.533 / 0.993 respectively.
These are kernel observations, not whole-solver speedups. Equality checks include
full residual scratch after nonfinite direction/RHS trials, and the retained
certificate composition with separate activity scans.

## Completed regression evidence

- 805 targeted native-tableau, pivot, point and perturbation checks passed.
- 15,689 semantic checks passed with `--compile=min`.
- All 100 external combinations were optimal, originally feasible and matched
  their reference objectives.
- Final indexing/certificate checks passed after the reviewer-requested
  one-based guard. The semantic/external runs preceded that guard; it adds only
  rejection of offset arrays and has no effect on their ordinary Vector inputs.
- The initial shape test failed 12 assertions, and the offset test failed four,
  before their respective validation changes. Their final forms pass.

## Full runtime pair

Both arms returned OPTIMAL after 54,591 iterations, with exactly matching
objective 51425691.76210138, original primal feasibility, numerical event counts,
and per-pivot state trace
`fa5df8df3f80092b61326fa004319b3769b9771b77696b973c06f9a096c0a4e8`.

| Recorded scope | Baseline seconds | Candidate seconds |
| --- | ---: | ---: |
| Entire measured solve | 458.43 | 431.29 |
| Compilation within solve | 33.56 | 33.37 |
| GC within solve | 34.89 | 10.86 |

The observed 5.9% elapsed reduction is mostly explained by GC variation; it is
not evidence of a stable 5.9% arithmetic speedup. Allocations were approximately
17.39 GB in both arms. Observer hashing is included identically in both runs.
All three pairs passed the trajectory and provenance audit. The project-wide
suite hit the compilation wall-time guard, as detailed below.


## Medium phase-I prefix

Both arms completed exactly 2,000 iterations with the same numerical events and
per-pivot trace `c7716cedc80db5039b28364dfbe1a4106551c3f06cd44ef14e80b51886f91d57`.
Baseline/candidate elapsed times were 189.074 / 189.339 seconds, compilation
33.663 / 33.669 seconds, and GC 22.775 / 23.399 seconds. Both allocated about
14.45 GB cumulatively. There is no measurable end-to-end benefit in this prefix.
These iteration-limited observations do not establish convergence of medium.

## Medium cleanup prefix

Both arms completed the same 640 additional cleanup iterations (335,686 total),
including 640 preserved-point events. Every numerical event count and the full
pivot trace matched: `1fa9b37839555f2356e1b648fcb205889125b34704cd0df8e841dada9141caeb`.

| Recorded scope | Baseline | Candidate |
| --- | ---: | ---: |
| Measured seconds | 301.985 | 270.355 |
| Compilation seconds | 9.942 | 10.199 |
| GC seconds | 118.415 | 91.041 |
| Cumulative allocated bytes | 38,503,778,992 | 30,341,351,472 |

This pair observed 10.5% less elapsed time and 21.2% fewer cumulative allocations.
GC accounts for 27.37 seconds of the 31.63-second elapsed difference. The measured
allocation reduction supports the intended reuse benefit; the precise wall-time
percentage needs repeated runs before being generalized. This prefix is not a
new full solve or certificate of optimality for medium.

## Provenance audit

`results/paired-summary.json` records all six reports, source hashes, events and
trace comparisons. `source-root-audit.json` additionally verifies each report's
source root equals the runner's effective project and the intended arm. Baseline
source hashes were checked against git `9f9c2a0`. All per-job pinned files remained
unchanged through the audit. Raw preflights and complete attempts remain locally
in `.superpowers/native-kernel-speedups`; results here retain compact process,
regression, kernel and external evidence. The profiling-only predecessor commits
are not part of the production integration.

## Reproduction entry points

`reproduce/run.py OUTPUT_DIRECTORY GUARD_SECONDS JULIA_ARGS...` refuses an existing
output directory or another Julia process. It pins sources and records the
process exit separately from the solver result. The local dependency paths in
that runner identify the retained guard, wrapper and saved handoff; they are not
portable fixtures included in git. `reproduce/validate.py` records the ordered
regression and six-arm comparison protocol. Use fresh output paths for a rerun.

For the kernel measurement, invoke the guarded runner with `-O1`,
`reproduce/kernels.jl` and a fresh TOML output path. For a paired measurement, use
`reproduce/paired.jl CASE REPORT.toml`, where CASE is `runtime`, `medium` or
`cleanup`. Override `--project` for the baseline arm. `reproduce/audit.py RAW OUT`
checks all three completed pairs and the 100-case external report; run it before
changing either source checkout because it rechecks the pinned files. The
additional source-root audit compares each arm to its intended checkout and
checks baseline hashes against the recorded git commit.

## Full project-suite limitation

The normal-compilation `-O1 test/runtests.jl` attempt did not finish within its
600-second outer guard (exit 75; about 610 seconds including termination). The
termination stack was in LLVM SROA/SSAUpdater compilation reached from
`dual_pivot_consistency_tests.jl:43`, not a reported failed assertion. Peak RSS
was 2,739,832 KiB. No memory-guard trigger occurred. This is an incomplete suite,
not a pass. The same targeted pivot-consistency tests passed in the separate
normal-compilation kernel regression run; semantic regressions also passed with
`--compile=min`. Complete failure evidence is retained in `results/project-suite.log`.

## Master integration verification

The self-contained change was cherry-picked onto master as `fec9f28`, excluding
the earlier profiling-only history. Source, test and diagnostic trees matched
the reviewed candidate exactly before the check. A fresh guarded normal-
compilation run on master passed 813 targeted checks, including dimensions,
offset rejection, generic reduced costs, native tableau/pivot consistency,
perturbed and joint point certificates, and allocation savings. It exited zero
in 126.1 seconds with unchanged pins and peak RSS 1,159,392 KiB. The retained
`master-integration.log` and process record contain the exact command and results.
