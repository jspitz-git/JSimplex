"""Offline synthetic admission tests only; no subprocess/Julia."""
from pathlib import Path
import sys,tempfile,json,hashlib
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import common,common_reviewed
results=[]
with tempfile.TemporaryDirectory(prefix='s5o-bindings-') as d:
 common.H=common_reviewed.H=Path(d)
 p=Path(d)/'manifest.json';p.write_text('{}');digest=hashlib.sha256(p.read_bytes()).hexdigest()
 other=Path(d)/'review.md';other.write_text('review');dh=hashlib.sha256(other.read_bytes()).hexdigest()
 for name,bindings,expected in [('empty',{},False),('missing_manifest',{str(other):dh},False),('wrong_hash',{str(p):'0'*64},False),('valid',{str(p):digest},True)]:
  f=Path(d)/(name+'.json');f.write_text(json.dumps({'accepted':True,'unresolved_findings':[],'reviewed_sha256':bindings}))
  def call(fn,*args):
   try:fn(*args);return True
   except AssertionError:return False
  old=call(common.accepted,f.name);new=call(common_reviewed.accepted,f.name,[p])
  assert new is expected
  results.append({'case':name,'original_accepts':old,'reviewed_accepts':new,'expected':expected})
assert results[0]['original_accepts'] and results[1]['original_accepts']
x={'all_passed':True,'RED_missing_binding_cases':2,'GREEN_cases':4,'cases':results,'sha256':{str(p):common_reviewed.sha(p) for p in (H/'common.py',H/'common_reviewed.py',H/'launcher.py',H/'launcher-reviewed.py',H/'review_fix.py',Path(__file__))}}
with (H/'review-fix.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps({'RED':2,'GREEN':4,'all_passed':True}))
