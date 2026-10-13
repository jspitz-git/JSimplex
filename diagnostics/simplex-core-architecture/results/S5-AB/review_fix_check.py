from pathlib import Path
import json,hashlib,tomllib
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent;O=H.parent/'S5-O'
sh=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
d=json.loads((H/'review-fix.json').read_text());old=json.loads((H/'source-contract.json').read_text());name='S5-HANDOFF-COVERAGE-RECONCILIATION.md';raw=tomllib.loads((O/'master-1/raw/report.toml').read_text());correct='adaptive_pricing_lifecycle_tests.jl';records=d['reviewed_integrations'];o=next(x for x in records if x['stage']=='S5-O')
c={'fix8_pass':len(d['checks'])==8 and d['all_passed'] and all(d['checks'].values()),'full7bindings':len(d['sha256'])==7 and all(sh(p)==v for p,v in d['sha256'].items()),'before_report_preserved':sh(H/(name+'.before-review'))==old['sha256'][str(D/name)]==d['before_report_sha256'],'actual_both_roots':all(sh(r/'test'/correct)==raw['test_sha256']==o['current_sha256'] for r in [R,Path('/home/jspitz/JSimplex.jl')]),'initial_rejection_preserved':'Verdict: REJECTED' in (H/'review-initial.md').read_text()}
with (H/'review-fix-independent.json').open('x') as f:json.dump(dict(checks=c,all_passed=all(c.values()),sha256={str(p):sh(p) for p in [H/'review-fix.json',H/'review-initial.md',H/'review_fix_check.py',D/name,H/(name+'.before-review')]}),f,indent=2);f.write('\n')
print(c);assert all(c.values())
