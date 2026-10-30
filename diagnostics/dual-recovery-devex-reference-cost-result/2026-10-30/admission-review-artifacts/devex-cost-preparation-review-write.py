from pathlib import Path
import hashlib,json
root=Path('/tmp');main=json.loads((root/'devex-cost-preparation-review-check-result.json').read_text());flow=json.loads((root/'devex-cost-preparation-review-flow-result.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
checks={**main['checks'],**{'flow: '+k:v for k,v in flow['checks'].items()}}
bindings={**main['bindings'],**flow['bindings']}
for p,h in bindings.items():
 if sha(p)!=h:raise AssertionError('review-bound input changed: '+p)
for name in ('devex-cost-preparation-review-check.py','devex-cost-preparation-review-check-result.json','devex-cost-preparation-review-check.log','devex-cost-preparation-review-flow.py','devex-cost-preparation-review-flow-result.json','devex-cost-preparation-review-flow.log','devex-cost-preparation-review.md','devex-cost-preparation-review-write.py'):
 p=root/name;bindings[str(p)]=sha(p)
report=root/'devex-cost-preparation-review.md'
r=dict(accepted=True,scope='offline_preparation',runtime_qualified=False,numerical_admission=False,production_admission=False,cost_qualified=False,checks=checks,bindings=bindings,review_report=str(report),review_report_sha256=sha(report),facts=main['facts'],findings=[],unnecessary_new_production_work_or_memory_found=False,execution_scope='New independent Python checkers only; selected new pure validator definitions; no Julia, submitted mains/guards/tests/old checkers',failures_preserved=[],remaining_seconds=766.3994027490844)
with (root/'devex-cost-preparation-review.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,scope=r['scope'],runtime_qualified=False,numerical_admission=False,checks=len(checks),bindings=len(bindings),report_sha256=r['review_report_sha256'])))
