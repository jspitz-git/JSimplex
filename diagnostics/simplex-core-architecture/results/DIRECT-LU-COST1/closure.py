from pathlib import Path
import sys
A=Path(__file__).resolve().parent.parent/'DIRECT-LU-COST-PREPARATION'
sys.path.insert(0,str(A))
from control import rd,sha,save,req,host,git,R
B=Path(__file__).resolve().parent

import subprocess,ast
import guard
checks={}
review=rd(B/'review.json')
checks['diagnostic_review_accepted']=review['accepted'] is True and review['findings']==[]
checks['review_bindings']=bool(review['sha256']) and all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in review['sha256'].items())
p=rd(B/'postcheck.json');checks['eleven_integrity_checks']=p['all_passed'] and len(p['checks'])==11
checks['postcheck_bindings']=all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in p['sha256'].items())
x=rd(B/'partial-analysis.json')
checks['four_exact_failures_preserved']=x['total_outputs']==5784 and x['exact_pass']==5780 and x['raw_exact_agree'] is True and len(x['failed_residuals'])==4 and [z['step'] for z in x['failed_residuals']]==[5,6,7,8] and all(z['exact_ratio']=='181942511239954432/9646280616882321' for z in x['failed_residuals'])
checks['partial_bindings']=all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in x['sha256'].items())
checks['sealed_launch_pins']=all(guard.pins_match(rd(A/n)) for n in ('cost1-sealed-pins.json','cost1-launch-pins.json'))
checks['false_audit_exit2_preserved']=rd(A/'cost1-audit.json')['all_passed'] is False and p['summary']['returncode']==2 and p['summary']['canonical_audit_pass'] is False
checks['no_cost2']=not any(A.glob('cost2-*'))
base=rd(A.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256']
checks['all514_baseline']=len(base)==514 and all(sha(R/n)==h for n,h in base.items())
m=rd(B/'continuation.json')['mappings']
checks['four_continuation_mappings']=len(m)==4 and all(sha(R/z['preserved_path'])==z['sha256']==rd(R/z['record'])['sha256'][z['key']] for z in m)
checks['textual_stage_status_mapping']=sha(B/'STATUS.md.before-cost1') in (A/'cost1-stage-review.md').read_text()
fresh=host(rd(B/'final-host.json')['groups']);save(B/'closure-host.json',fresh)
checks['fresh204_groups_sessions']=len(fresh['groups'])==204 and not fresh['matches']
checks['refs_boot']=all(fresh[k]==rd(B/'final-host.json')[k] for k in ('head','master','boot_id'))
for n in ('continue.py','closure.py','publication.py'):ast.parse((B/n).read_text())
checks['new_control_syntax']=True
checks['authored_diff_clean']=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
checks['continuation_rejection']='reservation CONSUMED; cost2 BLOCKED' in status.read_text() and 'source/saved-evidence diagnosis' in road.read_text()
files=[p for p in B.iterdir() if p.is_file() and p.name not in ('closure.json','publication.json')]+[p for p in A.glob('cost1-*') if p.is_file()]+[p for p in (A/'cost1-run').rglob('*') if p.is_file()]+[status,road,R/'diagnostics/simplex-core-architecture/DIRECT-LU-COST1.md']
result=dict(all_passed=all(checks.values()),scope='Diagnostic rejection closure only; numerical qualification FAILED',checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in sorted(files)})
save(B/'closure.json',result);req(result['all_passed'],'Diagnostic closure rejected')
print(dict(all_passed=True,checks=len(checks),bindings=len(result['sha256'])))
