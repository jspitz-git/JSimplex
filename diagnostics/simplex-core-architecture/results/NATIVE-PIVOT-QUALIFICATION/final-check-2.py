"""New post-correction author checks, no Julia or launch."""
from common import *
import ast
for p in Q.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks=dict(original842=bindings(rd(Q/'preparation-pins.json')),original_review843=bindings(rd(Q/'review.json')) and len(rd(Q/'review.json')['sha256'])==843 and rd(Q/'review.json')['accepted'] is False,fix8=rd(Q/'review-fix.json')['all_passed'] is True and bindings(rd(Q/'review-fix.json')),initial_checks=rd(Q/'offline-check.json')['all_passed'] is True and bindings(rd(Q/'offline-check.json')),oracle20=rd(Q/'oracle-regression.json')['all_passed'] is True and len(rd(Q/'oracle-regression.json')['refusals'])==20 and bindings(rd(Q/'oracle-regression.json')),reviewer_checks=len(rd(Q/'reviewer-check.json')['checks'])==13 and all(v is True for v in rd(Q/'reviewer-check.json')['checks'].values()) and rd(Q/'reviewer-check.json')['blocking_findings']==['R1'] and rd(Q/'reviewer-check.json')['review_accepted'] is False,python_syntax=True,no_runs=not (Q/'runs').exists() and not (R/'.superpowers/native-pivot-qualification').exists())
from control_reviewed import config
checks['red_command']='test-driver-reviewed.jl' in config('red')['command'][-4] and config('red')['seconds']==30 and config('red')['expected_exit']==1
checks['green_command']='test-driver-reviewed.jl' in config('green')['command'][-4] and config('green')['seconds']==60
checks['cost_command']='cost-driver.jl' in config('cost')['command'][-4] and config('cost')['seconds']==45
checks['separate_manifests']='preparation-pins-reviewed.json' in (Q/'seal-reviewed.py').read_text() and "D/'review-final.json'" in (Q/'seal-reviewed.py').read_text()
checks['canonical_auditor']='from audit_reviewed import audit' in (Q/'launch-reviewed.py').read_text() and 'from control_reviewed import *' in (Q/'audit_reviewed.py').read_text()
checks['candidate_unchanged']=all(sha(e['source'])==e['sha256'] for a in ['reference','candidate'] for e in rd(PREV/'overlay-manifest.json')[a])
checks['actual_unchanged']=not git('diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce')
paths=[Path(__file__),Q/'review-fix.json',Q/'oracle-regression.json',Q/'reviewer-check.json',Q/'continuation-text.md']
save(Q/'final-check-2.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in paths}))
require(all(checks.values()),'Final author check failed; preserve');print(dict(checks=len(checks),all_passed=True))
