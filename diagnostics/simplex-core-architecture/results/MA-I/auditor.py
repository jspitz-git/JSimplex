"""Pure fail-closed raw validation. No process launch, no old script execution."""
import json,math,tomllib
from pathlib import Path
from fractions import Fraction as Q
from finite_oracle import upper
D=Path(__file__).resolve().parent
COUNTS=json.loads((D/'test-counts.json').read_text())
FIX=tomllib.loads((D/'fixtures.toml').read_text())
def require(v,m):
 if not v:raise ValueError(m)
def finite(x):return type(x) in (int,float) and math.isfinite(x) and x>=0
def bits(label):return int(label[8:]) if label.startswith('BigFloat') else {'Float32':24,'Float64':53,'RationalBigInt':None}[label]
def value(v):return Q(v['value'].replace('//','/'))
def vector(v,n,label):
 require(type(v) is list and len(v)==n,'vector length')
 for x in v:
  require(set(x)=={'value','sign','precision'} and type(x['sign']) is bool and type(x['precision']) is int,'scalar schema')
  q=value(x);require(x['precision']==(bits(label) if label.startswith('BigFloat') else 0),'precision')
  require(not q or x['sign']==(q<0),'sign')
 return list(map(value,v))
def residual(f,x,label):
 A=[[Q(v) for v in row] for row in f['matrix']];b=list(map(Q,f['rhs']));n=f['n']
 r=max(abs(sum(A[i][j]*x[j] for j in range(n))-b[i]) for i in range(n))
 scale=max(Q(1),max(sum(map(abs,row)) for row in A)*max(map(abs,x)),max(map(abs,b)))
 p=bits(label);bound=Q(0) if p is None else 64*Q(1,2**(p-1))*scale
 require(r<=bound,'exact residual')
def metric(x,steady=False):
 require(set(x)=={'seconds','bytes','allocations','gc_seconds','compile_seconds','recompile_seconds'},'metric schema')
 require(all(finite(v) for v in x.values()),'metric finite')
 require(type(x['bytes']) is int and type(x['allocations']) is int,'metric counts')
 if steady:require(x['compile_seconds']==x['recompile_seconds']==0,'steady compilation')
def validate(raw,stage,side):
 require(raw['stage']==stage and raw['side']==side,'stage/side')
 require(raw['errors']==[] and raw['ambient_ok'] is True,'driver error/ambient')
 require(Path(raw['source']).resolve()==(D/'overlays'/side/'src/JSimplex.jl').resolve(),'loaded root')
 require(raw['version']=='1.13.0','runtime version')
 require(finite(raw['body_seconds']),'body time')
 if stage in ('red','qualification'):
  require(raw['context_restored'] is True,'test context restoration')
  if stage=='qualification':require(raw['route_entries']==dict(constructors=28,copies=28,reference=28,candidate=28,throws=6,successes=50),'route entries/outcomes')
  else:require('route_entries' not in raw,'RED must not run route tests')
  tree=raw['tests'];require(tree['name']=='MA-E' and tree['counts']==[0,0,0,0] and tree['nonpasses']==[],'outer tests')
  children=tree['children'];wanted=['MA upper dispatch and fallback'] if stage=='red' else list(COUNTS)
  require([c['name'] for c in children]==wanted,'testset entries/order')
  for c in children:
   require(c['children']==[],'unexpected child')
   expected=[0,2,0,0] if stage=='red' else [COUNTS[c['name']],0,0,0]
   require(c['counts']==expected,'assertion counts')
   if stage=='red':
    require(len(c['nonpasses'])==2 and all(p['kind']==2 for p in c['nonpasses']),'RED failures')
    require([p['expression'] for p in c['nonpasses']]==['isdefined(J, :_markowitz_upper_solve!)','isdefined(J, :_markowitz_ma_scratch)'],'RED exact expressions')
   else:require(c['nonpasses']==[],'qualification nonpass')
  require(raw['counts']==([0,2,0,0] if stage=='red' else [sum(COUNTS.values()),0,0,0]),'aggregate counts')
 if stage in ('red','qualification'):
  require(len(raw['compare_metrics'])==(0 if stage=='red' else 77) and len(raw['full_metrics'])==(0 if stage=='red' else 30),'instrumented call counts')
  for pair in raw['compare_metrics']:
   metric(pair['reference']);metric(pair['candidate'])
  for m in raw['full_metrics']:metric(m)
 if stage=='red':require(raw['records']==[],'RED work');return True
 expected=[(f,l) for f in FIX['fixtures'] for l in FIX['scalar_cases']]
 require(len(raw['records'])==len(expected),'48 entries')
 for r,(f,l) in zip(raw['records'],expected):
  require((r['name'],r['scalar'])==(f['name'],l),'case order')
  n=f['n'];m=r['metadata'];s=n-2 if f['family']=='star' else 0;k=n-1 if s else 0;e=int(bool(s) and l not in ('Float32','Float64'))
  require((m['S'],m['K'],m['E'])==(s,k,e),'constructor topology')
  require(sorted(m['rows'])==sorted(m['columns'])==list(range(1,n+1)),'permutations')
  require(len(m['upper_indices'])==len(m['upper_values'])==s and sum(map(len,m['upper_indices']))==k,'upper shape')
  require(len(m['diagonal'])==s,'diagonal shape')
  for inds,vals in zip(m['upper_indices'],m['upper_values']):
   require(all(type(i)is int and 1<=i<=n for i in inds),'upper index');vector(vals,len(inds),l)
  vector(m['diagonal'],s,l)
  rows=[[(i-1,value(v)) for i,v in zip(inds,vals)] for inds,vals in zip(m['upper_indices'],m['upper_values'])]
  diag=list(map(value,m['diagonal']))
  if stage=='qualification':
   prefix=vector(r['prefix'],n,l);out,trace=upper(prefix,rows,diag,s,bits(l))
   expected_out=[Q(0)]*n
   for i,col in enumerate(m['columns']):expected_out[col-1]=out[i]
   require(expected_out==list(map(value,r['actual'])),'offline sequential parity')
   require([(t['pivot']-1,value(t['value'][0])) for t in r['trace']]==trace,'offline row trace')
   require(r['seed_ok'] is True and r['expected']==r['actual'],'prefix/reference parity')
   residual(f,vector(r['actual'],n,l),l)
   require([t['pivot'] for t in r['trace']]==list(range(s,0,-1)),'row trace')
  else:
   for key in ('full_first','full_last','upper_first','upper_last','rhs','seed'):vector(r[key],n,l)
   require(r['full_first']==r['full_last'] and r['upper_first']==r['upper_last'],'repeat parity')
   require(r['rhs_preserved'] is True and r['retained_ok'] is True,'ownership')
   require(list(map(value,r['rhs']))==list(map(Q,f['rhs'])),'rhs values')
   residual(f,list(map(value,r['full_last'])),l)
   expected_seed=[Q(1)]*n
   for i in range(s):expected_seed[i]=Q(f['rhs'][m['rows'][i]-1])
   require(list(map(value,r['seed']))==expected_seed,'frozen preupper seed')
   expected_upper,_=upper(expected_seed,rows,diag,s,bits(l))
   require(list(map(value,r['upper_last']))==expected_upper,'offline upper sequential')
   for key in ('construction','first_full','steady_full','first_upper','steady_upper'):metric(r[key],key.startswith('steady'))
   target=l not in ('Float32','Float64');require(r['scratch_present'] is target,'scratch scope')
   if target:metric(r['scratch']);require(type(r['scratch_graph_bytes']) is int and r['scratch_graph_bytes']>=0,'scratch graph')
   require(type(r['backend_graph_bytes']) is int and r['backend_graph_bytes']>=0,'backend graph')
 return True

def paired(a,b):
 require(a['side']=='reference' and b['side']=='candidate','pair side')
 validate(a,'cost','reference');validate(b,'cost','candidate')
 for x,y in zip(a['records'],b['records']):
  for k in ('name','scalar','metadata','rhs','seed','full_first','full_last','upper_first','upper_last'):require(x[k]==y[k],'paired '+k)
 return True


def complete_grid(pairs):
 require(set(pairs)==set(range(1,11)), 'incomplete pair grid')
 for pair in range(1,11):
  require(set(pairs[pair])=={'reference','candidate'}, 'incomplete side grid')
  paired(pairs[pair]['reference'],pairs[pair]['candidate'])
 return True
