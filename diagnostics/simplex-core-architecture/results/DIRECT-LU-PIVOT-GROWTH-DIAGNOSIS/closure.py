from common import *
import ast
v=rd(F/'review.json');a=rd(F/'analysis.json');c=rd(F/'author-check.json');m=rd(F/'continuation.json')['mappings']
def previous(z):
 for n,h in z['sha256'].items():
  p=path(n)
  if sha(p)!=h:
   matches=[x for x in m if x['key']==str(p.relative_to(R)) and x['sha256']==h]
   if not matches or not all(sha(R/x['preserved_path'])==h for x in matches):return False
 return True
h=host();save(F/'closure-host.json',h)
checks=dict(accepted_review=v['accepted'] is True and v['findings']==[],review_bindings=bindings(v),analysis20=a['all_passed'] and len(a['checks'])==20 and all(a['checks'].values()),analysis_bindings=bindings(a),author10=c['all_passed'] and len(c['checks'])==10 and all(c['checks'].values()),author_bindings=bindings(c),four_continuation_mappings=len(m)==4 and all(rd(R/x['record'])['sha256'][x['key']]==x['sha256']==sha(R/x['preserved_path']) for x in m),prior_publication_preserved=previous(rd(E/'publication.json')),prior_closure_preserved=previous(rd(E/'closure.json')),baseline514=len(rd(F.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'])==514 and bindings(rd(F.parent/'DIRECT-LU-PREPARATION/baseline.json')),fresh206groups_sessions_noJulia=len(h['groups'])==206 and not h['matches'],refs_boot=all(h[k]==rd(F/'entry-host.json')[k] for k in ('head','master','boot_id')),old_cost_failed=rd(F.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False,no_cost2=not any((F.parent/'DIRECT-LU-COST-PREPARATION').glob('cost2-*')),diff_clean=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0)
for p in F.glob('*.py'):ast.parse(p.read_text())
checks['new_python_syntax']=True
paths=[p for p in F.rglob('*') if p.is_file() and p.name not in ('closure.json','publication.json')]+[R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md',R/'diagnostics/simplex-core-architecture/DIRECT-LU-PIVOT-GROWTH-DIAGNOSIS.md']
save(F/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in sorted(set(paths))}));req(all(checks.values()),'Closure failed; preserve and stop');print(dict(checks=len(checks),bindings=len(paths),all_passed=True))
