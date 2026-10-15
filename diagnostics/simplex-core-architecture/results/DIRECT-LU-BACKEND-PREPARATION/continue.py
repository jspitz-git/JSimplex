from control import *
import guard
v=rd(D/'preparation-review.json');validate_review(v,D/'preparation-pins.json',rd(D/'required.json'))
req(guard.pins_match(rd(D/'preparation-pins.json')),'Preparation changed')
s=R/'diagnostics/simplex-core-architecture/STATUS.md';r=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
req(s.read_bytes()==(D/'STATUS.md.before-backend').read_bytes(),'STATUS changed')
req(r.read_bytes()==(D/'roadmap.md.before-backend').read_bytes(),'Roadmap changed')
h=host(rd(D/'host.json')['groups']);save(D/'continuation-host.json',h)
req(not h['matches'] and all(h[k]==rd(D/'host.json')[k] for k in ('head','master','boot_id')),'Host changed')
t=s.read_text();a=t.index('## Exact next action');z=t.index('## Previous missing-zero experiment',a)
new='''## Exact next action

Direct LU backend diagnostic OFFLINE preparation completed and independently
reviewed. See DIRECT-LU-BACKEND-PREPARATION.md and its results directory.
No Julia query/parser/import/compile/native call, stage seal, reservation or
numerical execution. Task3 cost1 remains FAILED and CONSUMED; cost2 BLOCKED.
Original raw/false audit and partial n32 cost rejections are unchanged.

Concrete driver: exact sparse96 B0..B4/steps1..5, fresh native B4 versus original
FT/native four-update prefix plus refactor. Explicit total3factorizations/13FTRAN/
5BTRAN/4replacements/1refactor, two metadata snapshots, three live native factors.
Scaling orientation comes from do_recip captured in the SAME combined export;
fixed flag1=multiply/0=divide exact offline rule, no trial orientation or extra
solve. Original accepted plan frozen; separate reviewed scaling-contract ruling.
All18 residual booleans retained; nonreproduction is valid evidence, no retry.
Exact factor/application decomposition is not an intermediate native solve trace.

NEXT: fresh full204groups ANDsessions/noJulia/refs/boot preflight, seal the ONE
probe stage, then independent review of its exact immutable manifest BEFORE
launch. At most ONE <=45second diagnostic, same resource guards. Preparation
acceptance alone does not admit execution. Preserve every raw/exit/false result,
then independent result review/closure. No cost2, automatic repair, tuning,
promotion or master merge. Production/master6f68e24 unchanged; CIoff/HHdisabled,
automation paused, broader plan open. Original source-check selector failure
preserved; separate filename-only correction and52synthetic/17sourcechecks PASS.
Previous diagnosis closure/publication current STATUS/roadmap bindings map ONLY
to BACKEND-PREPARATION before-backend copies. All older mappings remain.

'''
s.write_text(t[:a]+new+t[z:])
with r.open('a') as f:f.write('''
### Direct LU backend diagnostic concrete preparation

The separate OFFLINE driver/admission/oracle preparation is independently reviewed;
see DIRECT-LU-BACKEND-PREPARATION.md. Next fresh seal and exact stage review,
then at most ONE45second diagnostic, not cost2 or a benchmark retry. Three live
native factors/two snapshots; do_recip selects fixed scaling interpretation in
one export call. No production change or numerical execution in preparation.
''')
C=D.parent/'DIRECT-LU-REFERENCE-DIAGNOSIS';m=[]
for name in ('closure.json','publication.json'):
 rec=rd(C/name)
 for path,before in ((s,D/'STATUS.md.before-backend'),(r,D/'roadmap.md.before-backend')):
  key=str(path.relative_to(R));req(rec['sha256'][key]==sha(before),'Before binding')
  m.append(dict(record=str((C/name).relative_to(R)),key=key,preserved_path=str(before.relative_to(R)),sha256=sha(before)))
save(D/'continuation.json',dict(mappings=m,scope='Only previous diagnosis current continuation bindings; all older mappings unchanged'))
with (R/'.superpowers/sdd/2026-10-14-direct-lu-markowitz/progress.md').open('a') as f:f.write('''
- Backend diagnostic OFFLINE preparation reviewed: fixed3factor/13F/5B/4replace/
  1refactor, two snapshots/three live native factors. No Julia or stage seal.
  Ruling: capture do_recip in same export; exact flag-selected multiplication or
  division, never fit orientation to residuals. Bound diagnostic memory only,
  no native/free/observer-neutrality proof. Next exact stage admission, then one
  <=45s diagnostic, no benchmark retry/cost2/automatic repair. Workspace preserved.
''')
print('Continuation updated; exact numerical stage admission remains pending')
