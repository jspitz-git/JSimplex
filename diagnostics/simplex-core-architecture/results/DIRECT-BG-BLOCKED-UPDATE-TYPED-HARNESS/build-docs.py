from pathlib import Path
import json,hashlib,re
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');B=R/'diagnostics/simplex-core-architecture/results';D=B/'DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS';F=B/'DIRECT-BG-BLOCKED-UPDATE-HARNESS'
def put(n,v):
 with (D/n).open('x') as f:f.write(v)
for name,src in [('build-driver.py','/tmp/bg-typed-driver.py'),('build-tests.py','/tmp/bg-typed-tests-build.py'),('build-docs.py',__file__)]:
 with (D/name).open('xb') as f:f.write(Path(src).read_bytes())
put('builder-provenance.md','prepare.py was saved before execution. build-driver.py and build-tests.py are exact copies of the new /tmp scripts after execution; build-docs.py is saved during execution. These copies document generation, not retroactive launch/self-input pins. No old builder was executed.\n')
put('REPORT.md','''# Blocked BG U typed RED/GREEN harness preparation

Prepared a new isolated harness from the accepted blocked-update Task2 design, incorporating the **byte-identical accepted shared-zero panel** and **byte-identical accepted typed P011 structural module**. Both future phases use these corrections; only the numerical stream subject switches scalar RED versus blocked GREEN. The original algorithm, pivot policy, tolerances, fixtures, reference route and all lifecycle/numerical test expressions remain unchanged.

The fault-injection panel receives the same immutable zero-tuple declaration and three replacements. Its exact inverse returns the frozen original fault source; all hooks, mutable counter owners and fault adapter remain unchanged. Existing immutable-zero qualification established counter-owner independence; no mutable shared object or new cache is introduced. This clone composition is newly prepared, not yet runtime qualified.

New driver includes all modules at top level before main, uses the repaired ordinary 75-file master stage, and writes each unit in finally. Twenty-eight ordered units cover the four panel groups, lifecycle/fault tests and 26 numerical streams. RED permits exactly six N026 blocked-route coverage failures, never P011. GREEN requires zero failures. All **168 source assertion sites** have frozen fixed or event-dependent multiplicity rules; a single pre-execution aggregate would misrepresent allowed pivot trajectories and optional catches.

The complete auditor checks 60 exact payload files (28 units, 28 unit cost records, three loading records and raw), source/runtime/environment/stage identities, admission and reservation linkage, process deadlines/resources/exit, all counts and actual observations, source-bound pre-entry API budgets, logs and external closure. It fails closed on incomplete output. Preparation costs explicitly include compilation and serialization; load records overlap and no speedup is inferred. See ADMISSION.md and MEMORY-WORK.md.

Fresh entry verified diagnostic 2821702085f6bdaceb48c71a8774c99200e242eb, master 26e2291745999f485a74f643298ca997d65c7205, all 286 historical groups AND sessions absent and no visible Julia. Prior typed GREEN 11768/11768, original RED failure, immutable-zero evidence and all historical raw records remain unchanged. New Python synthetic tests and source checks are offline evidence only. Independent review disposition is recorded separately.

No Julia query, parser, import, compilation, test, seal, outer, launcher, reservation, release or numerical output was executed/created here. No production/test/environment/CI/master/global STATUS/roadmap edit. Ordinary setup and broader Task2/Task3 remain unqualified. Completed artifacts are frozen after publication; later RED needs a fresh exact-run admission.
''')
put('ADMISSION.md','''# Concrete blocked BG U typed RED/GREEN admission preparation

**PREPARATION ONLY.** The current user explicitly prohibits Julia. Only future phases `red300` and `green300` in this new directory are prepared. Old RED/RED2/P011 reservations and outputs are never reused. An accepted offline review does not admit execution.

## Sources and routing

Ordinary master 26e2291 stage has 75 exact files; no rejected export-specialization loader. Driver includes recorder, the local shared-zero panel and unchanged adapter, isolated amended fault panel and unchanged fault adapter, typed structural tests and unchanged instrumented numerical/lifecycle tests at top level before main. No eval, invokelatest, method overwrite or inside-main includes. P011 helpers are included exactly once as part of the accepted test module. Both phases run candidate component prechecks; RED is scalar only for the stream subject.

The new panel is byte-identical to DIRECT-BG-ZERO-COUNTS-CANDIDATE/panel.jl (19dccf0d5259d730b19333b2b1c685a50ee76f93d2cc3b242cb54a762cae9295). New panel-tests is byte-identical to DIRECT-BG-P011-TYPED-REPAIR/panel-tests.jl (15faee72f0f40bddae911818379c99d56aeb4a96e24cb7ce901691f188888910). Fault transform has an exact inverse and does not change hooks. Source copies, transformations, qualified P011 GREEN receipt and all supporting inputs are frozen before any future seal.

## Oracle and fixed schedule

Same fixture file/order and 28-unit roster: panel; lifecycle; 13 fixtures times native threshold_one then Markowitz default. All original mathematical, preservation, factor/history, pivot and failure-cache predicates stay unchanged. Original-B FTRAN/BTRAN and chronological H-to-U exact residual bounds remain 128*n*2^-52; FMA may alter trajectories but no pivot-policy/tolerance/precision adjustment is admitted.

Panel must pass exactly11768 assertions in groups31/11619/74/44, all P001-P102 with their fixed multiplicities. P011 and P095-P102 require the four zero allocation counters, complete decisions and unchanged values/owners. No extra standalone P011 probe is added. Lifecycle L001-L040 and trace N001-N012 have fixed/conditional counts, including recorded optional catches. Streams N001-N026 have exact event-conditioned counts, complete API attempts and observations. Total source-site universe168. Exact aggregate is computed only by these predeclared formulas, never selected after output.

RED expects only N026 once in dense96/native, dense96/markowitz, dense256/native, dense256/markowitz, dense96-long32/native and dense96-long32/markowitz: **six failures**. All remaining assertions pass; no errors/broken/skipped/missing sites permitted. These failures demonstrate absence of the blocked route, not a solver defect. Unexpected unit failure saves that unit and raw prefix then stops before later units. GREEN requires accepted NEW RED audit, external outer closure and independent exact result receipt before sealing; no historical RED2/P011 result substitutes for this prerequisite.

## Process and immutable admission

Future one-attempt supervisor limit300s, inner guard292s; one Julia/BLAS thread, gcthreads1,0, heap hint2GiB, VM8GiB, available RAM>=6GiB, swap<=1GiB, compiled-modules=existing. No long model solve. Cold exact-rational relations can be cubic; fitting300s is not claimed. All timeout, resource or correctness failures remain failed and preserved. No auto-retry. A timeout-only extension needs separate reviewed conditions; no performance tuning follows a failure.

Future sequence: fresh refs, boot/start_ticks/commands and complete historical PGIDs AND SIDs/no visible Julia; waiting-only new-session outer; exact seal; independent exact-run acceptance; explicit release; one reservation and guarded execution. Preparation review must say launch_admitted=false. GREEN predecessor propagates external closure groups (including RED outer), avoiding the prior posthost-only omission. New permanent history starts with all286 IDs. Launch pins include seal/admission/prehost/release/outer invocation; exact member/resolved hash and tree checks remain active. Future host must match the seal. Ordinary loader pins do not prove hidden cache/loader neutrality.

## Complete output and audit

Separate exclusive payload and guard output. Payload exactly60files: raw.toml, unit-1..28.toml, cost-1..28.toml, load.toml, panel-load.toml, tests-load.toml. Each unit writes in finally before unexpected-failure handling. Each completed unit gets a cost record including its serialization and status check; a thrown unit may lack cost and will fail the complete audit. Raw is saved before aggregate exit when main is reached; early import/termination may leave only logs or a prefix. No missing output is treated as success or automatic timeout-only proof.

All31 cost records require exact six fields, finite nonnegative seconds<=300 and nonnegative integer bytes/events. Compilation/recompilation/GC are recorded rather than required zero in cold tests. Loader cost overlaps panel/test module records. Unit cost includes existing test compilation, snapshots, rational arithmetic, recorder and unit serialization; cost/raw serialization and startup/host/pin scans remain outside these partial records. No sums of overlapping measurements, no benchmark/speedup acceptance.

Auditor validates every file schema, site multiplicity, named group, failure identity, API attempt, trace begin/finish/panel/pure-row count, positive route and per-update observation. It reconciles every raw aggregate. Logs require28BEGIN/END pairs and precisely the six saved failure renderings for RED; warning/world-age/overwrite/error text is checked before any allowed failure removal. Numeric Test rendering is diagnostic, not an allocation-size oracle. Complete process/command/cwd/deadline/reservation/receipt/pin/resource identities and strict exit are mandatory. Any malformed, missing, extra, symlinked, interrupted or unexpected output rejects. Independent saved-result review and external full-group closure are required after execution.

No Task3 measurement or production integration is admitted by this preparation.
''')
put('MEMORY-WORK.md',(F/'MEMORY-WORK.md').read_text().replace('160 assertion sites','168 assertion sites').replace('28unit files+one raw file','28unit files +28unit cost files +three load files +one raw file').replace('one cheap-reject allocation check','the qualified typed P011 direct/consumed zero-byte/event checks')+'''

## Typed repair and preparation-cost amendment

The structural module is the accepted typed repair, adding eight assertions. One cold probe in that suite performs five warm and four measured eligibility entries plus P012 (ten entries versus three in the original structural code). It has a concrete typed Ref and two snapshots, each copying104leaf arrays plus three containers and retaining141 owner-reference slots including repeated references. Copies scale with n and packed/index/cache data, are outside the four inner allocation meters, and do not escape through returned probe data. This harness adds no second standalone probe. Existing snapshot/Test/compiler bookkeeping and exact arithmetic remain additional.

The hot candidate uses one immutable NTuple20 zero constant in three places; independent mutable BGPanelCounts objects still own distinct mutable identity. The fault namespace has its own immutable binding with the same values, not a shared mutable counter. No extra candidate vector/matrix scan, solve, refactor, per-step snapshot or mutable cache is added. No production code changes, so no new production computational or memory cost. The fault amendment is source-equivalent to the accepted constant change but its full lifecycle composition remains unexecuted.

New preparation instrumentation adds three top-level timing records and28 fixed unit timing records. Each creates a small metrics dictionary and output file; unit costs include test work, compilation and unit serialization. Load overlaps two module load records. Extra cost-file/raw serialization, dispatch/startup and host integrity work remain outside. No forced GC, hidden warmup, changed math or additional test case. All costs remain visible; zero inner P011 counters do not mean zero whole-test/process allocations. No Task3 cost gate or speedup can be claimed from these cold records.
''')
sites={}
for name in ['panel-tests.jl','lifecycle-tests.jl','numerical-tests.jl']:
 for i,line in enumerate((D/name).read_text().splitlines(),1):
  for site in re.findall(r'@check(?:throws)?\s+"([PLN]\d{3})"',line):
   if site in sites:raise RuntimeError('duplicate assertion site')
   sites[site]={'file':name,'line':i,'source':line.strip()}
if len(sites)!=168:raise RuntimeError('site universe')
put('assertion-sites.json',json.dumps(sites,indent=2)+'\n')
print('Saved concrete admission, work ledger and168sites')
