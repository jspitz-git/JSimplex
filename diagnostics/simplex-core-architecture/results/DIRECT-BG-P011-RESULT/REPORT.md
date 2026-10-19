# P011 reduced-wrapper diagnostic result

One independently admitted p011-300 attempt completed with Julia/guard exit0 and a passing complete auditor. Supervised time was7.050289828s (limit300s); guard interval6.500707796s. These inclusive intervals are not kernel benchmarks. The external post-return closure covers277 historical/new process groups AND sessions, with no visible Julia or remaining owned processes. Six resource samples had minimum available RAM22,231,908KiB and swap0; child maximum RSS489,704KiB. Master26e2291745999f485a74f643298ca997d65c7205 and diagnostic launch HEAD11ebe6bdd401084205ebe628d35539ebb2d5e8ae remained unchanged during execution.

## Measured scope

The unchanged reduced driver ran12 first/warm/sample records, including four alternating sample pairs. All17 payload files were present: four preparation records,12 individual records and raw. Decision/assignment predicates and full before/after input/replacement owner/value checks passed. Exact loaded paths and all sealed/launch hashes matched. No warning, world-age warning, timeout or cleanup error was reported. Each of the eight sample rows has zero compile/recompile/GC in all three outer windows. The60 eligibility calls are a source-schedule count, not an observed optimized-call count; all use the n32 dimension rejection. No factorization, basis solve or BG update lifecycle was run.

| Sample arm | Inner bytes (each of4) | Inner events (each of4) | Byte-wrapper outer bytes/events | Event-wrapper outer bytes/events | Consumed-result bytes/events |
|---|---:|---:|---:|---:|---:|
| Reduced original-shaped |608|4|1232/9|1232/9|400/3|
| Concrete Carrier helper |400|3|800/6|800/6|400/3|

Bytes and events are separate executions. Outer wrapper counters include measurement work; consumed-result includes a typed Ref store and is a separate scope. All12 consumed-result records show400bytes/3events. No cross-scope subtraction is used to assign causes. Sample byte-wrapper times are1.2–1.3microseconds in both arms, event-wrapper1.1–1.8microseconds original and1.0–1.3microseconds concrete, and consumed-result0.5–0.7microseconds original and0.6–1.0microseconds concrete. These four short pairs are not evidence of meaningful kernel or end-to-end speedup.

## Preparation costs

| Recorded scope | Seconds | Bytes | Events | Compilation seconds | Recompilation seconds | GC seconds |
|---|---:|---:|---:|---:|---:|---:|
| Load from driver start |3.727998874|213189144|3706122|0.698108976|0.065812905|0.057207405|
| Fixture setup |0.0000518|253000|1168|0|0|0|
| Before snapshots |0.086374004|19152048|349357|0.086201004|0|0|
| After snapshots |0.0001204|158712|1285|0|0|0|

First original byte-wrapper additionally reports0.0044429s compilation; first-call order shares already loaded/compiled code and is not an independent cold comparison. Preparation compilation and allocation traffic remain visible; counters are not peak/live-memory estimates. Startup before driver line1, surrounding driver compilation/bookkeeping, serialization and pre/post hashing lie outside some recorded windows. The table is not a complete process decomposition. The before/after cost difference includes first-time compilation and is not an optimization result.

## Decision and next boundary

The concrete helper reduces the recorded inner cost relative to the reduced original-shaped wrapper, but both remain nonzero. Changing the wrapper alone does not establish the zero-allocation property. The equal consumed-result observations also leave residual costs unresolved. These observations do not identify allocation sites or prove a boxing, inference or return-materialization cause. The original historical P011 caller was not re-executed, so its exact allocation magnitude/cause remains unmeasured; its failure and the six unreached N026 checks remain preserved. No RED/GREEN acceptance, candidate promotion or changed numerical policy follows.

Recommended next work is bounded source/IR-attribution design targeting the residual400bytes/3events and the wrapper-dependent difference, preserving the existing oracle and candidate. Start from these saved records and pinned source; any new Julia introspection or allocation profiling needs a separately prepared concrete driver and admission. Do not repeat this measurement or weaken P011 on the basis of the present result.

No production code changed and no unnecessary production computation/allocation/retention was introduced. Diagnostic fixture/snapshot storage, typed sink, integrity hashes and resource polling are bounded and separately scoped; they do not measure native-memory retention or general BigFloat/rational behavior. This result closes only the diagnostic attempt. The broader BG plan remains open.
