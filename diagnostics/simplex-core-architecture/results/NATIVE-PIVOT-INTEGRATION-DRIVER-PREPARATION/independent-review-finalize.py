"""Exclusive canonical OFFLINE review record; no staging or numerical admission."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;R=D.parents[3]
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
p=D/'preparation-pins.json';pins=rd(p)['sha256'];fresh={n:sha(n) for n in pins}
a=rd(D/'independent-review-checks.json');s=rd(D/'independent-review-supplement.json')
checks=dict(all1503_current=fresh==pins and len(pins)==1503,absolute_paths=all(Path(n).is_absolute() for n in pins),exact_required=set(pins)==set(rd(D/'required-paths.json')['paths']),initial_preserved=a['failed']==['environment exact'] and len(a['checks'])==4172,supplement_pass=s['all_passed'] is True and len(s['checks'])==6,no_stage=not (R/'.superpowers/native-pivot-integration/integration').exists(),no_runs=not (D/'runs').exists(),environment_limitation='separately named environment' in (D/'continuation-text.md').read_text() and 'Before a future seal' in (D/'ENVIRONMENT-AFTER-INTERRUPTION.md').read_text())
save(D/'independent-review-final-checks.json',dict(all_passed=all(checks.values()),checks=checks,preparation_pins_sha256=sha(p),scope='Final fresh offline read-time bindings; no runtime execution'))
if not all(checks.values()):raise RuntimeError('Final reviewer checks failed; preserve all evidence')
names=['independent-review.py','independent-review-checks.json','independent-review-environment.py','independent-review-environment.json','independent-review-supplement.py','independent-review-supplement.json','review-initial.json','review.md','independent-review-finalize.py','independent-review-final-checks.json','finalize.py','publication.py','author-check.py','continuation-text.md','continuation-text.md.before-environment-note','ENVIRONMENT-AFTER-INTERRUPTION.md','root-environment-observation.json']
evidence={str(D/n):sha(D/n) for n in names}
for n,h in s['source_sha256'].items():
 if sha(n)!=h:raise RuntimeError('Supplemental inspected Test source drift')
 evidence[n]=h
fresh[str(p)]=sha(p)
save(D/'review-final.json',dict(accepted=True,findings=[],scope='offline preparation',pins_sha256=sha(p),sha256=fresh,evidence_sha256=evidence,checks=dict(initial=4172,initial_noncontext_passed=4171,supplemental=6,final=8),runtime='UNEXECUTED',launch_ready=False,limitation='Current root/worker PATH mismatch is refused. Separate reviewed environment amendment before any stage, then fresh exact-stage admission, remains required. No environment or pin normalization/overwrite.'))
print(json.dumps(dict(accepted=True,scope='offline preparation',bindings=len(fresh),evidence_bindings=len(evidence),pins_sha256=sha(p),runtime='UNEXECUTED',launch_ready=False)))
