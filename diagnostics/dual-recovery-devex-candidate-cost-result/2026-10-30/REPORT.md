# Devex fallback: candidate and reference normal-API cost comparison

**Ordinary candidate tests: 272/272, child exit 0. Canonical audit accepted: True. Strict paired cost gates accepted: True.** Independent result review remains required. Production admission and master integration are not granted by this result.

Exactly one candidate-cost process ran against the frozen accepted reference. Actual solver src/test/environment/CI/master were unchanged. The original driver, fixtures, source overlays, guards, numerical tolerances and all original assertions were preserved; no tuning or retry was performed. Prior failed GREEN and all earlier raw evidence remain unchanged.

## Concrete admission and work

The candidate was independently admitted with 4744 true checks and 964 SHA bindings, including all 589 exact pins and the full closed reference. Admitted HEAD is 14720147d8850525c0603921064dfe3ba83d3fcb; master remains c0fa748ffa61ccb7c1caaf248c40324f60bc737b. Seal SHA256: 671caa90ed4bf4c5222fad3e35ae295792dfea5cbdf93a4f4ad395339a3934d1; pins SHA256: 693784a3acb3407812175b44d370bd165f86c9a1584907b2426845a51ccec8f1; admission SHA256: 7fc72cd5336c8779a503868256a48543d07b1f373f1984d80d21cbba848c3f3b. Fresh full739-group/session/identity/noJulia/resource/refs checks preceded admission and launch.

Eight fixed 64-dimensional Float32/Float64 cases cover sparse/dense coefficient patterns and reliable/finite-unreliable quality. Both matrix patterns are CSC, with190/4096 nonzeros; dense does not mean a distinct dense-array backend. Each case retains three warm and seven measured whole API calls plus one explicit post-warm GC. Per side there are80 whole API entries,40 real correction BTRAN entries,40 stop entries,eight explicit GCs and56 measured records. Whole calls retain original dimensions/alias guards, basis validation/assembly, RHS scratch copy, quality/refinement, stop and quality recording. A private factor forwards a real transposed solve before declaring zero correction in unreliable cases; this tests a controlled quality boundary, not native backend accuracy.

Reference uses the source-qualified exact legacy body with original helpers; candidate invokes the actual shared-kernel API. All74 files of its project match the tested GREEN2 candidate. All original input/policy/error/output bits, owner checks and work counts pass the ordinary assertions and complete canonical typed auditor. No generated-machine-code identity claim follows from source equivalence.

All56 candidate measured records have zero bytes/events/compile/recompile/in-windowGC: **True**. Reference had the same zero counters in all56 records. Paired per-case gates require median bytes/events and retained fixture graph not to increase, without a percentage waiver. Canonical audit error: `None`. All8 comparison entries and raw samples are retained even if a gate is false.

## Whole API comparison

Times are microseconds; ratio is candidate/reference. Ranges and MAD refer to candidate's seven samples. Graph is reference/candidate Julia fixture bytes.

|Type|Pattern|Quality|Reference median µs|Candidate median µs|Ratio|Candidate range µs|MAD µs|Candidate median B/events|Graph B|All strict gates|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
|Float32|sparse|reliable|1.5|1.7|1.133333|1.4–13.4|0.2|0/0|64596/64596|True|
|Float32|sparse|finite-unreliable|2.6|2.6|1.000000|2.5–26.2|0.1|0/0|64596/64596|True|
|Float32|dense|reliable|14.4|14.4|1.000000|14.3–26.4|0.1|0/0|158884/158884|True|
|Float32|dense|finite-unreliable|15.8|16|1.012658|15.8–41.4|0.2|0/0|158884/158884|True|
|Float64|sparse|reliable|1.6|1.5|0.937500|1.3–11.2|0.2|0/0|84296/84296|True|
|Float64|sparse|finite-unreliable|2.4|2.3|0.958333|2.1–19.9|0.2|0/0|84296/84296|True|
|Float64|dense|reliable|14.4|14.5|1.006944|14.2–24.1|0.2|0/0|272840/272840|True|
|Float64|dense|finite-unreliable|17.2|17.4|1.011628|17.2–39.1|0.2|0/0|272840/272840|True|

These are short windows from one sequential process per side, not temporally interleaved. Outliers, clock variation and compilation placement limit timing inference. There is no universal elapsed-time speedup gate and no end-to-end solver speedup claim. The purpose is to detect normal-API work/allocation regressions while retaining the separately qualified changed recovery trajectory. No change in iteration count is used as kernel performance evidence.

## Preparation and GC

Preparation tuples are seconds/bytes/events. Explicit GC records are separate and are never subtracted from API time.

|Type|Pattern|Quality|Reference preparation|Candidate preparation|Candidate post-warm GC|
|---|---|---|---|---|---|
|Float32|sparse|reliable|0.0001058/77376/194|0.0001109/77376/194|0.106005601/0/0|
|Float32|sparse|finite-unreliable|6.52e-05/77376/194|6.77e-05/77376/194|0.104239701/0/0|
|Float32|dense|reliable|6.19e-05/264512/202|7.52e-05/264512/202|0.0980476/0/0|
|Float32|dense|finite-unreliable|6.57e-05/264512/202|6.34e-05/264512/202|0.0960703/0/0|
|Float64|sparse|reliable|0.0003001/180264/274|0.0003152/180248/274|0.111847901/7552/170|
|Float64|sparse|finite-unreliable|8.89e-05/180168/272|9.05e-05/180168/272|0.1001797/64/4|
|Float64|dense|reliable|0.0002257/856528/283|0.0002382/856528/283|0.099637701/64/4|
|Float64|dense|finite-unreliable|0.0001979/856528/283|0.000197/856528/283|0.0974471/64/4|

Fixture preparation includes matrix/model/factor/workspace/private scratch setup. Owner census, saved input/model copies and result dictionaries are outside that profile and API windows but inside guarded process time. Entry compilation can occur outside individual profiles; measured zero compile counters do not mean process compilation is free. All warm/preparation/GC profiles and7 raw samples remain preserved. Base GC counters measure aggregate allocation traffic, potentially including native callbacks, not a native allocation/free ledger. summarysize(f) excludes surrounding snapshots/report dictionaries and hidden native memory; process RSS has a different scope.

## Process closure and shared limit

Candidate inclusive guarded elapsed: 37.37988920498174s. Previous use:1070.9948121299385s (including the actual37.39421487902291s reference and all prior failed time). Cumulative total: **1108.3747013349202/1800s**, remaining **691.6252986650798s**. Offline sealing/admission/final Python audit remain outside the defined guarded sum. Ordinary Test time 4.0s has a different scope and is not subtracted into startup/kernel cost.

All37 resource samples satisfy guards; minimum available RAM 22276368KiB, maximum swap 0KiB. Exact command/environment/interpreter/invocation, permit/current/gate/PDEATH9 hashes and identities, child/supervisor exits, no-timeout/kill flags and all589 unchanged inventory bindings were checked. Four dependency-import warnings remain verbatim; no loader repair was attempted. The canonical auditor explicitly deferred its live launcher, then standalone postexit closure and parent postcheck included it with all742 groups ANDsessions/noJulia.

- launcher: boot 781795f4-f7af-4c3b-9ce9-45c7cae76ecb, PID/PGID/SID 442277/442277/442277, start ticks 33923585.
- guard: boot 781795f4-f7af-4c3b-9ce9-45c7cae76ecb, PID/PGID/SID 442301/442301/442301, start ticks 33923647.
- child: boot 781795f4-f7af-4c3b-9ce9-45c7cae76ecb, PID/PGID/SID 442302/442302/442302, start ticks 33923664.

Child identity is the pre-exec gate, not a hidden Julia runtime command capture. Parent postcheck accepted is integrity/closure only; numerical/cost outcome remains the separate canonical audit. Standalone success closed.json exists only when canonical acceptance is true. All22 runtime files and102 external artifacts have explicit byte-exact portable maps. No runtime file was added or edited after closed.json, and the reference tree remains fully frozen.

## Computational work, memory and decision scope

No new production code, scan, solve, copy, conversion, persistent field, precision or safeguard change was introduced by this measurement/publication. The inherited shared kernel uses the same owned scratch, arithmetic and short-circuit ordering. Original finite/residual checks and alias defenses remain. Recovery-only eligibility norm/revalidation/reset work is real and was separately reported in GREEN2; it is outside these normal-API windows and is not claimed as a normal-path saving. Fixture/native/import/setup and update-chain operations are not fully instrumented by the80/40/40 entry counts.

The measured cost gate result is **True**. Functional GREEN2 and these normal-API comparisons have different scopes. Fixed64 Float32/64 cases do not prove general backend accuracy, all precisions, long chains, observer neutrality, native free balance, full-suite success or end-to-end solver speedup. Final independent paired result review is required. Any future production integration requires a separate concrete preparation/master verification step; this turn performs none. CI stays off, HH reuse disabled, all prior rejections remain preserved.
