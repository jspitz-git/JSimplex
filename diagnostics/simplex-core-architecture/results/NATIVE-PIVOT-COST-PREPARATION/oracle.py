"""Saved-data-only exact oracle. No Julia and no old auditor import."""
from control import *
from exact import residual,number,token,validate_controls,validate_info,validate_timing,stats
import math,statistics

def test_results(raw,phase):
 require(raw['complete'] is True and raw['fatal']=='','Incomplete test execution')
 root=raw['tests'];groups=root['children'];require(root['pass']==root['fail']==root['error']==root['broken']==0,'Root tests')
 require(raw['threads']==raw['blas_threads']==1,'Threads')
 if phase=='red':
  require(len(groups)==1,'RED group');g=groups[0]
  require(g['name']=='Missing native pivot policy contract' and g['pass']==g['error']==g['broken']==0 and g['fail']==4 and g['children']==[],'Expected RED failures only')
  names=['native_pivot_policy','_NativePivotPolicy','pivot_policy','_native_lu']
  require(len(g['failures'])==4 and all(n in msg for n,msg in zip(names,g['failures'])),'Exact named missing markers')
  require(raw['counts']=={} and raw['events']==[] and raw['equations']==[],'RED selected body work')
  return dict(expected_failure=True,selected_body_native_entries=0,scope='Import is additional work; no native hook trace')
 budget=rd(D/'budget.json');expected=budget['test_groups']
 require([g['name'] for g in groups]==list(expected),'Exact selected test groups/order')
 for g in groups:
  require(g['pass']==expected[g['name']] and g['fail']==g['error']==g['broken']==0 and not g['children'] and g['failures']==[],'Assertions '+g['name'])
 require(sum(g['pass'] for g in groups)==budget['green_assertions'],'Total assertions')
 require(raw['main_counts']==budget['main'],'Main work')
 total={k:budget['main'].get(k,0)+budget['neighbors'].get(k,0) for k in set(budget['main'])|set(budget['neighbors'])}
 require(raw['counts']==total,'Whole selected entry budget')
 events=raw['events'];require(len(events)==sum(total.values())<=raw['observation_limit']==2048,'Observation count')
 observed={}
 for e in events:
  k=e['call'];observed[k]=observed.get(k,0)+1;require(e['number']==observed[k] and isinstance(e['exception'],str),'Call sequence')
  require(('after_failure' in e)==bool(e['exception']),'Failure state')
  for key in ['before','after','after_failure']:
   z=e.get(key,{})
   if z.get('kind')=='UMFPACKBackend':
    require(z['policy'] in ['_NATIVE_PIVOT_DEFAULT','_NATIVE_PIVOT_ONE'],'State policy')
    if z['active']!='none':
     require(len(z['control'])==20,'State control shape')
     # Exact full controls are also checked by preserved Task1 controls tests.
     require(z['control'][3]==token(1. if z['policy']=='_NATIVE_PIVOT_ONE' else .1) and z['control'][7]==token(0.),'State selection')
 require(observed==total,'Observed budget')
 equations=raw['equations'];require(len(equations)==324,'All helper output equations')
 result=[]
 for e in equations:
  if e['matrix']['n']==0:
   require(e['matrix']==dict(n=0,colptr=[1],rowval=[],nzval=[]) and e['rhs']==e['output']==[],'Empty equation');continue
  r=residual(e['matrix'],e['output'],e['rhs'],e['transposed']);require(r['passed'],'Exact helper residual');result.append(r)
 return dict(assertions=budget['green_assertions'],entry_counts=total,equations=result,scope='Selected PRE-forward call entries include rejections/throws; internal factorization/reconstruction/Markowitz/HH work is additional, not a native-operation ledger.')

def cost_results(raw,windows):
 require(raw['complete'] is True and raw['fatal']=='' and raw['inputs_unchanged'] is True,'Completion/inputs')
 require(raw['threads']==raw['blas_threads']==1,'Threads')
 require(raw['windows']==len(windows)==88 and raw['counts']==dict(construction=88,refactor=176,forward=2816,transpose=1408),'Cost budget')
 require(raw['output_payload_bytes']==2162688 and raw['info_payload_bytes']==135168 and raw['diagnostic_graph_bytes']>=2297856,'Diagnostic storage')
 inputs=rd(D/'inputs.json');fs={f['name']:f for f in inputs['fixtures']};base=raw['default_control'];saved=rd(D/'saved-C.json')
 cost={};accuracy={'C':True,'P':True};res=[];matches=[];snapshots={};strategies={};cache={}
 for spec,w in zip(inputs['schedule'],windows):
  require(w['schedule']==spec,'Schedule');arm=spec['arm'];name=spec['fixture'];f=fs[name];n=f['matrix']['n']
  require(w['no_spare'] is True and w['fresh'] is True and w['reused'] is True,'Lifecycle')
  ids=w['owners'];require(len(ids)==6 and ids[0]==ids[3] and ids[1]==ids[4] and ids[2]==ids[5] and ids[0]!=ids[1],'Owner sequence')
  require(w['policy']==('_NATIVE_PIVOT_DEFAULT' if arm=='C' else '_NATIVE_PIVOT_ONE'),'Policy')
  validate_controls(arm,w['control'],base);validate_controls(arm,w['spare_control'],base)
  require(w['Wi']==w['W']==n and len(w['info'])==90,'Workspace/info')
  strategy=number(w['info'][18]);require(strategy in (1,3),'Actual strategy');strategies.setdefault(name+':'+arm,set()).add(strategy)
  require(len(w['outputs'])==len(w['solve_info'])==48,'Outputs')
  for k,(x,info) in enumerate(zip(w['outputs'],w['solve_info'])):
   rhs=('a','dse','unit')[k%3];key=(name,rhs,tuple(x))
   if key not in cache:cache[key]=residual(f['matrix'],x,f['rhs'][rhs],rhs=='unit')
   r=cache[key];accuracy[arm]&=r['passed'];res.append(dict(window=spec['id'],solve=k+1,**r));validate_info(arm,info)
  if arm=='C':matches.append(dict(window=spec['id'],fixture=name,matches_all_saved=all(w['outputs']==r['outputs'] for r in saved[name]),saved_hashes=[r['sha256'] for r in saved[name]]))
  for region in ['construction','refactor_fresh','refactor_spare','solve','total']:
   v=w[region];validate_timing(v)
   if not spec['warm']:
    require(v['compile_time']==v['recompile_time']==0,'Measured compilation')
    cost.setdefault((name,region,arm),{})[spec['round']]=v
  if spec['round']==11:
   m=w['factor'];require(m['m']==m['n']==m['nzd']==n and n<=m['lnz']<=n*(n+1)//2 and n<=m['unz']<=n*(n+1)//2 and m['graph_bytes']>0 and m['spare_W']==m['spare_Wi']==n,'Fill/memory')
   snapshots[name+':'+arm]=dict(**m,info=w['info'],control=w['control'],strategy=strategy)
  else:require('factor' not in w,'Unexpected snapshot')
 require(len(res)==4224 and len(snapshots)==8 and accuracy['P'],'Threshold-one residuals')
 comparisons={}
 for name in fs:
  for region in ['construction','refactor_fresh','refactor_spare','solve','total']:
   C=cost[name,region,'C'];P=cost[name,region,'P'];require(set(C)==set(P)==set(range(4,12)),'Eight matched samples')
   ratios=[P[r]['seconds']/C[r]['seconds'] for r in range(4,12)] if all(C[r]['seconds']>0 for r in range(4,12)) else None
   comparisons[name+':'+region]=dict(C=C,P=P,ratios=ratios,summary=stats(ratios) if ratios else None)
 return dict(accuracy=accuracy,residuals=res,paired_cost=comparisons,factors=snapshots,strategies={k:sorted(v) for k,v in strategies.items()},saved_C_comparison=matches,unexplained_C_mismatch=any(not m['matches_all_saved'] for m in matches),limits='Total includes nested timers; never sum twice. Same-candidate policy tradeoff, not prior-binary overhead. GC aggregates may include native traffic; graph and Info are not live native allocation/free balance. A default mismatch requires explanation in result review; no retry.')
