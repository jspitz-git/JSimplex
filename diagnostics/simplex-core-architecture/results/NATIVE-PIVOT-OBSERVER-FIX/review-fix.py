"""One-shot source-only correction checks; no Julia parsing/execution."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
old=(D/'regression.jl').read_text();new=(D/'regression-reviewed.jl').read_text()
a='copy(nonzeroinds(v))';b='copy(SparseArrays.nonzeroinds(v))'
c='nothing for x in v]';d='nothing for x in (v isa SparseVector ? nonzeros(v) : v)]'
pins=rd(D/'pins.json')['sha256'];review=rd(D/'review.json')
checks=dict(source_RED_api=a in old and b not in old,source_RED_owners=c in old and d not in old,source_GREEN_api=b in new and a not in new,source_GREEN_owners=d in new and c not in new,exact_two_edit_inverse=new.replace(b,a).replace(d,c)==old,prospective_assertions_unchanged=old.count('@test')==new.count('@test') and 12*9+4*2+1+2==119,initial33_preserved=len(pins)==33 and all(sha(n)==v for n,v in pins.items()),initial_rejection_preserved=review['accepted'] is False and len(review['findings'])==2,helper_driver_unchanged=all(sha(D/n)==pins[str(D/n)] for n in ['test-support-fixed.jl','test-driver-fixed.jl']),corrected_claims='Implicit zeros have value coverage' in (D/'REPORT-final.md').read_text(),canonical_finalizer="pins=D/'pins-reviewed.json';review=rd(D/'review-final.json')" in (D/'finalize-reviewed.py').read_text())
files=['regression.jl','regression-reviewed.jl','REPORT-final.md','continuation-text-reviewed.md','finalize-reviewed.py','review-fix.py','review.json','review.md','review-errata.json','review-errata.md','reviewer-check.py','reviewer-check.json','pins.json','test-support-fixed.jl','test-driver-fixed.jl']
with (D/'review-fix.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,sha256={str(D/n):sha(D/n) for n in files},scope='Source RED/GREEN only, 119 assertions UNEXECUTED; no Julia'),f,indent=2);f.write('\n')
if not all(checks.values()):raise RuntimeError(checks)
print(dict(checks=len(checks),bindings=len(files),all_passed=True))
