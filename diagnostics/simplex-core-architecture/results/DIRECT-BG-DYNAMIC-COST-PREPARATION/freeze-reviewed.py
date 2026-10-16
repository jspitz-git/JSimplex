"""New canonical successor inventory; never rewrites the original1826manifest."""
from control_reviewed import *
import ast
require(bindings(rd(D/'preparation-pins.json')),'Original1826 pins changed')
require(rd(D/'review-rejected-v1.json')['accepted'] is False,'Original rejected review')
for n in ['offline-tests-reviewed.json','prefix-tests-reviewed.json','fix-green.json']:require(rd(D/n)['all_passed'],'Corrected tests')
red=rd(D/'fix-red.json');require({k for k,v in red['checks'].items() if not v}=={'partial_reject_outputs','partial_reject_modes','first_process_stop_gate'},'Exact RED')
validate_environment();validate_sources();predecessor('cost1-300');h=full_host(rd(D/'host.json')['groups']);require(not h['matches'] and not (D/'runs').exists(),'No runtime')
require(rd(D/'config.json')=={p:config(p) for p in ['cost1-300','cost2-300','cost1-600','cost2-600']},'Unchanged phase commands')
for p in D.glob('*.py'):ast.parse(p.read_text())
save(D/'review-fix-check.json',dict(all_passed=True,checks=dict(original1826unchanged=True,rejection_preserved=True,red3expected=True,green_regressions=True,full91and23=True,source_runtime_stage=True,fresh_host=True,no_phase=True,unchanged_commands=True,python_syntax=True),host=h,canonical=['control_reviewed.py','analysis_reviewed.py','evidence_reviewed.py','audit_reviewed.py','seal_reviewed.py','launch_reviewed.py','close_reviewed.py','publish_reviewed.py','REPORT-reviewed.md','continuation-next-reviewed.md'],scope='Offline successor fix; no Julia'))
files=set(rd(D/'preparation-pins.json')['sha256'])|{str(p) for p in D.iterdir() if p.is_file()}|{str(D/'required-paths-reviewed.json')}
save(D/'required-paths-reviewed.json',dict(paths=sorted(files)))
save(D/'preparation-pins-reviewed.json',dict(scope='Canonical offline cost preparation; original1826and initial rejection preserved; not runtime admission',sha256={n:sha(n) for n in sorted(files)}))
require(bindings(rd(D/'preparation-pins-reviewed.json')),'New inventory')
print('Review fix10PASS; canonical',len(files),'bindings; initial1826unchanged')
