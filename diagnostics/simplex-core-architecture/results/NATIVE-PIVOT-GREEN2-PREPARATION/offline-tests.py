"""New pure Python admission tests; no seal/launcher/Julia execution."""
from pathlib import Path
import json,copy,sys
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
checks={}
try:
 import control
 from oracle import regression_results
 def rejects(f):
  try:f();return False
  except (ValueError,RuntimeError,KeyError,TypeError):return True
 cfg=control.config('green2')
 checks['new_paths']=cfg['stage'].endswith('/native-pivot-green2/green2') and cfg['run']==str(D/'runs/green2') and cfg['output']==str(D/'runs/green2/output')
 checks['60_seconds']=cfg['seconds']==60 and cfg['expected_exit']==0 and cfg['arm']=='candidate'
 checks['old_phases_rejected']=all(rejects(lambda p=p:control.config(p)) for p in ['red','green','cost','../green2'])
 control.validate_prerequisites({'all_passed':True,'phase':'red'},{'all_passed':False,'phase':'green'})
 checks['distinct_predecessors']=True
 checks['red_failure_rejected']=rejects(lambda:control.validate_prerequisites({'all_passed':False,'phase':'red'},{'all_passed':False,'phase':'green'}))
 checks['green_success_substitution_rejected']=rejects(lambda:control.validate_prerequisites({'all_passed':True,'phase':'red'},{'all_passed':True,'phase':'green'}))
 root=dict(name='regression',pass_count=0)
 root={'name':'regression','pass':0,'fail':0,'error':0,'broken':0,'failures':[],'children':[{'name':'Dense diagnostic tokens preserve sparse inputs','pass':119,'fail':0,'error':0,'broken':0,'failures':[],'children':[]}]}
 good=dict(regression_tests=root,regression_helper_calls=16,regression_counts_before={},regression_counts_after={},phase='green2')
 regression_results(good);checks['119_synthetic_accept']=True
 for key,value in [('pass',118),('pass',120),('fail',1),('error',1),('broken',1),('children',[{}]),('failures',['hidden'])]:
  z=copy.deepcopy(good);z['regression_tests']['children'][0][key]=value
  checks['reject_child_'+key+'_'+str(value)]=rejects(lambda z=z:regression_results(z))
 for key,value in [('regression_helper_calls',15),('regression_helper_calls',17),('regression_counts_before',{'forward_solve':1}),('regression_counts_after',{'forward_solve':1}),('phase','green')]:
  z=copy.deepcopy(good);z[key]=value;checks['reject_'+key+'_'+str(value)]=rejects(lambda z=z:regression_results(z))
 checks['missing_raw_rejected']=rejects(lambda:regression_results({}))
 checks['missing_review_rejected']=rejects(lambda:control.verify_review({},D/'absent',[],'offline preparation'))
except Exception as e:
 checks['preparation_available']=False;error=repr(e)
else:error=''
result=dict(all_passed=all(checks.values()),checks=checks,error=error,scope='Pure synthetic Python gates only; no Julia or stored numerical audit rerun')
with (D/sys.argv[1]).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(dict(all_passed=result['all_passed'],checks=len(checks),error=error))
if not result['all_passed']:sys.exit(1)
