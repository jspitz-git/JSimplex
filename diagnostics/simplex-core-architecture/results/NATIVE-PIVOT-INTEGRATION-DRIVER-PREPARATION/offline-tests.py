"""Synthetic Python gate tests only. Never imports a launcher or runs Julia."""
from pathlib import Path
import sys,json,copy,tempfile
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));checks={}
def rejects(f):
 try:f();return False
 except (RuntimeError,ValueError,TypeError,KeyError,FileNotFoundError):return True
try:
 import control as c
 from oracle import test_results
 cfg=c.config('integration')
 checks['new_phase']=cfg['seconds']==60 and cfg['stage'].endswith('/native-pivot-integration/integration')
 checks['wrong_phase']=all(rejects(lambda p=p:c.config(p)) for p in ['green2','cost','../integration','red'])
 g=c.guard_command(cfg,D/'fake',100.)
 checks['inner52']=g[g.index('--seconds')+1]=='52' and g[g.index('--deadline')+1]=='152.0'
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'manifest';p.write_text('{}');v=dict(accepted=True,findings=[],scope='exact-stage admission',phase='integration',pins_sha256=c.sha(p),sha256={str(p):c.sha(p)})
  c.verify_review(v,p,[str(p)],'exact-stage admission','integration');checks['review_good']=True
  for k,x in [('accepted',False),('findings',['x']),('scope','offline preparation'),('phase','cost'),('pins_sha256','bad'),('sha256',{})]:
   z=copy.deepcopy(v);z[k]=x;checks['review_bad_'+k]=rejects(lambda z=z:c.verify_review(z,p,[str(p)],'exact-stage admission','integration'))
 raw=json.loads((D/'synthetic-good.json').read_text());test_results(raw,'integration');checks['good_raw']=True
 mutations=[('complete',False),('fatal','error'),('phase','cost'),('threads',2),('probe_failed',True),('started',8),('active',1)]
 for k,x in mutations:
  z=copy.deepcopy(raw);z[k]=x;checks['raw_bad_'+k]=rejects(lambda z=z:test_results(z,'integration'))
 for tag,mut in [('cap',lambda z:z['cases'][0]['attempts'].__setitem__(0,65)),('negative',lambda z:z['cases'][0]['attempts'].__setitem__(2,-1)),('boolcount',lambda z:z['cases'][0]['attempts'].__setitem__(2,True)),('emptyonly',lambda z:z['cases'][0]['empty'].__setitem__(0,1)),('missingcase',lambda z:z['cases'].pop()),('order',lambda z:z['cases'][0].__setitem__('id','wrong')),('control',lambda z:z['cases'][1]['last_controls'].__setitem__(0,'wrong')),('policy',lambda z:z['cases'][1].__setitem__('policy','default')),('unfinished',lambda z:z['cases'][0].__setitem__('finished',False)),('nonfinite',lambda z:z['cases'][0].__setitem__('objective','7ff0000000000000')),('point',lambda z:z['cases'][0]['point'].__setitem__(0,'0000000000000000')),('recoveryF',lambda z:z['cases'][8]['attempts'].__setitem__(2,3)),('recoveryB',lambda z:z['cases'][8]['attempts'].__setitem__(3,7)),('failure',lambda z:z['tests']['children'][0]['children'][0].__setitem__('fail',1)),('extra_test',lambda z:z['tests']['children'].append(copy.deepcopy(z['tests']['children'][1])))]:
  z=copy.deepcopy(raw);mut(z);checks[tag]=rejects(lambda z=z:test_results(z,'integration'))
 checks['missing_raw']=rejects(lambda:test_results({},'integration'))
 checks['no_stage']=not Path(cfg['stage']).exists() and not (D/'runs').exists()
except Exception as e:error=repr(e);checks['prepared']=False
else:error=''
with (D/sys.argv[1]).open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,error=error,scope='Synthetic offline gate tests, not a Julia run'),f,indent=2);f.write('\n')
print(dict(checks=len(checks),all_passed=all(checks.values()),error=error))
if not all(checks.values()):sys.exit(1)
