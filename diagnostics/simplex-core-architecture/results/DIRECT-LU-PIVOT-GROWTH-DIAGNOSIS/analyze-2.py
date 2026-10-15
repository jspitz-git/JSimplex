"""Exact arithmetic on saved data only. No solver, old auditor, or native calls."""
from pathlib import Path
from fractions import Fraction as Q
import hashlib,json,struct,tomllib
F=Path(__file__).resolve().parent;R=F.parents[3];D=F.parent/'DIRECT-LU-BACKEND-PREPARATION';E=F.parent/'DIRECT-LU-BACKEND-DIAGNOSTIC'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def q(t):return Q(struct.unpack('>d',bytes.fromhex(t))[0])
def sparse(n,ptr,ids,vals,csr=False):
 a=[{} for _ in range(n)]
 for c in range(n):
  for k in range(ptr[c]-1,ptr[c+1]-1):
   i,j=(c,ids[k]-1) if csr else (ids[k]-1,c);a[i][j]=q(vals[k])
 return a
def mv(a,x):return [sum((v*x[j] for j,v in row.items()),Q(0)) for row in a]
def maximum(a):return max((abs(v),i+1,j+1) for i,row in enumerate(a) for j,v in row.items())
inputs=F.parent/'DIRECT-LU-COST-PREPARATION/inputs.json';fixture=next(z for z in read(inputs)['fixtures'] if z['name']=='sparse96')
m=fixture['matrices'][4];n=m['n'];B=sparse(n,m['colptr'],m['rowval'],m['nzval'])
f=tomllib.loads((D/'probe-run/fresh.toml').read_text());g=tomllib.loads((D/'probe-run/prefix.toml').read_text());a=f['factor'];s=list(map(q,a['Rs']));p=[i-1 for i in a['p']];c=[i-1 for i in a['q']];inv={v:k for k,v in enumerate(c)}
if a['do_recip']==0:s=[1/v for v in s]
L=sparse(n,a['L']['ptr'],a['L']['indices'],a['L']['values'],True);U=sparse(n,a['U']['ptr'],a['U']['indices'],a['U']['values'])
M=[{inv[j]:s[i]*v for j,v in B[i].items()} for i in p];P=[{} for _ in range(n)]
for i,row in enumerate(L):
 for k,v in row.items():
  for j,w in U[k].items():P[i][j]=P[i].get(j,Q(0))+v*w
err=[{j:P[i].get(j,Q(0))-M[i].get(j,Q(0)) for j in set(P[i])|set(M[i])} for i in range(n)]
rank=sorted(((abs(v),i,j,v) for i,row in enumerate(err) for j,v in row.items() if v),reverse=True)
x=list(map(q,f['outputs'][1]));y=[x[j] for j in c];b=list(map(q,fixture['steps'][4]['dse']));t=[s[i]*b[i] for i in p]
rep=mv(err,y);app=[v-w for v,w in zip(mv(P,y),t)];orig=[v-w for v,w in zip(mv(B,x),b)]
idx=30;col=30;terms=[dict(k=k+1,value=str(v*U[k].get(col,Q(0)))) for k,v in L[idx].items() if U[k].get(col,0)]
ux=mv(U,y);ledger=[]
for i in range(24,32):
 ledger.append(dict(row=i+1,original_row=p[i]+1,original_column=c[i]+1,L={str(j+1):str(v) for j,v in L[i].items()},U={str(j+1):str(v) for j,v in U[i].items()},Ux=str(ux[i]),sum_abs_Ux_terms=str(sum((abs(v*y[j]) for j,v in U[i].items()),Q(0)))))
controls=list(map(q,a['control']));info=list(map(q,a['info']));ud=[abs(U[i][i]) for i in range(n)]
source=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src/solvers')
wrapper=(source/'wrappers.jl').read_text();header=F.parent/'S4-L/upstream-umfpack-v7.10.1.h';doc=header.read_text()
constants=dict(STRATEGY_USED=18,RCOND=67,UMIN=71,UMAX=72,PIVOT_TOLERANCE=3,DROPTOL=18,IRSTEP=7,STRATEGY_UNSYMMETRIC=1)
# Permute each original row so its unique largest entry is on the diagonal.
# Distinct columns prove this is a column permutation, preserving infinity norm.
dominant=[max(row,key=lambda j:abs(row[j])) for row in B];margin=min(2*max(map(abs,row.values()))-sum(map(abs,row.values())) for row in B);bnorm=max(sum(map(abs,row.values())) for row in B)
old=read(D/'probe-audit.json')['result'];res=next(z for z in old['residuals'] if z['name']=='fresh_dse');olddec=old['decomposition']['fresh']
checks=dict(dimension96=n==96,factors_identical_except_info=all(a[k]==g['factor'][k] for k in a if k!='info'),native_inputs_match=a['native_match'] and a['native_nzval']==m['nzval'] and a['native_colptr']==[i-1 for i in m['colptr']] and a['native_rowval']==[i-1 for i in m['rowval']],multiply_scale=a['do_recip']==1,
 triangular=all(L[i].get(i)==1 and all(j<=i for j in L[i]) and U[i].get(i,0)!=0 and all(j>=i for j in U[i]) for i in range(n)),
 permutation_dominance=len(set(dominant))==n and margin==Q(103,32) and bnorm==Q(153,32),
 installed_constant_mapping=all(f'const UMFPACK_{k} = {v}' in wrapper for k,v in constants.items()),
 documented_threshold='Default: 0.1.' in doc and 'Larger values can lead' in doc,
 actual_unsymmetric=info[18]==1,actual_controls=controls[3]==Q(float(.1)) and controls[7]==0 and controls[18]==0,
 info_diagonal_extrema=info[71]==min(ud) and info[72]==max(ud),info_rcond_rounded_ratio=float(info[67])==float(min(ud)/max(ud)),
 max_U_at31=maximum(U)[1:]==(31,31),largest_factor_error_at31=rank[0][1:3]==(30,30),zero_target=M[idx].get(col,0)==0 and B[86].get(0,0)==0,
 three_term_cancellation=len(terms)==3 and sum(Q(z['value']) for z in terms)==err[idx][col],
 exact_saved_decomposition=[str(v) for v in rep]==olddec['representation_action'] and [str(v) for v in app]==olddec['combined_application'],
 exact_original_vector=[str(v) for v in orig]==res['residual'],
 row87_identity=orig[86]==(app[idx]-rep[idx])/s[86],
 unchanged_failure=old['failed_residuals']==['fresh_dse','tail_dse','base_dse'] and res['passed'] is False)
result=dict(max_L=str(maximum(L)[0]),max_U=str(maximum(U)[0]),max_B=str(maximum(B)[0]),max_scaled_B=str(maximum(M)[0]),growth_scaled=str(maximum(U)[0]/maximum(M)[0]),growth_unscaled=str(maximum(U)[0]/maximum(B)[0]),condition_inf_upper=str(bnorm/margin),rcond_info=str(info[67]),udiag_ratio=str(min(ud)/max(ud)),factor_error_nonzeros=len(rank),top_factor_errors=[dict(row=i+1,col=j+1,original_row=p[i]+1,original_col=c[j]+1,value=str(v)) for _,i,j,v in rank[:12]],row31_col31_terms=terms,row31_col31_sum=str(err[idx][col]),row31_col31_sum_abs=str(sum(abs(Q(z['value'])) for z in terms)),rows25through32=ledger,row87=dict(residual=str(orig[86]),bound=res['bound'],ratio=res['ratio'],representation=str(rep[idx]/s[86]),combined_application=str(app[idx]/s[86])),scope='Exact algebra of saved factors/outputs; growth and cancellation demonstrated, not a native operation trace, pivot-decision capture, new solve or repair qualification')
paths=[Path(__file__),inputs,D/'probe-run/fresh.toml',D/'probe-run/prefix.toml',D/'probe-audit.json',E/'interpretation.json',header,F.parent/'S4-L/upstream-umfpack-v7.10.1.provenance.json',source/'wrappers.jl',source/'umfpack.jl',R/'src/factorization.jl']
# No retroactive launch pins: these are fresh read-time bindings only.
out=dict(all_passed=all(checks.values()),checks=checks,result=result,sha256={str(p):sha(p) for p in paths})
with (F/'analysis.json').open('x') as h:json.dump(out,h,indent=2);h.write('\n')
print(json.dumps(dict(checks=checks,result={k:v for k,v in result.items() if k not in ('rows25through32','top_factor_errors')}),indent=2))
if not out['all_passed']:raise SystemExit('Preserve failed analysis')
