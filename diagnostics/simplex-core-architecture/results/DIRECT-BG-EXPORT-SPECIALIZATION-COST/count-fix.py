"""Separate final-counter schema correction; all intermediate evidence preserved."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((D/'review-correction.json').read_text())
if r['accepted'] is not False:raise ValueError('Expected preserved correction rejection')
mapping={}
for n in ['control.py','evidence.py']:
 p=D/n;q=D/(n+'.before-count-fix')
 with q.open('xb') as f:f.write(p.read_bytes())
 mapping[str(p)]={'preserved':str(q),'sha256':sha(q)}
p=D/'evidence.py';s=p.read_text();needle=' schema.probe(v)';replacement=' schema.probe(v);counters(v[\'counts\'])'
if s.count(needle)!=1:raise ValueError('Expected exact probe entry')
p.write_text(s.replace(needle,replacement))
p=D/'control.py';s=p.read_text().replace('preparation-pins-reviewed.json','preparation-pins-final.json').replace('required-paths-reviewed.json','required-paths-final.json');p.write_text(s)
with (D/'count-fix-map.json').open('x') as f:json.dump(dict(mapping=mapping,scope='Intermediate2594 pins and2922authorcheck live control/evidence bind only these exact before-count-fix copies; initialbefore-review mapping unchanged.'),f,indent=2);f.write('\n')
print('Strict final counters added; control manifest reference advanced; Julia unchanged.')
