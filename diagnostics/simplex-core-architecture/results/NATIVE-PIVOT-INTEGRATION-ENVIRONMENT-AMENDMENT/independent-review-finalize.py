"""New exclusive final review writer; read-only validation plus this review output only."""
from pathlib import Path
import hashlib,json,sys
D=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
import control as c
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
m=rd(D/'preparation-pins.json');initial=rd(D/'independent-review-checks.json');supp=rd(D/'independent-review-supplement.json')
assert initial['findings']==['test_selector_only_correction'] and len(initial['checks'])==198
assert supp['all_passed'] is True and len(supp['checks'])==6
assert len(m['sha256'])==1561 and set(m['sha256'])==set(rd(D/'required-paths.json')['paths'])
assert all(Path(n).is_absolute() and sha(Path(n))==h for n,h in m['sha256'].items())
c.validate_environment()
names=['independent-review.py','independent-review-checks.json','independent-review-supplement.py','independent-review-supplement.json','independent-review-finalize.py','review.md','finalize.py','publication.py','author-check.py','verify-publication.py','actual-baseline.json','continuation-text.md']
bindings={n:sha(Path(n)) for n in m['sha256']};bindings[str(D/'preparation-pins.json')]=sha(D/'preparation-pins.json')
assert len(bindings)==1562
review=dict(accepted=True,findings=[],scope='offline preparation',pins_sha256=sha(D/'preparation-pins.json'),sha256=bindings,evidence_sha256={str(D/n):sha(D/n) for n in names},checks=dict(initial_checks=198,initial_checks_passed=197,initial_reviewer_comparison_defect_resolved_by_supplement=True,supplement_checks=6,supplement_all_passed=True),runtime='UNEXECUTED',launch_ready=False,limitation='Offline amendment acceptance only. Fresh exact environment and host/pin validation, a fresh stage and separate independent exact-stage admission remain mandatory before one bounded attempt. No normalization, waiver or numerical execution.')
with (D/'review-final.json').open('x') as f:json.dump(review,f,indent=2);f.write('\n')
c.verify_review(rd(D/'review-final.json'),D/'preparation-pins.json',list(m['sha256'])+[str(D/'preparation-pins.json')],'offline preparation')
assert all(sha(Path(n))==h for n,h in review['evidence_sha256'].items())
print(json.dumps(dict(accepted=True,pins=1561,review_bindings=len(bindings),supplemental_bindings=len(names),runtime='UNEXECUTED',pins_sha256=review['pins_sha256'])))
