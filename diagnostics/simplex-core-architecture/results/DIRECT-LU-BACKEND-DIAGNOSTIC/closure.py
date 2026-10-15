from pathlib import Path
import sys,ast
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-LU-BACKEND-PREPARATION';sys.path.insert(0,str(D))
from control import *
import guard
checks={};v=rd(E/'review.json');a=rd(D/'probe-audit.json');p=rd(E/'postcheck.json');i=rd(E/'interpretation.json')
checks['independent_review']=v['accepted'] is True and v['findings']==[]
for label,z in (('review',v),('postcheck',p),('interpretation',i),('audit',a)):
 checks[label+'_bindings']=all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in z['sha256'].items())
reviewcheck=rd(E/'result-review-check.json');checks['independent28checks']=reviewcheck['all_passed'] is True and len(reviewcheck['checks'])==28
checks['canonical12integrity']=a['all_passed'] is True and len(a['checks'])==12 and all(a['checks'].values())
checks['fifteen_pass_three_false']=len(a['result']['residuals'])==18 and sum(z['passed'] for z in a['result']['residuals'])==15 and a['result']['failed_residuals']==['fresh_dse','tail_dse','base_dse']
checks['postcheck10']=p['all_passed'] is True and len(p['checks'])==10
checks['interpretation10']=i['all_passed'] is True and len(i['checks'])==10
pins=rd(D/'probe-launch-pins.json');checks['full4749launchpins']=len(pins['inventory'])==4749 and guard.pins_match(pins)
sealed=D/'probe-sealed-pins.json';validate_review(rd(D/'probe-admission.json'),sealed,rd(sealed)['files']+[str(sealed)]);checks['exact_stage_admission']=True
base=rd(E.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];checks['baseline514']=len(base)==514 and all(sha(R/n)==h for n,h in base.items())
checks['old_cost_false_no_cost2']=rd(E.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False and not any((E.parent/'DIRECT-LU-COST-PREPARATION').glob('cost2-*'))
m=rd(E/'continuation.json')['mappings'];checks['four_before_mappings']=len(m)==4 and all(sha(R/z['preserved_path'])==z['sha256']==rd(R/z['record'])['sha256'][z['key']] for z in m)
h=host(rd(E/'post-host.json')['groups']);save(E/'closure-host.json',h)
checks['fresh206groups_sessions_noJulia']=len(h['groups'])==206 and not h['matches']
checks['refs_boot']=all(h[k]==rd(E/'entry-host.json')[k] for k in ('head','master','boot_id'))
for n in ('continue.py','closure.py','publication.py'):ast.parse((E/n).read_text())
checks['new_control_syntax']=True
checks['diff_clean']=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0
s=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';report=R/'diagnostics/simplex-core-architecture/DIRECT-LU-BACKEND-DIAGNOSTIC.md'
checks['continuation_consumed_offline']='allowance is CONSUMED' in s.read_text() and 'Next bounded offline saved-evidence/source' in road.read_text()
paths=[p for p in E.rglob('*') if p.is_file() and p.name not in ('closure.json','publication.json')]
paths += [p for p in D.glob('probe-*') if p.is_file()]+[p for p in (D/'probe-run').iterdir() if p.is_file()]+[s,road,report]
out=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in sorted(set(paths))})
save(E/'closure.json',out);req(out['all_passed'],'Closure failed; preserve and stop');print(dict(checks=len(checks),bindings=len(out['sha256']),all_passed=True))
