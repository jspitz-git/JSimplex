"""Seal the independent offline review; no integration, numerical or publication action."""
from pathlib import Path
import hashlib,json
Q=Path(__file__).resolve().parent;R=Q.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readj(n):return json.loads((Q/n).read_text())
a=readj('review-checks.json');b=readj('review-amendment-checks.json')
assert a['all_passed'] and b['all_passed']
pins=dict(a['sha256']);pins.update(b['sha256'])
for n in ['review-checks.json','review-amendment-checks.json','review-check.py','review-amendment-check.py','review-amendment-check-2.py','review-amendment-check.failure.json','review-final.md','review-finalize.py','review-initial.json','review-fix.py','review-fix.json','plan.before-review.md']:
 p=Q/n;pins[str(p.relative_to(R))]=sha(p)
for n,h in pins.items():
 p=Path(n) if Path(n).is_absolute() else R/n
 assert sha(p)==h,n
result=dict(scope='production integration preparation',accepted=True,findings=[],numerical_admission=False,production_integrated=False,initial_finding_resolved=True,checks=dict(all_passed=True,main=307,amendment=26),sha256=pins,author_preservation_mapping=a['details']['author_preservation_mapping'],work_memory=dict(unnecessary_new_production_work_found=False,unnecessary_new_retained_memory_found=False,evidence='review-final.md: complete source inverse, unchanged solve/update bodies, fixed control setup, 88-window stored cost reconciliation; policy-induced fill and uncertainty retained.'),limitations='Offline whole-candidate preparation review only. Future actual-master final-seal independent exact-stage acceptance required before any Julia launch. No universal speedup, complete native-work, all-custom-precision, full-suite or direct-prototype qualification.')
with (Q/'review-final.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('ACCEPTED production integration preparation;',len(pins),'bindings; no numerical admission')
