"""One offline review correction; preserve before documents, no Julia."""
from pathlib import Path
import json,hashlib
r=Path.cwd();o=r/'diagnostics/simplex-core-architecture/results/S4-L';p=r/'docs/superpowers/plans/2026-10-12-hh-symbolic-cost-measurement.md';q=r/'diagnostics/simplex-core-architecture/S4-SYMBOLIC-COST-CONTRACT.md'
oldp=p.read_text();oldq=q.read_text()
with (o/'measurement-plan-before-review.md').open('x') as f:f.write(oldp)
with (o/'report-before-review.md').open('x') as f:f.write(oldq)
def checks(plan,report):
 balanced='floor((r-1)/2) mod2' in plan
 schedule=[{'round':r,'phase':((r-1)//2)%2 if balanced else (r-1)%2,'order':'RC' if r%2 else 'CR'} for r in range(1,9)]
 return {'phase0_both_orders':sum(x['phase']==0 and x['order']=='RC' for x in schedule)==sum(x['phase']==0 and x['order']=='CR' for x in schedule)==2,'phase1_both_orders':sum(x['phase']==1 and x['order']=='RC' for x in schedule)==sum(x['phase']==1 and x['order']=='CR' for x in schedule)==2,'wrapper_CSC_correct_classification':'wrapper-owned Julia CSC arrays' in report and 'into native-owned storage' not in report},schedule
red,oldschedule=checks(oldp,oldq);assert not any(red.values())
newp=oldp.replace('(r-1) mod2. Odd rounds','floor((r-1)/2) mod2 (0,0,1,1,0,0,1,1). Odd rounds')
assert newp!=oldp
newq=oldq.replace('CSC values/indices into native-owned storage','CSC values/indices into wrapper-owned Julia CSC arrays')
assert newq!=oldq
p.write_text(newp);q.write_text(newq)
green,schedule=checks(newp,newq);assert all(green.values())
sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
result={'original_reviewer_severity':'Minor for both','author_severity':'Important for measurement validity and memory-classification premise','red':red,'green':green,'before_schedule':oldschedule,'schedule':schedule,'before_plan_sha256':sha(oldp),'after_plan_sha256':sha(newp),'before_report_sha256':sha(oldq),'after_report_sha256':sha(newq),'numeric_calls':0,'old_evidence_untouched':True}
with (o/'review-fix.json').open('x') as f:json.dump(result,f,indent=2)
print({'RED':red,'GREEN':green,'numerical_calls':0})
