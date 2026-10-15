from common import *
import ast
v=rd(F/'review.json');a=rd(F/'source-check.json');fix=rd(F/'review-fix.json');m=rd(F/'continuation.json')['mappings']
plan=R/'docs/superpowers/plans/2026-10-15-native-float64-accuracy-policy.md'
def prior(z):
 for n,h in z['sha256'].items():
  p=path(n)
  if sha(p)!=h:
   maps=[x for x in m if x['key']==str(p.relative_to(R)) and x['sha256']==h]
   if not maps or not all(sha(R/x['preserved_path'])==h for x in maps):return False
 return True
def initial_source():
 return all(sha(F/'plan.before-review.md' if path(n)==plan else path(n))==h for n,h in a['sha256'].items())
h=host();save(F/'closure-host.json',h)
checks=dict(accepted_review=v['accepted'] is True and v['findings']==[],review_bindings=bindings(v),initial_source16=a['all_passed'] and len(a['checks'])==16 and all(a['checks'].values()),initial19_preserved=len(a['sha256'])==19 and initial_source(),review_fix=fix['all_passed'] and all(fix['checks'].values()) and bindings(fix),prior_closure=prior(rd(E/'closure.json')),prior_publication=prior(rd(E/'publication.json')),four_mappings=len(m)==4 and all(rd(R/x['record'])['sha256'][x['key']]==x['sha256']==sha(R/x['preserved_path']) for x in m),baseline514=len(rd(F.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'])==514 and bindings(rd(F.parent/'DIRECT-LU-PREPARATION/baseline.json')),groups206_noJulia=len(h['groups'])==206 and not h['matches'],refs_boot=all(h[k]==rd(F/'entry-host.json')[k] for k in ('head','master','boot_id')),old_cost_false=rd(F.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False,no_cost2=not any((F.parent/'DIRECT-LU-COST-PREPARATION').glob('cost2-*')),diff_clean=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0)
rm=rd(F/'review-mappings.json')['mappings'];checks['three_initial_plan_mappings']=len(rm)==3 and all(rd(R/z['record'])['sha256'][z['key']]==z['sha256']==sha(R/z['preserved_path']) for z in rm)
for p in F.glob('*.py'):ast.parse(p.read_text())
checks['new_python_syntax']=True
paths=[p for p in F.rglob('*') if p.is_file() and p.name not in ('closure.json','publication.json')]+[plan,R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
save(F/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in sorted(set(paths))}));req(all(checks.values()),'Closure failed; preserve and stop');print(dict(checks=len(checks),bindings=len(paths),all_passed=True))
