from pathlib import Path
import json,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,s):
 with p.open('x') as f:f.write(s)
script=D/'independent-finalization-initial-review.py';save(script,Path(__file__).read_text())
findings=[dict(priority=1,file='finalize.py',line=5,issue='Finalizer checks acceptance flags without verifying prerequisite bindings and omits finalization-preparation review before writing reports and continuations.',required='Require accepted preparation review and validate all prerequisite bindings before writes; resolve historical master source/index bindings only through validated exact beforeimages.'),dict(priority=2,file='closure.py',line=60,issue='The maps closure claim does not validate historical-path-map master_source_before against the integration map; before() bypasses that field.',required='Use verify_historical_maps with actual integration/final maps and exact baseline, index and selected names, check final master_before, and require2674 preparation entries.'),dict(priority=2,file='finalize.py',line=52,issue='Compilation and cold specialization costs are described as accounted for despite incomplete attribution in accepted cost review.',required='Explicitly retain outer-driver/startup, per-variant cold specialization metadata and native-retention coverage limits; distinguish included whole-call closure cost.')]
md='''# Initial finalization preparation review — not accepted

Three issues must be resolved before executing the finalization controls: missing bound-review preflight before continuation writes; missing exact master-source/index historical-map validation behind the closure claim; and overstatement of cold compilation cost attribution. The requested corrections are recorded precisely in finalization-preparation-initial-review.json.

Original unexecuted finalize.py and closure.py are preserved. Separate corrected canonical controls will require their own accepted preparation review; this record grants no execution or publication admission. The new finalization controls were created after GREEN launch pinning and are not retroactive GREEN pins. GREEN remains active; this review performed no Julia, old-script execution, imports of task code, Git operation or no-Julia host audit.
'''
report=D/'FINALIZATION-PREPARATION-INITIAL-REVIEW.md';save(report,md)
paths=[script,report]+[D/n for n in ['finalize.py','closure.py','diagnostic-publish.py','final-controls-prepare.py','finalization_checks.py','publication_checks.py','RESULT-REVIEW.md','result-review.json','GREEN-run/pins.json']]
data=dict(accepted=False,findings=findings,Julia_executed=False,Git_operations=False,host_audit_performed=False,scope='unexecuted initial finalization controls; separate reviewed corrections required',bindings={str(p):sha(p) for p in paths})
save(D/'finalization-preparation-initial-review.json',json.dumps(data,indent=2,sort_keys=True)+'\n')
print('Initial rejected preparation preserved with three findings; no active run touched.')
