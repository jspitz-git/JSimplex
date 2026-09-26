# Legacy simplex stability investigation

The branch repairs reproduced early numerical failures and excessive legacy
refactorizations using native-precision corrections and consistent primal
feasibility checks. Complete-solve performance remains unresolved: every final
runtime and medium attempt reaches the six-minute time limit. Fast0507 and the
small external corpus solve optimally and pass independent checks. Adaptive
strategy semantics and feasibility tolerance values are unchanged.

Measurements apply to functional revision `d5472bc` (base `0065da8`), with
production SHA-256
`31c9cb3de87c46bccf98349b30db3f53432a66553250c79209792482768b6f68`.
Jobs run sequentially with one Julia and one BLAS thread under a 24 GiB virtual
address-space limit. See [`environment.json`](environment.json) for versions.
The user-supplied second-machine log is retained separately and cannot be
attributed to this revision.

## Final measurements

All runs use legacy simplex, steepest-edge pricing, native refactorization,
configured initial interval 80, relaxed integrality, and an iteration limit of
1,000,000. Existing clean-cycle interval growth can still operate. Fast0507
values are medians of three measured repetitions after a full-model warmup;
large cases receive one 360-second attempt after an AFIRO warmup. These runs have
no diagnostic observer or kernel timers.

| Model | Algorithm | Update | Status | Median/attempt seconds | Pivots | Refactorizations |
| --- | --- | --- | --- | ---: | ---: | ---: |
| fast0507 | primal | bartels_golub | OPTIMAL | 14.887 | 5,254 | 67 |
| fast0507 | primal | pfi | OPTIMAL | 13.103 | 4,923 | 63 |
| fast0507 | dual | bartels_golub | OPTIMAL | 9.778 | 7,507 | 94 |
| fast0507 | dual | pfi | OPTIMAL | 8.712 | 7,175 | 50 |
| runtime | primal | bartels_golub | TIME_LIMIT | 360.803 | 6,322 | 170 |
| runtime | primal | pfi | TIME_LIMIT | 360.879 | 5,211 | 310 |
| runtime | dual | bartels_golub | TIME_LIMIT | 360.004 | 30,376 | 380 |
| runtime | dual | pfi | TIME_LIMIT | 360.000 | 96,908 | 864 |
| medium | primal | bartels_golub | TIME_LIMIT | 360.008 | 6,105 | 77 |
| medium | dual | bartels_golub | TIME_LIMIT | 360.065 | 4,534 | 56 |

All optimal samples, including warmups, pass original-input primal certification
and agree with the hash-matched independent objective reference. TIME_LIMIT
samples are not certified solutions and have no reported solution objective.
Detailed records are in [`external-benchmarks.json`](external-benchmarks.json).
The process-wide peak RSS is 4,410,077,184 bytes (4.11 GiB); cumulative
allocations in the records must not be interpreted as resident memory. Neither
medium run hits the memory limit. The excluded files `big.mps`, `largo.mps`, and
`AnyMod.mps` are not solved or factorized.

The repairs remove the captured early primal termination within these attempts
and reduce the diagnosed dual refactorization storm. They do not establish
convergence on runtime or medium. Primal candidate rejection and repricing
remain expensive, and native factor accuracy on ill-conditioned bases remains
a limitation. A six-minute attempt cannot rule out later numerical failure.

The archived [HiGHS reference](../simplex-performance/highs-reference.json)
solves runtime in 18.27 seconds dual and 80.85 seconds primal on this architecture;
both reference solutions pass the independent original-input primal check.
Medium reference times are 108.53 and 224.12 seconds, but both fail the strict
absolute `1e-7` original-input row check by approximately `1.78e-7`. Those medium
times are context, not accepted same-tolerance solves. No tolerance is weakened
to match them.

## Verification

The monolithic production gate exceeded its 14,400-second limit after completing
301 of 312 test files. It stopped in `solver_tests.jl` without a reported test
failure. This is an incomplete gate, not a passing full suite. Source and test
inventory remained unchanged (`a83144426f11df8f0150afd605b78a5c1292c1295304773aa1ab9c934acf125f`).
The original log is preserved locally with SHA-256
`1d5474a5c9643fa143ba7f7c56ed2ba79994af76a03642cb9a94628691cd6017`.
The remaining 11 files completed in a fresh process in 1,352.10 seconds, in
original order with unchanged assertions: 9,702 checks passed, zero assertions
failed, and one testset errored because the isolated harness omitted the shared
`RecordingSimplexLogger` fixture. Replaying that exact original testset with the
original fixture passes 4/4 checks in 45.84 seconds. This was a harness error;
production code and tests were not changed. The union of completed file markers
matches all 312 includes in `test/runtests.jl`. The initial 301-file portion has
no final aggregate assertion count because its outer testset was interrupted.
This establishes file coverage across recorded processes, not a successful
monolithic gate. Development checks pass 1,208/1,208, including 249 JET checks,
in 1,434.70 seconds. The separate GLPK comparison passes 6/6 in 48.58 seconds.
Final external measurements are recorded above. Full per-gate records, source
inventory hashes, and log hashes are in [`validation.json`](validation.json).

The separate small corpus passes 200 checks covering 64 solves: eight NetLib and
MIPLib LP inputs, both algorithms, and all four basis-update backends. Every solve
is optimal, reference-matched, and original-input primal-certified; see
[`quick-corpus.json`](quick-corpus.json). A read-only independent review and
addressed findings are recorded in [`review.md`](review.md).

After measurement, one extra blank line at the end of
`test/legacy_harris_feasibility_tests.jl` was removed. Julia parsing confirms
identical test expressions before and after this formatting-only cleanup.
Production files and their fingerprint are unchanged. The original validation
inventory hash remains attached to each recorded run; the post-cleanup inventory
is recorded separately in the environment file.

## Reproduced causes

The original primal failure occurs after 766 total pivots. A leaving row activity is about -7.20e-8 below its zero lower bound, within the 1e-7 primal tolerance. The ratio test clips its negative ratio to zero. Subsequent basis recomputation nevertheless assigns the row exactly zero: with a pivot of about 0.0109, that implies an entering displacement of about -6.62e-6. The predicted zero step and actual recomputed point disagree; the resulting maximum bound violation is about 1.67e-5. A fresh factorization preserves the error. This is an inconsistent pivot-point transition, not evidence that LU must be repeated.

Rejecting unsafe bound snaps preserves feasibility but alone is insufficient. Runtime then exposes an inconclusive best-priced candidate while other entering columns are usable, followed by persistent tiny pivots after refresh. Finite candidate retry and one refresh per unchanged basis avoid these early numerical terminations. They are safeguards, not a complete performance fix: a six-minute intermediate run reaches only 2,048 pivots and rejects 7,583 candidates.

The dual baseline completes 32,335 pivots in a 360-second diagnostic attempt, with 1,777 refactorizations. Of these, 531 follow residual checks; 264 residual repairs occur after only one update. Each of the first eight saved failures passes the original acceptance threshold after one compensated Float64 residual correction using the same updated factor. No tolerance increase or arbitrary-precision arithmetic is needed for those samples.

Native correction eliminates residual-triggered refactorizations in a subsequent six-minute run: 864 successful corrections, 203 total refactorizations, and zero residual refactorizations. However, only 21,777 pivots fit that budget. Existing clean-cycle bookkeeping treats corrected cycles as clean and grows the update interval from 80 to 320. The branch therefore records whether a cycle required native correction and excludes that cycle from evidence for interval growth. Genuinely clean productive cycles can still grow, and recovery from a previously shortened interval remains available.

After correcting cycle bookkeeping, a further 360-second dual attempt reaches 29,684 pivots, with 371 total refactorizations (370 scheduled, one other), zero residual refactorizations, 627 successful native corrections out of 629 attempts, and a maximum update chain of 80. It still reaches the time limit. The reduced refactorization storm is established; a complete-solve speedup is not.

Preserving tolerated primal row values also survives a 360-second attempt without numerical termination, with zero reported primal infeasibility and a maximum raw bound violation of 9.89e-8. However, it reaches only 2,572 pivots and still performs 206 tiny-pivot refactorizations. Its current reduced phase has 28,453 rows, whereas the original captured failure had 43,021 rows; pivot totals across these trajectories do not establish equivalent progress. This intermediate result motivated the subsequent diagnosis of tiny-pivot selection. It is not a solved case.

## Harris feasibility mismatch

A 60-second diagnostic prefix captured eight tiny-pivot refreshes. In the first three, a strong Harris candidate was discarded solely because the *sum* of individually tolerated bound errors exceeded the primal tolerance:

| Snapshot | Strict fallback pivot magnitude | Strong candidate magnitude | Maximum predicted bound error | Sum of predicted errors |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1.74e-14 | 5.10e6 | 8.50e-8 | 4.59e-7 |
| 2 | 9.02e-15 | 2.00e6 | 8.00e-8 | 2.55e-7 |
| 3 | 2.04e-14 | 8.59e6 | 8.00e-8 | 2.26e-7 |

The existing workspace and original-model feasibility checks allow each bound an error of at most 1e-7. The extra aggregate restriction therefore redirects selection toward a near-zero pivot even though the strong candidate satisfies the original per-bound criterion. A two-row regression reproduces this with row activities -7e-8 and candidate coefficients 1e-14 and 1. Legacy Harris validation now uses the per-bound criterion; the tolerance values and final original-model certification are unchanged. Adaptive aggregation retains its existing behavior.

## Ill-conditioned point reconstruction

After the Harris repair, runtime progresses to 6,310 pivots in about 59 diagnostic seconds, with only two tiny-pivot refactorizations. A later unit zero pivot exposes another independent failure: fresh LU reconstructs an infeasible point even on the preceding basis. The previously stored point passes feasibility certification for the workspace's unperturbed working model, which may be a phase-I model; its full row-equation residual is about 7e-13. This is not certification of the original input LP. Compensated native corrections through that fresh factor worsen the bound violations instead of correcting them.

The fallback retains the predicted primal point only when ordinary reconstruction loses feasibility. It independently checks the unperturbed workspace model's structural/row bounds and consistency with all stored row activities at the unchanged primal tolerance. Final certification against the original input model remains unchanged. The values remain in the problem's floating type. Ambiguous certificate enclosures use the existing exact certification fallback; no higher-precision solve or tolerance increase is introduced. Cancellation, exceptions, and failed certification restore the computed values. Adaptive, staged, validated-recovery, and incremental policies bypass this fallback.

## Transpose-row validation before primal pivots

The next captured failure first becomes singular at local iteration 5,345, five pivots before a scheduled refactor. Replaying the updates from the preceding fresh factor isolates a false pivot: the updated forward solve gives 0.870364, while a fresh solve gives 8.997e-17. The updated transpose estimate agrees with the wrong forward estimate, and the existing forward residual test passes. However, the transpose equation residual fails the existing legacy criterion by a factor of 1.759e13. Native correction cannot repair this row.

Legacy primal now checks the transpose row before changing the basis. It tries native correction first, permits one refresh of an unchanged updated basis, and rejects a persistently unusable entering candidate. Steepest-edge and Devex reuse that validated row for their weight updates. Adaptive and explicit validated/refinement/incremental policies retain their existing path. A stale-factor regression confirms that the false pivot is rejected; another confirms that a correctable row needs no refactorization. The combined related suite passes 549/549 checks.

The final candidate also passes 200 checks covering 64 external LP solves: eight hash-matched NetLib/MIPLib inputs, both algorithms, and all four update backends. Every solve returns OPTIMAL, agrees with the independent objective reference, and passes original-model primal certification. See `quick-corpus.json` for individual records.

## Latest runtime diagnostic candidate

At source `d5472bc`, the primal BG80 diagnostic reaches TIME_LIMIT after 363.190 seconds and 6,322 total pivots. Reported working primal infeasibility is zero. There are 170 refactorizations: 89 residual-triggered, 76 scheduled, three tiny-pivot refreshes, and two other refreshes. The run accepts 95 native corrections from 134 attempts, preserves 59 independently certified points, and rejects 366 entering candidates.

The captured singular-pivot termination does not recur in this attempt. This does not establish completion: the reduced-model route still falls back to the original LP, and pricing remains expensive after repeated repairs. Nested diagnostic timings attribute 315.16 seconds to pricing and 279.79 seconds to FTRAN; these overlap and must not be summed. Final measurements without diagnostic instrumentation are reported above.

## Timing comparison scope

The final measurements use the user's refactorization interval of 80. The
previous performance report's default-PFI timings (8.255 seconds dual and
12.688 seconds primal on fast0507) used the constructor default interval of 20.
Those historical timings are not a controlled comparison with the present
interval-80 measurements. In contrast, the runtime BG80 diagnostic baselines
collected for this investigation use the reported interval of 80. No broad
complete-solve speedup is claimed from unmatched configurations.

## Validation compilation cost

The full production gate exposes substantially longer elapsed times in existing
precision-recovery blocks than the previous branch's recorded gate:

| Test file | Previous gate seconds | This gate seconds |
| --- | ---: | ---: |
| simplex_precision_recovery_state_tests.jl | 234.61 | 1547.31 |
| simplex_precision_exception_tests.jl | 43.71 | 171.07 |
| simplex_precision_decision_tests.jl | 378.55 | 1724.28 |
| simplex_precision_guard_tests.jl | 98.64 | 417.91 |

All four blocks pass. Non-terminating process stack samples during the long
blocks show compiler type inference, subtype/backedge processing, and garbage
collection rather than simplex iterations. These samples locate the observed
work but do not establish the cause of the regression. For comparison, the
Markowitz block takes 440.97 seconds versus 445.61 previously. Test-process
compilation cost must be kept separate from warmed solver timings. The fresh-process continuation completes `solver_tests.jl` in 830.86 seconds
and `moi/result_tests.jl` in 415.75 seconds; these differ substantially from the
long-lived process and do not isolate a cause by themselves. The branch does
not yet claim to have repaired this compilation slowdown. The user has requested
a separate cause investigation after the stability verification.

Reproduction commands and measurement semantics are documented in
[`reproduce/README.md`](reproduce/README.md).

## Additional user evidence

The user supplied an incomplete dual runtime log from a second computer while
this branch was under validation. The reduced model reportedly failed after
approximately two hours; the full-model solve was still running. The excerpt
ends at iteration 277,207 and logged elapsed time 21,105.68 seconds, with primal
infeasibility 6,525.21 (count 4,869) and zero reported dual infeasibility. The
second computer's revision and environment are unknown. Preserve this as
independent user evidence, not a measurement of the current candidate. See
[`second-machine/README.md`](second-machine/README.md) for the original log,
hash, all parsed samples, and limitations.
