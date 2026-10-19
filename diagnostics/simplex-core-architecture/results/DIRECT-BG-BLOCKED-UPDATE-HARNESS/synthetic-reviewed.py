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
   sites=o.panel_counts();names=['budget and cheap eligibility','independent arithmetic, policy and canonical zeros','packed commit, incidence, support and source counters','computed commit cap and independent work witnesses'];children=[node(n,0) for n in names];children[0]['pass']=sum(sites.values())
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
  r=dict(sites=sites,events=e,apis=apis,failures=[dict(site='N026',kind='fail',detail='synthetic coverage')] if fail else [],failure_count=fail,active='')
  rows[f'unit-{idx}.toml']=dict(index=idx,name=name,complete=True,fatal='',tests=t,records=r,observations=obs)
  total=[x+y for x,y in zip(total,o.tree(t))]
 raw=dict(phase=mode+'300',complete=True,fatal='',units_completed=28,loaded={},threads=1,blas_threads=1,totals=total)
 return raw,rows

def run():
 for mode in ['red','green']:
  raw,rows=mock(mode);check(mode+'_complete',o.test_results(raw,rows,S,{},mode+'300')['expected_failures']==(6 if mode=='red' else 0))
  mutations={
   'unknown_event':lambda r,w:w['unit-3.toml']['records']['events'].update(unknown_event=1),
   'pure_without_rows':lambda r,w:w['unit-3.toml']['records']['events'].update(event_pure=1),
   'unknown_stream_catch':lambda r,w:w['unit-3.toml']['records']['events'].update(catch_overflow=1),
   'missing_unit':lambda r,w:w.pop('unit-28.toml'),
   'missing_site':lambda r,w:w['unit-3.toml']['records']['sites'].pop('N005'),
   'missing_finish_even_if_tests_removed':lambda r,w:w['unit-3.toml']['records']['events'].update(finish=15,event_finish=15),
   'missing_begin':lambda r,w:w['unit-3.toml']['records']['events'].update(event_begin=15),
   'wrong_api_attempts':lambda r,w:w['unit-2.toml']['records']['apis'].update(FTRAN=12),
   'wrong_unit_order':lambda r,w:w['unit-3.toml'].update(name='dense32/native'),
   'extra_site':lambda r,w:w['unit-1.toml']['records']['sites'].update(P999=1),
   'wrong_fixed_count':lambda r,w:w['unit-1.toml']['records']['sites'].update(P019=5759),
   'lost_private_attempt':lambda r,w:w['unit-3.toml']['records']['events'].update(event_panel_pivot=1),
   'extra_observation':lambda r,w:w['unit-3.toml']['observations'].append(copy.deepcopy(w['unit-3.toml']['observations'][0])),
   'nonfinite_pivot':lambda r,w:w['unit-3.toml']['observations'][0].update(minpivot=float('nan')),
   'negative_pivot':lambda r,w:w['unit-3.toml']['observations'][0].update(minpivot=0.),
   'excessive_rejections':lambda r,w:w['unit-3.toml']['observations'][0].update(rejections=2),
   'broken_test':lambda r,w:w['unit-1.toml']['tests'].update(broken=1),
   'false_complete':lambda r,w:r.update(complete=False),
   'bool_thread':lambda r,w:r.update(threads=True),
   'wrong_loaded_path':lambda r,w:r.update(loaded={'JSimplex':'bad'}),
   'aggregate_drift':lambda r,w:r['totals'].__setitem__(0,0),
   'interrupted_site':lambda r,w:w['unit-2.toml']['records'].update(active='L001'),
   'missing_catch_counter':lambda r,w:w['unit-2.toml']['records']['sites'].update(L025=1),
   'extra_unit_schema':lambda r,w:w['unit-1.toml'].update(extra=True),
   'extra_failure':lambda r,w:w['unit-3.toml']['records']['failures'].append(dict(site='N005',kind='fail',detail='wrong'))}
  for name,fn in mutations.items():
   r,w=copy.deepcopy((raw,rows));fn(r,w);rejects(mode+'_'+name,lambda:o.test_results(r,w,S,{},mode+'300'))
  if mode=='red':
   first=next(k for k,v in rows.items() if v['records']['failures']);r,w=copy.deepcopy((raw,rows));w[first]['records']['failures'][0]['site']='N005';rejects('red_wrong_failure_identity',lambda:o.test_results(r,w,S,{},mode+'300'))
  else:
   first=next(k for k,v in rows.items() if v['name'] in S['expected_red_units']);r,w=copy.deepcopy((raw,rows));w[first]['observations'][0]['panels']=0;rejects('green_missing_positive_route',lambda:o.test_results(r,w,S,{},mode+'300'))
  check(mode+'_empty_prefix',o.prefix({},S,mode+'300'));check(mode+'_valid_prefix',o.prefix({'unit-1.toml':rows['unit-1.toml']},S,mode+'300'))
  rejects(mode+'_prefix_hole',lambda:o.prefix({'unit-2.toml':rows['unit-2.toml']},S,mode+'300'))
 check('warning_world_age',o.warning_log('WARNING: world age issue'))
 check('no_warning_clean',not o.warning_log('UNIT END 1 panel'))
 return checks
if __name__=='__main__':
 result=run()
 with (D/'synthetic-reviewed.json').open('x') as f:json.dump(dict(all_passed=True,checks=result,scope=__doc__),f,indent=2)
 print('Synthetic pure oracle PASS',len(result))
