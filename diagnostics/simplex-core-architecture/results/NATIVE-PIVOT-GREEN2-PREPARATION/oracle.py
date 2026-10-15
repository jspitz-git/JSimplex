"""Saved-data-only exact oracle. No Julia and no old auditor import."""
from control import *
from exact import residual,number,token,validate_controls,validate_info,validate_timing,stats
import math,statistics

def test_results(raw,phase):
 require(raw['complete'] is True and raw['fatal']=='','Incomplete test execution')
 root=raw['tests'];groups=root['children'];require(root['pass']==root['fail']==root['error']==root['broken']==0,'Root tests')
 require(raw['threads']==raw['blas_threads']==1,'Threads')
 require(phase=='green2' and raw['phase']==phase,'GREEN-2 phase')
 regression=regression_results(raw)
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
 return dict(regression=regression,assertions=budget['green_assertions'],entry_counts=total,equations=result,scope='Selected PRE-forward call entries include rejections/throws; internal factorization/reconstruction/Markowitz/HH work is additional, not a native-operation ledger.')

def regression_results(raw):
 require(raw['phase']=='green2','Regression phase')
 root=raw['regression_tests'];groups=root['children']
 require(root['name']=='regression' and root['pass']==root['fail']==root['error']==root['broken']==0 and root['failures']==[],'Regression root')
 require(len(groups)==1,'Regression group count');g=groups[0]
 require(g['name']=='Dense diagnostic tokens preserve sparse inputs' and g['pass']==119 and g['fail']==g['error']==g['broken']==0 and g['failures']==[] and g['children']==[],'All 119 regression assertions')
 require(raw['regression_helper_calls']==16,'Regression helper budget')
 require(raw['regression_counts_before']==raw['regression_counts_after']=={},'Regression selected production calls')
 return dict(assertions=119,helper_calls=16,selected_production_calls=0,scope='Separate cold regression work; no runtime/native-internal zero-work claim')
