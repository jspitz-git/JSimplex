from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(v,m):
 if not v:raise ValueError(m)
p=read(D/'green-pins.json');require(len(p['files'])==290 and all(sha(n)==v['sha256'] and str(Path(n).resolve())==v['resolved'] for n,v in p['inventory'].items()),'290 actual pins')
for name in ['green-admission.json','result-review.json']:
 a=read(D/name);require(a['accepted'] is True and a['pins_sha256']==sha(D/'green-pins.json'),name+' manifest binding')
a=read(D/'result-review.json');require(all(sha(n)==h for n,h in a['bindings'].items()),'review actual bindings')
q=read(D/'postcheck.json');require(q['accepted'] is True and all(x['passed'] for x in q['checks']),'postchecks')
for stage,code in [('red',1),('underflow-red',1),('lifetime-red',1),('green',0)]:
 r=read(D/(stage+'-run/result.json'));require(r['accepted'] is True and r['exit']==code,stage)
require(q['runs']['green']['assertions']==555 and sum(v for n,v in q['runs']['green']['testsets'].items() if n.startswith('Task3 '))==184,'555 total/184 Task3 observed assertions')
for n,v in read(D/'completion-before-map.json').items():require(sha(v['preserved'])==v['sha256'] and n in a['bindings'] and sha(n)==a['bindings'][n],'pending/current continuation mapping')
c=read(D/'closure.json');require(c['accepted'] is True and all(x['passed'] for x in c['checks']) and all(sha(n)==h for n,h in c['bindings'].items()),'closure/checks/bindings')
print(f"PASS Task3: observed{q['runs']['green']['assertions']}/{q['runs']['green']['assertions']} GREEN,{len(q['checks'])}postchecks,accepted independent review,290currentpins; no Julia rerun")
