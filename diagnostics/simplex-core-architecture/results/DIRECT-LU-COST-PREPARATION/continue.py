"""Publish continuation only after independently accepted offline preparation."""
from control import *
review=rd(D/'preparation-review-final.json') if (D/'preparation-review-final.json').exists() else rd(D/'preparation-review.json')
req(review['accepted'] is True and review['findings']==[],'Offline preparation not accepted')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
req(status.read_bytes()==(D/'STATUS.md.before-cost').read_bytes(),'STATUS changed')
req(road.read_bytes()==(D/'roadmap.md.before-cost').read_bytes(),'Roadmap changed')
s=status.read_text();start=s.index('## Exact next action');end=s.index('## Previous missing-zero experiment',start)
new='''## Exact next action

Direct LU / Markowitz Task3 OFFLINE cost preparation is independently accepted.
See DIRECT-LU-COST-PREPARATION.md and results/DIRECT-LU-COST-PREPARATION reviews.
No Julia/parser/import/compile/cost execution, stage seal or reservation in this
step. Tasks1–2 correctedGREEN remains accepted19557PASS; oldfailedGREEN andRED,
all inputs/scripts/raw/reviews remain frozen. Production/master6f68e24 unchanged.

Next: fresh host refs/boot/start_ticks/command/full202groups ANDsessions/noJulia,
then exact cost1 seal and independent numerical/work/memory stage admission,
then ONE guarded <=90s inclusive cost1 process. Use canonical controls identified
in the preparation review; do not execute superseded drafts. Cost2 needs accepted
immutable cost1 audit/raw and closure including its new groups, fresh seal and
independent stage admission; ONE further <=90s process only. No automatic retry.

24cells:4 n32/96 sparse/dense fixtures xFT/SS/BG xnative/Markowitz. Per process
3warm+7measured alternating pairs, reversed firstside in process2; whole fresh
construction/8updates/2refactors measured, all allocations/GC/compile and final
reachablefactor memory retained. Exact residuals outside windows; no extra solves.
Time/bytes/events/memory selection percell; all4cells required permanager/backend.
No performance acceptance yet, no automatic publicintegration/defaultpromotion.
CIoff/automationpaused/HHreuse disabled; broader programme remains open.

'''
status.write_text(s[:start]+new+s[end:])
with road.open('a') as f:f.write('\n### Direct LU Task3 offline cost preparation\n\nExact four-fixture/two-process cost driver and admission independently reviewed.\nNo cost executed; next fresh cost1 seal and exact independent stage admission.\nSee diagnostics/simplex-core-architecture/DIRECT-LU-COST-PREPARATION.md.\nAll prior rejections, evidence and production defaults remain unchanged.\n')
with (R/'.superpowers/sdd/2026-10-14-direct-lu-markowitz/progress.md').open('a') as f:f.write('\n- Task3 OFFLINE driver/input/admission prepared and independently reviewed; no\n Julia execution. Four fixtures101790 tokens,24cells,two<=90s processes pending.\n Ruling: separate inputs.json/toml and cost.jl under new results directory preserve\n frozen Task1–2 fixtures and overlay; same accepted interfaces/formulas/budgets.\n Ruling: >10% retained-memory rejection applies to any measured pair, conservatively.\n Cost stages remain incomplete; no generic task-done rerun or workspace deletion.\n')
print('Continuation updated; numerical Task3 remains pending')
