"""Pure Python rejection and exact-oracle checks; never launches a subprocess."""
from pathlib import Path
import json,sys,struct,copy
D=Path(__file__).resolve().parent
mode=sys.argv[1]
checks={}
try:
 from analysis import validate_info,validate_timing,validate_counts,validate_controls,residual,require
 def tok(x):return struct.pack('>d',float(x)).hex()
 def rejected(name,fn):
  try:fn();checks[name]=False
  except (ValueError,KeyError,TypeError):checks[name]=True
 checks['valid_R']=validate_info('R',list(map(tok,(0,1,2,12)))) is None
 checks['valid_C']=validate_info('C',list(map(tok,(0,0,0,12)))) is None
 for label,arm,values in [('negative','R',(0,0,-1,12)),('excess','R',(0,0,3,12)),('taken','R',(0,2,1,12)),('fraction','R',(0,.5,1,12)),('status','R',(1,0,0,12)),('C_attempt','C',(0,0,1,12)),('P_taken','P',(0,1,1,12)),('nan','R',(0,0,0,float('nan'))),('negative_flops','R',(0,0,0,-1))]:rejected(label,lambda arm=arm,values=values:validate_info(arm,list(map(tok,values))))
 valid=dict(seconds=1.,bytes=0,events=0,gctime=0.,compile_time=0.,recompile_time=0.)
 checks['valid_timing']=validate_timing(valid) is None
 for k,v in [('seconds',-1),('bytes',True),('events',1.5),('compile_time',float('inf')),('gctime',-1)]:
  d=dict(valid);d[k]=v;rejected('timing_'+k,lambda d=d:validate_timing(d))
 expected=dict(fresh=141,refactor=9,copy=3,ftran=4245,btran=2133,snapshot=12)
 checks['valid_counts']=validate_counts(expected) is None
 for k in expected:
  d=dict(expected);d[k]+=1;rejected('count_'+k,lambda d=d:validate_counts(d))
 b=[tok(0)]*20;b[3]=tok(.1);b[15]=tok(.001);c=list(b);c[3]=tok(1)
 checks['P_controls']=validate_controls('P',c,b) is None
 c[15]=tok(1);rejected('third_control',lambda:validate_controls('P',c,b))
 m=dict(n=2,colptr=[1,2,3],rowval=[1,2],nzval=[tok(1),tok(1)])
 checks['identity_exact']=residual(m,[tok(1),tok(2)],[tok(1),tok(2)])['passed'] is True
 checks['bad_residual_preserved']=residual(m,[tok(1),tok(2.1)],[tok(1),tok(2)])['passed'] is False
 rejected('nan_output',lambda:residual(m,[tok(float('nan')),tok(2)],[tok(1),tok(2)]))
 rejected('dimension',lambda:residual(m,[tok(1)],[tok(1),tok(2)]))
 error=''
except ModuleNotFoundError as e:error=repr(e)
out=dict(phase=mode,all_passed=bool(checks) and all(checks.values()),checks=checks,error=error,scope='Pure helper/negative data tests; not Julia or native qualification')
with (D/('contract-'+mode+'.json')).open('x') as h:json.dump(out,h,indent=2);h.write('\n')
print(json.dumps(out))
if mode=='red':
 if not error:raise SystemExit('Expected absent implementation')
elif not out['all_passed']:raise SystemExit('Contract failed')
