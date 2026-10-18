# BG private export/import workspace: testing and cost decision

The fixed candidate passes correctness qualification but is NOT accepted for performance or production integration. The all-eight-cell first-process gate failed. Task3 stops after this one cost process; no second process, tuning, new candidate, or numerical rerun is authorized by this result. The broader architectural plan remains open.

## Completed testing

The previously accepted RED produced exactly six expected missing-contract failures. Original GREEN is preserved with 7934 passes and one diagnostic empty-reduction error. A separate reviewed harness amendment added only `init=0` to that test sum; no candidate arithmetic or fixture changed. Independently accepted GREEN2 passed exactly 7935 assertions in eleven groups, no errors/failures/warnings. GREEN2 evidence is frozen at diagnostic commit6fb6539c; original failed GREEN at3c6e5cc7. The six original missing-contract RED failures are not runtime numerical failures of this candidate.

## Cost outcome

One separately admitted cost1-300 process completed eight cells and160 windows (48warm,112measured), exit0, admitted correctness/integrity audit PASS. There are3840 timed-window outputs plus576 untimed probe outputs. Exact paired output/mode checks, original input preservation, exact rational residual bounds, control/copy/shrink/fallback checks and loaded-source checks passed. All112 measured windows have zero compilation and recompilation. The 300-second guard's inclusive elapsed time was14.121770624005876s; that includes compilation/setup/diagnostics and is not a performance comparison. The author saved-result postcheck passed71 checks. Independent result review and closure are separate records.

Each row below is seven measured pairs. Time is median(candidate/reference) of whole lifecycles; allocation columns are side medians, not medians of ratios. Memory is final reachable Julia graph including wrapper/workspace. Candidate/reference timings include construction, eight updates,16FTRAN,8BTRAN and two refactors. Required time ratio<=0.95, no increase in median bytes OR events, all final/probe graphs<=1.10reference, and at least3/7 faster pairs.

| Fixture | Backend | Paired time ratio | Ratio MAD | Bytes ref→cand | Events ref→cand | Final graph ref→cand B | Faster pairs | First gate |
|---|---|---:|---:|---:|---:|---:|---:|---|
| sparse32 | native | 0.971360 | 0.165330 | 294824→292968 | 1274→1279 | 11568→11592 | 4/7 | FAIL |
| sparse32 | markowitz | 0.945180 | 0.076342 | 273376→271232 | 3848→3847 | 11488→11512 | 6/7 | PASS |
| dense32 | native | 0.873998 | 0.099564 | 755648→743032 | 1282→1291 | 25696→25824 | 4/7 | FAIL |
| dense32 | markowitz | 0.988451 | 0.069385 | 349712→336744 | 1132→1129 | 25696→25824 | 4/7 | FAIL |
| sparse96 | native | 0.980969 | 0.118998 | 663576→657752 | 2513→2514 | 32208→32344 | 4/7 | FAIL |
| sparse96 | markowitz | 1.047716 | 0.029290 | 770216→764616 | 10571→10570 | 31808→31832 | 1/7 | FAIL |
| dense96 | native | 0.981826 | 0.081143 | 4682296→4563680 | 2785→2779 | 173152→176552 | 4/7 | FAIL |
| dense96 | markowitz | 1.006278 | 0.029700 | 2598264→2486192 | 2635→2632 | 173152→173288 | 3/7 | FAIL |

Only sparse32/Markowitz passed all first-process conditions. Dense32/native passed the time condition but increased allocation events by9. Native sparse32 and sparse96 increased events by5 and1 respectively. Bytes fell in every cell, roughly0.63–4.31% by side medians. Every final and intermediate measured graph passed the+10% cap; final graph growth was approximately0.08–1.96%. The memory cap passing does not compensate for time/event failures. Sparse96/Markowitz had a1.047716 paired median and only1/7 faster pairs. No universal/component qualification or end-to-end solver speedup is claimed.

GC and outliers are preserved, not discarded or subtracted. Measured native sparse96 reference had16.413201ms GC, native dense96 reference5.315801ms, and Markowitz dense96 reference/candidate3.956/3.9486ms. Other measured cells had zero in-window GC. Paired time ranges are broad (including0.018021 for sparse96/native and4.192580 for dense96/Markowitz). Small microsecond windows, one process and diagnostic root lifetime limit causal attribution. Source-level savings do not prove the origin of every observed event or timing difference.

## Timing subsets and work

Nested side medians below are microseconds in constructor/FTRAN/BTRAN/update/refactor4/refactor8 order. They are subsets of the whole timer; medians need not sum and no pure-kernel or isolated import speedup is inferred.

| Fixture/backend | Reference µs | Candidate µs |
|---|---|---|
| sparse32/native | 26.90, 11.50, 6.40, 26.80, 24.50, 22.00 | 25.20, 10.90, 6.10, 25.00, 23.20, 22.90 |
| sparse32/markowitz | 16.00, 10.40, 5.60, 23.70, 20.20, 20.40 | 14.80, 9.70, 5.30, 22.30, 18.70, 18.70 |
| dense32/native | 55.90, 14.80, 10.50, 70.40, 44.30, 47.20 | 44.90, 13.00, 8.60, 62.90, 45.20, 42.10 |
| dense32/markowitz | 19.20, 14.00, 10.00, 64.30, 19.60, 19.30 | 17.90, 13.50, 9.40, 60.50, 18.00, 16.90 |
| sparse96/native | 53.90, 27.10, 14.40, 50.40, 59.90, 62.10 | 59.70, 28.70, 15.30, 52.00, 58.70, 57.70 |
| sparse96/markowitz | 40.80, 27.10, 15.70, 54.50, 68.90, 78.80 | 42.80, 28.70, 15.90, 59.40, 71.50, 74.10 |
| dense96/native | 284.10, 76.40, 58.40, 805.70, 269.60, 255.10 | 273.40, 78.10, 58.20, 836.20, 259.80, 240.40 |
| dense96/markowitz | 122.80, 76.30, 57.40, 827.50, 113.80, 106.00 | 116.40, 80.20, 57.70, 844.90, 104.30, 105.60 |

Actual completed source-bound driver schedule totals204 constructors,412 refactors,1472 updates,2944 FTRAN,1472 BTRAN and4 copies across timed, preflight, probe and controls. It is an explicit API budget, not instrumentation of every backend attempt. The native orientation bound is<=308 additional solves; Markowitz orientation count is zero. The source-inverse probe separately observed3 factorization/extraction entries,2refactor entries,6triangle/6permutation checks per cell; native probes3orientation solves/12products, Markowitz0. Original safeguards, policy, precision, inputs and candidate implementation stayed unchanged. See MEMORY-WORK.md and raw counters for complete diagnostic work/retention scope.

## Workspace and memory observations

| Fixture/backend | Peak cache charge B | Probe explicit allocation requests | Requested payload B | Normalized U stores | Sampled build coexistence graph B |
|---|---:|---:|---:|---:|---:|
| sparse32/native | 0 | 219 | 12248 | 236 | 44176 |
| sparse32/markowitz | 0 | 207 | 9096 | 231 | 79302 |
| dense32/native | 520 | 217 | 33800 | 1584 | 100160 |
| dense32/markowitz | 520 | 205 | 30728 | 1584 | 91616 |
| sparse96/native | 528 | 602 | 36864 | 718 | 126016 |
| sparse96/markowitz | 0 | 591 | 26448 | 642 | 231708 |
| dense96/native | 3600 | 593 | 242704 | 13968 | 700400 |
| dense96/markowitz | 528 | 589 | 239632 | 13968 | 621120 |

The probe counted no raw/fallback stores on normal lifecycle inputs; separate bounded controls exercised normalize=false and first/last normalization rejection. Source-request payload excludes allocator headers/capacity/native heap. Cache charge is the preaccepted budget formula, not a physical retained-memory measurement. Coexistence graphs include reachable new inner/backend/raw/owner (including old inner) at one build seam; they are not a universal peak or a paired native-heap bound. Copy controls start with empty private cache and exercise independent refactor; large→small controls passed. Unused diagnostic records stay outside timed windows. Existing candidate cache ownership and immutable policy do not imply complete native release or observer neutrality.

13 resource samples had minimum available RAM22313672KiB and swap0; child maximum RSS816908KiB, terminal available22991540KiB/swap0. Runner74597 start_ticks6121930 and child74598 start_ticks6121985 on boot1ecae454-f1f5-4e2e-a95c-7b5474243126 terminated. Fresh checks cover all254 historical/new groups AND sessions, with no matching process or unreadable process identity; inaccessible executable links remain explicitly disclosed in host records. RSS is whole-process, not per-candidate native memory.

## Preservation and next state

The initial offline prepare.py root-end selector failure and separate prepare-finish.py are preserved. The reviewed2100-path preparation,2104-file exact seal, admission, raw199 output files, one-shot audit and all reviews remain frozen. No old driver/auditor was rerun. No actual src/test/environment/CI/master/STATUS/roadmap change occurred. Master remains26e2291745999f485a74f643298ca997d65c7205. CI remains off and HH reuse disabled.

This candidate's testing and scheduled first-process measurement are complete. The fixed all-eight performance design is stopped. Any different optimization would require a new concrete plan; this result does not reopen stopped historical routes or authorize production integration. Independent review explicitly assesses unnecessary computational work, allocations and retained memory. The documentation/measurement harness adds no new production work; existing candidate event increases and cache retention are reported above, not dismissed.
