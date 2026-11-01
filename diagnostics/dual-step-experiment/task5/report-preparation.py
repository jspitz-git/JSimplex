from pathlib import Path
import json,hashlib,shutil,os
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');D=W/'diagnostics/dual-step-experiment/task5'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2)
q=read(D/'postcheck.json')
if q['accepted'] is not True:raise ValueError('postcheck required')
g=q['qualification'];r=W/'diagnostics/dual-step-experiment/README.md';old=D/'README.md.before-Task5';shutil.copyfile(r,old)
expected=read(D.parent/'task4/closure.json')['bindings'][str(r)]
if sha(old)!=expected:raise ValueError('Task4 continuation bytes')
put(D/'continuation-map.json',{str(r):dict(sha256=expected,preserved=str(old))})
t=r.read_text();start=t.index('- Status:');end=t.index('\n',start);t=t[:start]+f'- Status: Tasks1–5 qualified. Opt-in complete-solve handoff composite qualification passed {g["assertions"]} ordinary assertions; four frozen sparse/dense cases executed normal E pivots and all twelve MPS configurations completed with matching original-model outcomes. [Task5 report](task5/REPORT.md), [work/ownership ledger](task5/WORK-MEMORY.md). Task6 total-cost comparison remains open; no master merge/push or speedup claim.'+t[end:];r.write_text(t)
qualified={}
for p in sorted((W/'experimental/dual_engine').rglob('*.jl'))+[W/'src/solver.jl',W/'src/dual_simplex.jl']:
 dest=D/'qualified-source'/p.relative_to(W);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);qualified[str(p)]=dict(sha256=sha(p),preserved=str(dest))
put(D/'qualified-sources.json',qualified);put(D/'source-aliases.json',{str(D/'project/src'):os.readlink(D/'project/src')})
rows='\n'.join('| '+x['n']+' | '+x['dense']+' | '+x['status']+' | '+x['commits']+' | '+x['sparse_prices']+' / '+x['dense_prices']+' | '+x['fallbacks']+' |' for x in g['activations'])
corpus='\n'.join('| '+x['name']+' | '+x['presolve']+' | '+x['reference']+' / '+x['candidate']+' | '+x['commits']+' | '+x['original_cleanups']+' |' for x in g['corpus'])
new=sum(v for n,v in g['testsets'].items() if n.startswith('Task5 '));legacy=g['assertions']-709-new
report=f'''# Task5 opt-in complete-solve handoff

Task5 of the approved experimental dual-engine plan is implemented and qualified on `codex/dual-step-experiment`, based on `8e31807121f4e709fcfca0d9ba379aa0a2199d8c`. Master `9940bdabe149e922afa60b5364227a7e7393bc75` is unchanged. Only `src/solver.jl` and `src/dual_simplex.jl` acquire minimal internal optional hooks; public `solve` remains unchanged and defaults to the original path. The experimental module remains opt-in, absent from default package initialization. No environment/CI/master merge/push. Task6 remains open.

## Complete-solve behavior and owner handoff

`E.solve_experimental` calls the existing internal solver once with a phase functor and original shared scalar deadline. Validation, original continuous model copy, presolve, scaling and initial/auxiliary feasibility remain existing code. Only the eligible main dual optimization boundary may import E. Unsupported type/backend/pricing/mutable observer and unqualified adaptive factor policy preserve legacy execution before engine import. Actual stop guard must wrap the same internal scalar deadline; arbitrary stop closures keep the legacy route. A no-pivot or presolve-only solve reports zero accepted pivots truthfully.

A fixed opt-in active-workspace/recoverability holder adopts the owned phase workspace before subsequent numerical catches, timeout/counter aggregation and ordinary cleanup. It allocates only when a hook is selected. A working `PrimalFeasible` outcome proceeds through the original cost restoration, recompute, optional primal cleanup, original witness/point certification, unscale/postsolve and original-model cleanup/retry. It is never directly converted to a public optimal result. Unsafe no-payload exits do not invoke workspace recovery. Exhaustion may request one verified main legacy continuation, without re-entering E. Original retry/cleanup/wide-recovery entries remain explicit notices with actual legacy diagnostic counts; a cleanup wrapper's internal retry is included in its cleanup entry, not separately claimed counted. No recursive public solve or complete solver clone.

Scalar output counters retain no EngineState/model/factor graph. A private accepted-event monitor carries legacy zero-step/nonzero-since-refactor/last-step scalars; a caller mutating its public output record cannot poison numerical monitor state. Event data is immutable; original event exceptions escape numerical catches by identity. Existing mutable observers remain on their original route and retain DiagnosticObserverFailure provenance. Import inherits min(configured, previously shortened) factor ceiling; original time/start/phase offsets/local iteration limit are unchanged. Tests cover the initial Nothing failure and actual late fault/deadline owner counters, not just nominal successful adoption.

Export adopts existing numeric/basis/factor/scaling owners through fixed wrappers. Three ratio lists become logically empty while retaining their actual backing Memory. Indexed steps/gains stay reserved. Ordinary legacy recompute validates its basic mask before use. No eager extra mask pass or factor-policy reconfiguration remains: fixed scheduling already uses actual updates and the inherited cap. Adaptive factor policies decline before import so their unqualified economic/growth checks stay on the original path.

## Observed ordinary qualification

Composite qualification: **{g['assertions']} passed**, **{g['skipped']} source-preserved platform skips**, zero numerical assertion failures across the accepted sections. The main GREEN2 whole process remains rejected for its missing-helper setup error; the separately admitted complete public regression process must exit0. Counts include709 unchanged Task1–4 assertions, {new} Task5 assertions and {legacy} assertions in seven unchanged whole regression files. Those files are native_basic_stationarity, native_certificate_recovery, native_terminal_primal, legacy_primal_point_recovery, dual_entry_phase, simplex_driver and solver_tests. This is focused qualification, not the full repository suite or x64/CI proof. Platform FTZ skips, if any, are explicitly reported separately and not counted passed.

All four preselected activation cases have real E commits, no main legacy fallback and zero outer original retry/cleanup/recovery. Sparse and dense pricing both execute. These cases were fixed before outcomes; no failed case was substituted.

| n | Dense input | Status | E commits | Sparse / dense prices | Main legacy fallback |
|---:|---|---|---:|---:|---:|
{rows}

All twelve fixed MPS/presolve configurations remain in the record. Original feasibility/objective checks and unchanged final certificates decide validity; iteration/state trajectories need not match reference. Presolve-only cases are inactive E cases, not engine speedups. The retained small coupled cleanup case separately reports genuine main activation plus original cleanup.

| MPS | Presolve | Reference / candidate | E commits | Original cleanup entries |
|---|---|---|---:|---:|
{corpus}

The new tests additionally check actual hook/default routing, unsupportedFloat32/HH/observer, immutable event exception identity, zero pivots, deadline/iteration payload absence, original input immutability, actual backing Memory identity after logical reset, ordinary native recompute, source shortened safety ceiling, consumed owner behavior, one honest infeasible legacy boundary, original cleanup, original witness rejection and unsafe17/9 counter/no-payload propagation. Test-only certificate and late-exception factor wrappers forward real native work before declared fault/substitution. The deliberate17/9 metadata are discrimination values, not17 real pivots/9 real refactors. No custom Test recorder/manual stack/emergency serializer; ordinary Test and plain case lines only.

## Preserved failures and review corrections

Initial469-pin RED observed4Pass/5Fail, zero errors, exit1 before implementation: missing opt-in interfaces and actual hook call/result. First461-pin admission rejected an unenforced staged source-directory alias; exact pre/post symlink and resolved source binding closed it, with original manifest/script/rejection preserved.

Initial506-pin GREEN source review withheld approval for Nothing initialization recovery and stale posthandoff crash-timeout counters. Separate522-pin boundary RED observed4Pass/2Fail, zero errors, exit1: actual FieldError(Nothing,:progress), and a genuine native FTRAN followed by5.05second fault delay under5second crash deadline exposing stale owner counters. The fault-triggered and TIME assertions passed. Minimal guard/order fixes were made only after this RED; exact ordinary test body is reused in a new GREEN file, never rerunning the frozen standalone driver. Source review also removed unnecessary N+m eager mask writes and redundant native factor/update metadata walks; native recompute/retained metadata tests prove existing preconditions suffice. Adaptive factor mode and arbitrary caller stop decline before ownership.

First admitted542-pin GREEN observed824Pass/1Fail, zero errors, exit1 after156.392704100s. Four designated activation cases and all twelve MPS cases passed; later full regression files were not reached. The sole failure was a wrong fixture premise: a coupled2x2 bidiagonal LP is not completely removed by presolve. The solver itself was unchanged. Keep the original zero-entry/pivot assertions on independent2x2 singleton rows, add a structural0x0 presolve check, and retain the original coupled LP separately with analytic31/16 objective, true E activation, original cleanup and original feasibility. Every old numerical/ownership/status assertion remains. No designated activation or MPS input was replaced. New565-pin GREEN2 independently admitted the test-only correction and observed all709+146component assertions plus2869assertions in six whole regression files, all passing. It then passed424assertions in the first13public-file testsets but encountered one setupError before the Phase-I/MAX logger assertions: RecordingSimplexLogger had not been loaded from the earlier shared workspace-test file. Its whole-process result remains rejected,4148Pass/1Error,1145.851168772s. No numerical assertion failed. A new independently admitted public-green completion loads the exact original definitions-only logger prefix and the entire unchanged solver_tests.jl, with E loaded in the same package context. Six already completed files/core855 are not rerun. Repeated424public prefix assertions must match exactly and are counted only once. This is explicit composite qualification, not retroactively passing GREEN2. All sources, shared helper bytes, inputs, tolerances, failures and old approvals remain frozen; there is no custom Test recorder or manual test stack.

Postexit offline composite checks accepted: **{len(q['checks'])}**, including all590 actual completion pins/resolved paths, strict historical461/469/506/522/542/565 version mappings, actual commands/admissions/resources/ordinary summaries, complete709 prior prefix, all4 activation and12 MPS records, retained coupled helper, current refs/full groups ANDsessions/noJulia and exactly the two planned source changes. Postexit check/review hashes are separate, not retroactive launch pins.

| Process | Accepted expected outcome | Inclusive seconds | Samples | Min available KiB | Max swap KiB | Child maxRSS KiB |
|---|---|---:|---:|---:|---:|---:|
'''
for stage in ['red','boundary-red','green','green2','public-green']:
 out=D/(stage+'-run');r0=read(out/'result.json');pr=read(out/'guard/process.json');samples=[json.loads(x) for x in (out/'guard/resources.jsonl').read_text().splitlines()]
 report+=f"| {stage} | {r0['accepted']} | {r0['elapsed_seconds']:.9f} | {len(samples)} | {min(x['available_kib'] for x in samples)} | {max(x['swap_used_kib'] for x in samples)} | {pr['child_maxrss_kib']} |\n"
report+='''
These inclusive times contain loading, compilation, setup, tests, diagnostic warm lifecycles and cold oracles; they are not performance samples. Per-case scalar elapsed records are likewise unpaired qualification output, not speedup evidence. Initial readonly pin I/O precedes reservation; the common1800s process allowance starts at reservation and includes final pin/terminal checks. No native allocation/free ledger, observer neutrality or complete hidden backend/import budget is claimed.

## Work, retained memory and continuation

Default nothing path constructs no engine/boundary/output record and adds no per-iteration/candidate scan, solve or copy. It retains original numerical bodies and one default finally options write. Opt-in adds fixed scalar/counter/owner headers; the private event monitor adds fixed scalar comparison/stores per accepted pivot, with their cost included rather than treated free. Bounded legacy diagnostics/dictionaries and64event capacity are setup/legacy costs that Task6 must match/qualify in its reference comparison. Record snapshots are scalar copies once on phase exit.

Phase import still performs the already-budgeted owned copies, current-B assembly/new native factor, row index and validation. Parent entryworkspace can overlap those owners until return; native/rebuild/finalizer retention is not inferred from Julia reachability. No whole factor/workspace copy per pivot or growing trace. Export keeps the same arrays/factor, up to3N source-level logical clear visits once and fixed wrappers; backing Memory identity is tested. Ordinary mask validation and fixed factor scheduling already existed, so removing their eager duplicate export passes actually removes work. Task4's new retained payload16N+8m and prior source budgets remain applicable. The pre-existing Task1 cold inverse-map zeros()+fill duplication remains deferred and unchanged; it is not new Task5 work. Independent source admission found no remaining unnecessary new production work/memory in this scope; actual allocation and total-solution benefit remain unmeasured. Task6 must judge all setup, normal work, fallback, cleanup and original certification inclusively.

qualified-sources.json binds current E and the two qualified production sources. source-aliases.json records the package symlink. Task4 root README closure/publication/review bindings map only through continuation-map.json to README.md.before-Task5; Task4 source bindings map only through task4-before-map.json to its frozen qualified copies. All older maps remain unchanged. Initial Task5 source/test/manifest versions resolve only through loader/production/handoff/boundary/source-review/cleanup-fixture before maps at exact matching hashes. No old script/audit/raw record was rerun or rewritten. Frozen failed test entrypoints are historical records; the qualified result is the complete deduplicated ordinary source-test coverage across the main and completion processes. Final independent whole-branch/result review, PASS closure and exact complete local committed names/blobs are required before closing Task5. No master promotion/push or Task6 numerical work is included.
'''
(D/'REPORT.md').write_text(report);print('report/maps/qualified sources prepared',len(qualified))
