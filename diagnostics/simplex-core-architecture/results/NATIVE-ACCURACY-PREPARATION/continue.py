"""Continuation update only after accepted preparation review; preserve prior text."""
from common import *
from control import validate_review
import guard
validate_review(rd(F/'review-final.json'),F/'preparation-pins-reviewed.json',rd(F/'required-paths-reviewed.json'));req(guard.pins_match(rd(F/'preparation-pins-reviewed.json')),'Preparation changed')
h=host();save(F/'continuation-host.json',h);req(not h['matches'] and all(h[k]==rd(F/'host.json')[k] for k in ('head','master','boot_id')),'Fresh host mismatch')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';roadmap=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
for p,b in [(status,F/'STATUS.md.before-preparation'),(roadmap,F/'roadmap.md.before-preparation')]:req(p.read_bytes()==b.read_bytes(),'Continuation bytes changed before preservation')
m=[]
for record in ('closure.json','publication.json'):
 z=rd(E/record)
 for p,b in [(status,F/'STATUS.md.before-preparation'),(roadmap,F/'roadmap.md.before-preparation')]:
  key=str(p.relative_to(R));req(z['sha256'][key]==sha(b),'Prior continuation mismatch');m.append(dict(record=str((E/record).relative_to(R)),key=key,sha256=sha(b),preserved_path=str(b.relative_to(R))))
text='''Native Float64 accuracy-policy Task1 OFFLINE preparation independently accepted.
See NATIVE-ACCURACY-PREPARATION.md and results/NATIVE-ACCURACY-PREPARATION/review-final.md.
Driver remains UNEXECUTED: no Julia query/parser/import/compile/native measurement,
no actual src/test/env/CI/master changes. Accepted design plan remains frozen.

NEXT: Task2 fresh seal in results/NATIVE-ACCURACY-QUALIFICATION using prepared
seal.py accuracy, then fresh independent gpt-6-astra exact-stage admission binding
that manifest, then ONE <=45s accuracy process using launch.py accuracy. Standing
human permission for short runs already exists; no repeat permission question.
Never launch merely because preparation review passed. Fresh refs/boot/start_ticks/
command/full206groups ANDsessions/noJulia/RAM/swap and immutable exact command,
source/runtime/input/control/environment/pins must pass first. No retry or tuning.

Fixed C(.1/0),P(1/0),R(.1/2), four sparse/dense32/96 saved inputs,132windows,
141freshLU/9lu!/3copy/4245F+2133B/12snapshots. Every output uses the original
128*n*eps bound. Residual FALSE rejects arm accuracy but remains diagnostic data;
structural/exception/count/measured-compile failure stops. Constructor and solve
costs, all samples/GC, attempted refinement, strategy, fill and R extra32n bytes
per workspace are separate. No presumed remedy or production propagation.

Current plan closure/publication STATUS/roadmap bindings map ONLY to the new
NATIVE-ACCURACY-PREPARATION before-preparation copies (continuation.json maps four
keys). Earlier mappings remain unchanged. Initial preparation offline-test seal/
launch source bindings map ONLY to before-preparation-fix copies. Initial rejected namespace/HWM review and manifest remain preserved; current
seal reads preparation-pins-reviewed.json/required-paths-reviewed.json/review-final.json.
Five initial source/report keys map ONLY to before-review copies (review-fix.json).
All prior raw,
scripts/audits/false results/reviews/plans remain FROZEN, NEVER RERUN or rewrite.
Original cost1 FAILED/CONSUMED, cost2 BLOCKED; no benchmark retry or promotion.
Master6f68e24 unchanged, CIoff/HHdisabled/automationpaused. Broader plan stays OPEN.
'''
s=status.read_text();a=s.index('## Exact next action\n');b=s.index('## Previous missing-zero experiment',a);status.write_text(s[:a]+'## Exact next action\n\n'+text+'\n'+s[b:])
with roadmap.open('a') as f:f.write('\n### Native Float64 accuracy-policy concrete preparation\n\nTask1 OFFLINE preparation independently accepted; driver remains UNEXECUTED.\nSee diagnostics/simplex-core-architecture/NATIVE-ACCURACY-PREPARATION.md. Next\nTask2 fresh seal and exact independent admission, then at most ONE45second\ncomponent experiment. All three fixed arms, 132windows and6378solve entries are\nprospective, not results. Original failed cost1/cost2 block, production defaults,\nmaster, CIoff/HHdisabled/automationpaused and all historical evidence unchanged.\n')
save(F/'continuation.json',dict(mappings=m,sha256={str(p.relative_to(R)):sha(p) for p in [status,roadmap,F/'STATUS.md.before-preparation',F/'roadmap.md.before-preparation']}))
