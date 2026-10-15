from pathlib import Path
import sys,json,subprocess,hashlib,ast
D=Path(__file__).resolve().parent;A=D.parent/'DIRECT-LU-COST-PREPARATION';B=D.parent/'DIRECT-LU-COST1'
sys.path.insert(0,str(A))
from control import R,sha,rd,req,save,host,git

v=rd(D/'review.json');a=rd(D/'analysis.json');p=rd(D/'pin-supplement.json');checks={}
checks['independent_review']=v['accepted'] is True and v['findings']==[]
for label,record in [('review',v),('analysis',a),('supplement',p)]:checks[label+'_bindings']=all(sha(Path(n) if Path(n).is_absolute() else R/n)==h for n,h in record['sha256'].items())
checks['original_false_preserved']=a['all_passed'] is False and sum(a['checks'].values())==17 and a['checks']['selected_sources_match_launch'] is False
checks['pin_supplement']=p['all_passed'] is True and len(p['checks'])==4
pins=rd(A/'cost1-launch-pins.json')['inventory'];checks['fifteen_actual_launch_sources']=all(sha(n)==pins[n]['sha256'] and str(Path(n).resolve())==pins[n]['resolved'] for n in list(a['sha256'])[:15])
base=rd(A.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];checks['baseline514']=len(base)==514 and all(sha(R/n)==h for n,h in base.items())
checks['original_cost_failed_no_cost2']=rd(A/'cost1-audit.json')['all_passed'] is False and not any(A.glob('cost2-*'))
m=rd(D/'continuation.json')['mappings'];checks['four_before_mappings']=len(m)==4 and all(sha(R/z['preserved_path'])==z['sha256']==rd(R/z['record'])['sha256'][z['key']] for z in m)
h=host(rd(D/'host.json')['groups']);save(D/'closure-host.json',h)
checks['fresh204_groups_sessions']=len(h['groups'])==204 and not h['matches'];checks['refs_boot']=all(h[k]==rd(D/'host.json')[k] for k in ('head','master','boot_id'))
for n in ('continue.py','closure-final.py','publication.py'):ast.parse((D/n).read_text())
checks['new_control_syntax']=True
checks['diff_clean']=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0
s=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';report=R/'diagnostics/simplex-core-architecture/DIRECT-LU-REFERENCE-DIAGNOSIS.md';plan=R/'docs/superpowers/plans/2026-10-15-direct-lu-reference-backend-diagnostic.md'
checks['continuation_preparation_only']='No launch until concrete immutable' in s.read_text() and 'not cost2 or a benchmark retry' in road.read_text()
paths=[p for p in D.iterdir() if p.is_file() and p.name not in ('closure.json','publication.json')]+[s,road,report,plan]
out=dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in sorted(paths)})
save(D/'closure.json',out);req(out['all_passed'],'Closure failed');print(dict(checks=len(checks),bindings=len(out['sha256']),all_passed=True))
