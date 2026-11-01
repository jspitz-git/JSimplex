from pathlib import Path
import json,hashlib,importlib.util,sys,os
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;cache={}
def read(p):return json.loads(p.read_text())
def sha(p):
 p=str(p)
 if p not in cache:
  with open(p,'rb') as f:cache[p]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[p]
def require(v,m):
 if not v:raise ValueError(m)
s=importlib.util.spec_from_file_location('task5verifyguard',D/'guard/guard_reviewed.py');G=importlib.util.module_from_spec(s);s.loader.exec_module(G)
require(G.pins_match(read(D/'public-green-pins.json')),'590 current pins')
q=read(D/'postcheck.json');g=q['qualification'];require(q['accepted'] is True and g['accepted'] is True and g['assertions']==4669 and g['skipped']==0 and g['public_repeated_passes']==424 and all(x['passed'] for x in q['checks']),'observed4669 unique ordinary tests and3699postchecks')
require(read(D/'green2-run/result.json')['accepted'] is False and read(D/'public-green-run/result.json')['accepted'] is True,'failed global main and accepted complete public file preserved')
a=read(D/'result-review.json');require(a['accepted'] is True and a['pins_sha256']==sha(D/'public-green-pins.json'),'exact independent result review')
for n,h in a['bindings'].items():require(sha(n)==h,'review binding '+n)
c=read(D/'closure.json');require(c['accepted'] is True and all(x['passed'] for x in c['checks']),'PASS closure')
for n,h in c['bindings'].items():require(sha(n)==h,'closure binding '+n)
for n,target in c['aliases'].items():require(Path(n).is_symlink() and os.readlink(n)==target and Path(n).resolve(strict=True)==D.parents[2]/'src','exact source alias')
print('PASS Task5 composite:4669 unique assertions/no skips,3699postchecks,590pins,independent review/closure; original GREEN2 remains failed; no Julia rerun')
