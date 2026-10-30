from pathlib import Path
import json,hashlib
base=Path('/tmp')
result=json.loads((base/'devex-green2-result-review-check-result.json').read_text())
assert result['accepted'] is True and all(v is True for v in result['checks'].values())
bindings=dict(result['bindings'])
for n in ['devex-green2-result-review-check.py','devex-green2-result-review-check-result.json','devex-green2-result-review-check.log','devex-green2-result-review.md','devex-green2-result-review-finalize.py']:
 p=base/n;bindings[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
report=str(base/'devex-green2-result-review.md')
out=dict(accepted=True,scope='green2_result_only',runtime_accepted=True,production_admission=False,cost_qualified=False,checks=result['checks'],bindings=bindings,review_report=report,review_report_sha256=bindings[report],facts=result['facts'],findings=[],unnecessary_new_production_work_or_memory_found=False)
path=base/'devex-green2-result-review.json'
with path.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(dict(accepted=True,checks=len(out['checks']),bindings=len(bindings),review_report=report,review_report_sha256=out['review_report_sha256'],review_json=str(path),review_json_sha256=hashlib.sha256(path.read_bytes()).hexdigest())))
