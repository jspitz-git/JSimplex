# Shared KLU unit-BTRAN experiment: rejected weight qualification, useful kernel and preparation evidence

**The complete experiment is NOT ACCEPTED.** On all six runtime bases the native KLU reference, full exported control and local candidate return false during the first sampled unit's production refinement. The guarded process completed all cases but ordinary Test has **13816 pass /217 fail**, exit1; the supervisor rejects it and the original full auditor still rejects it. There is no runtime complete-weight or inclusive-cycle speedup claim and no production integration. The saved run also contains valid isolated-kernel and preparation measurements, and allocation-stack evidence explaining the old preparation's dominant small allocations. These are narrower diagnostic findings, not a waiver of failed gates.

## What ran and what failed

Diagnostic baseline5b9880a8f5ddd2e253300a9c23e531f45d3e31bf; masterc0fa748ffa61ccb7c1caaf248c40324f60bc737b unchanged. One numerical comparison-2 process,46.177s inclusive, twelve cases,1344 uniformly spaced original unit-row positions per sweep, independent native/full/local contexts. All134 launch bindings unchanged. Production sources, permanent tests, environments and CI unchanged; HH reuse remains disabled. No LP solve, new MPS parse, pivot replay or original-model certificate. The algebraic workspace holder uses captured A/basis and unbounded unused bounds/zero costs; it supplies real production basis assembly/refinement, not a recreation of historical recovery.

A first comparison-1 process failed in5.163s at driver parse before main: compact generator `)for` lacked required whitespace. It did not reach captured-input loading, factors, tests or measurement; imports/helper definitions may have run. Its exit1,126 unchanged pins and rejected supervisor remain frozen. Separate driver-loadfix.jl makes17 whitespace-only line changes; source tokens/numerics/expectations unchanged. Distinct REVIEW-LOADFIX-ADMISSION.md binds comparison-2, fresh preflight and new manifest. Candidate, consumer and accepted copied FTRAN were not changed. No numerical retry or tuning followed comparison-2.

All217 failed assertions classify exactly:

-18 cold whole-handler calls returned false:6runtime cases x3arms.
-126 steady whole-handler calls returned false, including warm rounds:6x3x7.
-72 fresh inclusive cycles returned false, including warm rounds:6x3x4.
-One cold stop-count equality failed for runtime40000/B80: native had4 stop calls/two generic correction solves, full/local had2 stop calls/one correction. None succeeded.

There are zero errored tests and no kernel-residual, reference-endpoint, input-preservation, index, compilation or memory-pressure failure in this partition. This does not turn the217 rejected expectations into passes. results-2.toml's completed=true means final serialization was reached; it is explicitly not acceptance. strict-auditor-rejection.json preserves the unmodified auditor's exit1. analyze_rejected.py separately verifies the failure classification and bounded usable evidence; its diagnostic_accepted=true is not whole_experiment_accepted (which is false).

## Whole-weight coverage and the first rejected predicate

Each runtime handler actually invokes the unit solver **once**, for original row position1, then returns false. Source/path/stop-count evidence establishes this: one unit route plus one generic correction (two for native40000/B80), no stop cancellation, and the unchanged consumer's refine_basis_solve!(...).reliable gate precedes norm/publication. In the one-correction cases the counts imply an initially finite/unreliable quality and no accepted correction; the native40000/B80 counts are consistent with one accepted improvement then another unsuccessful correction. These are source/counter inferences, not captured SolveQuality snapshots. We did not store the rejected component index, actual absolute/relative error, detailed trial-quality fields, or vectors before/after correction, so the exact component/rounding/refinement branch remains unresolved. Do not assert a solver/backend defect or the same cause for all cases.

The policy is the original legacy/native NumericalPolicy: solve_tolerance=5.684341886080802e-14, max_refinements3, solve_refinement=false, with original finite/componentwise/error checks still active. That componentwise reliability condition differs from the cold diagnostic's globally normalized residual bound. A small global backward residual is not proof of per-component reliability. No tolerance, correction budget, precision or numerical safeguard was changed to rescue the comparison.

Runtime cold weight arrays remain their initial ones. Their equal/finite values are therefore vacuous evidence of rebuilt weights. The raw unit_calls128 fields in timed handler records are requested sample counts, not observed completed work: path counters show only one unit. All90 measured runtime whole-handler windows and54 runtime inclusive windows are excluded from complete-handler speed ratios. Their raw times are preserved, never normalized as128 successful weights or added to preparation to claim a lifecycle win.

Fast0507 and the three small controls do complete their sampled handlers, with8640 measured whole-handler and5184 measured inclusive unit calls in total. Fast and default small controls use the identical NativeOnly bypass; no algorithmic speedup is inferred there. The forced coupled64 control exercises local and budget-fallback paths on all64 rows but is tiny synthetic algebra, not a representative successful runtime workload. Callback tests cover pre-row stop/publication and sentinel identity in the adapted handler, not interruption during a live correction; perturbed-output testing exercises the diagnostic residual helper, not a forced production rejection. Actual production refinement is unmodified and used on every handler row.

## Isolated unit BTRAN: complete cold checks and measured windows

The kernel-only windows process all128 sampled runtime units, not the first-row prefix. Across all cases they complete **20160 measured unit calls**, with two prior cold cycles (8064 calls), original-B transpose residual checks, nonzero-bit full/local agreement, signed-zero accounting and36 independent UMFPACK endpoint checks. Maximum globally normalized residual is1.531e-15 across controls, runtime<=6.104e-17; maximum local/native relative output difference2.835e-14. This is component algebra qualification under the stated diagnostic oracle, not the failed production reliability acceptance.

Ratios below are paired local/native times across five measured rounds. Each kernel batch includes all unit RHS filling, guards, work reset, active solves/reverse propagation, scaling/permutation output, fixed path counters and checksum; no residual/weight/callback work inside kernel windows. Full/local/native arm contexts are separate. The same values are not advertised as complete-weight speedups.

| fixed runtime base | native batch ms (128units) | local batch ms | paired local/native median (range) | full/native median |
|---|---:|---:|---:|---:|
| runtime-30000-B0 | 27.250 | 11.312 | 0.4194 (0.3797–0.4275) | 1.6074 |
| runtime-30000-B80 | 25.431 | 10.295 | 0.3996 (0.3924–0.4129) | 1.7553 |
| runtime-30000-B160 | 26.429 | 11.276 | 0.4390 (0.4115–0.4610) | 1.6342 |
| runtime-40000-B0 | 33.023 | 12.993 | 0.4020 (0.3879–0.4569) | 1.4789 |
| runtime-40000-B80 | 33.069 | 14.518 | 0.4390 (0.4238–0.4500) | 1.5261 |
| runtime-40000-B160 | 30.263 | 13.015 | 0.4253 (0.4122–0.4692) | 1.5719 |

Local kernel paired medians0.400–0.439 mean about56–60% less isolated batch time (roughly2.3–2.5x throughput); every runtime kernel pair was faster. Full exported Julia is slower than native (1.48–1.76 medians), so local traversal removes actual work rather than getting a free Julia-vs-C advantage. Runtime local batches record16B/1event, native0B/0events; this is per-batch observation, not16B per unit or a universal zero-allocation guarantee. All recorded measured compilation/recompilation are zero, including108 setup records and nested stages; GC remains recorded.

Signed-zero mismatches between full/local are4.35–4.79million per runtime case over two cold cycles. Nonzero bits match for local paths, but broad scalar-observability equivalence remains unproved. Both that limitation and failed complete reliability prevent any production promotion. Default fast/small bypass ratios near1 remain controls for noise/context layout; no optimization occurred in those paths.

## Preparation: staged specialization removes the large small-object count

The original accepted FTRAN preparation is measured unchanged as an unsplit control. Staged preparation moves the SAME validation/map body behind metadata_stage(p,n), then separately builds scratch and the additional transpose index. All original predicates remain; cold metadata/parts equality checks pass. This is itself a function-barrier/specialization change, not transparent timing probes. We compare whole original/staged preparations and do not assert their stages decompose identical compiled execution.

Each cell is the median of three measured preparation rounds after two warm rounds; native/staged/original order rotates. Measured compile/recompile zero throughout. Aggregate counters may include native allocator callbacks and are not pure Julia-object memory.

| base | native preparation ms/events | original unsplit FTRAN ms/events | shared staged (+BTRAN index) ms/events |
|---|---:|---:|---:|
| runtime-30000-B0 | 9.639 / 1323 | 21.380 / 578231 | 10.825 / 1516 |
| runtime-30000-B80 | 9.365 / 1296 | 23.226 / 578192 | 10.734 / 1489 |
| runtime-30000-B160 | 9.015 / 1322 | 21.517 / 577851 | 10.588 / 1515 |
| runtime-40000-B0 | 12.414 / 1627 | 25.407 / 572771 | 14.397 / 1820 |
| runtime-40000-B80 | 14.365 / 1628 | 26.820 / 572656 | 16.083 / 1821 |
| runtime-40000-B160 | 11.262 / 1639 | 24.963 / 572949 | 13.090 / 1832 |

Original unsplit prep21.4–26.8ms with572656–578231events; shared staged10.6–16.1ms with1489–1832events despite the added reverse index. Native preparation in this process9.0–14.4ms/1296–1639events. These are current paired experimental counters; earlier FTRAN process native18events is not a baseline to subtract here. Import/UMFPACK-reference/callback execution history differs and actual allocator pointer state was not captured; do not claim a cross-process allocation regression or assign that discrepancy to one initialization.

Runtime staged metadata/validation takes about0.62–0.71ms and36events. Extraction/native sort about0.68–1.00ms/72events; scratch/context about0.010–0.036ms/14events; new transpose index about0.228–0.248ms/21events. Factorization dominates the staged total. Stage observations are included in outer totals, which also include wrappers/tuple observation overhead. No numeric validation was removed. Original/staged array/map equivalence and immutable source hashes are part of the cold tests.

### Standard allocation samples locate the old source loop

Profile.Allocs was warmed and used only outside timing windows for one original and one staged runtime30000/B0 preparation, sample_rate0.01. Original:5865 sampled Julia allocations; **5864/5865 (99.98%) have first diagnostic frames in ftran.jl lines37,39,40**, the block-map/weight-construction loop.5159 samples (about88%) are Int64, the remainder there Tuple{Int64,Int64}/UnitRange{Int64}. This identifies boxed scalar/iteration objects at that loop; it does not blame the later three generator validation predicates. Staged profiling has only2 samples, so it cannot support detailed per-site estimates, but the aggregate staged metadata36events and whole-preparation event reduction support the specialization effect in this process.

This is a statistical Julia allocation-stack finding, not exact native allocation/free accounting, byte attribution for rare large arrays, or compiler-IR proof of which specific variable lost inference. The observed fix is isolating the typed metadata calculation behind a function boundary, preserving its body/guards. No code rewrite was made after observing the result. allocation-profile.toml preserves all grouped types/counts/first frames and available diagnostic stacks. The profiler was cleared and roots released outside measurement; its overhead is part of process RSS/time only.

## Memory and guard closure

Transpose index payload is1.644–1.738MB (1.57–1.66MiB), including inverseQ, rowptr, F-position/source-column indices, transpose block weights and7 path counters. It holds no duplicate L/U/F numeric values and no O(nb^2) reach cache. Together with shared forward exports/scratch the candidate adds about7.10–8.47MiB primitive payload over NativeOnly on runtime. Reported Julia context graph grows from2.47–2.62MB to9.91–11.50MB; native reported factor memory6.44–7.80MB is equal per arm and additional to the Julia graph. There is no native-free/retention or OS reclaim proof. Benchmark contexts are independent and kept concurrently for fairness; future single-context production memory is not the sum of all three benchmark arms.

BTRAN uses minheap increasing blocks, transpose work weights/row incidence, Q gather and final P scatter/divide by Rs. Tests cover nonunit scaling, reverse-index shape, both-direction interleaving on shared scratch, epoch rollover, partial-overlap/private aliases, real factor replacement invalidation and singular replacement preservation, generic nonfinite and postscale-overflow native fallbacks, stop/throw prefix and input preservation. Retained numerical callbacks/quality scans remain necessary; failed handler work is not a complete-rebuild benchmark. Per-row basis state validation/assembly, original residual quality, optional corrections and dot norm were never removed.

The numerical guard collected46 resource samples, minimum available RAM21669688KiB, maximum swap0KiB; child high-water RSS1102596KiB covers JIT/profiler/workspaces too. All723 historical/current groups AND sessions absent afterward, no Julia. No timeout/resource kill or restart occurred; normal exit1 reflects Test failures.

## Decision and next concrete work

Keep this as a rejected complete-weight qualification with useful partial diagnostics. Do not promote the shared BTRAN/weight consumer, tune rows to avoid failure, relax solve_tolerance, remove production refinement or rerun this benchmark unchanged.

The smallest missing diagnosis is runtime30000/B0/unit1: capture actual initial/returned SolveQuality fields, the first offending component and pre/post-correction witnesses; compare KLU/native, exported local and an ordinary UMFPACK solve under the SAME production reliability checks. That should be a short ordinary test, not another large recorder or full benchmark. Current saved data identify the first unit/reliability gate but cannot reconstruct its exact residual component. Failure occurs in the reference too, so tuning the graph kernel alone is not a justified fix or proof of production-master failure.

Independently, the preparation specialization is a concrete improvement to the isolated cache and can be qualified for FTRAN without waiting for the BTRAN reliability investigation. New whole prep+FTRAN lifecycle data would be needed before revising previous break-even/speed conclusions; combining medians from different processes is not such evidence. No production integration was requested or performed here.

Raw failed assertions, first parse failure, both immutable launch manifests, original strict auditor and rejection, all numeric records, allocation samples, diagnostic-samples.csv (explicit valid_complete/requested/actual fields) and diagnostic-analysis.json accompany this decision. The diagnostic analyzer's positive checks validate classification, preserved kernels/setup and scope; they never waive any original gate. Independent final review must accept only this bounded diagnostic decision, with no claim that the experiment passed.
