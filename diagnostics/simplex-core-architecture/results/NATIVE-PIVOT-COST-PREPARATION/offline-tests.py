"""New Python control/refusal tests. No launch, guard run, or historical audit."""
from pathlib import Path
import json,sys,copy,tempfile
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));checks={}
def rejects(f):
 try:f();return False
 except (RuntimeError,ValueError,KeyError,TypeError,FileNotFoundError):return True
try:
 import control as c
 cfg=c.config('cost')
 checks['cost_only_paths']=cfg['stage'].endswith('/native-pivot-cost/cost') and cfg['run']==str(D/'runs/cost') and cfg['output']==str(D/'runs/cost/output')
 checks['limits']=cfg['seconds']==45 and cfg['expected_exit']==0 and cfg['arm']=='candidate'
 checks['wrong_phases']=all(rejects(lambda p=p:c.config(p)) for p in ['red','green','green2','cost2','../cost'])
 checks['command']=cfg['command'][-4:]==[str(D/'cost-driver.jl'),cfg['output'],cfg['stage'],str(D/'inputs.toml')] and '--compiled-modules=existing' in cfg['command'] and '--threads=1' in cfg['command']
 cmd=c.guard_command(cfg,D/'fake-pins',100.)
 checks['inner37']=cmd[cmd.index('--seconds')+1]=='37' and cmd[cmd.index('--deadline')+1]=='137.0'
 good={'all_passed':True,'phase':'green2'};old={'all_passed':False,'phase':'green'}
 c.validate_prerequisites(good,old);checks['accepted_green2']=True
 for key,value in [('all_passed',False),('phase','green'),('phase','red')]:
  v=dict(good);v[key]=value;checks['reject_new_'+key+str(value)]=rejects(lambda v=v:c.validate_prerequisites(v,old))
 checks['old_failure_preserved']=rejects(lambda:c.validate_prerequisites(good,dict(old,all_passed=True)))
 checks['missing_review']=rejects(lambda:c.verify_review({},D/'missing',[],'offline preparation'))
 with tempfile.TemporaryDirectory() as temp:
  p=Path(temp)/'pins.json';p.write_text('{}');v={'accepted':True,'findings':[],'scope':'exact-stage admission','phase':'cost','pins_sha256':c.sha(p),'sha256':{str(p):c.sha(p)}}
  c.verify_review(v,p,[str(p)],'exact-stage admission','cost');checks['review_accept']=True
  for key,value in [('accepted',False),('findings',['unresolved']),('scope','offline preparation'),('phase','green2'),('pins_sha256','wrong'),('sha256',{})]:
   z=copy.deepcopy(v);z[key]=value;checks['reject_review_'+key]=rejects(lambda z=z:c.verify_review(z,p,[str(p)],'exact-stage admission','cost'))
  p.write_text('{"changed":true}');checks['changed_review_input']=rejects(lambda:c.verify_review(v,p,[str(p)],'exact-stage admission','cost'))
 from exact import validate_controls,validate_info,validate_timing,token
 base=[token(0.)]*20;base[3]=token(.1);policy=list(base);policy[3]=token(1.)
 validate_controls('P',policy,base);checks['policy_controls']=True
 bad=list(policy);bad[15]=token(1.);checks['reject_extra_control']=rejects(lambda:validate_controls('P',bad,base))
 checks['reject_refinement']=rejects(lambda:validate_info('P',[token(0.),token(1.),token(1.),token(0.)]))
 timing=dict(seconds=1.,bytes=0,events=0,gctime=0.,compile_time=0.,recompile_time=0.)
 validate_timing(timing);checks['timing_valid']=True
 for key,value in [('seconds',float('nan')),('bytes',-1),('events',.5)]:
  v=dict(timing);v[key]=value;checks['reject_timing_'+key]=rejects(lambda v=v:validate_timing(v))
 checks['no_run_or_stage']=not (D/'runs').exists() and not Path(cfg['stage']).exists()
except Exception as e:error=repr(e);checks['preparation_available']=False
else:error=''
z=dict(all_passed=all(checks.values()),checks=checks,error=error,scope='Synthetic offline gates only; not a numerical test or performance result')
with (D/sys.argv[1]).open('x') as f:json.dump(z,f,indent=2);f.write('\n')
print(dict(all_passed=z['all_passed'],checks=len(checks),error=error))
if not z['all_passed']:sys.exit(1)
