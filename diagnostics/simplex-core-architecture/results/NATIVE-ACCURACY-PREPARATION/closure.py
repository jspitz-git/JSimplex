"""Separate final preparation closure; never executes the numerical launcher."""
from common import *
from control import validate_review
import guard,ast
review=rd(F/'review-final.json');validate_review(review,F/'preparation-pins-reviewed.json',rd(F/'required-paths-reviewed.json'))
continuation=rd(F/'continuation.json');m=continuation['mappings']
def prior(record):
 z=rd(E/record)
 for n,h in z['sha256'].items():
  p=path(n)
  if sha(p)!=h:
   maps=[x for x in m if x['record']==str((E/record).relative_to(R)) and x['key']==n and x['sha256']==h]
   if len(maps)!=1 or sha(R/maps[0]['preserved_path'])!=h:return False
 return True
def mapped(z):
 for n,h in z['sha256'].items():
  if sha(path(n))==h:continue
  candidates=[]
  for v in rd(F/'review-fix.json')['mappings'].values():
   if v['sha256']==h:candidates.append(v['preserved'])
  for v in rd(F/'preparation-fix.json')['mappings'].values():
   if v['old_sha256']==h:candidates.append(v['preserved'])
  if not candidates or not any(sha(p)==h for p in candidates):return False
 return True
h=host();save(F/'closure-host.json',h)
fix=rd(F/'preparation-fix.json');test=rd(F/'offline-tests.json')
checks=dict(accepted=review['accepted'] is True and review['findings']==[],review_bindings=bindings(review),preparation_pins=guard.pins_match(rd(F/'preparation-pins-reviewed.json')),source20=rd(F/'source-check.json')['all_passed'] and mapped(rd(F/'source-check.json')),helper30=rd(F/'contract-green.json')['all_passed'] and len(rd(F/'contract-green.json')['checks'])==30,expected_python_red=rd(F/'contract-red.json')['all_passed'] is False,admission24=test['all_passed'] and len(test['checks'])==24,schema31=rd(F/'schema-tests.json')['all_passed'] and mapped(rd(F/'schema-tests.json')),fix4=fix['all_passed'] and mapped(fix),tested_drafts_preserved=all(test['sha256'][n]==z['old_sha256']==sha(z['preserved']) for n,z in fix['mappings'].items()),four_continuation_mappings=len(m)==4 and all(rd(R/z['record'])['sha256'][z['key']]==z['sha256']==sha(R/z['preserved_path']) for z in m),prior_closure=prior('closure.json'),prior_publication=prior('publication.json'),continuation_bound=bindings(continuation),baseline514=len(rd(F.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'])==514 and bindings(rd(F.parent/'DIRECT-LU-PREPARATION/baseline.json')),groups206_noJulia=len(h['groups'])==206 and not h['matches'],refs_boot=all(h[k]==rd(F/'host.json')[k] for k in ('head','master','boot_id')),no_numerical_stage=not (F.parent/'NATIVE-ACCURACY-QUALIFICATION').exists(),old_false=rd(F.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False,no_cost2=not any((F.parent/'DIRECT-LU-COST-PREPARATION').glob('cost2-*')),diff_clean=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0)
checks['rejected_review_preserved']=rd(F/'review.json')['accepted'] is False and mapped(rd(F/'review.json'))
checks['review_fix9']=rd(F/'review-fix.json')['all_passed'] and bindings(rd(F/'review-fix.json'))
checks['review_fix_tests18']=rd(F/'review-fix-tests.json')['all_passed'] and bindings(rd(F/'review-fix-tests.json'))
checks['admission24_all_bindings']=mapped(test)
for p in F.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['python_source_syntax']=True
paths=[p for p in F.rglob('*') if p.is_file() and p.name not in ('closure.json','publication.json')]+[R/'diagnostics/simplex-core-architecture/NATIVE-ACCURACY-PREPARATION.md',R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']
save(F/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in sorted(set(paths))},scope='Offline preparation only; no Julia/native run or admission'))
req(all(checks.values()),'Closure failed; preserve and stop');print(dict(checks=len(checks),bindings=len(paths),all_passed=True))
