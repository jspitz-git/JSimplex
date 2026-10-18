# Block BG contiguous U — first comparative cost result

**Decision: correctness/integrity accepted; the fixed design fails first-process cost admission and is STOPPED.** No second process, tuning, selected-cell rerun or production integration. Dense96 is locally promising, but does not satisfy the all-eight-cell contract.

## Execution and correctness

One independently admitted `cost1-300` process completed normally with exit0. Eight cells,160 windows (48warm/112measured),4,416 exact residual checks and bitwise reference/candidate comparisons passed the original auditor. Inputs, policies, stage/runtime hashes, measured compilation and re-compilation gates passed. No warnings were reported. The accepted prior GREEN correctness run was reused, never rerun.

The supervisor-inclusive elapsed time was 16.125132s; this is not a benchmark metric. Resource sampling: 15 samples, minimum available RAM 22588872KiB, maximum swap 0KiB, child high-water RSS 829184KiB. Fresh closure found all240 historical/new PGIDs ANDsessions absent and no visible Julia; unreadable exe links remain an explicit visibility limit.

## Saved comparative results

Time is median of seven paired candidate/reference ratios, including full construction/export/normalization, updates, solves and refactors. Bytes/events are side medians of aggregate GC-counter traffic, potentially including native callbacks. Graph values are reachable Julia graphs, not native live bytes or physical peak.

| Input | Backend | Time ratio | Bytes ref→candidate | Events ref→candidate | Final graph B ref→candidate | Max checkpoint graph ratio | Faster pairs |
|---|---|---:|---:|---:|---:|---:|---:|
| sparse32 | native | 1.103726 | 295032 → 319648 | 1274 → 1393 | 11568 → 11376 | 1.736831 | 0/7 |
| sparse32 | markowitz | 1.132893 | 273376 → 297480 | 3848 → 3984 | 11488 → 11276 | 1.726824 | 0/7 |
| dense32 | native | 0.985160 | 755632 → 744840 | 1282 → 1261 | 25696 → 27256 | 1.060710 | 4/7 |
| dense32 | markowitz | 1.000693 | 349712 → 339912 | 1132 → 1129 | 25696 → 27256 | 1.060710 | 3/7 |
| sparse96 | native | 1.161275 | 663576 → 699952 | 2513 → 2117 | 32208 → 28360 | 1.675493 | 0/7 |
| sparse96 | markowitz | 1.111570 | 770216 → 822992 | 10571 → 10347 | 31808 → 27860 | 1.672242 | 0/7 |
| dense96 | native | 0.843831 | 4682104 → 4524912 | 2785 → 2091 | 173152 → 189560 | 1.094761 | 6/7 |
| dense96 | markowitz | 0.811318 | 2598264 → 2471168 | 2635 → 2167 | 173152 → 189560 | 1.094761 | 7/7 |

Both dense96 cells meet all first-process cost conditions, with about16–19% lower paired time and reduced median bytes/events. Both dense32 cells pass allocation and memory gates but miss the required5% time improvement. All four sparse cells fail time, allocation-byte and checkpoint-memory gates; sparse96 event counts decrease, which does not compensate for increased bytes.

Every measured final graph pair passes the+10% limit. The `memory_gate` in the original audit combines final and probe memory; sparse failures arise before refactor at intermediate checkpoints. The worst sparse32 native checkpoint is step1:18,528→32,180B; sparse96 native step1:55,136→92,380B. Refactor resets the structure, so final graphs alone would hide these increases. This is a saved-graph observation, not a native allocator attribution.

All distributions, GC samples and outliers remain in the raw files and audit. One short process cannot establish universal or public-solver speedup. The prescribed opposite-order second process is not eligible because the first process failed the fixed all-eight gate.

## Work and memory scope

The driver times the same lifecycle on both sides. Source budget:200 constructors,400 refactors,1,472 replacements,2,944 FTRAN and1,472 BTRAN entries across timed/preflight/probe work; no factor copies. These API/source counts are not a complete observed native-backend budget. Timed instrumentation has14 literal clock sites and70 executed explicit time_ns reads/lifecycle; internal @timed work is additional. Untimed source-inverse probes record29 storage counters and11 checkpoints/cell; the separate64-insertion structural growth probe has no backend solve. Full backing-capacity/header/descriptor/slab/row accounting is retained in raw probes.

No production source changed. The observed sparse time/byte/retention increases are material costs and fail acceptance; they are not justified by additional numerical safeguards. This result does not isolate hardware/cache causes or prove a different design impossible. All original source, numerical order, policy, tolerances and precision remain fixed.

## Provenance and next boundary

The first seal invocation refused session-specific PATH drift before creating any run directory/reservation. Original refusal is preserved in preseal-refusal.json. Independent environment review verified identical resolved tools, then accepted subprocess-only restoration of the original pinned PATH via scoped-entry.py. No persistent environment, source or frozen control was edited. The subsequent seal and exact-stage admission preceded the single numerical launch.

Independent exact-stage admission passed169 checks and bound1,825 inputs plus20 supporting evidence files, including the separate timing-count erratum. The original audit and new11-check postcheck remain distinct. Independent result review is stored in result-review.md and the run result-review.json; diagnostic closure does not relabel failed cost gates.

One read-only exploratory inspection initially asked for nonexistent probe["checkpoints"] and raised KeyError; the stored schema uses probe["states"]. It altered no files, checker, gate or numerical output. The corrected read confirmed the checkpoint figures above.

Frozen inputs and all resulting scripts/raw/checks/reviews must not be rerun or rewritten. Master26e2291745999f485a74f643298ca997d65c7205, production/src/test/environment/CI remain unchanged; CIoff,HHreuse disabled,automation paused. The broader performance plan remains open, but this exact design has no further cost execution allowance under its stopped contract.
