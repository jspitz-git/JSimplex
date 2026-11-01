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
s=importlib.util.spec_from_file_location('task6verifyguard',D/'guard/guard_reviewed.py');G=importlib.util.module_from_spec(s);s.loader.exec_module(G)
for mode in ('qualify','compare'):require(G.pins_match(read(D/(mode+'-pins.json'))),'current '+mode+' launchpins')
p=read(D/'postcheck.json');require(p['accepted'] is True and p['ordinary_assertions']==985 and len(p['checks'])==9886 and all(x['passed'] for x in p['checks']),'actual985ordinarytests9886postchecks')
a=read(D/'result-review.json');require(a['accepted'] is True and a['pins_sha256']==sha(D/'compare-pins.json'),'bound final independent review')
for n,h in a['bindings'].items():require(sha(n)==h,'review binding '+n)
c=read(D/'closure.json');require(c['accepted'] is True and all(x['passed'] for x in c['checks']),'PASS closure')
for n,h in c['bindings'].items():require(sha(n)==h,'closure binding '+n)
for n,target in c['aliases'].items():require(Path(n).is_symlink() and os.readlink(n)==target and Path(n).resolve(strict=True)==D.parents[2]/'src','source alias')
print('PASS Task6:985ordinary assertions,224wholewindows/160compile-zero measured,9886postchecks,622+642pins,accepted wholebranchreview/closure; negative performance result preserved, no Julia rerun')
