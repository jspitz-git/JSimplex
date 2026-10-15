"""Pure exact saved-data oracle. No Julia, subprocess, or numerical replay."""
from fractions import Fraction as Q
import struct,math,statistics as st
COUNTS=dict(fresh=141,refactor=9,copy=3,ftran=4245,btran=2133,snapshot=12)
def require(v,m):
 if not v:raise ValueError(m)
def integer(v):return type(v) is int
def number(t):
 require(type(t) is str and len(t)==16 and all(c in '0123456789abcdef' for c in t),'Binary64 token')
 x=struct.unpack('>d',bytes.fromhex(t))[0];require(math.isfinite(x),'Nonfinite value');return x
def exact(t):return Q(number(t))
def token(x):return struct.pack('>d',float(x)).hex()
def validate_info(arm,v):
 require(arm in ('C','P','R') and len(v)==4,'Info schema');s,t,a,f=map(number,v)
 require(s==0 and t.is_integer() and a.is_integer() and 0<=t<=a<=(2 if arm=='R' else 0) and f>=0,'Info status/refinement/work')
def validate_timing(v):
 require(set(v)=={'seconds','bytes','events','gctime','compile_time','recompile_time'},'Timing schema')
 for k,x in v.items():require(type(x) in (int,float) and math.isfinite(x) and x>=0 and (k not in ('bytes','events') or integer(x)),'Timing '+k)
def validate_counts(v):require(v==COUNTS and all(integer(x) for x in v.values()),'Whole call counts')
def validate_controls(arm,v,base):
 require(arm in ('C','P','R') and len(v)==len(base)==20,'Control schema')
 for x in v+base:number(x)
 require(base[3]==token(.1) and base[7]==token(0),'Reference defaults')
 expected=list(base);expected[3]=token(1 if arm=='P' else .1);expected[7]=token(2 if arm=='R' else 0)
 require(v==expected,'Control mutation')
def matrix(m,trans=False):
 n=m['n'];p=m['colptr'];r=m['rowval'];v=m['nzval']
 require(integer(n) and n>0 and len(p)==n+1 and p[0]==1 and p[-1]==len(v)+1 and len(r)==len(v),'CSC dimensions')
 require(all(integer(x) for x in p+r) and all(1<=x<=n for x in r) and all(a<=b for a,b in zip(p,p[1:])),'CSC indices')
 rows=[{} for _ in range(n)]
 for j in range(n):
  prev=0
  for k in range(p[j]-1,p[j+1]-1):
   i=r[k]-1;require(r[k]>prev,'CSC ordering');prev=r[k];a,b=(j,i) if trans else (i,j);rows[a][b]=exact(v[k])
 return rows
def residual(m,x,b,trans=False):
 rows=matrix(m,trans);n=len(rows);require(len(x)==len(b)==n,'RHS/output dimensions');x=list(map(exact,x));b=list(map(exact,b))
 e=max(abs(sum((v*x[j] for j,v in row.items()),Q(0))-b[i]) for i,row in enumerate(rows));norm=max(sum(map(abs,row.values()),Q(0)) for row in rows)
 bound=Q(128*n,2**52)*max(Q(1),norm*max(map(abs,x)),max(map(abs,b)))
 return dict(passed=e<=bound,max_residual=str(e),bound=str(bound),ratio=float(e/bound))
def state(v,arm,base,n):
 require(all(v[k] is True for k in ('native_owned','native_match','control_private','control_equal')),'Ownership/state')
 validate_controls(arm,v['control'],base);require(v['sym_pivot']==base[15],'Symmetric pivot changed')
 require(type(v['strategy']) in (int,float) and v['strategy'] in (1,3),'Captured strategy')
 require(integer(v['Wi']) and integer(v['W']) and v['Wi']==n and v['W']==n*(5 if arm=='R' else 1),'Workspace sizes')
def factor_report(v,m,arm,base):
 n=m['n'];require(v['n']==n and v['status']==0 and v['nzd']==n and v['do_recip'] in (0,1),'Factor metadata')
 validate_controls(arm,v['control'],base);require(len(v['info'])==90,'Native Info size')
 # Only documented post-solve-surviving factorization fields are interpreted.
 info={k:number(v['info'][i]) for k,i in {'strategy':18,'peak_units':41,'numeric_units':40,'factor_flops':42,'unit_bytes':3}.items()}
 require(info['strategy'] in (1,3) and all(x>=0 for x in info.values()),'Factor Info')
 require(integer(v['graph_bytes']) and v['graph_bytes']>0,'Reachable Julia graph')
 def sparse(w,fmt,count):
  require(w['format']==fmt and len(w['values'])==count and len(w['indices'])==count,'Factor format/fill')
  rows=matrix(dict(n=n,colptr=w['ptr'],rowval=w['indices'],nzval=w['values']),trans=fmt=='csr');return rows
 L=sparse(v['L'],'csr',v['lnz']);U=sparse(v['U'],'csc',v['unz'])
 require(all(j<=i for i,row in enumerate(L) for j in row) and all(j>=i for i,row in enumerate(U) for j in row),'Triangular factors')
 require(all(L[i].get(i)==1 and U[i].get(i,0)!=0 for i in range(n)),'Unit lower/nonsingular upper')
 require(sorted(v['p'])==sorted(v['q'])==list(range(1,n+1)) and all(integer(x) for x in v['p']+v['q']),'Permutations')
 rs=list(map(exact,v['Rs']));require(len(rs)==n and all(x>0 for x in rs),'Row scales')
 B=matrix(m);scaled=[{j:(a*rs[i] if v['do_recip'] else a/rs[i]) for j,a in row.items()} for i,row in enumerate(B)]
 maximum=max(abs(a) for row in scaled for a in row.values());umax=max(abs(a) for row in U for a in row.values());error=Q(0)
 for i,row in enumerate(L):
  product={}
  for k,a in row.items():
   for j,b in U[k].items():product[j]=product.get(j,Q(0))+a*b
  for j in range(n):error=max(error,abs(product.get(j,Q(0))-scaled[v['p'][i]-1].get(v['q'][j]-1,Q(0))))
 return dict(fill_L=v['lnz'],fill_U=v['unz'],graph_bytes=v['graph_bytes'],native_info=info,max_U=str(umax),max_scaled_B=str(maximum),growth=float(umax/maximum),factor_identity_residual=str(error),factor_identity_exact=error==0)
def stats(xs):
 med=st.median(xs);return dict(median=med,minimum=min(xs),maximum=max(xs),mad=st.median(abs(x-med) for x in xs))
def analyze(raw,lives,windows,data,old_dse):
 require(raw['completed'] is True and raw['inputs_unchanged'] is True and raw['fatal']=='','Completion/inputs')
 validate_counts(raw['counts']);require(raw['threads']==raw['blas_threads']==1 and raw['index_bits']==64,'Runtime shape')
 require(set(raw['stdlib_paths'])=={'SparseArrays','LinearAlgebra','TOML'},'Loaded stdlibs')
 fs={x['name']:x for x in data['fixtures']};base=lives['C']['initial']['control'];cache={};occurrences=[];bits={};metadata={a:dict(attempted=0,taken=0,flops=0) for a in 'CPR'};accuracy={a:True for a in 'CPR'}
 def check(label,arm,m,x,b,trans):
  key=(id(m),trans,tuple(b),tuple(x))
  if key not in cache:cache[key]=residual(m,x,b,trans)
  r=cache[key];accuracy[arm]&=r['passed'];occurrences.append(dict(label=label,arm=arm,**r))
 def meta(arm,vals):
  validate_info(arm,vals);_,t,a,f=map(number,vals);metadata[arm]['attempted']+=int(a);metadata[arm]['taken']+=int(t);metadata[arm]['flops']+=f
 for arm,v in lives.items():
  require(arm in 'CPR' and v['arm']==arm,'Lifecycle arm')
  require(all(v[k] is True for k in ('poisoned_private','copy_contract','independent_T','independent_V','preserved','singular')),'Lifecycle predicates')
  require(v['cause'] in ('SingularException','LinearAlgebra.SingularException') and v['status']==1,'Singular cause/status')
  require(len(v['outputs'])==len(v['info'])==14,'Lifecycle calls')
  for k in ('initial','first','second','fresh','finalF','finalS'):state(v[k],arm,base,32)
  for k,(x,inf) in enumerate(zip(v['outputs'],v['info'])):
   f=data['lifecycle'] if k<4 or k>=10 else fs['sparse32'];trans=k%2==1;rhs='unit' if trans else ('a' if k<4 or k>=10 else 'dse')
   check(f'life-{arm}-{k+1}',arm,f['matrix'],x,f['rhs'][rhs],trans);meta(arm,inf)
 require(set(lives)==set('CPR') and len(windows)==len(data['schedule'])==132,'Fixed membership')
 snapshots={};cost={};compile_zero=True;strategies={};reference_matches=[]
 for spec,v in zip(data['schedule'],windows):
  require(v['schedule']==spec,'Schedule identity');arm=spec['arm'];name=spec['fixture'];f=fs[name];n=f['matrix']['n']
  require(len(v['outputs'])==len(v['info'])==48,'Window calls')
  for k in ('before','after'):state(v[k],arm,base,n)
  require(v['before']==v['after'],'Policy/workspace/strategy changed during solves')
  strategies.setdefault(name+':'+arm,set()).add(v['before']['strategy'])
  for k,(x,inf) in enumerate(zip(v['outputs'],v['info'])):
   rhs=('a','dse','unit')[k%3];check(f'window-{spec["id"]}-{k+1}',arm,f['matrix'],x,f['rhs'][rhs],rhs=='unit');meta(arm,inf)
   bits.setdefault((name,arm,rhs),set()).add(tuple(x))
   if name=='sparse96' and arm=='C' and rhs=='dse':reference_matches.append(x==old_dse)
  for region in ('construction','solve'):
   timing=v[region];validate_timing(timing)
   if not spec['warm']:
    compile_zero &= timing['compile_time']==timing['recompile_time']==0
    cost.setdefault((name,arm,region),{})[spec['round']]=timing
  if spec['round']==11:snapshots[name+':'+arm]=factor_report(v['factor'],f['matrix'],arm,base)
  else:require('factor' not in v,'Unexpected snapshot')
 require(len(occurrences)==6378 and len(snapshots)==12,'Oracle/snapshot budget')
 comparison={}
 for name in fs:
  for region in ('construction','solve'):
   ref=cost[(name,'C',region)]
   for arm in 'CPR':
    samples=cost[(name,arm,region)];require(set(samples)==set(ref)==set(range(4,12)),'Measured rounds')
    fields={k:stats([samples[r][k] for r in range(4,12)]) for k in samples[4]}
    ratios={k:stats([samples[r][k]/ref[r][k] for r in range(4,12)]) if all(ref[r][k]>0 for r in range(4,12)) else None for k in ('seconds','bytes','events')}
    comparison[name+':'+arm+':'+region]=dict(samples=samples,summary=fields,paired_C_ratios=ratios)
 return dict(diagnostic_integrity=True,accuracy=accuracy,interpretable_cost=bool(compile_zero),remedy_eligible={a:accuracy[a] and compile_zero and all(len(v)==1 for k,v in bits.items() if k[1]==a) for a in 'PR'},residuals=occurrences,unique_exact_evaluations=len(cache),metadata=metadata,factors=snapshots,cost=comparison,strategies={k:sorted(v) for k,v in strategies.items()},within_arm_distinct_bits={':'.join(k):len(v) for k,v in bits.items()},C_saved_DSE_matches=reference_matches,extra_R_workspace_payload={str(n):32*n for n in (32,96)},limits='Component entries and native Info, not complete native work/free accounting. All GC and all samples retained; no solver or manager qualification.')
