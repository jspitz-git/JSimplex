"""Separate offline final-counter correction checks; no Julia or operational audit."""
from pathlib import Path
import copy,hashlib,json,math,struct,sys,types,ast
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import evidence as e,analysis as a
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rd=lambda p:json.loads(Path(p).read_text());checks={}
def ck(n,v):checks[n]=bool(v)
def refuses(fn):
 try:fn();return False
 except (ValueError,RuntimeError,KeyError,TypeError,IndexError):return True
s=(D/'reviewer-check.py').read_text();exec(compile(s[s.index('def tok(x):'):s.index("with tempfile.TemporaryDirectory(prefix='bgxs-reviewer-pure-')")],'preserved-fixtures-only','exec'))
old=types.ModuleType('intermediate_pure_evidence');exec(compile((D/'evidence.py.before-count-fix').read_text(),'preserved-intermediate-evidence','exec'),old.__dict__)
f=fx[0];matrices=[(e.matrix(m),e.matrix(m,True)) for m in f['matrices']];v=probe()
ck('positive_native_probe',e.probe_ok(v,f,matrices,'native'));ck('positive_markowitz_probe',e.probe_ok(v,f,matrices,'markowitz'))
for k,n in v['counts'].items():
 # Detached dict: no accidental simultaneous mutation of the last checkpoint.
 z=copy.deepcopy(v);z['counts']=dict(v['counts']);z['counts'][k]=float(n)
 ck('RED_float:'+k,not refuses(lambda:old.probe_ok(z,f,matrices,'native')))
 ck('GREEN_float:'+k,refuses(lambda:e.probe_ok(z,f,matrices,'native')))
 if n in (0,1):
  z['counts'][k]=bool(n);ck('RED_bool:'+k,not refuses(lambda:old.probe_ok(z,f,matrices,'native')));ck('GREEN_bool:'+k,refuses(lambda:e.probe_ok(z,f,matrices,'native')))
 for bad in [-1,float('inf'),'0',None]:
  z['counts'][k]=bad;ck('invalid:'+k+':'+repr(bad),refuses(lambda:e.probe_ok(z,f,matrices,'native')))
for mutate in [lambda z:z['counts'].update(unknown=0),lambda z:z['counts'].pop('factorizations')]:
 z=copy.deepcopy(v);z['counts']=dict(v['counts']);mutate(z);ck('count_membership:'+str(len(checks)),refuses(lambda:e.probe_ok(z,f,matrices,'native')))
initial=rd(D/'review-fix-map.json')['mapping'];intermediate=rd(D/'count-fix-map.json')['mapping']
for name,mp in [('preparation-pins.json',initial),('source-check.json',initial),('offline-tests-2.json',initial),('preparation-pins-reviewed.json',intermediate),('review-fix-check.json',intermediate)]:
 for n,h in rd(D/name)['sha256'].items():ck('binding:'+name+':'+n,sha(mp[n]['preserved'] if n in mp else n)==h)
for n in ['audit.py','record_schema.py','cost.jl','probe.jl','analysis.py','stages.json','guard.py','supervisor.py','outer.py','seal.py','launch.py']:
 ck('unchanged:'+n,sha(D/n)==rd(D/'preparation-pins-reviewed.json')['sha256'][str(D/n)])
for n in ['control.py','evidence.py']:ast.parse((D/n).read_text());ck('syntax:'+n,True)
oldtext=(D/'evidence.py.before-count-fix').read_text();ck('single_validation_change',(D/'evidence.py').read_text()==oldtext.replace(' schema.probe(v)'," schema.probe(v);counters(v['counts'])"))
files=[D/n for n in ['count-fix-check.py','count-fix.py','count-fix-map.json','evidence.py','control.py','review-correction.json','review-fix-check.json']]
z=dict(all_passed=all(checks.values()),checks=checks,failed=[n for n,v in checks.items() if not v],sha256={str(p):sha(p) for p in files},scope='Detached final-counter synthetic RED/GREEN and exact preserved-lineage bindings only; no runtime proof')
with (D/'count-fix-check.json').open('x') as f:json.dump(z,f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=z['all_passed'],checks=len(checks),failed=z['failed'])))
if not z['all_passed']:raise SystemExit(1)
