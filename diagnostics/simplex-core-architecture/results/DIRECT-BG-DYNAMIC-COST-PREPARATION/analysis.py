"""Pure offline exact residual and paired-cost predicates; no Julia calls."""
import math,struct,statistics
from fractions import Fraction as Q

def require(ok,message):
 if not ok:raise ValueError(message)
def number(s):
 require(isinstance(s,str) and len(s)==16 and all(c in '0123456789abcdef' for c in s),'Malformed Float64 token')
 x=struct.unpack('>d',bytes.fromhex(s))[0];require(math.isfinite(x),'Nonfinite Float64 token');return x

def scaled(tokens):
 pairs=[number(s).as_integer_ratio() for s in tokens];e=max((d.bit_length()-1 for _,d in pairs),default=0)
 return [n << (e-(d.bit_length()-1)) for n,d in pairs],e

def matrix(m,transpose=False):
 n=m['n'];v,e=scaled(m['nzval']);rows=[[] for _ in range(n)]
 require(len(m['colptr'])==n+1 and m['colptr'][0]==1 and m['colptr'][-1]==len(v)+1 and len(v)==len(m['rowval']),'CSC shape')
 for j in range(n):
  inds=m['rowval'][m['colptr'][j]-1:m['colptr'][j+1]-1]
  require(inds==sorted(set(inds)) and all(1<=i<=n for i in inds),'CSC rows')
  for k in range(m['colptr'][j]-1,m['colptr'][j+1]-1):
   i=m['rowval'][k]-1;row,col=(j,i) if transpose else (i,j);rows[row].append((col,v[k]))
 return rows,e,max((sum(abs(v) for _,v in row) for row in rows),default=0)

def residual(M,tokens,rhs):
 rows,em,nm=M;x,ex=scaled(tokens);b,eb=scaled(rhs);n=len(rows)
 require(len(x)==len(b)==n,'Solution dimensions')
 e=max(em+ex,eb);r=max((abs((sum(v*x[j] for j,v in row) << (e-em-ex))-(b[i] << (e-eb))) for i,row in enumerate(rows)),default=0)
 nx=max(map(abs,x),default=0);nb=max(map(abs,b),default=0)
 bound=Q(128*n,2**52)*max(Q(1),Q(nm*nx,2**(em+ex)),Q(nb,2**eb))
 return Q(r,2**e)<=bound

def schedule(process,pair):return ['reference','candidate'] if ((pair%2==1) != (process==2)) else ['candidate','reference']
def finite_nonnegative(v):return type(v) in (float,int) and math.isfinite(v) and v>=0

def window_ok(row,f,process,pair,order,matrices):
 require(set(row)==set('pair order side measured policy correct inputs_unchanged modes seconds bytes events gc_seconds compile_seconds recompile_seconds retained_bytes nested_seconds outputs'.split()),'Exact window schema')
 require(type(row['pair']) is int and type(row['order']) is int and type(row['measured']) is bool,'Schedule types')
 side=schedule(process,pair)[order-1]
 require(row['pair']==pair and row['order']==order and row['side']==side and row['measured']==(pair>3),'Window schedule')
 require(row['correct'] is True and row['inputs_unchanged'] is True,'Raw correctness false')
 require(len(row['modes'])==3 and all(m in ('normalized','direct','fallback') for m in row['modes']),'Mode drift')
 require(all(finite_nonnegative(row[k]) for k in ('seconds','bytes','events','gc_seconds','compile_seconds','recompile_seconds','retained_bytes')),'Invalid metrics')
 require(row['seconds']>0 and all(type(row[k]) is int for k in ('bytes','events','retained_bytes')),'Metric types')
 require(len(row['nested_seconds'])==6 and all(finite_nonnegative(x) for x in row['nested_seconds']),'Nested metrics')
 require(sum(row['nested_seconds'])<=row['seconds']+1e-9,'Nested timers exceed total')
 require(pair<=3 or (row['compile_seconds']==0 and row['recompile_seconds']==0),'Measured compilation')
 require(len(row['outputs'])==24,'Output count')
 for k,s in enumerate(f['steps']):
  require(residual(matrices[k][0],row['outputs'][3*k],s['a']),'Entering residual')
  require(residual(matrices[k][0],row['outputs'][3*k+1],s['dse']),'DSE residual')
  require(residual(matrices[k+1][1],row['outputs'][3*k+2],s['unit']),'BTRAN residual')
 return True

def stats(values):
 m=statistics.median(values)
 return dict(median=m,mad=statistics.median(abs(x-m) for x in values),minimum=min(values),maximum=max(values),values=values)
def summarize(rows):
 pairs=[]
 for p in range(4,11):
  d={r['side']:r for r in rows if r['pair']==p};require(set(d)=={'reference','candidate'},'Incomplete pair');pairs.append(d)
 result={}
 for metric in ('seconds','bytes','events','retained_bytes','gc_seconds','compile_seconds','recompile_seconds'):
  a=[p['reference'][metric] for p in pairs];b=[p['candidate'][metric] for p in pairs]
  result[metric]=dict(reference=stats(a),candidate=stats(b))
  if all(a):result[metric]['paired_ratio']=stats([y/x for x,y in zip(a,b)])
 result['nested_seconds']=[dict(reference=stats([p['reference']['nested_seconds'][i] for p in pairs]),candidate=stats([p['candidate']['nested_seconds'][i] for p in pairs])) for i in range(6)]
 result['faster_pairs']=sum(p['candidate']['seconds']<p['reference']['seconds'] for p in pairs)
 result['time_median_gate']=result['seconds']['paired_ratio']['median']<=.95
 result['allocation_gate']=all(result[k]['candidate']['median']<=result[k]['reference']['median'] for k in ('bytes','events'))
 # Conservative fixed interpretation: EVERY measured memory pair <=+10%,
 # not a median hiding an occasional retained-capacity increase.
 result['memory_gate']=all(10*p['candidate']['retained_bytes']<=11*p['reference']['retained_bytes'] for p in pairs)
 return result

def qualify(a,b):
 return all(x['time_median_gate'] and x['allocation_gate'] and x['memory_gate'] for x in (a,b)) and a['faster_pairs']+b['faster_pairs']>=10
