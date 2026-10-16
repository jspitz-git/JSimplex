"""Serialize reviewed admission; independently rehash, no project imports."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
s=json.loads((P/'sealed.json').read_text());checks=json.loads((P/'admission-independent-checks-v2.json').read_text())
assert checks['all_passed'] is True and checks['count']==393 and all(x['passed'] for x in checks['checks'])
assert sha(P/'sealed.json')==checks['facts']['sealed_sha256']=='80c08e9e0312c58605121d9082ff1dbffa4745aa0c6b419cc3fa3d8d75e53d6d'
assert all(sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in s['inventory'].items())
assert not any((P/n).exists() for n in ['output','reservation.json','invocation.json','launch-pins.json','admission.json'])
names=s['files']+[str(P/'sealed.json')];assert len(names)==len(set(names))==1810
evidence=['admission.md','admission-independent-check.py','admission-independent-checks.json','admission-independent-first-check-note.json','admission-independent-check-v2.py','admission-independent-checks-v2.json','admission-write.py']
a=dict(accepted=True,findings=[],scope='direct adapter matched cost admission',phase='cost1-300',pins_sha256=sha(P/'sealed.json'),sha256={n:sha(n) for n in names},evidence_sha256={str(P/n):sha(P/n) for n in evidence})
with (P/'admission.json').open('x') as f:json.dump(a,f,indent=2);f.write('\n')
saved=json.loads((P/'admission.json').read_text());assert saved==a and all(sha(n)==v for n,v in saved['evidence_sha256'].items())
print(json.dumps(dict(accepted=True,findings=[],checks=393,bindings=len(saved['sha256']),evidence=len(saved['evidence_sha256']),pins_sha256=saved['pins_sha256'],admission_sha256=sha(P/'admission.json'))))
