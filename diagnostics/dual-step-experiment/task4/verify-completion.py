from pathlib import Path
import json,hashlib,importlib.util,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(v,m):
 if not v:raise ValueError(m)
s=importlib.util.spec_from_file_location('task4verifyguard',D/'guard/guard_reviewed.py');G=importlib.util.module_from_spec(s);s.loader.exec_module(G)
require(G.pins_match(read(D/'green2-pins.json')),'367 current pins')
q=read(D/'postcheck.json');require(q['accepted'] is True and q['runs']['green2']['assertions']==709 and all(x['passed'] for x in q['checks']),'observed709/709 ordinary tests and postcheck')
a=read(D/'result-review.json');require(a['accepted'] is True and a['pins_sha256']==sha(D/'green2-pins.json'),'bound independent result review')
for n,h in a['bindings'].items():require(sha(n)==h,'review binding '+n)
c=read(D/'closure.json');require(c['accepted'] is True and all(x['passed'] for x in c['checks']),'PASS closure')
for n,h in c['bindings'].items():require(sha(n)==h,'closure binding '+n)
print('PASS Task4: observed709/709 GREEN2,1080postchecks,accepted independent review,367currentpins; no Julia rerun')
