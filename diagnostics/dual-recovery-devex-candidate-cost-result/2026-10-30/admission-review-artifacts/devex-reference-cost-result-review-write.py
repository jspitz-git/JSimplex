from pathlib import Path
import json,hashlib
base=Path('/tmp/devex-reference-cost-result-review-check-result.json');q=json.loads(base.read_text());assert q['accepted'] is True and len(q['checks'])==2394 and all(type(x) is bool and x for x in q['checks'].values())
b=dict(q['bindings'])
paths=[base,Path('/tmp/devex-reference-cost-result-review-check.log'),Path('/tmp/devex-reference-cost-result-review.md'),Path(__file__),Path('/tmp/devex-reference-cost-run-20261030/close-publish.py'),Path('/mnt/c/Users/jiris/.codex/plugins/cache/openai-curated-remote/superpowers/7.0.1/skills/using-superpowers/SKILL.md')]
for p in paths:b[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
report=Path('/tmp/devex-reference-cost-result-review.md')
result=dict(accepted=True,scope='reference_cost_result_only',runtime_accepted=True,cost_qualified=False,production_admission=False,findings=[],checks=q['checks'],bindings=b,review_report=str(report),review_report_sha256=b[str(report)],counts={**q['counts'],'final_review_bindings':len(b)},host=q['host'],elapsed_inclusive_seconds=q['elapsed_inclusive_seconds'],total_inclusive_seconds=q['total_inclusive_seconds'],remaining_seconds=q['remaining_seconds'],candidate_run=False,publication_script_executed=False)
with Path('/tmp/devex-reference-cost-result-review.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'accepted':True,'checks':len(result['checks']),'bindings':len(b),'report_sha256':b[str(report)]}))
