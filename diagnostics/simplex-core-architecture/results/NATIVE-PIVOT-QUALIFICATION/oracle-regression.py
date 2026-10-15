"""New pure schema/oracle tests using stored tokens; NOT a new measurement.
No Julia, launches, stage writes, old script imports or historical audit reruns.
"""
from common import *
from oracle import cost_results,test_results
import copy,tomllib,math
A=Q.parent/'NATIVE-ACCURACY-PREPARATION';old=Q.parent/'NATIVE-ACCURACY-QUALIFICATION/portable'
schedule=rd(A/'inputs.json')['schedule'];old_windows={}
for spec in schedule:
 if spec['arm'] in ('C','P') and spec['round']==11:old_windows[spec['fixture'],spec['arm']]=tomllib.loads((old/f"window-{spec['id']:03d}.toml").read_text())
windows=[]
for spec in rd(Q/'inputs.json')['schedule']:
 source=old_windows[spec['fixture'],spec['arm']];n=source['before']['Wi']
 w=dict(schedule=spec,no_spare=True,fresh=True,reused=True,policy='_NATIVE_PIVOT_DEFAULT' if spec['arm']=='C' else '_NATIVE_PIVOT_ONE',owners=['a','b','c','a','b','c'],control=source['before']['control'],spare_control=source['before']['control'],info=source['factor']['info'],Wi=n,W=n,outputs=source['outputs'],solve_info=source['info'])
 for region in ['construction','refactor_fresh','refactor_spare','solve','total']:w[region]=dict(seconds=1.0,bytes=100,events=1,gctime=0.0,compile_time=0.0,recompile_time=0.0)
 if spec['round']==11:
  f=source['factor'];w['factor']=dict(lnz=f['lnz'],unz=f['unz'],m=n,n=n,nzd=n,graph_bytes=f['graph_bytes'],spare_W=n,spare_Wi=n)
 windows.append(w)
raw=dict(complete=True,fatal='',inputs_unchanged=True,threads=1,blas_threads=1,windows=88,counts=dict(construction=88,refactor=176,forward=2816,transpose=1408),output_payload_bytes=2162688,info_payload_bytes=135168,diagnostic_graph_bytes=2297856,default_control=old_windows['sparse32','C']['before']['control'])
positive=cost_results(raw,windows);require(positive['accuracy']['P'] and not positive['accuracy']['C'],'Known P/C oracle semantics')
cases=[]
def reject(name,r,w):
 try:cost_results(r,w)
 except (ValueError,RuntimeError,KeyError,TypeError):cases.append(name);return
 raise RuntimeError('Accepted mutation '+name)
for name,k,value in [('incomplete','complete',False),('wrong count','windows',87),('input mutation','inputs_unchanged',False),('missing Info buffer','info_payload_bytes',0)]:
 r=copy.deepcopy(raw);r[k]=value;reject(name,r,windows)
reject('missing window',raw,windows[:-1])
for name,key,value in [('policy reset','policy','_NATIVE_PIVOT_DEFAULT'),('owner collision','owners',['a']*6),('missing solve','outputs',[]),('short Info','solve_info',[]),('spare path absent','reused',False),('wrong scratch','W',0)]:
 w=copy.deepcopy(windows);w[1][key]=value;reject(name,raw,w)
w=copy.deepcopy(windows);w[6]['solve']['compile_time']=1.;reject('measured compile',raw,w)
w=copy.deepcopy(windows);w[1]['outputs'][0]=['0000000000000000']*32;reject('selected residual failure',raw,w)
w=copy.deepcopy(windows);w[1]['spare_control'][7]='4000000000000000';reject('refinement changed',raw,w)
w=copy.deepcopy(windows);w[0]['factor']={};reject('extra snapshot',raw,w)
w=copy.deepcopy(windows);w[0]['total']['seconds']=float('nan');reject('NaN timing',raw,w)
# Exact GREEN count gates refuse incomplete or plausible but wrong aggregate data.
b=rd(Q/'budget.json');groups=[dict(name=n,**{'pass':v,'fail':0,'error':0,'broken':0,'children':[],'failures':[]}) for n,v in b['test_groups'].items()]
g=dict(complete=True,fatal='',threads=1,blas_threads=1,tests=dict(children=groups,**{'pass':0,'fail':0,'error':0,'broken':0}),main_counts=b['main'],counts={},events=[],observation_limit=2048,equations=[])
for name,mutate in [('missing group',lambda z:z['tests']['children'].pop()),('wrong assertion count',lambda z:z['tests']['children'][0].update({'pass':4945})),('lost exception counter',lambda z:z['main_counts'].update({'refactorize':119})),('missing whole counts',lambda z:None)]:
 z=copy.deepcopy(g);mutate(z)
 try:test_results(z,'green')
 except (ValueError,RuntimeError,KeyError,TypeError):cases.append(name);continue
 raise RuntimeError('Accepted GREEN mutation '+name)
save(Q/'oracle-regression.json',dict(all_passed=True,refusals=cases,positive_known_C_false_P_true=True,scope='Pure synthetic metadata using preserved output tokens; unit tests of new oracle only. Synthetic seconds1/bytes100/events1 are NOT measurements.',sha256={str(p):sha(p) for p in [Path(__file__),Q/'oracle.py',Q/'exact.py',Q/'budget.json',Q/'inputs.json',Q/'saved-C.json']}))
print(dict(all_passed=True,refusals=len(cases)))
