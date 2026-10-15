"""Exact offline diagnostic predicates. No numerical execution or result-fitting."""
import math,struct,re
from fractions import Fraction as Q

def req(ok,message):
 if not ok:raise ValueError(message)
def keys(x,names):req(type(x) is dict and set(x)==set(names.split()),'Schema: '+names)
def token(s):req(type(s) is str and re.fullmatch('[0-9a-f]{16}',s) is not None,'Float64 token');return s
def q(s):
 x=struct.unpack('>d',bytes.fromhex(token(s)))[0];req(math.isfinite(x),'Nonfinite numeric value');return Q(x)
def vec(v,n):req(type(v) is list and len(v)==n,'Vector length');return list(map(q,v))
def indices(a,n):req(type(a) is list and all(type(x) is int and 1<=x<=n for x in a),'Index range')
def sparse(n,ptr,inds,vals,csr=False):
 req(type(n) is int and 0<n<=96,'Dimension')
 indices(inds,n);v=vec(vals,len(inds))
 req(type(ptr) is list and len(ptr)==n+1 and all(type(x) is int for x in ptr) and ptr[0]==1 and ptr[-1]==len(v)+1 and ptr==sorted(ptr),'Sparse pointers')
 M=[{} for _ in range(n)]
 for j in range(n):
  ids=inds[ptr[j]-1:ptr[j+1]-1];req(ids==sorted(set(ids)),'Unique sorted indices')
  for k in range(ptr[j]-1,ptr[j+1]-1):
   i=inds[k]-1;r,c=(j,i) if csr else (i,j);M[r][c]=v[k]
 return M
def matrix(m):return sparse(m['n'],m['colptr'],m['rowval'],m['nzval'])
def transpose(M):
 out=[{} for _ in M]
 for i,row in enumerate(M):
  for j,x in row.items():out[j][i]=x
 return out
def mv(M,x):return [sum((a*x[j] for j,a in row.items()),Q(0)) for row in M]
def norm(v):return max(map(abs,v),default=Q(0))
def residual(M,tokens,rhs):
 n=len(M);x=vec(tokens,n);b=vec(rhs,n);r=[a-z for a,z in zip(mv(M,x),b)]
 bound=Q(128*n,2**52)*max(Q(1),max(sum(map(abs,row.values()),Q(0)) for row in M)*norm(x),norm(b))
 return dict(passed=norm(r)<=bound,max_abs=str(norm(r)),bound=str(bound),ratio=float(norm(r)/bound),residual=[str(x) for x in r])
def control(c):
 keys(c,'tokens irstep_index irstep_zero');req(c['irstep_index']==8 and c['irstep_zero'] is True,'IRSTEP metadata')
 v=vec(c['tokens'],20);req(v[7]==0,'Native refinement changed');return c['tokens']
def factors(f,m):
 keys(f,'n lnz unz nzd status do_recip L U p q Rs control info native_owned native_match native_colptr native_rowval native_nzval')
 n=m['n'];req(f['n']==n and f['nzd']==n and f['status']==0,'Factor shape/status')
 for k,fmt in (('L','csr'),('U','csc')):
  z=f[k];keys(z,'format ptr indices values');req(z['format']==fmt,'Factor representation')
  size=f['lnz' if k=='L' else 'unz'];req(type(size) is int and n<=size<=n*(n+1)//2 and size==len(z['values']),'Factor fill')
 L=sparse(n,f['L']['ptr'],f['L']['indices'],f['L']['values'],True)
 U=sparse(n,f['U']['ptr'],f['U']['indices'],f['U']['values'])
 req(all(all(j<=i for j in row) and row.get(i)==1 for i,row in enumerate(L)),'Unit lower')
 req(all(all(j>=i for j in row) and row.get(i,0)!=0 for i,row in enumerate(U)),'Nonsingular upper')
 for name in ('p','q'):
  indices(f[name],n);req(sorted(f[name])==list(range(1,n+1)),'Permutation')
 req(type(f['do_recip']) is int and f['do_recip'] in (0,1),'Scaling orientation')
 rs=vec(f['Rs'],n);req(all(x>0 for x in rs),'Positive scaling');s=rs if f['do_recip']==1 else [1/x for x in rs]
 vec(f['control'],20);req(len(f['info'])==90,'Info size');[token(x) for x in f['info']]
 req(f['native_owned'] is True and f['native_match'] is True,'Native input ownership')
 req(f['native_colptr']==[x-1 for x in m['colptr']] and f['native_rowval']==[x-1 for x in m['rowval']] and f['native_nzval']==m['nzval'],'Native CSC values')
 product=[{} for _ in range(n)]
 for i,row in enumerate(L):
  for k,a in row.items():
   for j,b in U[k].items():product[i][j]=product[i].get(j,Q(0))+a*b
 M=matrix(m);p=[x-1 for x in f['p']];perm=[x-1 for x in f['q']];inv={j:k for k,j in enumerate(perm)}
 scaled=[{inv[j]:s[i]*a for j,a in M[i].items()} for i in p]
 E=[{j:product[i].get(j,Q(0))-scaled[i].get(j,Q(0)) for j in set(product[i])|set(scaled[i])} for i in range(n)]
 return product,scaled,E,p,perm,s
def decomposition(data,tokens,rhs):
 P,M,E,p,perm,s=data;n=len(M);x=vec(tokens,n);b=vec(rhs,n);y=[x[j] for j in perm];t=[s[i]*b[i] for i in p]
 rep=mv(E,y);app=[a-z for a,z in zip(mv(P,y),t)];original=[a-z for a,z in zip(mv(M,y),t)]
 req(original==[a-r for a,r in zip(app,rep)],'Exact decomposition identity')
 return dict(factor_identity_exact=all(a==0 for row in E for a in row.values()),factor_identity_max=str(max((abs(a) for row in E for a in row.values()),default=0)),representation_action=[str(x) for x in rep],combined_application=[str(x) for x in app],scaled_original=[str(x) for x in original],scope='Combined LU application consistency only; no captured intermediate triangular solve')
RESET='empty_history no_shared_updates identity_upper identity_columns identity_positions identity_row_order empty_operations zero_update_count not_permuted empty_active_upper upper_clean prepared_invalid no_sparse spare_present spare_is_original new_active'.split()
def analyze(raw,fresh,prefix,fixture,old,project):
 keys(raw,'completed fatal loaded_path counts inputs_unchanged')
 req(raw['completed'] is True and raw['inputs_unchanged'] is True and raw['fatal']=='' and raw['loaded_path']==project+'/src/JSimplex.jl','Raw completion/source')
 req(raw['counts']==dict(factorization=3,ftran=13,btran=5,replace=4,refactor=1,snapshot=2),'Explicit budget')
 keys(fresh,'controls_before controls_after outputs factor')
 keys(prefix,'controls_before controls_after_refactor controls_after reset prefix_outputs tail_outputs ordinary_before_base factor fresh_context_retained')
 req(set(prefix['reset'])==set(RESET) and all(x is True for x in prefix['reset'].values()) and prefix['fresh_context_retained'] is True,'Reset/retention')
 controls=[control(z[k]) for z,ks in ((fresh,['controls_before','controls_after']),(prefix,['controls_before','controls_after_refactor','controls_after'])) for k in ks]
 req(all(c==controls[0] for c in controls) and fresh['factor']['control']==prefix['factor']['control']==controls[0],'Control changes')
 req(len(fresh['outputs'])==3 and len(prefix['prefix_outputs'])==12 and len(prefix['tail_outputs'])==3,'Output count')
 req(prefix['ordinary_before_base']==prefix['tail_outputs'][:2],'Later call mutated ordinary output')
 M=[matrix(m) for m in fixture['matrices'][:5]];steps=fixture['steps'][:5];rows=[]
 def add(name,m,x,b):rows.append(dict(name=name,**residual(m,x,b)))
 s=steps[4]
 for name,x,b,m in zip(('fresh_enter','fresh_dse','fresh_btran'),fresh['outputs'],(s['a'],s['dse'],s['unit']),(M[4],M[4],transpose(M[4]))):add(name,m,x,b)
 for k,st in enumerate(steps[:4]):
  for j,(name,b,m) in enumerate((('enter',st['a'],M[k]),('dse',st['dse'],M[k]),('btran',st['unit'],transpose(M[k+1])))):add(f'prefix{k+1}_{name}',m,prefix['prefix_outputs'][3*k+j],b)
 for name,x,b in zip(('tail_enter','tail_dse','base_dse'),prefix['tail_outputs'],(s['a'],s['dse'],s['dse'])):add(name,M[4],x,b)
 a=factors(fresh['factor'],fixture['matrices'][4]);b=factors(prefix['factor'],fixture['matrices'][4])
 return dict(residuals=rows,failed_residuals=[r['name'] for r in rows if not r['passed']],
 comparisons=dict(prefix_dse_matches_original_failure=prefix['tail_outputs'][1]==old['outputs'][13],ordinary_equals_base=prefix['tail_outputs'][1]==prefix['tail_outputs'][2],fresh_equals_ordinary=fresh['outputs'][1]==prefix['tail_outputs'][1]),
 decomposition=dict(fresh=decomposition(a,fresh['outputs'][1],s['dse']),ordinary=decomposition(b,prefix['tail_outputs'][1],s['dse']),base=decomposition(b,prefix['tail_outputs'][2],s['dse'])),
 cost_qualified=False,scope='Diagnostic integrity; residual FALSE and nonreproduction are preserved outcomes, no retry or promotion')
