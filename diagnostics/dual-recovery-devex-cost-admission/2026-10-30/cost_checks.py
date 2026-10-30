"""Pure typed cost/bit/work/paired acceptance; never numerical Julia work."""
import math,struct,statistics
KEYS=[(T,layout,bad) for T in ('Float32','Float64') for layout in ('sparse','dense') for bad in (False,True)]
def require(v,m):
 if not v:raise ValueError(m)
def integer(v):return type(v) is int and v>=0
def number(v):return type(v) in (int,float) and math.isfinite(v) and v>=0
def stats_ok(r,measured=False):
 require(type(r) is dict,'stats type')
 require(all(number(r[k]) for k in ('seconds','gc_seconds','compile_seconds','recompile_seconds')),'time type/range')
 require(integer(r['bytes']) and integer(r['events']),'allocation type/range')
 if measured:require(r['compile_seconds']==r['recompile_seconds']==0,'measured compilation')
def bits(v,T):return struct.pack('>f' if T=='Float32' else '>d',v).hex()
def expected_matrix(T,layout):
 return [bits(64.0 if i==j else ((-1 if (i+j)%2==0 else 1)*(1+(i+2*j)%5))/64 if layout=='dense' or abs(i-j)==1 else 0.0,T) for j in range(1,65) for i in range(1,65)]
def check_cost(r,side):
 require(type(r) is dict and r.get('side')==side and side in ('reference','candidate'),'cost side')
 require(type(r.get('cases')) is list and len(r['cases'])==8,'eight cases')
 for expected,q in zip(KEYS,r['cases']):
  require(type(q) is dict and type(q['type']) is str and type(q['layout']) is str and type(q['unreliable']) is bool,'case key types')
  key=(q['type'],q['layout'],q['unreliable']);require(key==expected,'exact case order/membership')
  T,layout,bad=key;require(type(q['dimension']) is int and q['dimension']==64,'dimension')
  matrix=expected_matrix(T,layout);zero=bits(0,T);rhs=matrix[0::64];point=[bits(.5 if bad else 1,T)]+[zero]*63
  require(q['matrix_bits']==matrix,'matrix bits')
  require(type(q['nnz']) is int and q['nnz']==(190 if layout=='sparse' else 4096),'nnz')
  require(q['policy_solve_tolerance_bits']==bits(2.**(-15 if T=='Float32' else -44),T),'policy tolerance bits256eps')
  require(type(q['warm']) is list and len(q['warm'])==3 and type(q['samples']) is list and len(q['samples'])==7,'three warm/seven measured')
  stats_ok(q['preparation']);stats_ok(q['post_warm_gc'])
  for w in q['warm']:stats_ok(w)
  require(type(q['solve_entries_total']) is int and type(q['stop_entries_total']) is int and q['solve_entries_total']==q['stop_entries_total']==(10 if bad else 0),'total whole-call work')
  require(integer(q['retained_julia_bytes']),'retained Julia type')
  for i,s in enumerate(q['samples'],1):
   stats_ok(s,True)
   require(type(s['index']) is int and s['index']==i,'sample index')
   require(s['finite'] is True and s['reliable'] is (not bad) and s['owners_preserved'] is True,'finite/reliable/owner booleans')
   require(s['point_bits']==point and s['rhs_bits']==rhs,'input/output bits')
   require(s['absolute_bits']==bits(32 if bad else 0,T) and s['relative_bits']==bits(1/3 if bad else 0,T),'quality error bits')
   require(type(s['solve_entries']) is int and type(s['stop_entries']) is int and s['solve_entries']==s['stop_entries']==int(bad),'sample solve/stop work')
 return True
def series(values):
 m=statistics.median(values)
 return dict(median=m,minimum=min(values),maximum=max(values),MAD=statistics.median(abs(v-m) for v in values),values=values)
def comparison_data(ref,can):
 check_cost(ref,'reference');check_cost(can,'candidate');cases=[];accepted=True
 for a,b in zip(ref['cases'],can['cases']):
  require((a['type'],a['layout'],a['unreliable'])==(b['type'],b['layout'],b['unreliable']),'paired key')
  require(all(a[k]==b[k] for k in ('matrix_bits','nnz','dimension','policy_solve_tolerance_bits')),'paired original inputs/policy')
  for x,y in zip(a['samples'],b['samples']):
   require(all(x[k]==y[k] for k in ('absolute_bits','relative_bits','point_bits','rhs_bits','finite','reliable','solve_entries','stop_entries','owners_preserved')),'paired output/work')
  rs={k:series([s[k] for s in a['samples']]) for k in ('seconds','bytes','events','gc_seconds')}
  cs={k:series([s[k] for s in b['samples']]) for k in ('seconds','bytes','events','gc_seconds')}
  require(rs['seconds']['median']>0,'zero reference median')
  gates=dict(bytes_nonincrease=cs['bytes']['median']<=rs['bytes']['median'],events_nonincrease=cs['events']['median']<=rs['events']['median'],retained_graph_nonincrease=b['retained_julia_bytes']<=a['retained_julia_bytes'])
  accepted=accepted and all(gates.values())
  cases.append(dict(type=a['type'],layout=a['layout'],unreliable=a['unreliable'],gates=gates,reference=rs,candidate=cs,median_time_ratio=cs['seconds']['median']/rs['seconds']['median'],reference_retained_julia_bytes=a['retained_julia_bytes'],candidate_retained_julia_bytes=b['retained_julia_bytes'],reference_preparation=a['preparation'],candidate_preparation=b['preparation'],reference_post_warm_gc=a['post_warm_gc'],candidate_post_warm_gc=b['post_warm_gc'],reference_warm=a['warm'],candidate_warm=b['warm']))
 return dict(accepted=accepted,cases=cases,scope='strict paired output/work and medianbytes/events/graph gates; no percent waiver',limitation='Separate processes, not temporal interleaving; no universal/end-to-end speedup or native-memory claim')
def compare_cost(ref,can):
 report=comparison_data(ref,can);require(report['accepted'],'systematic allocation/event/retained-graph increase');return report
