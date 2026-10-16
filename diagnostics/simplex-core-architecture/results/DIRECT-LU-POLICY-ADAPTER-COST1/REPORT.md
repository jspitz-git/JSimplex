# Direct LU policy adapters — Task3 first matched cost process

One admitted cost1-300 completed; numerical/integrity/compilation audit PASS. This is the first process only, not the complete two-process comparison or production admission. No cost2, retry, old executable or public solver was run. Master26e2291 and frozen candidate remain unchanged.

## Execution and correctness

Inclusive launcher elapsed 13.070884787s, exit0; this includes loading, compilation, diagnostic output and guard overhead and is NOT a benchmark time.24cells,480windows (144warm/336measured),11520exact binary64 residual checks pass. Three warm/seven measured pairs per cell; both sides use native threshold_one or Markowitz default. All336measured compile/recompile times are zero. All240candidate windows report normalized at construction/B4/B8 (720 observations), no fallback. Actual preflight controls/strategies and unchanged inputs pass.

Admission393checks/1810exact bindings; admitted auditor ran once and accepted all558output files. New postcheck9PASS and summary8PASS are saved-output checks only. 12resource samples, minimum availableRAM 22437856KiB, maximumswap0, childmaxRSS 668936KiB, terminalavailable 22965768KiB. Full historical and new groups ANDsessions are absent; no Julia remains. Resource RSS is whole-process peak, not factor/native retained memory.

## First-process cost disposition

All24cells miss both the first-process time gate and median allocation gate; all24pass the reachable-memory gate. Every cell has higher median bytes AND events and lower final reachable memory. The current candidate is not recommended for performance promotion on this workload. This is a valid negative cost result, not a numerical failure. A future second process cannot erase a failed mandatory first-process criterion; nevertheless the specified reversed-order two-process dataset has not been completed. No general impossibility or public solver slowdown is inferred.

Paired whole-time ratios are candidate/reference (lower is better). Each row below is one process and seven measured pairs; MAD and range retain all outliers. Bytes/events/memory are side medians. No aggregation across managers.

| Fixture | Manager | Backend | Paired time median / MAD / range | Faster /7 | Bytes ref / candidate | Events ref / candidate | Reachable bytes ref / candidate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sparse32 | FT | native | 1.203077 / 0.010199 / 1.173134–1.242553 | 0 | 203816 / 270312 | 430 / 1126 | 24024 / 9400 |
| sparse32 | FT | markowitz | 1.442344 / 0.203629 / 0.884472–1.645973 | 1 | 86800 / 247632 | 1450 / 3697 | 64159 / 9320 |
| sparse32 | SS | native | 1.191724 / 0.070248 / 1.070284–1.284732 | 0 | 205480 / 270360 | 469 / 1126 | 25368 / 9400 |
| sparse32 | SS | markowitz | 1.399247 / 0.071378 / 1.327869–1.652087 | 0 | 88624 / 247792 | 1489 / 3697 | 65503 / 9320 |
| sparse32 | BG | native | 1.331944 / 0.026629 / 1.183082–1.433465 | 0 | 208104 / 294248 | 522 / 1274 | 27384 / 11568 |
| sparse32 | BG | markowitz | 1.601386 / 0.067205 / 1.396142–1.750000 | 0 | 91824 / 273376 | 1542 / 3848 | 67519 / 11488 |
| dense32 | FT | native | 1.414758 / 0.062098 / 1.337872–1.508385 | 0 | 500480 / 714336 | 413 / 1014 | 50504 / 23528 |
| dense32 | FT | markowitz | 2.092760 / 0.036726 / 1.887734–2.151316 | 0 | 37104 / 308448 | 247 / 864 | 33416 / 23528 |
| dense32 | SS | native | 1.442808 / 0.049052 / 1.288095–94.120705 | 0 | 502288 / 714480 | 452 / 1014 | 51848 / 23528 |
| dense32 | SS | markowitz | 2.012346 / 0.042070 / 1.955508–2.218818 | 0 | 38928 / 308608 | 286 / 864 | 34760 / 23528 |
| dense32 | BG | native | 1.791019 / 0.067202 / 1.610935–2.249071 | 0 | 505504 / 755600 | 505 / 1282 | 53864 / 25696 |
| dense32 | BG | markowitz | 2.856859 / 0.113722 / 2.065053–3.188377 | 0 | 42128 / 349712 | 339 / 1132 | 36776 / 25696 |
| sparse96 | FT | native | 1.256026 / 0.023330 / 1.232696–1.357659 | 0 | 437112 / 611856 | 690 / 2120 | 53928 / 25944 |
| sparse96 | FT | markowitz | 1.375607 / 0.019370 / 0.844602–1.498554 | 1 | 255040 / 712336 | 4204 / 10158 | 187497 / 25544 |
| sparse96 | SS | native | 1.204261 / 0.054036 / 1.150224–1.444816 | 0 | 461144 / 612016 | 814 / 2120 | 52104 / 25944 |
| sparse96 | SS | markowitz | 1.381651 / 0.048927 / 0.856822–1.623487 | 1 | 279024 / 712496 | 4328 / 10158 | 185673 / 25544 |
| sparse96 | BG | native | 1.377943 / 0.079442 / 0.068230–1.471734 | 1 | 457040 / 663560 | 965 / 2513 | 68040 / 32208 |
| sparse96 | BG | markowitz | 1.526590 / 0.072815 / 1.410076–1.644533 | 0 | 274872 / 770216 | 4479 / 10571 | 201609 / 31808 |
| dense96 | FT | native | 1.630511 / 1.203426 / 0.375952–5.218257 | 3 | 2824720 / 4395120 | 666 / 1805 | 334600 / 166888 |
| dense96 | FT | markowitz | 3.168763 / 0.258121 / 2.656333–11.598592 | 0 | 194336 / 2314816 | 503 / 1658 | 188488 / 166888 |
| dense96 | SS | native | 1.664414 / 0.043770 / 0.411440–5.424187 | 1 | 2829920 / 4395376 | 770 / 1805 | 338280 / 166888 |
| dense96 | SS | markowitz | 3.232609 / 0.277082 / 2.924520–31.445083 | 0 | 199376 / 2314976 | 607 / 1658 | 192168 / 166888 |
| dense96 | BG | native | 2.956255 / 2.328934 / 0.627321–6.050414 | 2 | 2845864 / 4682344 | 953 / 2785 | 349288 / 173152 |
| dense96 | BG | markowitz | 6.229656 / 0.557581 / 5.430863–21.807421 | 0 | 215320 / 2598264 | 790 / 2635 | 203176 / 173152 |

GC occurred in 19 of336measured windows (7reference/12candidate). All outliers stay in the raw data/statistics. Dense32 SS/native ratio94.120705 coincides with candidate GC9.9653ms; sparse96 BG/native ratio0.068230 coincides with reference GC2.9818ms. This association is not a proof of the complete cause or observer neutrality. Dense96 ratios are particularly dispersed; do not infer kernel savings from whole-window ratios alone.

## Nested whole-cycle breakdown

The following side medians in microseconds describe construction, FTRAN, BTRAN, updates and the two refactors. They are subsets of whole time; summing medians is not a whole-time reconstruction. Allocation/GC counters describe whole windows, not attribution to an individual substage. Full raw series and GC/compile statistics remain in audit.json.

| Fixture | Manager | Backend | Whole ref / candidate us | Construct | FTRAN | BTRAN | Updates | Refactor4 | Refactor8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sparse32 | FT | native | 67.000 / 80.400 | 13.300 / 17.100 | 12.100 / 8.600 | 6.400 / 5.100 | 4.100 / 9.200 | 13.500 / 17.700 | 12.900 / 17.800 |
| sparse32 | FT | markowitz | 65.200 / 76.300 | 12.100 / 13.700 | 9.200 / 9.300 | 6.100 / 5.400 | 5.900 / 10.300 | 12.700 / 17.600 | 11.300 / 17.100 |
| sparse32 | SS | native | 72.700 / 86.800 | 14.200 / 19.600 | 12.400 / 9.000 | 6.800 / 5.800 | 5.400 / 10.000 | 15.000 / 19.000 | 14.500 / 19.800 |
| sparse32 | SS | markowitz | 53.100 / 77.300 | 10.500 / 13.600 | 8.800 / 8.900 | 5.100 / 5.000 | 5.500 / 10.100 | 10.300 / 17.000 | 9.000 / 17.100 |
| sparse32 | BG | native | 76.300 / 102.100 | 15.500 / 19.500 | 13.000 / 9.400 | 7.100 / 5.300 | 7.700 / 23.900 | 14.800 / 19.600 | 14.200 / 21.000 |
| sparse32 | BG | markowitz | 60.000 / 96.800 | 11.200 / 13.600 | 9.900 / 9.300 | 5.300 / 5.200 | 7.800 / 25.000 | 11.500 / 18.800 | 10.100 / 19.800 |
| dense32 | FT | native | 114.500 / 160.200 | 31.800 / 39.500 | 17.000 / 12.400 | 8.900 / 8.500 | 4.500 / 19.100 | 28.400 / 39.200 | 19.900 / 37.300 |
| dense32 | FT | markowitz | 45.600 / 94.200 | 7.600 / 17.500 | 10.900 / 12.400 | 6.200 / 8.500 | 4.000 / 17.500 | 6.500 / 16.800 | 6.000 / 16.900 |
| dense32 | SS | native | 115.400 / 166.500 | 30.800 / 40.900 | 16.900 / 12.600 | 9.300 / 8.900 | 5.400 / 22.200 | 29.300 / 38.800 | 19.700 / 38.700 |
| dense32 | SS | markowitz | 47.200 / 95.500 | 7.300 / 18.000 | 11.200 / 12.100 | 6.200 / 8.400 | 5.300 / 19.300 | 7.000 / 16.800 | 5.900 / 17.100 |
| dense32 | BG | native | 119.200 / 207.400 | 31.600 / 38.400 | 17.300 / 12.700 | 9.100 / 9.000 | 8.300 / 66.900 | 28.900 / 38.200 | 19.500 / 38.000 |
| dense32 | BG | markowitz | 50.300 / 141.500 | 7.900 / 17.600 | 11.300 / 12.400 | 6.300 / 9.100 | 7.300 / 62.900 | 6.900 / 17.200 | 6.200 / 17.200 |
| sparse96 | FT | native | 153.500 / 193.400 | 35.400 / 43.200 | 20.900 / 22.200 | 11.400 / 12.600 | 7.800 / 16.000 | 37.000 / 47.600 | 36.800 / 47.800 |
| sparse96 | FT | markowitz | 172.900 / 238.600 | 31.200 / 37.500 | 21.200 / 23.500 | 12.100 / 13.500 | 8.600 / 20.500 | 48.400 / 63.600 | 43.500 / 66.700 |
| sparse96 | SS | native | 162.300 / 202.500 | 36.700 / 42.800 | 21.100 / 22.500 | 12.100 / 12.600 | 12.400 / 17.400 | 37.400 / 50.400 | 38.000 / 48.900 |
| sparse96 | SS | markowitz | 165.200 / 225.900 | 29.800 / 36.000 | 20.600 / 23.200 | 11.400 / 13.300 | 11.700 / 18.900 | 45.300 / 63.100 | 41.700 / 64.400 |
| sparse96 | BG | native | 159.200 / 224.000 | 35.000 / 43.900 | 21.400 / 22.700 | 11.500 / 12.200 | 16.100 / 42.200 | 35.900 / 49.000 | 35.800 / 46.400 |
| sparse96 | BG | markowitz | 174.700 / 268.700 | 31.100 / 37.700 | 21.600 / 23.400 | 12.100 / 14.200 | 16.800 / 54.600 | 47.100 / 64.600 | 43.600 / 65.100 |
| dense96 | FT | native | 630.100 / 1052.800 | 188.900 / 232.400 | 76.800 / 69.600 | 39.900 / 53.000 | 9.000 / 180.000 | 187.900 / 237.000 | 119.800 / 230.000 |
| dense96 | FT | markowitz | 208.100 / 604.600 | 41.900 / 101.100 | 37.000 / 70.400 | 23.000 / 54.800 | 9.000 / 181.000 | 38.100 / 93.900 | 36.100 / 91.900 |
| dense96 | SS | native | 602.800 / 1004.600 | 177.500 / 239.500 | 74.900 / 69.300 | 39.200 / 53.000 | 12.100 / 185.400 | 172.400 / 225.800 | 123.200 / 222.100 |
| dense96 | SS | markowitz | 189.200 / 643.700 | 39.600 / 105.700 | 37.200 / 74.800 | 24.300 / 57.300 | 12.700 / 179.900 | 38.100 / 95.700 | 33.600 / 90.200 |
| dense96 | BG | native | 676.400 / 1878.700 | 198.200 / 273.400 | 83.000 / 78.200 | 44.500 / 59.500 | 21.700 / 801.600 | 187.300 / 256.300 | 130.400 / 262.100 |
| dense96 | BG | markowitz | 220.801 / 1255.900 | 44.800 / 123.400 | 41.800 / 77.400 | 26.100 / 60.000 | 21.400 / 786.200 | 39.600 / 106.900 | 37.000 / 104.600 |

## Work and memory interpretation

Timed API entries are480constructions960refactors3840updates7680FTRAN3840BTRAN. Separate policy preflight adds48constructions96refactors and no explicit solve; source-derived conditional native orientation is additional (at most396candidate export orientation solves over timed plus preflight work). This is not complete instrumented PREforward/native work accounting. Construction includes export/validation/normalization/packed-U/scratch; direct refactors rebuild the whole manager while ordinary refactors can reuse buffers/spares. These existing costs are included, not removed to improve the comparison. No new production code/work/cache or retained-memory structure was introduced.

Aggregate Julia GC counters may include native allocator traffic; final Base.summarysize includes Julia-reachable pools/capacity/spares, not native live/peak/free accounting. One factor survives each window to detached checks, then roots are released without a native-free guarantee. Diagnostic output buffers,504input scans,480graph scans, residual probes and serialization are outside measured totals but inside process lifetime; observer-neutrality is not established.

## Preserved evidence and continuation

The admission reviewer first checked historical GREEN continuation hashes against live updated paths; its failed new checker remains preserved and the corrected checker uses accepted before-cost mappings. No numerical retry or original source mutation. Prior preparation author/reviewer failures are unchanged.

Independent result review is required before closure/publication and before any second-process admission. The latest request authorizes only this first300s process. Preserve all run files and old audits; never rerun this launcher/auditor. Future work must keep the negative first-process gates, fixed inputs/policies and existing separate-admission contract. Task4 public routing, broader plan, CI/full-suite and native-memory limitations remain open. CIoff,HHdisabled,automationpaused.
