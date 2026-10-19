"""Strict pure saved-payload validation. No Julia, I/O, process or release actions."""
import math,re
# Exact saved rendering of the frozen original test source and recorder.
# Any different expression/location/extra content fails closed; no byte count is prescribed.
RED_FAILURE_DETAIL='Test Failed at /home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS/panel-tests.jl:103\n  Expression: $(Expr(:escape, :(#= /home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS/panel-tests.jl:103 =# @allocated(K._bgb_eligibility(f, 1)) == 0)))'
PREPARATION=('load.toml','panel-load.toml','tests-load.toml','probe-setup.toml','probe-cost.toml','tests-cost.toml')
PAYLOAD=set(PREPARATION)|{'raw.toml','probe.toml','unit-1.toml'}
METRICS={'seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds'}
NAMES=['budget and cheap eligibility','independent arithmetic, policy and canonical zeros','packed commit, incidence, support and source counters','computed commit cap and independent work witnesses']
def need(v,m):
 if not v:raise ValueError(m)
def integer(v):return type(v) is int and 0<=v<=2**63-1
def metrics(v):
 need(type(v) is dict and set(v)==METRICS,'Metric fields')
 need(all(integer(v[k]) for k in ('bytes','events')),'Integral allocation counters')
 need(all(type(v[k]) in (int,float) and math.isfinite(v[k]) and 0<=v[k]<=300 for k in METRICS-{'bytes','events'}),'Finite bounded times')
 return v
def panel_counts(phase):
 need(phase in ('p011-red300','p011-green300'),'Phase')
 d={f'P{i:03d}':1 for i in range(1,95)}
 for i,n in [(1,5),(13,2),(15,4),(27,3),(66,2)]:d[f'P{i:03d}']=n
 for lo,hi,n in [(16,18,10),(19,20,5760),(21,26,10),(34,45,4),(62,64,3),(85,91,3)]:
  for i in range(lo,hi+1):d[f'P{i:03d}']=n
 if phase=='p011-green300':d.update({f'P{i:03d}':1 for i in range(95,103)})
 return d
def decision(d):
 expected=dict(start=1,count=0,accepted=False,reason='dimensions',finite=True,counters=[0]*20)
 need(type(d) is dict and set(d)==set(expected) and d==expected,'Complete decision')
 need(type(d['start']) is int and type(d['count']) is int and d['accepted'] is False and d['finite'] is True,'Decision types')
 need(type(d['counters']) is list and all(type(v) is int for v in d['counters']),'Counter types')
def probe(p):
 keys={'bytes','events','consumed_bytes','consumed_events','warm','bytes_decision','events_decision','values_unchanged','owners_unchanged'}
 need(type(p) is dict and set(p)==keys,'Probe fields')
 need(all(type(p[k]) is int and p[k]==0 for k in ('bytes','events','consumed_bytes','consumed_events')),'Four zero counters')
 need(p['values_unchanged'] is True and p['owners_unchanged'] is True,'Input preservation')
 for k in ('warm','bytes_decision','events_decision'):decision(p[k])
 return p

def unit(u,phase):
 need(type(u) is dict and set(u)=={'index','name','complete','fatal','tests','records'},'Unit fields')
 need(type(u['index']) is int and u['index']==1 and u['name']=='panel' and u['complete'] is True and u['fatal']=='','Unit completion')
 r=u['records'];need(type(r) is dict and set(r)=={'sites','events','apis','failures','failure_count','active'},'Record fields')
 expected=panel_counts(phase);need(type(r['sites']) is dict and r['sites']==expected and all(type(v) is int for v in r['sites'].values()),'Exact assertion sites')
 need(r['events']=={} and r['apis']=={} and r['active']=='','No extra work/active assertion')
 nf=1 if phase=='p011-red300' else 0
 failures=r['failures'];need(type(failures) is list and len(failures)==nf and type(r['failure_count']) is int and r['failure_count']==nf,'Failure count')
 for f in failures:need(type(f) is dict and set(f)=={'site','kind','detail'} and f['site']=='P011' and f['kind']=='fail' and type(f['detail']) is str and f['detail']==RED_FAILURE_DETAIL,'Only P011 expected failure')
 t=u['tests']
 def node(t,name):
  need(type(t) is dict and set(t)=={'name','pass','fail','error','broken','children'} and t['name']==name and type(t['children']) is list,'Tree schema/name')
  need(all(integer(t[k]) for k in ('pass','fail','error','broken')),'Tree counts')
 node(t,'panel');need(len(t['children'])==4 and all(t[k]==0 for k in ('pass','fail','error','broken')),'Four named children/root')
 ranges=[(1,15),(16,33),(34,65),(66,94)];total=[0,0,0,0]
 for index,(child,name,(lo,hi)) in enumerate(zip(t['children'],NAMES,ranges)):
  node(child,name);need(child['children']==[],'No hidden nested children')
  count=sum(expected[f'P{i:03d}'] for i in range(lo,hi+1))+(8 if index==0 and phase=='p011-green300' else 0)
  failed=nf if index==0 else 0;a=[child[k] for k in ('pass','fail','error','broken')]
  need(a==[count-failed,failed,0,0],'Exact child counts');total=[a+b for a,b in zip(total,a)]
 need(sum(total)==sum(expected.values()),'Total/site reconciliation')
 return total

def validate(payload,loaded,phase,test_source):
 need(type(payload) is dict and set(payload)==PAYLOAD,'Exact nine payload files')
 prep={name:metrics(payload[name]) for name in PREPARATION}
 p=probe(payload['probe.toml']);totals=unit(payload['unit-1.toml'],phase)
 raw=payload['raw.toml'];keys={'schema','phase','complete','fatal','qualification','test_source','loaded','threads','blas_threads','probe','unit','totals'}
 need(type(raw) is dict and set(raw)==keys,'Raw fields')
 need(type(raw['schema']) is int and raw['schema']==1 and raw['phase']==phase and raw['complete'] is True and raw['fatal']=='','Raw completion')
 need(raw['qualification']=='p011_typed_structural' and raw['test_source']==test_source and type(raw['loaded']) is dict and raw['loaded']==loaded,'Source paths/scope')
 need(type(raw['threads']) is int and type(raw['blas_threads']) is int and raw['threads']==raw['blas_threads']==1,'Threads')
 probe(raw['probe']);unit(raw['unit'],phase)
 need(raw['probe']==p and raw['unit']==payload['unit-1.toml'],'Duplicated raw records')
 need(type(raw['totals']) is list and all(integer(v) for v in raw['totals']) and raw['totals']==totals,'Aggregate totals')
 return dict(totals=totals,preparation=prep,probe=p,expected_failure_sites=['P011'] if phase=='p011-red300' else [],
  scope='Structural P011 measurement qualification only, no lifecycle/streams or speedup; preparation records overlap load and probe/test costs include compilation')

def warning_log(log,payload,phase):
 # Remove exactly the one independently validated expected failure rendering.
 if phase=='p011-red300':
  detail=payload['unit-1.toml']['records']['failures'][0]['detail']
  if detail!=RED_FAILURE_DETAIL:return True
  # Check warning/error text before removing the exact expected Test rendering.
  if re.search(r'warning|world.?age|method.*overwrit|LoadError|ERROR:|OutOfMemoryError',log,re.I):return True
  token='TEST FAILURE: P011 '+detail
  if log.count(token)!=1:return True
  log=log.replace(token,'',1)
 return bool(re.search(r'warning|world.?age|method.*overwrit|LoadError|ERROR:|OutOfMemoryError|Test Failed|Test Error|TEST FAILURE',log,re.I))
