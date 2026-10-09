# Final certificate work validation

All times in the table are warmed median milliseconds per point certificate. Nine alternating rounds, three calls per round; measured compilation time is zero. Ratios are baseline/final.

| Case | Type | Baseline | Scratch | Bounds/scan | Shared sums | Ratio | Baseline/final bytes |
|---|---|---:|---:|---:|---:|---:|---:|
| fast | Float32 | 0.032267 | 0.032400 | 0.032067 | 0.033233 | 0.971 | 32/0 |
| sparse_overlap | Float32 | 0.156767 | 0.150000 | 0.135167 | 0.111867 | 1.401 | 183000/0 |
| dense_overlap | Float32 | 0.458133 | 0.483833 | 0.484667 | 0.308733 | 1.484 | 10400/0 |
| consistency_only | Float32 | 0.112300 | 0.105767 | 0.088433 | 0.088700 | 1.266 | 99728/0 |
| partial_overlap | Float32 | 0.131600 | 0.129300 | 0.110467 | 0.103400 | 1.273 | 145904/0 |
| fast | Float64 | 0.033700 | 0.032333 | 0.032633 | 0.032700 | 1.031 | 32/0 |
| sparse_overlap | Float64 | 0.158200 | 0.151433 | 0.130100 | 0.105333 | 1.502 | 248536/0 |
| dense_overlap | Float64 | 0.475000 | 0.466233 | 0.460933 | 0.309433 | 1.535 | 14664/0 |
| consistency_only | Float64 | 0.118767 | 0.113900 | 0.091067 | 0.092467 | 1.284 | 140688/0 |
| partial_overlap | Float64 | 0.141967 | 0.135133 | 0.114367 | 0.107133 | 1.325 | 199152/0 |
| medium-primal | Float64 | 17.842188 | 17.660988 | 16.020635 | 14.872257 | 1.200 | 1.87843e+07/0 |
| medium-dual | Float64 | 18.360521 | 18.174900 | 16.625933 | 15.310523 | 1.199 | 1.87843e+07/0 |

The two medium rows are saved endpoints reached after 32 primal cleanup steps, from different original handoffs. The full allocated point-buffer footprint is 17,452,176 bytes at each endpoint; it is not a separately measured baseline memory delta. Vector capacity may exceed logical lengths. Initialization, exact fallback allocation, and unrelated solver allocations are excluded from these native-only steady-state figures.

The fast-path controls show small timing noise, not a demonstrated speedup. Sharing adds little when only one check needs native sums; the allocation and bound-view savings still apply. Dense cancellation and overlapping selections benefit more. No complete medium solve speed claim is made.

## Regression and trajectory evidence

- `final-broad-semantic`: exit 0, source/input digests unchanged; Native terminal certificate semantic regressions | 15689  15689  1m40.8s.
- `final-cleanup`: exit 0, source/input digests unchanged; explicit script assertions passed.
- `final-differential-v2`: exit 0, source/input digests unchanged; Frozen point certificate accepted/rejected differential | 1680   1680  3.7s.
- `final-external`: exit 0, source/input digests unchanged; External LP relaxations: native and Markowitz basis managers |  305    305  12m35.7s.
- `final-products`: exit 0, source/input digests unchanged; explicit script assertions passed.
- `final-runtime`: exit 0, source/input digests unchanged; explicit script assertions passed.
- `final-semantic`: exit 0, source/input digests unchanged; Point certificate regression coverage | 1304   1304  2.8s.
- `final-stages`: exit 0, source/input digests unchanged; explicit script assertions passed.
- `merged-semantic`: exit 0, source/input digests unchanged; Point certificate regression coverage | 1304   1304  3.0s.
- `merged-targeted`: exit 0, source/input digests unchanged; Point certificate regression coverage | 1216   1216  17.9s.
- `step3-targeted-v2`: exit 0, source/input digests unchanged; Point certificate regression coverage | 1216   1216  17.3s.

The external matrix contains exactly 100 unique combinations (five models, five basis managers, two algorithms, two refactorization backends); all are optimal, match reference objectives, and pass original-model primal certification.

Both 128-step medium cleanup comparisons have identical event and state hashes. Fresh handoffs are deserialized for each arm. These are bounded continuations with ITERATION_LIMIT by design, not completed medium solves. Their single baseline-first cold timings include compilation/initialization and are not speedup evidence.

The full HH/native320 dual runtime solve is OPTIMAL after 54,591 iterations and 194 refactorizations; objective 51425691.7621, original-model feasible. Both event and sampled-state hashes match the prior baseline. Instrumented elapsed time 176.044s includes 0.046s compilation. This single full run validates trajectory and correctness, not an end-to-end performance claim.

The complete project suite was not rerun. The broad semantic selection uses --compile=min; allocation checks and external/full solves use normal compilation. Earlier incomplete compilation and fixture/script errors are listed in README and attempts.json. No missing or interrupted report is counted as successful.

## Work and memory review

Independent review found no correctness blocker or remaining material unnecessary work/memory cost. No basis solves, high-precision conversions, full matrix copies, or numerical relaxations were added. Scratch is lazy, workspace owned, O(m+k); cached sums exist only for a fixed point certificate. The second check retains independent bounds and exact fallback. The product-count probe confirms the overlapping three-term fixture uses 384 rather than 768 native products. Cold first-call allocation and peak union storage are deliberate tradeoffs for eliminating repeated allocations and overlapping CSC work.
