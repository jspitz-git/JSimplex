from pathlib import Path
import json,sys
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER';Q=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-RED');N=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-PREPARATION');sys.path.insert(0,str(D));import control as c
report='''# Fixed post-warm GC preparation amendment — OFFLINE ONLY

This separate driver adds exactly one requested full GC after both sides of the existing third warm pair in each of sparse32, dense32 and sparse96, before pair4. Both RED and GREEN use this same schedule. No Julia, parser, import, compilation, numerical workload, profiler or launcher has been executed for this amendment. Runtime correctness, finalizer warming and performance improvement remain unqualified.

## Why this change

The sole prior RED300 attempt (diagnostic commit509fa509fdd8d3187e5aac6a4229bce707ffe227) is rejected. It saved two expected allocation failures, then stopped on measured compilation in sparse96 candidate pair5/order2: compile0.0068022s, GC0.031775499s, whole0.039607799s and refactor2 wall0.039375399s. It is the first GC-containing saved window, not proven first collection of the process. All50saved windows/1200residual bindings were independently reviewed; original false audit remains false/non-timeout. No method-level compilation trace exists. Installed pinned UMFPACK registers Julia Numeric/Symbolic finalizers; successful exported BG stores no ordinary native fallback. GC-associated lazy compilation is a source-supported hypothesis, not an identified compiled method or proven compiler cause.

The human explicitly requested this separate amendment. It supersedes only the prospective preparation schedule for a future newly admitted experiment, never changes the old plan/raw/driver, and cannot retroactively accept RED300. Standing short-run authorization persists; this turn is explicitly offline.

## Exact changes and interfaces

`driver.jl` is the complete old driver with six explicit transformations recorded in source-map.json: header; fresh phase IDs redgc300/greengc300; top-level preparation.jl include after kernels; one pair==3 call after the paired output/mode check; completion counter gate; two raw-finally counters. Full text inverse recovers the old driver byte-for-byte. Kernels, recorder, inputs and expected-tests are byte-identical copies. GREEN still includes the four frozen Task1 test files by their original absolute paths. No include occurs inside main or a timed window.

`prepare_gc!(cell,fixture)` receives only an integer and name. Existing window() has returned its detached data after complete factor checks; no whole factor/timed result is passed into the helper or stored in its two counters. Existing paired dictionaries and fixture/output storage stay in scope as before. Scope exit/source lifetime is not proof that every object is unreachable or collected.

The helper checks calls==completed==cell-1, increments attempted calls before invoking `@timed GC.gc(true)` once, saves `preparation-<cell>.toml`, then increments completed. It returns nothing. No extra factor constructors, solves, updates or refactors, no extra warm pair, no loop until stable, no manual finalization, GC disabling or finalizer disabling. The original 3warm+7observed alternating pairs, compile/recompile-zero observed gates, numerical predicates, seven-sample allocation conjunctions and source arithmetic remain unchanged.

A thrown GC or saving failure escapes to existing fatal handling; finally records preparation_calls and preparations_completed alongside the original Test tree. A failed GC may lack its cost row; a failed save may leave a partial file. Both require rejection/preservation, not retry. Count3 is required before raw complete=true. Counters count source-bound attempts/records, not hidden native finalizer calls. New expected Test totals remain3RED allocation failures and8640GREEN passes if all prospective checks succeed; require() gates do not add Test assertions. Their outcomes are not guaranteed.

## Preparation output schema

Each row has exactly18keys: phase,fixture,cell,after_pair,before_pair,requested_full_gc,calls,cumulative_calls,returned,seconds,bytes,events,gc_seconds,compile_seconds,recompile_seconds,gc_pauses,full_collections. Identity is exact newphase / cell1..3 / fixed fixture order / after_pair3 / before_pair4 / one request / cumulative_calls=cell. Booleans must be actual booleans. Metrics must be finite/nonnegative; counters must be actual integers, not booleans. Preparation compilation/GC is allowed and reported, never subtracted from lifecycle measurements. GC and compilation intervals may overlap: no sum-based bound or subtraction oracle. Record the actual GC pause/full-collection counters without assuming precisely one observed pause/collection or complete native cleanup.

`preparation_schema.py` is a pure validator, NOT a complete run auditor. Full output needs all3records; partial output permits only the correctly named cell prefix. It rejects missing/extra keys, invalid identity/order/counters and nonfinite/negative metrics. Future admission must also bind source, output membership, raw attempt/completion counters, process/exit/resources, modules, all original windows, all Test counts and exact residuals. Synthetic Python tests do not parse or execute Julia.

## Work and memory budget

The unchanged lifecycle schedule has60windows,60constructors,120refactors,480updates,960explicit FTRAN and480explicit BTRAN,1440saved solve outputs;18warm+42observed windows. Backend internal work/orientation calls and the complete GREEN structural suite remain additional as documented by the original Task2 package. No new solve or candidate operation is introduced.

New cost: exactly3full-GC API requests per complete process, plus3preparation records and2cold Ref counters. A fixed request count is NOT a bound on collection work: each full collection traverses process-wide heap roots/live objects, and finalizers depend on accumulated managed/native garbage, including earlier fixtures, imports and GREEN structural suites. Native frees and finalizer compilation may be additional. No native-memory-release or bounded-duration claim follows. The future300second guard must include preparation, not give GC an extra unguarded allowance.

Each preparation @timed captures the GC expression's elapsed time, managed/runtime aggregate allocation bytes/events, GC time and compilation/recompilation; pauses/full collections are counter deltas. The helper entry/counter checks, @timed result construction,18-entry dictionary, serialization/file I/O and final counter increment are outside that inner accounting. They are additional cold diagnostic work and remain included in future whole-process duration/resources; do not label the inner row as complete process-startup or all preparation overhead. No array of factor roots or growing preparation ledger is retained. The final raw adds2scalar fields. Three output files do not imply three allocations.

The amended schedule changes heap state and later GC placement even when applied symmetrically. Compare reference/candidate and RED/GREEN only under the new declared schedule, preserving their distinct setup/structural-test histories. No per-window GC is added, in-window GC stays enabled and every raw/outlier is preserved. Neither old/new cross-process timing nor removed cold cleanup can be credited as a production kernel speedup. No new production work, retained fields, scans or numerical safeguards are introduced or removed.

## Execution remains a separate task

No launcher, reservation, seal or numerical admission is created here. New phase IDs deliberately cannot pass the frozen launcher's phase configuration. Do NOT pass this driver to that old launcher/auditor: the old output-membership/raw schema rejects the new records. Future preparation must create a separate admission/auditor for new phase IDs, include the3preparation TOMLs and2raw fields in strict schemas, reconcile request/completed counts with each present record, bind the unchanged full lifecycle tests and use new output paths. Complete successful runs require3records and calls=completed=3; any preparation fault rejects. Partial timeout review must account for attempted-but-incomplete GC without assuming a record was written. The old RED is not a successful predecessor and not a pure-timeout retry base; GREEN requires a new separately accepted RED result under this amendment.

Before any future run: fresh host refs/boot/startticks/commands/all259groups ANDsessions/noJulia, exact new manifest, independent concrete admission; limits300/292s,oneJulia/BLAS1,heap2GiB,VM8GiB,RAMfloor6GiB,swapceiling1GiB. Do not enable CI/HH reuse or edit source/test/env/master. Preserve all old frozen failures and reviews. A future repeated measured compilation remains a rejection; do not adaptively change warm-up, drop samples or weaken the compile gate.
'''
with (N/'PREPARATION.md').open('x') as f:f.write(report)
with (N/'request.txt').open('x') as f:f.write('Prosím připrav oddělenou úpravu driveru s jedním GC po zahřívacích párech každého případu, včetně záznamu nákladů přípravy, a nech ji nezávisle zkontrolovat, zatím bez spuštění Julie.\n')
paths=set(c.preparation())
for p in [Q/'publication.json',D/'publication.json']:
 j=c.rd(p);c.require(c.bindings(j),'Prior publication drift');paths.add(str(p));paths.update(str(c.path(x)) for x in j['sha256'])
paths.update(str(p) for p in N.iterdir() if p.is_file())
c.save(N/'preparation-pins.json',dict(sha256={p:c.sha(p) for p in sorted(paths)},scope='Offline preparation read-time bindings, not a launch seal; old paths preserve original provenance'))
print('Saved preparation report and read-time bindings',len(paths))
