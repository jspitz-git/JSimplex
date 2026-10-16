# Dynamic BG U: GREEN correctness qualification

Exactly one independently admitted `green300` run completed successfully. All **8,776 assertions in nine groups passed**, with zero failures, errors, or broken tests. The original admitted auditor passed; a separate 15-check postcheck and independent 32-check result review passed. No numerical run or original auditor was repeated. Actual production source, tests, environment, CI and master `26e2291745999f485a74f643298ca997d65c7205` remain unchanged.

## Admission and world age

The sealed run binds 1,889 files; independent admission binds these plus the seal, with 32 supplementary evidence bindings. Fresh host/process identity, source/stage/runtime/environment, accepted RED and resource gates passed before launch. Independent admission accepted the exact 81-file GREEN stage and the frozen driver without modification.

`WORLD-AGE.md` and `WORLD-AGE-RUNTIME.md` document the include/binding accesses and installed Julia 1.13.0 source, headers and read-only disassembly. `invokelatest` protects the method invocation, while preceding module/function binding access can still warn. The installed compatibility branch permits the backdated constant access under this run's options. This is scoped to the pinned runtime, not a guarantee of future compatibility or a warning-free driver.

Seven warnings actually occurred: Main.DynamicBGSlotTests, DynamicBGSlotTests.run_slots, Main.DynamicBGTests, and DynamicBGTests.lifecycles, rejection_and_aliases, export_modes, focused_updates. Every expected suite began and ended. All warnings remain verbatim in run.log; none were suppressed or repaired. The source/header evidence is newly read admission evidence, not a retroactive RED launch pin.

## Results

| Group | Passing assertions |
|---|---:|
| Import and stable q | 51 |
| Unlink, exact zero, free reuse and local guards | 154 |
| Capacity and allocation failure | 56 |
| Swaps and rotations | 53 |
| Checker detects corrupt structures | 13 |
| Seven fixed fixtures, two policies, direct reference | 7,634 |
| Private scratch and supported routes | 115 |
| Fallback, normalization fallback, q, transactional refactor | 461 |
| Exact storage branches, failures, ordering | 239 |

These tests qualify the scoped candidate's structural, ordering, ownership, supported-route, differential solve, export and failure assertions. They do not qualify public solver trajectories, other backends or a production integration.

The child exited zero. Inclusive supervisor elapsed time was 14.07480891700834 seconds under the 300/292 second limits; **this is not a benchmark**. Thirteen resource samples had minimum available RAM 22,311,372 KiB and zero swap usage; terminal available RAM was 22,861,612 KiB, child maximum RSS 689,904 KiB. Runner PID/PGID/session 357653, start_ticks 22063209; child PID/PGID/session 357654, start_ticks 22063261; boot 284d2228-1d9a-4c5f-913c-b9f1098b5838. Post-exit checks covered all 232 historical/current process groups and sessions, with no matching processes or Julia remaining. Visibility limitations remain those recorded by the host collector.

## Work and memory scope

The frozen source-derived ledger is 62 manager constructors, 132 refactor attempts (194 backend attempts total: 110 native and 84 Markowitz, including 14 singular cases), 26 copies, 698 FTRAN and 238 BTRAN valid solves, 212 replacement entries including two expected partial failures, and rejection cases of 24 solves, 14 replacements and four factories. There are 196 unit-metadata entries; exports comprise 132 real, 30 supplied, four unavailable and 14 throwing; native orientation solves have an upper bound of 66. Maximum dimension is 16. These are source-derived entry counts, not dynamically observed full backend work counters.

No new production code was introduced by this qualification. No unnecessary new production work or retained memory was found by independent review. Diagnostic structural scans, reference comparisons, snapshots and test bookkeeping are intentional correctness costs; their inclusion does not measure candidate speed or allocation savings. Allocations, retained memory and comparative timing remain unqualified pending Task3 cost measurements.

## Evidence and next step

Raw evidence is under `../DIRECT-BG-DYNAMIC-DRIVER-PREPARATION/runs/green300`; the accepted `result-review.json` binds every other run file. Admission and result review scripts/proofs in this directory are separate, executed once. Original RED, all frozen candidates/tests/stages and controls remain unchanged. GREEN allowance is consumed; no retry, GREEN600 or cost process was launched.

Next is offline preparation of the concrete Task3 comparative cost driver and launch conditions, followed by independent review before any cost run. Preserve the accepted fixed sparse/dense cases, matched backend arms and full preparation/work/allocations/retention timing scope. Correctness PASS is not performance acceptance or production promotion.

Current RED STATUS/roadmap closure/publication bindings will map only to this directory's exact before-GREEN copies through continuation-map.json. All older mappings remain unchanged. Separate closure and exact staged-name/blob publication proofs precede diagnostic commit/push. Master, CI-off, HH-disabled and paused automation remain unchanged; the broader plan stays open.
