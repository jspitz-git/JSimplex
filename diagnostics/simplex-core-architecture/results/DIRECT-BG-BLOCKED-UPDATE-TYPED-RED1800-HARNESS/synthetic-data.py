"""Synthetic saved-data controls only; no Julia, outer, seal, guard or launcher execution."""
from pathlib import Path
import json,copy,sys
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
import oracle as o
S=json.loads((D/'schedule.json').read_text())
checks={}
def check(n,v):
 if not v:raise RuntimeError(n)
 checks[n]=True
def rejects(n,f):
 try:f()
 except (ValueError,KeyError,TypeError,RuntimeError):check(n,True)
 else:check(n,False)
def node(name,n,fail=0,children=None):return dict(name=name,**{'pass':n-fail,'fail':fail,'error':0,'broken':0},children=children or [])
def mock(mode):
 rows={};total=[0,0,0,0]
 for idx,name in enumerate(S['units'],1):
  e={};apis={};obs=[];children=[]
  if idx==1:
   sites=o.panel_counts();names=['budget and cheap eligibility','independent arithmetic, policy and canonical zeros','packed commit, incidence, support and source counters','computed commit cap and independent work witnesses'];children=[node(n,k) for n,k in zip(names,[31,11619,74,44])]
  elif idx==2:
   e={'finish':3,'event_finish':3,'event_begin':3,'pivot':12,'event_scalar_pivot':12}
   sites={f'L{i:03d}':1 for i in range(1,41)}
   for lo,hi,n in [(1,22,2),(31,32,2),(33,35,3)]:
    for i in range(lo,hi+1):sites[f'L{i:03d}']=n
   sites.update(L025=0,L030=0);sites.update(o.trace_counts(e,3))
   apis={'factory_candidate':2,'factory_micro':12,'FTRAN':13,'BTRAN':2,'replace':8,'copy':6,'refactor':8,'eliminate':8,'eliminate_fault':4}
   children=[node('blocked BG lifecycle and failure ownership',sum(sites.values()))]
  else:
   f=S['fixtures'][(idx-3)//2];u=f['updates'];panels=0 if mode=='red' else f['minimum_panels'];e={'finish':2*u,'event_finish':2*u,'event_begin':2*u,'pivot':2*u,'event_scalar_pivot':2*u}
   if panels:e.update(event_panel_begin=panels,event_panel_commit=panels,event_eligibility=panels,event_panel_pivot=8*panels,pivot=2*u+8*panels)
   sites=o.trace_counts(e,2*u);sites.update({f'N{i:03d}':u for i in range(15,26)});sites.update(N013=1,N014=1,N021=2*u,N024=u if f['pivot_agreement'] else 0,N026=1)
   apis={'factory_reference':1,'factory_candidate':1,'FTRAN':6*u,'BTRAN':2*u,'replace_reference':u,'replace_candidate':u}
   obs=[dict(panels=panels if i==0 else 0,rejections=0,growth=4.,minpivot=1.) for i in range(u)]
  sites=o.sparse(sites);fail=int(mode=='red' and name in S['expected_red_units']);n=sum(sites.values())
  t=node(name,0 if children else n,fail,children)
  r=dict(sites=sites,events=e,apis=apis,failures=[dict(site='N026',kind='fail',detail='Test Failed at numerical-tests.jl:163\n  Expression: sum(o.panels for o in observed) >= f["minimum_panels"]')] if fail else [],failure_count=fail,active='')
  rows[f'unit-{idx}.toml']=dict(index=idx,name=name,complete=True,fatal='',tests=t,records=r,observations=obs)
  total=[x+y for x,y in zip(total,o.tree(t))]
 raw=dict(phase=mode+'300',complete=True,fatal='',units_completed=28,loaded={},threads=1,blas_threads=1,totals=total)
 return raw,rows

def metric():return dict(seconds=.1,bytes=80,events=2,gc_seconds=.01,compile_seconds=.02,recompile_seconds=.0)
LOADED={}
def fixture(phase):
 raw,rows=mock('red' if phase=='red300' else 'green')
 return {**rows,'raw.toml':raw,**{n:metric() for n in o.PREPARATION}}
def logfile(phase,payload):
 out='BEGIN BG blocked U driver '+phase+'\n'
 for i in range(1,29):
  u=payload[f'unit-{i}.toml'];out+=f"UNIT BEGIN {i} {u['name']}\n"
  for f in u['records']['failures']:out+='TEST FAILURE: '+f['site']+' '+f['detail']+'\n'
  out+=f"UNIT END {i} {u['name']}\n"
 return out
