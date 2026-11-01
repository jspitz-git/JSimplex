from pathlib import Path
import json,hashlib,shutil
W=Path('/home/jspitz/.codex/worktrees/dual-step-experiment/JSimplex.jl');D=W/'diagnostics/dual-step-experiment/measurement'
def read(p):return json.loads(p.read_text())
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
q=read(D/'qualify-run/audit.json');c=read(D/'compare-run/audit.json');post=read(D/'postcheck.json')
if not (post['accepted'] is True and q['accepted'] is True and c['accepted'] is True):raise ValueError('accepted actual evidence required')
summary=c['summary'];active=[k for k,v in summary.items() if v['activated']]
wins=[k for k in active if summary[k]['paired_seconds']['max']<1];losses=[k for k in active if summary[k]['paired_seconds']['min']>1];mixed=[k for k in active if k not in wins+losses]
rows=[]
for case,s in summary.items():
 t=s['paired_seconds'];b=s['paired_bytes'];events=s['paired_allocs'];ref=s['reference'];e=s['candidate']
 rows.append(f"| {case} | {str(s['activated'])} | {ref['seconds']['median']*1e3:.4f} / {e['seconds']['median']*1e3:.4f} | {t['median']:.4f} [{t['min']:.4f},{t['max']:.4f}] | {t['mad']:.4f} | {b['median']:.4f} | {events['median']:.4f} | {ref['iterations']['median']:.0f} / {e['iterations']['median']:.0f} |")
work=[]
for case,v in q['summary'].items():
 work.append('| '+case+' | '+' | '.join(v[k] for k in ('EC_accepted_pivots','EC_proposals','EC_rejections','EC_ftran','EC_btran','EC_bfrt_ftran','EC_corrections','RC_refactor_attempts','KC_rhs_capture_entries','KC_output_capture_entries','KC_residual_terms','RC_journal_fields','original_cleanups'))+' |')
capacity=[]
for case in q['summary']:
 r=[x for x in q['records']['INSPECT'] if x['case']==case]
 if r:
  a=next(x for x in r if x['stage']=='setup');b=next(x for x in r if x['stage']=='exit')
  capacity.append('| '+case+' | '+a['graph_bytes']+' / '+b['graph_bytes']+' | '+a['unique_vector_payload_bytes']+' / '+b['unique_vector_payload_bytes']+' |')
report=f'''# Task6 same-policy whole-solve comparison

Task6 is completed on the experimental branch, parent `0a06785c508f89103a09b3c4c6a238baca0db36f`, with original master `9940bdabe149e922afa60b5364227a7e7393bc75` unchanged. No engine/production/test/environment/CI code was changed in Task6. The user explicitly authorized publishing the accumulated experiment branch after completion; no production promotion or master push is included.

## Decision and practical limits

All16 fixed cases return original-certified OPTIMAL on both sides, with original-model feasibility/objective/input-preservation checks. Qualification passed236 ordinary assertions over66 complete solves; comparison passed749 over224 complete windows (64warm,160measured). All160 measured compile/recompile times are zero. The genuine separately qualified infeasible fallback stays an honest INFEASIBLE/no-payload boundary, not a speed result. Initial diagnostic admission rejection and parser RED remain preserved; no numerical attempt failed or was repeated.

Of the {len(active)} cases with real E normal commits and no main fallback, all five observed time ratios are below1 in {len(wins)}, above1 in {len(losses)}, and straddle1 in {len(mixed)}. These are descriptive five-pair ranges, not confidence intervals or statistical significance. The inactive/presolve-only cases remain visible and receive no engine-saving interpretation. Entire solve time includes original model copy/presolve/scaling/init, E private import/index/newfactor, normal and rejected work, repair/refactor, export, any legacy cleanup/retry and final original certification. Different numerical trajectories/iteration counts must not be called kernel-only savings. No single kernel window substitutes for a verified result.

This small-case comparison does not establish a large-LP end-to-end benefit, an order-of-magnitude saving, or production readiness. Saved runtime/fast0507 basis/history inputs are not a source-bound short complete fixed-Devex/PFI solve schedule; their conditional admission was not established. They were not run or replaced by component windows. No integration proposal is accepted from this record; retain the implementation as an opt-in experiment. Any wider input/precision/backend or intended-policy/DSE comparison needs its own concrete admission.

## Complete-window measurements

Ratios are E/reference within the same pair. Two complete warm solves per arm precede five alternating measured pairs per case; first pair reference then E, second E then reference, continuing rotation. Both observers are nothing; reference is ordinary public J.solve with no diagnostics, E is unchanged solve_experimental with its required bounded diagnostics/counters and NoEvents. Thus intrinsic E counter/record overhead is included, not subtracted. Reference event/kernel counts are qualified separately, never substituted for these uninstrumented wall times. All medians/ranges/MAD/times/bytes/allocation events/GC/iteration/refactor values are in compare-run/audit.json, and every raw sample remains in guard/run.log.

| Case | Activated | Ref / E median ms | Paired time median [range] | MAD | Bytes ratio | Events ratio | Ref / E whole iterations |
|---|---|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

Warm compilation and all case preparation, external correctness/input checks, one explicit postwarm full-GC per case and formatting are outside the solve windows and recorded separately. The complete solve function itself—including record/diagnostic allocation, its setup and certification—is inside every window. Natural measured GC and outliers are retained. Two warm calls are the frozen schedule, not repeated tuning; no allocation threshold from old generic tests is applied. GC bytes/events are aggregate allocation traffic, potentially including native callbacks, not live memory/native malloc/free accounting. GC pressure and preparation/release costs must not be inferred absent from zero in-window GC.

## Actual work attribution

The following E counters include the whole imported main phase and its recovery. They exclude original init/auxiliary/cleanup bodies, which remain explicitly separately counted boundaries; original work/time is included in total windows. Candidate measured EC/KC/RC/legacy count fields match separately qualified counts in every measured sample (postcheck), while fixed primitive counters remain enabled inside all timed E phases. PC candidate/ratio/plan/flip/Devex counters and their physical arrays are read only by the independently qualified diagnostic clone at setup/exit; they are not copied/walked in timed phases. Cold captured PC values are retained in qualify-run/audit.json INSPECT records, not advertised as independently observed hidden native work.

| Case | E commits | Proposals | Rejected | FTRAN | BTRAN | BFRT F | Corrections | Refactor attempts | RHS capture | Output capture | Direction residual terms | Journal fields | Original cleanup |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(work)+'''

Frequency/source attribution:

- Setup: existing full original copy/presolve/scaling/initial factor work; E additionally validates/copies owned numeric/basis/scaling state, builds one current-B factor and row index, and classifies invariants. phase_factor_builds/row_index_builds/entry_validated_values/invariant_rebuilds quantify named portions. Initial source owners overlap the imported graph until return. Task1's unchanged duplicate cold inverse-zeroing pass remains deferred.
- Each proposal/candidate: maintained leaving membership, full mathematical relevant-support Harris/BFRT and candidate validation, planned field/union enumeration and Devex terms. Cold PC counters expose their actual visits; no hidden dropped coefficient or tolerance change. These operations can dominate dense affected unions even though repeated global invariants were removed.
- Each solve: genuine native factor interface call, saved RHS capture and dense output/support capture, plus original complete BTRAN row residual. Kernel row_checks counts entries, not the native/original row-residual interior terms. Direction residual rows/terms and pricing entries are observed. Native private scaling/orientation/refinement/packing work is not completely instrumented; no source-derived bound is relabelled an observed count. Counters overlap by definition and must not be summed as a global native-work budget.
- Each commit/recovery: checked planned writes, journal entries/fields and classification of changed values; factor update and every retry/refactor/correction is counted. Refactor rebuilds can add actual primal/cost solves, residual checks and invariant rebuilds. The controller never credits a rejected proposal as a pivot. The qualified INFEASIBLE boundary exercises3 rejected proposals, no accepted pivot and one legacy continuation; its rejection/rebuild work is not treated as ordinary successful speed.
- Legacy and final answer: all setup/aux/primal cleanup/original retry/certification scans and solves are retained. Reference instrumentation uses existing diagnostics(kernel_timing=true) once per case; its full primal/iterations/refactors match public reference. Existing diagnostic spans are not complete backend entry counts or PREforward proof. Precision-boost/lp-refinement/repair/certification event fields are preserved, as are E original boundary notices. No whole-vector scan, native factor overlap, callback cost or full-state invariant is silently claimed zero.

## Retention and process memory

Cold diagnostic clone changes only its own nominal adapter type and two read-only snapshots, verified by exact inverse. It uses original controls and matches E results/phase counters. Actual Vector backing Memory capacities are captured with identity deduplication at setup/exit; fixed proposal/journal/invariant/support/receipt/recovery/index reserves do not shrink or grow. The payload measure covers selected vectors and excludes native/backend-private allocation, headers and other ownership overlap. Julia reachable graph bytes include model/factor references and have different scope; neither is live native heap, peak memory or proof of release. No engine graph is retained in the scalar output record. Record retained Julia size is measured after each primary E solve; solution/current input/check snapshot and current scalar records are the bounded diagnostic roots.

| Case | E setup / exit reachable graph B | Selected setup / exit vector payload B |
|---|---:|---:|
'''+ '\n'.join(capacity)+'''

Process resource high-water includes compilation, both arms, native code/data and the diagnostic process. It is not an isolated per-arm memory comparison. Full sampled records, terminal memory and child getrusage maxRSS remain in each guard directory.

| Process | Inclusive seconds | Samples | Min available KiB | Max swap KiB | Child maxRSS KiB |
|---|---:|---:|---:|---:|---:|
'''
for mode,r in post['runs'].items():report+=f"| {mode} | {r['elapsed_seconds']:.9f} | {r['samples']} | {r['min_available_kib']} | {r['max_swap_kib']} | {r['child_maxrss_kib']} |\n"
report+='''
Both processes had separately admitted common1800s allowances including loading/warmup/output/audit/terminal checks, exact boot/start/command/group ANDsession closure, one Julia/BLAS1 and original memory guards. The initial622 qualification and642 comparison manifests pin actual source/project/runtime/input/guard paths; later audits/reviews are separate read-time bindings, not retroactive launch pins. No old numerical driver or auditor was rerun.

## Review, preservation and next decision

Initial607 admission rejected the zero-argument macro delimiter and incomplete parser ordinary-summary/case-ID gates before Julia. Actual pure offline RED exposed missing ordinary-count rejection; corrected code has27 separate synthetic parser checks. Initial607 sources/pins/review/RED remain under before-admission-review/admission-before-map; both actual numerical processes used separately accepted corrected manifests. Postcheck binds985 successful ordinary assertions and all named work/capacity/guard checks. Final whole-branch/result review must explicitly assess correctness, work and retention; no promotion is automatic.

Rulings: cold exact-inverse inspector and separately instrumented reference are qualification-only (cost if wrong: neutrality must fail admission, not be assumed); primary E intrinsic counters remain charged (cost: this is the actual current opt-in implementation, not a hypothetical stripped engine); runtime/fast0507 whole-model viability is unestablished (cost: no conclusion for those large models); no intended-policy comparison is claimed for an unimplemented E-DSE path (cost: only same-policy organizational evidence). Existing cold Task1 duplicate inverse-zeroing is deferred unchanged; no tuning/fix is smuggled into timing.

Task5 root README closure/review/publication bindings map only through continuation-map.json to README.md.before-Task6. Task5 source files remain current and byte-identical, so no source remapping is needed. All older maps/failed records/raw/reviews stay frozen. Exact local commit and the user-authorized normal push must preserve all work; master remains unchanged and CI disabled.
'''
(D/'REPORT.md').write_text(report)
r=W/'diagnostics/dual-step-experiment/README.md';before=D/'README.md.before-Task6';shutil.copyfile(r,before)
expected=read(D.parent/'task5/closure.json')['bindings'][str(r)]
if sha(before)!=expected:raise ValueError('exact Task5 continuation')
(D/'continuation-map.json').write_text(json.dumps({str(r):dict(sha256=expected,preserved=str(before))},indent=2))
s=r.read_text();start=s.index('- Status:');end=s.index('\n',start);s=s[:start]+f'- Status: Tasks1–6 completed on the experiment branch. Task6 qualification236 and comparison749 assertions passed;16 fixed whole-solve cases,160 measured compile-zero windows, all original-certified optimal. [Task6 report](measurement/REPORT.md) records all paired results and limits; no large-model/production speed claim or master promotion. Publication of the accumulated experimental branch is user-authorized.'+s[end:];r.write_text(s)
print('Prepared complete Task6 report',len(active),'active; observed rangesbelow1',wins,'above1',losses,'mixed',mixed)
