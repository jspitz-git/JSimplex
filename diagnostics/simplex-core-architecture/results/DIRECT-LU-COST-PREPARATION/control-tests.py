"""New fail-closed synthetic controls. No process launch, seal, Julia or old audit."""
from pathlib import Path
import copy,json,tempfile,ast
import control as c
from analysis import *
D=c.D;checks={}
def check(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
def refuses(n,f):
 try:f()
 except (ValueError,KeyError,TypeError):check(n,True)
 else:check(n,False)
original=c.rd;config=original(D/'config.json')
for phase in ('cost1','cost2'):
 check(phase+'_exact',c.phase_config(phase)==c.expected_config(phase))
 for key in ('seconds','expected_exit','output','project','cells','pairs','warm_pairs','measured_pairs','windows','command'):
  changed=copy.deepcopy(config);changed[phase][key]='invalid';c.rd=lambda p,changed=changed:changed
  refuses(phase+'_reject_'+key,lambda:c.phase_config(phase))
 c.rd=original
refuses('reject_third_phase',lambda:c.phase_config('cost3'))
with tempfile.TemporaryDirectory(prefix='direct-lu-cost-test-') as td:
 p=Path(td)/'pins';p.write_text('{}');required=[str(p)]
 r=dict(accepted=True,findings=[],pins_sha256=c.sha(p),sha256={str(p):c.sha(p)})
 check('valid_review',c.validate_review(r,p,required) is None)
 for key,val in [('accepted',False),('findings',['unresolved']),('pins_sha256','wrong'),('sha256',{}),('sha256',{str(p):'wrong'})]:
  x=copy.deepcopy(r);x[key]=val;refuses('review_'+key+str(len(checks)),lambda:c.validate_review(x,p,required))
# Complete tiny synthetic row exercises actual window predicates.
import struct
def tok(x):return struct.pack('>d',x).hex()
m=dict(n=2,colptr=[1,2,3],rowval=[1,2],nzval=[tok(1.),tok(1.)]);step=dict(j=1,a=[tok(1.),tok(0.)],dse=[tok(.5),tok(1.)],unit=[tok(1.),tok(0.)]);f=dict(steps=[step]*8)
matrices=[(matrix(m),matrix(m,True))]*9
row=dict(pair=4,order=1,side='candidate',measured=True,correct=True,inputs_unchanged=True,modes=['normalized']*3,seconds=1.,bytes=100,events=10,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,retained_bytes=100,nested_seconds=[.1]*6,outputs=[step[k] for _ in range(8) for k in ('a','dse','unit')])
check('window_valid',window_ok(row,f,1,4,1,matrices))
for key,val in [('pair',3),('side','reference'),('measured',False),('correct',False),('inputs_unchanged',False),('modes',['fallback']*3),('seconds',float('nan')),('bytes',-1),('events',1.5),('compile_seconds',1e-9),('recompile_seconds',1e-9),('nested_seconds',[.2]*6),('outputs',[])]:
 x=copy.deepcopy(row);x[key]=val;refuses('window_'+key,lambda:window_ok(x,f,1,4,1,matrices))
x=copy.deepcopy(row);x['outputs'][0]=[tok(0.),tok(0.)];refuses('exact_residual_failure',lambda:window_ok(x,f,1,4,1,matrices))
# Boundary arithmetic for paired selection, preserve GC and outliers.
rows=[]
for pair in range(4,11):
 for side,time,mem in [('reference',1.,100),('candidate',.9,110)]:
  rows.append(dict(row,pair=pair,side=side,seconds=time,retained_bytes=mem,gc_seconds=.01))
s=summarize(rows);check('boundary110_memory_pass',s['memory_gate']);check('gc_retained',s['gc_seconds']['candidate']['median']==.01)
rows[-1]['retained_bytes']=111;check('one_memory_increase_rejects',not summarize(rows)['memory_gate'])
rows[-1]['seconds']=100.;check('outlier_retained',summarize(rows)['seconds']['paired_ratio']['maximum']==100.)
for path in D.glob('*.py'):
 ast.parse(path.read_text(),filename=str(path));check('python_syntax_'+path.name,True)
check('guard_byte_identity',c.sha(D/'guard.py')==original(D/'source-lineage.json')['guard_sources']['guard.py'])
check('supervisor_byte_identity',c.sha(D/'supervisor.py')==original(D/'source-lineage.json')['guard_sources']['supervisor.py'])
with (D/'control-tests.json').open('x') as o:json.dump(dict(all_passed=all(checks.values()),checks=checks),o,indent=2)
print(json.dumps(dict(all_passed=True,checks=len(checks))))
