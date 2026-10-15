"""New source/design closure; no numerical or historical auditor execution."""
from common import *
import ast
review=rd(Q/'review-final.json');c=rd(Q/'continuation.json');maps=c['mappings']
def prior(rec):
 for n,digest in rd(rec)['sha256'].items():
  if sha(path(n))==digest:continue
  mm=[m for m in maps if m['record']==str(rec.relative_to(R)) and m['key']==n and m['sha256']==digest]
  if len(mm)!=1 or sha(R/mm[0]['preserved_path'])!=digest:return False
 return True
fix=rd(Q/'review-fix.json');link=rd(Q/'review-link-fix.json')
def amendment_bound():
 m=link['mapping']
 if m['record']!=str(Q/'review-fix.json'):return False
 for n,digest in fix['sha256'].items():
  if sha(path(n))==digest:continue
  if n!=m['key'] or digest!=m['sha256'] or sha(m['preserved'])!=digest:return False
 return True
def initial_bound(rec):
 for n,digest in rd(rec)['sha256'].items():
  if sha(path(n))==digest:continue
  m=fix['mappings'].get(str(path(n)))
  if m is None or m['sha256']!=digest or sha(m['preserved'])!=digest:return False
 return True
h=host();save(Q/'closure-host.json',h);verify_host(h)
required=set(rd(Q/'review-final-required.json')['paths'])|{str(Q/'review-final-required.json')}
checks=dict(accepted=review['accepted'] is True and not review['findings'],review_bindings=bindings(review),review_membership=required<=set(review['sha256']),entry=rd(Q/'entry.json')['all_passed'] is True and bindings(rd(Q/'entry.json')),source=rd(Q/'source-evidence.json')['all_passed'] is True and initial_bound(Q/'source-evidence.json'),baseline514=len(rd(Q.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'])==514 and bindings(rd(Q.parent/'DIRECT-LU-PREPARATION/baseline.json')),qualification_review=rd(PREV/'result-review.json')['accepted'] is True and bindings(rd(PREV/'result-review.json')),qualification_closure=prior(PREV/'closure.json'),qualification_publication=prior(PREV/'publication.json'),qualification_continuation=prior(PREV/'continuation.json'),six_exact_maps=len(maps)==6 and all(rd(R/m['record'])['sha256'][m['key']]==m['sha256']==sha(R/m['preserved_path']) for m in maps),continuation=bindings(c),refs_boot=h['head']==HEAD and h['master']==MASTER and h['boot_id']==rd(Q/'host.json')['boot_id'],full208groups_sessions=len(h['groups'])==208 and not h['matches'],old_cost1_false=rd(Q.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False,no_cost2=not any((Q.parent/'DIRECT-LU-COST-PREPARATION').glob('cost2-*')),no_candidate_or_run=not (Q.parent/'NATIVE-PIVOT-PREPARATION').exists() and not (Q.parent/'NATIVE-PIVOT-QUALIFICATION').exists(),production_untouched=not git('diff','--name-only','--','src','test','.github','Project.toml','diagnostics/direct-lu-markowitz/reproduce'),index_empty=not git('diff','--cached','--name-only'),diff_clean=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0)
checks.update(initial_rejection_preserved=rd(Q/'review.json')['accepted'] is False and initial_bound(Q/'review.json'),initial_checker_false_preserved=rd(Q/'reviewer-check.json')['all_passed'] is False and sum(v is False for v in rd(Q/'reviewer-check.json')['checks'].values())==1,amendment_eight_checks=fix['all_passed'] is True and len(fix['checks'])==8 and all(fix['checks'].values()) and amendment_bound(),final_checker=rd(Q/'reviewer-check-final.json')['all_passed'] is True and all(rd(Q/'reviewer-check-final.json')['checks'].values()),final_checker_bound=all(review['sha256'].get(str(Q/n))==sha(Q/n) for n in ['reviewer-check-final.py','reviewer-check-final.json']),three_before_review_maps=len(fix['mappings'])==3 and all(sha(m['preserved'])==m['sha256'] for m in fix['mappings'].values()))
checks['final_link_amendment']=link['all_passed'] is True and len(link['checks'])==4 and all(link['checks'].values()) and bindings(link) and all(review['sha256'].get(str(Q/n))==sha(Q/n) for n in ['review-link-fix.py','review-link-fix.json','continuation.before-final-link.md'])
for p in Q.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['python_syntax']=True
paths=sorted([p for p in Q.rglob('*') if p.is_file() and p.name not in ('closure.json','publication.json')]+[R/'docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md',R/'docs/superpowers/plans/2026-10-15-native-pivot-policy.md',STATUS,ROAD])
save(Q/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in paths},scope='Source/design only; next isolated offline candidate preparation, no execution admission'))
require(all(checks.values()),'Closure failed; preserve');print(dict(all_passed=True,checks=len(checks),bindings=len(paths)))
