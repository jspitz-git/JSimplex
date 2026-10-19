# Specialized BG export/import — first Task3 cost process

Saved audit accepted: **True**. First-process ALL-EIGHT performance gate: **False**. Pure timeout: **False**.

One admitted `cost1-300` attempt, process exit `0`, reason `exit0`. Guard elapsed 15.734074278007029 s; supervisor elapsed 16.534495189989684 s; outer including immutable checks and auditor 46.75977760500973 s. These inclusive durations are not the warmed lifecycle benchmark. Auditor error: ``.

Saved windows: 160, measured: 112, window outputs: 3840. Validated counts: `{'cells': 8, 'windows': 160, 'window_outputs': 3840, 'probe_outputs': 576}`.

| Case / backend | Median paired time C/R (range) | Median bytes R → C | Median events R → C | Median factor graph bytes R → C | Faster pairs | Time / allocation / memory gates |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| sparse32 / native | 0.926087 (0.740925–1.258123) | 294552 → 291960 | 1274 → 1263 | 11568 → 11592 | 5/7 | True / True / True |
| sparse32 / markowitz | 0.949378 (0.747853–1.159509) | 273376 → 270864 | 3848 → 3837 | 11488 → 11512 | 5/7 | True / True / True |
| dense32 / native | 1.007063 (0.678314–1.090433) | 755584 → 742152 | 1282 → 1263 | 25696 → 25824 | 3/7 | False / True / True |
| dense32 / markowitz | 1.051200 (0.973236–2.000000) | 349712 → 336280 | 1132 → 1113 | 25696 → 25824 | 2/7 | False / True / True |
| sparse96 / native | 0.965712 (0.883589–1.076386) | 663592 → 657080 | 2513 → 2498 | 32208 → 32344 | 4/7 | False / True / True |
| sparse96 / markowitz | 0.978809 (0.855471–1.846722) | 770216 → 764248 | 10571 → 10560 | 31808 → 31832 | 4/7 | False / True / True |
| dense96 / native | 0.973578 (0.057855–48.847753) | 4.6823e+06 → 4.56302e+06 | 2785 → 2751 | 173152 → 176552 | 5/7 | False / True / True |
| dense96 / markowitz | 1.001713 (0.149862–1.110788) | 2.59826e+06 → 2.48573e+06 | 2635 → 2616 | 173152 → 173288 | 3/7 | False / True / True |

Every cell keeps all raw warm/measured samples and the six nested timers. Time is the median of paired candidate/reference ratios, not a ratio of side medians. Ranges and MAD remain in postcheck/audit. Nested timers are subsets of whole lifecycle time; no subtraction or summing into an independent total. All input, policy, residual, bitwise-output and normalization gates are carried by the saved auditor; incomplete failed output is not relabelled as accepted.

Measured compile/recompile nonzero windows: 0/0; in-window GC nonzero windows: 3. Warmup and process compilation remain separate from measured windows. Task3 preserved its no-explicit-GC schedule; Task2's separate GC preparation amendment was not generalized.

Resource samples: 15; minimum available RAM 22077120 KiB; maximum swap 0 KiB; child maximum RSS 834532 KiB; terminal memory `{'available_kib': 22755160, 'swap_used_kib': 0}`. Reachable Julia factor/checkpoint/coexistence graphs, aggregate GC allocation traffic and whole-process RSS are distinct. None proves total native allocation/free balance, constant retention or public-solver speedup.

Source budget stays 204 constructors, 412 refactors, 1472 updates, 2944 FTRAN, 1472 BTRAN, four factor copies, one synthetic orientation and three importer controls. These entry counts plus up-to308 native orientation bound are source-derived, not a complete observed native-work budget. Actual untimed probe counts remain in raw/audit. No source/candidate/stage/environment/CI/master change. No second or longer numerical process in this deliverable.

The first-process gate is not satisfied. Stop this fixed candidate/design: no reversed-order cost2 run, post-result tuning, removed samples or changed thresholds. A pure timeout is separately labelled only when the saved auditor validates that exact prefix; any later longer attempt needs its own admission. No universal/end-to-end speedup or production promotion.

Independent result review is recorded separately; this report does not substitute for it. Historical failures and all original raw evidence remain immutable.
