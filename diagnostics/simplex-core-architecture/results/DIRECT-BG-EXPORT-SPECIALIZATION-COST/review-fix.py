"""One bounded offline review correction; original bound bytes preserved first."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=json.loads((D/'review.json').read_text())
if review['accepted'] is not False:raise ValueError('Expected preserved initial rejection')
names=['audit.py','evidence.py','control.py'];mapping={}
for n in names:
 p=D/n;q=D/(n+'.before-review')
 with q.open('xb') as f:f.write(p.read_bytes())
 mapping[str(p)]={'preserved':str(q),'sha256':sha(q)}
for n in ['review.md','review.json']:
 p=D/n;q=D/(n+'.initial')
 with q.open('xb') as f:f.write(p.read_bytes())
# Final review uses distinct reviewed receipt, leaving initial rejection in place.
p=D/'control.py';s=p.read_text().replace("m=D/'preparation-pins.json'","m=D/'preparation-pins-reviewed.json'").replace("rd(D/'required-paths.json')","rd(D/'required-paths-reviewed.json')").replace("rd(D/'review.json');verify_review","rd(D/'review-final.json');verify_review").replace("str(D/'review.json')","str(D/'review-final.json')");p.write_text(s)
p=D/'audit.py';s=p.read_text().replace('import tomllib,math','import tomllib,math\nimport record_schema as schema')
s=s.replace("resources,'Missing samples')","resources,'Missing samples')\n schema.runtime(p,cur,inv,resources,[pre,hs,post],cfg['seconds'])")
s=s.replace("p['returncode']==0 and p['reason']=='exit0' and sup['returncode']==0 and sup['accepted'] is True","schema.success(p,sup)");p.write_text(s)
p=D/'evidence.py';s=p.read_text().replace('from analysis import *','from analysis import *\nimport record_schema as schema')
s=s.replace('def probe_ok(v,f,matrices,backend):','def probe_ok(v,f,matrices,backend):\n schema.probe(v)')
s=s.replace('def control_ok(v):','def control_ok(v):\n schema.controls(v)')
s=s.replace("require(len(rows)==20 and read(out/end)==dict(identity,windows=20),'Complete cell')","ended=read(out/end);schema.cell(ended)\n    require(len(rows)==20 and ended==dict(identity,windows=20),'Complete cell')")
s=s.replace("raw=read(out/'raw.toml');require(","raw=read(out/'raw.toml');schema.raw(raw);require(")
s=s.replace("['hard_timeout','child_kill','guard_term','guard_kill']","['soft_timeout','hard_timeout','child_kill','guard_term','guard_kill','accepted']")
s=s.replace("and not sup.get('hard_timeout')","and sup.get('soft_timeout') is False and sup.get('accepted') is False and not sup.get('hard_timeout')");p.write_text(s)
with (D/'review-fix-map.json').open('x') as f:json.dump({'mapping':mapping,'scope':'Initial 2569 pins, initial 132/223 checks and rejected review retain exact before-review identities; canonical manifest binds corrected sources separately. No retroactive pass.'},f,indent=2);f.write('\n')
print('Preserved three initial sources and rejected review; applied cold validator hooks only.')
