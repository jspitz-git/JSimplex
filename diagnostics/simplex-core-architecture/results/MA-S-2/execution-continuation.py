from pathlib import Path
import json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-S-2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=json.loads((D/'execution-postcheck.json').read_text())
if not checks['all_passed'] or checks['qualification_accepted']:raise SystemExit('Unexpected outcome')
maps=[]
for p,n in [(R/'diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-MA-S-2-execution'),(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-MA-S-2-execution')]:
 q=D/n
 if p.read_bytes()!=q.read_bytes():raise SystemExit('Beforecopy mismatch')
 for source in ('admission-review.json','numerical-review.json','closure.json','publication.json'):
  s=json.loads((D/source).read_text())['sha256'][str(p)]
  if sha(q)!=s:raise SystemExit('Binding mismatch')
  maps.append(dict(source=str(D/source),path=str(p),preserved=str(q),sha256=s))
with (D/'execution-continuation-map.json').open('x') as f:json.dump(dict(old_bindings=maps,scope='Only eight current MA-S-2 preparation/numerical review and closure/publication continuation bindings. All older maps unchanged.'),f,indent=2);f.write('\n')
block='''MA-S-2 executed once and closed: three exit0 processes, stage audits23/21/21PASS,
160correctness cases/4329assertions plus16smoke; exact expected missing-route RED2.
Corrected LOAD driver works in this sequence. All36BigFloat targets pass, but four
fallback controls fail allocation gates: aggregate48/52,accepted=false. Targets
paired medians0.535572–0.743382; no end-to-end speedup claim or production promotion.
BigFloat scoped fallback+128bytes/+8events per4calls, rational fallback+0–32bytes
with unchanged event counts. All control time gates pass; causes remain unproved.
3120windows/2184measured,compile/recompile0,52GCwindows(39measured)retained.
New result-analysis16PASS/postcheck18PASS/full4304pins/source514/protected6,
full166groups ANDsessions absent/noJulia. Three durations total39.348553s NOTbenchmark.
See MA-DENSELU-BIGFLOAT-SECOND-QUALIFICATION.md and results/MA-S-2/result-review.
No rerun/tuning/threshold change or Task3 integration; sequence consumed/frozen.
Next useful work: separate bounded offline fallback-allocation analysis using stored
results and pinned sources, then independent review before any changed candidate
or new admitted short experiment. No numerical retry is authorized by this record.
Standing short-run permission persists; broader plan OPEN. Eight current MA-S-2
review/seal/closure/publication continuation bindings map ONLY to before-MA-S-2-
execution copies via execution-continuation-map.json; all older mappings unchanged.
Production/test/userenv/master6f68e24 unchanged; CIoff/HHdisabled/automationpaused.
'''
p=R/'diagnostics/simplex-core-architecture/STATUS.md';s=p.read_text();start=s.index('## Exact next action\n');end=s.index('\n## Previous MA-S admission preparation',start);p.write_text(s[:start]+'## Exact next action\n\n'+block+s[end:])
p=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';s=p.read_text();p.write_text(s.rstrip()+'\n\n## MA-S-2 executed: target savings, fallback allocation rejection (2026-10-14)\n\n'+block)
print('8 exact continuation mappings; STATUS and roadmap updated after all runtime checks')
