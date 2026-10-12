from pathlib import Path
from fractions import Fraction as F
import struct,json,hashlib,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture';E=D/'results/S4-P';E.mkdir(exist_ok=False);(E/'host-before.json').write_bytes(Path('/tmp/s4-p-host.json').read_bytes())
def bits(x):
 y=float(x);assert F.from_float(y)==x
 return struct.pack('>d',y).hex()
n=48;cols=[3,17,31,31,17,3];zF=[F((-1)**i) for i in range(1,n+1)];zB=[F(i%3-1) for i in range(1,n+1)];fixtures=[];checks={};total=96
for kind in ['sparse','dense']:
 def entry(i,j):
  if i==j:return F(6)+F(i%5,32)
  if kind=='sparse':return F(1,64) if j==i+1 else F(-1,128) if i==j+1 else F(0)
  return F((i+2*j)%3+1,4096) if i<j else -F((2*i+j)%5+1,8192)
 base=[[entry(i,j) for j in range(1,n+1)] for i in range(1,n+1)];states=[];active=set();mats=[]
 for k in range(7):
  if k>0:
   if k<=3:active.add(cols[k-1])
   else:active.remove(cols[k-1])
  A=[row[:] for row in base]
  for j in active:A[j-1][j-1]+=F(1,8);A[j][j-1]+=F(1,256)
  vals=[];rows=[];ptr=[1]
  for j in range(n):
   for i in range(n):
    if A[i][j]:vals.append(A[i][j]);rows.append(i+1)
   ptr.append(len(vals)+1)
  bF=[sum((A[i][j]*zF[j] for j in range(n)),F(0)) for i in range(n)]
  bB=[sum((A[j][i]*zB[j] for j in range(n)),F(0)) for i in range(n)]
  margin=min(A[i][i]-sum((abs(A[i][j]) for j in range(n) if j!=i),F(0)) for i in range(n))
  assert margin>5 and any(A[i][j]!=A[j][i] for i in range(n) for j in range(n))
  s=dict(stage=k,active_columns=sorted(active),n=n,nnz=len(vals),colptr=ptr,rowval=rows,nzval_bits=[bits(x) for x in vals],rhsF_bits=[bits(x) for x in bF],rhsB_bits=[bits(x) for x in bB],row_dominance_margin=str(margin));states.append(s);mats.append(A);total+=len(vals)+2*n
 transitions=[]
 for k,j in enumerate(cols,1):
  old=mats[k-1];new=mats[k];a=[row[j-1] for row in new];delta=[new[i][j-1]-old[i][j-1] for i in range(n)]
  margin=F(states[k-1]['row_dominance_margin']);bound=F(1)-max(map(abs,delta))/margin
  assert bound>F(39,40)
  assert delta[j-2]==0 and old[j-2][j-1]!=0 and delta[j-1]!=0
  assert all(old[i][c]==new[i][c] for i in range(n) for c in range(n) if c!=j-1)
  transitions.append(dict(step=k,column=j,from_stage=k-1,to_stage=k,incoming_bits=[bits(x) for x in a],exact_pivot_lower_bound=str(bound),nonunit_reason='delta is nonzero but has zero row j-1 where old column is nonzero; therefore not proportional to old column'))
  total+=n
 assert mats[0]==mats[6];assert all(s['colptr']==states[0]['colptr'] and s['rowval']==states[0]['rowval'] for s in states)
 checks[kind+'_strict_dominance_all7']=True;checks[kind+'_nonsymmetric_all7']=True;checks[kind+'_six_nonunit_column_changes']=True;checks[kind+'_pivot_lower_gt39over40']=True;checks[kind+'_same_pattern_and_return']=True
 fixtures.append(dict(name=kind,states=states,transitions=transitions))
obj=dict(n=n,zF_bits=[bits(x) for x in zF],zB_bits=[bits(x) for x in zB],fixtures=fixtures,residual_oracle='exact norm_inf(M*z-b) <= 64*2^-52*max(1,norm_inf(M)*norm_inf(z),norm_inf(b)); M=B for forward/direction, transpose(B) for BTRAN; direction uses OLD basis and incoming column',coefficient_rhs_incoming_solution_entries=total)
(E/'exact-inputs.json').write_text(json.dumps(obj,indent=2)+'\n')
(E/'offline-input-checks.json').write_text(json.dumps(dict(checks=checks,all_passed=all(checks.values()),bit_roundtrips=total,exact_inputs_sha256=hashlib.sha256((E/'exact-inputs.json').read_bytes()).hexdigest(),scope='Exact rational construction/dominance proof only, zero factorization/Julia/native calls'),indent=2)+'\n')
print('checks',len(checks),'entries',total,'nnz',[(f['name'],f['states'][0]['nnz']) for f in fixtures]);print('margins',[f['states'][0]['row_dominance_margin'] for f in fixtures])
