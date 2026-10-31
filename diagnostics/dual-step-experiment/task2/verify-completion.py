from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(v,m):
 if not v:raise ValueError(m)
p=read(D/'green-pins.json');require(len(p['files'])==149,'pin count')
require(all(sha(n)==v['sha256'] and str(Path(n).resolve())==v['resolved'] for n,v in p['inventory'].items()),'current launchpins')
require(read(D/'green-admission.json')['accepted'] is True and read(D/'green-admission.json')['pins_sha256']==sha(D/'green-pins.json'),'admission')
q=read(D/'postcheck.json');require(q['accepted'] is True and len(q['checks'])==498 and all(x['passed'] for x in q['checks']),'postchecks')
require(q['runs']['green']['assertions']==371,'assertions')
a=read(D/'result-review.json');require(a['accepted'] is True and a['pins_sha256']==sha(D/'green-pins.json'),'independent resultreview manifest binding')
require(all(sha(n)==h for n,h in a['bindings'].items()),'resultreview actual artifact bindings')
require(read(D/'red-run/result.json')['accepted'] is True and read(D/'red-run/result.json')['exit']==1,'RED')
require(read(D/'green-run/result.json')['accepted'] is True and read(D/'green-run/result.json')['exit']==0,'GREEN')
c=read(D/'closure.json');require(c['accepted'] is True and all(x['passed'] for x in c['checks']),'closure')
require(all(sha(n)==h for n,h in c['bindings'].items()),'closure bindings')
print('PASS Task2: observed371/371 GREEN,498postchecks,accepted independent review,149currentpins; no Julia rerun')
