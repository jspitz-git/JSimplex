"""New OFFLINE Task1 closure, not a historical audit rerun."""
from common import *
import ast
review=rd(Q/'review-final.json');continuation=rd(Q/'continuation.json');maps=continuation['mappings']
def prior(rec):
 for n,digest in rd(rec)['sha256'].items():
  if sha(path(n))==digest:continue
  mm=[m for m in maps if m['record']==str(rec.relative_to(R)) and m['key']==n and m['sha256']==digest]
  if len(mm)!=1 or sha(R/mm[0]['preserved_path'])!=digest:return False
 return True
fix=rd(Q/'review-fix.json')
def initial_bound(rec):
 for n,digest in rd(rec)['sha256'].items():
  if sha(path(n))==digest:continue
  m=fix['mappings'].get(str(path(n)))
  if m is None or m['sha256']!=digest or sha(m['preserved'])!=digest:return False
 return True
h=host();save(Q/'closure-final-host.json',h);verify_host(h)
required=set(rd(Q/'review-final-required.json')['paths'])|{str(Q/'review-final-required.json')}
checks=dict(accepted=review['accepted'] is True and not review['findings'],review_bindings=bindings(review),review_membership=required<=set(review['sha256']),entry=rd(Q/'entry.json')['all_passed'] is True and bindings(rd(Q/'entry.json')),source=rd(Q/'source-check.json')['all_passed'] is True and initial_bound(Q/'source-check.json'),author=rd(Q/'author-check.json')['all_passed'] is True and initial_bound(Q/'author-check.json'),review_checker=rd(Q/'reviewer-check-final.json')['all_passed'] is True,baseline514=len(rd(Q.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'])==514 and bindings(rd(Q.parent/'DIRECT-LU-PREPARATION/baseline.json')),original_plan_review=rd(PREV/'review-final.json')['accepted'] is True and bindings(rd(PREV/'review-final.json')),plan_closure=prior(PREV/'closure.json'),plan_publication=prior(PREV/'publication.json'),plan_continuation=prior(PREV/'continuation.json'),six_exact_maps=len(maps)==6 and all(rd(R/m['record'])['sha256'][m['key']]==m['sha256']==sha(R/m['preserved_path']) for m in maps),continuation=bindings(continuation),refs_boot=h['head']==HEAD and h['master']==MASTER and h['boot_id']==rd(Q/'host.json')['boot_id'],full208groups_sessions=len(h['groups'])==208 and not h['matches'],old_cost1_false=rd(Q.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False,no_cost2=not any((Q.parent/'DIRECT-LU-COST-PREPARATION').glob('cost2-*')),no_run=not (Q.parent/'NATIVE-PIVOT-QUALIFICATION').exists(),production_untouched=not git('diff','--name-only','--','src','test','.github','Project.toml','diagnostics/direct-lu-markowitz/reproduce'),index_empty=not git('diff','--cached','--name-only'),diff_clean=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0,initial_author_failure_preserved=rd(Q/'author-check-failure.json')['exit_code']==1 and rd(Q/'author-check-failure.json')['source_sha256']==sha(Q/'author-check.py'))
checks.update(initial_rejection_preserved=rd(Q/'review.json')['accepted'] is False and initial_bound(Q/'review.json'),initial_prepare_preserved=initial_bound(Q/'prepare.json'),ten_fix_checks=fix['all_passed'] is True and len(fix['checks'])==10 and all(fix['checks'].values()) and bindings(fix),five_before_maps=len(fix['mappings'])==5 and all(sha(m['preserved'])==m['sha256'] for m in fix['mappings'].values()),final_checker_bound=all(review['sha256'].get(str(Q/n))==sha(Q/n) for n in ['reviewer-check-final.py','reviewer-check-final.json']),overlay_current_hashes=all(sha(e['source'])==e['sha256'] for arm in ['reference','candidate'] for e in rd(Q/'overlay-manifest.json')[arm]),inverse_candidate_hashes=all(sha(n)==h for n,h in rd(Q/'inverse.json')['candidate'].items()),overlay_unexecuted=not (R/'.superpowers/native-pivot-qualification').exists())
checks.update(original_closure_preserved=rd(Q/'closure.json')['all_passed'] is True and bindings(rd(Q/'closure.json')),whitespace_supplement=rd(Q/'whitespace-supplement.json')['all_passed'] is True and bindings(rd(Q/'whitespace-supplement.json')),publication_review=rd(Q/'publication-review.json')['accepted'] is True and not rd(Q/'publication-review.json')['findings'] and bindings(rd(Q/'publication-review.json')),failed_publication_preserved=rd(Q/'publication-failure.json')['exit_code']==1 and bindings(rd(Q/'publication-failure.json')))
for p in Q.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['python_syntax']=True
paths=sorted([p for p in Q.rglob('*') if p.is_file() and p.name not in ('closure-final.json','publication-final.json')]+[STATUS,ROAD])
save(Q/'closure-final.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in paths},scope='Task1 OFFLINE preparation only; no Julia, numerical or production admission'))
require(all(checks.values()),'Closure failed; preserve');print(dict(all_passed=True,checks=len(checks),bindings=len(paths)))
