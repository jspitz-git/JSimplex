"""One-shot OFFLINE preparation closure, never launches Julia."""
from control import *
import ast
pins=D/'preparation-pins.json';review=rd(D/'review.json')
verify_review(review,pins,list(rd(pins)['sha256'])+[str(pins)],'offline preparation')
h=full_host();save(D/'closure-host.json',h);verify_host(h)
cont=rd(D/'continuation.json');maps=cont['mappings']
def prior(rec):
 for n,digest in rd(rec)['sha256'].items():
  if sha(path(n))==digest:continue
  hit=[m for m in maps if m['record']==str(rec.relative_to(R)) and m['key']==n and m['sha256']==digest]
  if len(hit)!=1 or sha(R/hit[0]['preserved_path'])!=digest:return False
 return True
checks=dict(review=review['accepted'] is True and review['findings']==[],preparation_pins=bindings(rd(pins)),review_bindings=bindings(review),entry=bindings(rd(D/'entry.json')),continuation=bindings(cont),prior_closure=prior(PREV/'closure-final.json'),prior_publication=prior(PREV/'publication-final.json'),prior_continuation=prior(PREV/'continuation.json'),original_candidate=all(sha(e['source'])==e['sha256'] for arm in ['reference','candidate'] for e in rd(PREV/'overlay-manifest.json')[arm]),host=not h['matches'] and len(h['groups'])==208,no_run=not (D/'runs').exists(),no_overlay=not (R/'.superpowers/native-pivot-qualification').exists(),actual_unchanged=not git('diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce'),index_empty=not git('diff','--cached','--name-only'),old_cost1_false=rd(D.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False)
for p in D.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
checks['python_syntax']=True
names=rd(D/'publication-names.json')['names'];planned={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}|{str(STATUS.relative_to(R)),str(ROAD.relative_to(R)),str((D/'closure.json').relative_to(R)),str((D/'publication.json').relative_to(R))}
checks['exact_planned_names']=set(names)==planned and len(names)==len(set(names))
paths=[R/n for n in names if n not in [str((D/'closure.json').relative_to(R)),str((D/'publication.json').relative_to(R))]]
save(D/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in paths},scope='Offline preparation only; three numerical stages unexecuted'))
require(all(checks.values()),'Closure failed; preserve');print(dict(checks=len(checks),bindings=len(paths),all_passed=True))
