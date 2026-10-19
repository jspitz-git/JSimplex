"""Pure, strict saved-data validation; no execution or file writes."""
import math,re

def need(v,m):
 if not v:raise ValueError(m)
def integer(x):return type(x) is int and x>=0
def counts(x):return type(x) is dict and all(type(k) is str and integer(v) and v>0 for k,v in x.items())
def sparse(d):return {k:v for k,v in d.items() if v}
def warning_log(s):return bool(re.search(r'warning|world.?age|method.*overwrite',s,re.I))
def tree(t):
 need(type(t) is dict and set(t)=={'name','pass','fail','error','broken','children'},'Test tree schema')
 need(type(t['name']) is str and type(t['children']) is list,'Tree types')
 a=[t[k] for k in ['pass','fail','error','broken']];need(all(integer(x) for x in a),'Tree counts')
 for c in t['children']:a=[x+y for x,y in zip(a,tree(c))]
 return a

TRACE_EVENTS={'pivot','pure_row','finish','declined_before_gather'}|{'event_'+s for s in ['begin','finish','panel_begin','panel_pivot','scalar_pivot','pure','panel_reject','panel_commit','eligibility','scalar_suffix']}
def trace_counts(e,finished):
 need(set(e)<=TRACE_EVENTS|{'catch_overflow','catch_nonfinite'},'Unknown trace event')
 need(e.get('event_pure',0)<=e.get('pure_row',0) and (e.get('event_pure',0)==0)==(e.get('pure_row',0)==0),'Pure event/row consistency')
 need(e.get('event_scalar_suffix',0)<=finished,'At most one scalar suffix/trace')
 begun=e.get('event_panel_begin',0);committed=e.get('event_panel_commit',0);rejected=e.get('event_panel_reject',0);declined=e.get('declined_before_gather',0)
 need(0<=declined<=rejected<=finished and begun==committed+rejected-declined and e.get('event_eligibility',0)==begun+declined,'Panel/eligibility attempt accounting')
 need(8*committed<=e.get('event_panel_pivot',0)<=8*begun,'Panel raw pivot budget')
 need(e.get('finish',0)==e.get('event_finish',0)==e.get('event_begin',0)==finished,'Mandatory trace completions')
 p=e.get('pivot',0);z=e.get('pure_row',0)
 need(p==e.get('event_panel_pivot',0)+e.get('event_scalar_pivot',0),'Raw pivot attempts')
 return {**{f'N{i:03d}':p for i in range(1,4)},'N004':z,**{f'N{i:03d}':finished for i in range(5,13)}}
def panel_counts():
 d={f'P{i:03d}':1 for i in range(1,95)}
 for i,n in [(1,5),(13,2),(15,4),(27,3),(66,2)]:d[f'P{i:03d}']=n
 for lo,hi,n in [(16,18,10),(19,20,5760),(21,26,10),(34,45,4),(62,64,3),(85,91,3)]:
  for i in range(lo,hi+1):d[f'P{i:03d}']=n
 return d

def unit(row,index,schedule,mode):
 need(set(row)=={'index','name','complete','fatal','tests','records','observations'},'Unit schema')
 name=schedule['units'][index-1]
 need(type(row['index']) is int and row['index']==index and row['name']==name and row['complete'] is True and row['fatal']=='','Unit completion/order')
 r=row['records'];need(set(r)=={'sites','events','apis','failures','failure_count','active'},'Records schema')
 need(all(counts(r[k]) for k in ['sites','events','apis']) and r['active']=='','Counter types/active assertion')
 e=r['events'];apis=r['apis'];obs=row['observations']
 need(type(obs) is list,'Observation list')
 if index==1:
  expected=panel_counts();need(e=={} and apis=={} and obs==[],'Panel work')
  children=['budget and cheap eligibility','independent arithmetic, policy and canonical zeros','packed commit, incidence, support and source counters','computed commit cap and independent work witnesses']
 elif index==2:
  expected={f'L{i:03d}':1 for i in range(1,41)}
  for lo,hi,n in [(1,22,2),(31,32,2),(33,35,3)]:
   for i in range(lo,hi+1):expected[f'L{i:03d}']=n
  # Negative fallback may either return nonfinite or throw ZeroPivotException.
  need(e.get('catch_overflow',0) in (0,1) and e.get('catch_nonfinite',0) in (0,1,2),'Optional catch bounds')
  expected['L025']=e.get('catch_overflow',0);expected['L030']=e.get('catch_nonfinite',0)
  expected.update(trace_counts(e,3))
  need(apis=={'factory_candidate':2,'factory_micro':12,'FTRAN':13,'BTRAN':2,'replace':8,'copy':6,'refactor':8,'eliminate':8,'eliminate_fault':4},'Lifecycle PREentry API budget')
  need(obs==[],'Lifecycle observations');children=['blocked BG lifecycle and failure ownership']
 else:
  f=schedule['fixtures'][(index-3)//2];u=f['updates'];n=f['n']
  need(set(e)<=TRACE_EVENTS,'Unexpected stream catch/event')
  expected=trace_counts(e,2*u)
  need(e.get('pure_row',0)+e.get('event_scalar_pivot',0)+e.get('event_panel_pivot',0)<=2*u*(n-1+8),'Bounded raw pivot work')
  need(e.get('event_panel_reject',0)<=u and e.get('event_panel_begin',0)==e.get('event_panel_commit',0)+e.get('event_panel_reject',0)-e.get('declined_before_gather',0),'Panel accounting')
  expected.update({f'N{i:03d}':u for i in range(15,26)})
  expected.update(N013=1,N014=1,N021=2*u,N024=u if f['pivot_agreement'] else 0,N026=1)
  need(apis=={'factory_reference':1,'factory_candidate':1,'FTRAN':6*u,'BTRAN':2*u,'replace_reference':u,'replace_candidate':u},'Stream PREentry API budget')
  need(len(obs)==u,'Observation count')
  for o in obs:
   need(type(o) is dict and set(o)=={'panels','rejections','growth','minpivot'},'Observation schema')
   need(integer(o['panels']) and integer(o['rejections']) and o['rejections']<=1,'Observation work')
   need(all(type(o[k]) is float and math.isfinite(o[k]) and o[k]>0 for k in ['growth','minpivot']),'Finite growth/pivot')
  need(sum(o['panels'] for o in obs)==e.get('event_panel_commit',0) and sum(o['rejections'] for o in obs)==e.get('event_panel_reject',0),'Observed route ledger')
  if mode=='red':need(e.get('event_panel_begin',0)==e.get('event_panel_commit',0)==e.get('event_eligibility',0)==e.get('event_panel_reject',0)==0,'RED scalar route')
  else:need(sum(o['panels'] for o in obs)>=f['minimum_panels'],'GREEN positive route')
  children=[]
 need(r['sites']==sparse(expected),'Exact event-conditioned assertion counts')
 t=row['tests'];need(t['name']==name and [c['name'] for c in t['children']]==children,'Named test groups')
 need(all(c['children']==[] for c in t['children']),'No hidden nested groups')
 if children:need(all(t[k]==0 for k in ['pass','fail','error','broken']),'No unlisted root checks')
 a=tree(t);expected_fail=1 if mode=='red' and name in schedule['expected_red_units'] else 0
 need(sum(a)==sum(expected.values()) and a[1:]==[expected_fail,0,0],'Exact result counts')
 failures=r['failures'];need(type(failures) is list and type(r['failure_count']) is int and r['failure_count']==len(failures)==expected_fail,'Named failure count')
 for f in failures:need(set(f)=={'site','kind','detail'} and f['site']=='N026' and f['kind']=='fail' and type(f['detail']) is str and f['detail'],'Expected RED site')
 return a

def test_results(raw,rows,schedule,loaded,phase):
 need(type(raw) is dict and set(raw)=={'phase','complete','fatal','units_completed','loaded','threads','blas_threads','totals'},'Raw schema')
 need(raw['phase']==phase and raw['complete'] is True and raw['fatal']=='' and type(raw['units_completed']) is int and raw['units_completed']==28,'Raw completion')
 need(raw['loaded']==loaded and type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1,'Loaded paths/threads')
 need(set(rows)=={f'unit-{i}.toml' for i in range(1,29)},'Full unit roster')
 total=[0,0,0,0]
 for i in range(1,29):total=[x+y for x,y in zip(total,unit(rows[f'unit-{i}.toml'],i,schedule,'red' if phase=='red300' else 'green'))]
 need(type(raw['totals']) is list and all(integer(x) for x in raw['totals']) and raw['totals']==total,'Aggregate reconciliation')
 return {'totals':total,'units':28,'expected_failures':6 if phase=='red300' else 0,'scope':'Source-bound event-conditioned counts; no performance acceptance'}

def prefix(rows,schedule,phase):
 need(set(rows)=={f'unit-{i}.toml' for i in range(1,len(rows)+1)} and len(rows)<=28,'Saved unit prefix')
 # Fully saved successful units are checked even in a timeout. An interrupted
 # unit is preserved but cannot establish timeout-only status automatically.
 for i in range(1,len(rows)+1):unit(rows[f'unit-{i}.toml'],i,schedule,'red' if phase=='red300' else 'green')
 return True
