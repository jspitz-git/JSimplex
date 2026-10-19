"""Offline source checks, documentation and immutable preparation inventory."""
from pathlib import Path
import sys,ast,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS';sys.path.insert(0,str(D));import control as c
H=c.OLD;S=c.REPAIR;checks={}
def ck(n,v):c.require(v,n);checks[n]=True
def write(n,t):
 with (D/n).open('x') as f:f.write(t)
c.validate_environment();c.validate_sources();ck('baseline_runtime_stage_verified',True)
for n,v in c.rd(D/'copied-files.json').items():ck('copy_'+n,c.sha(D/n)==c.sha(v['source'])==v['sha256'])
for n in ['launch.py','outer.py','audit.py']:ck('inverse_'+n,(D/n).read_text().replace('BG blocked U RED2 exact-stage admission','BG blocked U exact-stage admission')==(H/n).read_text())
a=ast.parse((D/'control.py').read_text());b=ast.parse((H/'control.py').read_text());functions=lambda tree:{x.name:ast.dump(x) for x in tree.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
af,bf=functions(a),functions(b);changed={n for n in af if af[n]!=bf.get(n)};ck('only_five_control_functions_changed',changed=={'config','validate_sources','validate_stage_binding','preparation','predecessor'})
ck('source_RED_three',sum(v is False for v in c.rd(D/'routing-source-red.json')['checks'].values())==3)
ck('routing_tests_25',c.rd(D/'routing-tests.json')['all_passed'] and len(c.rd(D/'routing-tests.json')['checks'])==25)
ck('full_auditor_tests_31',c.rd(D/'auditor-tests.json')['all_passed'] and len(c.rd(D/'auditor-tests.json')['checks'])==31)
ck('candidate14_unchanged',all(c.sha(p)==h for p,h in c.rd(S/'verification.json')['candidate_sha256'].items()))
ck('old_preparation_unchanged',c.bindings(c.rd(H/'preparation-pins-reviewed.json')) and c.bindings(c.rd(H/'review.json')))
ck('repair_publication_unchanged',c.bindings(c.rd(S/'publication.json')))
ck('old_red_unaccepted',c.rd(H/'runs/red300/audit.json')['all_passed'] is False and not (H/'runs/red300/result-review.json').exists())
ck('no_launch_artifacts',not any((D/n).exists() for n in ['runs','outers','reservation.json','sealed.json']))
for p in D.glob('*.py'):ast.parse(p.read_text(),filename=str(p));checks['syntax_'+p.name]=True
write('MEMORY-WORK.md',(H/'MEMORY-WORK.md').read_text()+'''\n## RED2 scope\n\nThis package changes Python prelaunch integrity/routing only. The driver, recorder, all three test clones, numerical oracle, guard and supervisor are byte-identical to the accepted first harness. No additional Julia scan, solve, conversion, assertion, fixture or retained owner is introduced. Whole master stage replaces the seven stale production-baseline source files as separately reviewed; its existing policy setup cost is included, not eliminated. Python validation additionally reads stage-repair review/publication hashes outside numerical execution. Cold arbitrary-precision oracles and compilation remain potentially expensive; no promise that the roster finishes within300s and no performance acceptance.\n''')
write('ADMISSION.md','''# Separate blocked BG RED2 launch preparation

OFFLINE ONLY. No Julia/query/parser/import/compile/numerics or outer/seal/reservation/release is permitted by this preparation request. This is preparation acceptance, not exact-run admission. The original failed RED and its stage remain frozen and unqualified.

## Target and immutable routing

Diagnostic parent commit ee7d652cd4939d2fbce32f10c56073fbc62b640c; master26e2291745999f485a74f643298ca997d65c7205. Only `red300` is supported, under this NEW package's `runs/red300` and `outers/red300`. Its phase label stays `red300` to preserve all diagnostic Julia/oracle bytes; the absolute package root distinguishes it from the historical run. GREEN/600s/unknown phases fail closed. New preparation scope is `BG blocked U RED2 preparation`; future exact-run receipt scope is `BG blocked U RED2 exact-stage admission`. An old acceptance receipt cannot admit this package.

Stage is the separately accepted `.superpowers/sdd/2026-10-19-direct-bg-blocked-update/task2-master-stage`,75files, exact committed master plus unchanged ordinary direct adapters and environment. `validate_stage_binding` binds stage/master/file hashes and accepted repair review/publication. `stages.json`, stage files, driver and actual pathof are pinned and checked; no enum shim, old-stage substitution, candidate tuning or test weakening. Driver resolves all modules at top level before main. Any warning/world-age/method-overwrite diagnostic rejects the result. Runtime import/dispatch remain unverified until a future admitted run.

## Fixed correctness outcome

All original160 assertion sites and occurrence rules,28 ordered units,13fixtures/26stream cells,512 replacements/begin/finish events are unchanged. Only six N026 coverage failures are expected: dense96,dense256,dense96-long32, each native/Markowitz. All mathematical, ownership, policy, original-B residual, history relation, negative/fallback and API-attempt checks must pass. Common candidate structural/lifecycle prechecks are retained, so RED is not an entirely scalar process. Exact actual aggregate counts follow the predeclared trajectory-dependent rules; no invented fixed total or output-driven count selection. Successful RED uses Julia exit1 only in conjunction with full auditor acceptance; any load error, missing unit/raw, other failure or warning rejects qualification.

## Resource and execution gates

Inclusive guarded process budget300seconds, inner292seconds plus8seconds supervisor cleanup. One Julia process/one BLAS thread, gcthreads1,0,heap hint2GiB,VM8GiB,available RAM>=6GiB,swap<=1GiB. Preserve compiled-modules=existing and wrapper/environment/runtime inventories. The outer may wait1200seconds for human-independent admission without Julia; its pre/post hashing and review wait are outside the numerical budget, never benchmark data. Full271 prior PGIDs AND sessions plus future identities, boot/start_ticks/command/no visible Julia, fresh local/remote refs, unchanged source/runtime/stage/environment and clean tracked/index state are mandatory at sealing and launch. Inaccessible executable symlinks remain an explicit host-visibility limitation.

Future sequence, NOT EXECUTED here: fresh host check; start NEW waiting-only isolated outer; execute new seal.py red300; independent exact sealed-input admission with exact membership/hash/currentrefs; release that outer once; new launcher validates again and reserves one attempt; audit saved complete/prefix results; after outer return execute new post-return.py red300; independent result review and exact publication. Do not run old seal/launch/audit against new paths. No automatic retry, GREEN or cost measurement. Pure timeout remains failed and can only motivate separately reviewed longer admission; numerical failure stops qualification.

## Evidence and limitations

New routing source checks establish three missing guarantees in old controls, then25positive/refusal tests pass with the new controls. These three source checks are not the six numerical RED assertions. New31 full-auditor synthetic tests exercise saved-data validation with process/hash/TOML boundaries explicitly mocked; they are not process execution or Julia correctness evidence. Original guard/supervisor bytes and prior accepted evidence are reused; no historical checker is rerun. See MEMORY-WORK.md for unchanged full direct-call schedule and cold oracle costs.
''')
write('REPORT.md','''# RED2 master-stage harness preparation

Prepared a separate RED-only control package for the accepted75-file master stage. The new absolute package roots isolate all future run, outer, seal, review, reservation and output files from the failed first RED. Exactly five control functions differ; launch/outer/audit only change exact-admission scope. All Julia driver/recorder/test clones, numerical oracle, resource guard and supervisor are unchanged. No production, permanent tests, environment, master, CI, candidate or historical evidence changes.

Author checks bind the complete original preparation and repair publication, exact candidate14files and repaired stage. Python-only source/configuration and full synthetic auditor tests passed. No Julia was executed and no run artifacts exist. A later explicit run request still requires fresh exact-run admission; this preparation alone cannot launch. Independent review and publication are recorded separately. Broader qualification and performance gates remain open.
''')
ledger=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/progress.md';before=ledger.read_text();write('progress.md.before-red2',before)
after=before+'''\nTask2 RED2 harness preparation at ee7d652c: separate RED-only package binds accepted task2-master-stage and preserves failed first RED. Ruling: explicit user scope prohibits Julia; only Python source/configuration and synthetic auditor tests run, no suite/import/outer/launch. New300s admission remains future; skill workspace cleanup is excluded to preserve frozen evidence. No numerical or performance acceptance. No new production work/memory; cold test oracles remain unchanged. Independent review and exact publication required.\n'''
ledger.write_text(after);write('progress.md.after-red2',after)
c.save(D/'source-check.json',dict(all_passed=True,checks=checks,sha256={str(p):c.sha(p) for p in D.iterdir() if p.is_file()},scope=__doc__))
# Bind transitive historical review dependencies and new immutable preparation inputs.
paths=set(c.rd(H/'preparation-pins-reviewed.json')['sha256'])|set(c.rd(H/'review.json')['sha256'])|set(c.rd(H/'review.json').get('evidence_sha256',{}))|{str(H/'review.json')}
paths |=set(c.rd(S/'publication.json')['sha256'])|{str(S/'publication.json')}|set(c.rd(S/'review.json')['sha256'])|set(c.rd(S/'review.json').get('evidence_sha256',{}))
paths|={str(p) for p in D.iterdir() if p.is_file()};paths|=set(c.rd(S/'stage.json')['sha256'])
c.save(D/'required-paths.json',dict(paths=sorted(paths)))
# Required-paths is an independent sealed input; include it in its own exact list.
j=c.rd(D/'required-paths.json');j['paths'].append(str(D/'required-paths.json'));j['paths'].sort();(D/'required-paths.json').write_text(json.dumps(j,indent=2)+'\n')
c.save(D/'preparation-pins.json',dict(sha256={n:c.sha(n) for n in j['paths']},scope='Offline RED2 preparation, not launch pins',launch_admitted=False))
print('Author source checks',len(checks),'preparation files',len(j['paths']))
