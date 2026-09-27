# Basis update and postsolve cleanup investigation

Baseline: `1ffdbc2f6abf951c31c4ae5676a47dcc92924600`.

The user supplied `runtime-dual-user.log` from another machine. Its exact source revision and environment are unknown. Configuration: legacy dual simplex, steepest-edge pricing, native Bartels–Golub updates, refactorization interval 80, iteration limit 1,000,000, unlimited time, integrality relaxed.

Reduced solve: iteration 56004 at 2063.2132997 s, objective 51425691.762097925, zero reported primal infeasibility. Original cleanup starts at iteration 56008. Projection temporarily reaches zero primal infeasibility and the target objective, then the previous infeasible basis reappears. Final: OPTIMAL, iteration 119197, 9114.1910496 s. About 7051 seconds (77% of solve time) follow the reduced solve. The log alone does not identify why projection was rejected.

User log SHA-256: `6709b0ad00b027e636c5027d685ffa1abfe5e2c2cccfde55504c0a9aee0e923b`.

## Composed dense row histories

At 28,000 rows, replacing distinct identity columns generates actual pure-rotation histories. Before: FTRAN 171.8/415.2/890.4 microseconds and BTRAN 324.1/913.7/3133.9 microseconds for 20/80/320 updates. After composing permutations: FTRAN 142.7/134.6/150.7 microseconds and BTRAN 118.1/119.8/119.3 microseconds. These isolated identity-basis timings demonstrate removal of redundant permutation traversal, not whole-solver speedup. Arithmetic operations remain in their original order.

Validation: 22,888 checks passed across the new differential suite, factorization, triangular reuse/reset, hypersparse history and pivot atomicity tests. The new suite compares floating results with explicit old-history replay using `isequal`, checks exact arithmetic and residuals against actual updated matrices, aliases, independent copies, and changing dimensions.

Baseline runtime dual, interval80: TIME_LIMIT at360.002s,21,619 iterations,271 refactorizations, peak RSS2.12GiB. FTRAN30.44s, BTRAN33.41s, refactorization6.60s, pricing7.79s. Replacement appears in14,250 of26,502 profiler samples, motivating a separate pure-swap batching change. Compilation/startup outside solver time makes outer time413.02s.

## Batched BG factor updates

Pure adjacent row swaps now visit each affected packed column once and rotate its row indices/values as a group. The existing spike scratch marks unique affected columns; short runs do not scan the full matrix. Nonzero elimination arithmetic and pivot comparisons retain their scalar path. On the identity-history benchmark, per-update time fell from 640.7–748.0 to 399.8–484.0 microseconds.

The combined regression suite passed 30,797 checks, including 1,200 assertions comparing every updated packed upper factor and pivot-history record with the scalar implementation from baseline `1ffdbc2`.

## Other basis managers

The user explicitly requested coverage of every manager. FT and SS now use the same composed-permutation representation, retaining their addition operations; BG retains subtraction. SS histories that never permute rows skip the gather/scatter. All 32,421 focused factor checks passed. See the all-manager history logs for identity and coupled-column results. Before this extension, coupled histories at320 updates required BTRAN3.671ms (FT) and3.390ms (SS); the composed path removes that repeated permutation traffic. PFI has no such permutations and remains unchanged at this stage. Real-model history replay is still required to assess its coefficient-dependent cost.
