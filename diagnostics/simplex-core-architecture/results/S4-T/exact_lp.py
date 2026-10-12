from pathlib import Path
from fractions import Fraction as F
import json,struct,hashlib
E=Path('diagnostics/simplex-core-architecture/results/S4-T')
def dump(name,obj):
 with (E/name).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
def enc(x):
 if isinstance(x,F):return str(x)
 if isinstance(x,list):return [enc(v) for v in x]
 if isinstance(x,dict):return {k:enc(v) for k,v in x.items()}
 return x
def solve(B,b):
 d=B[0][0]*B[1][1]-B[0][1]*B[1][0];assert d
 return [(b[0]*B[1][1]-B[0][1]*b[1])/d,(B[0][0]*b[1]-b[0]*B[1][0])/d]
def dot(a,b):return sum((x*y for x,y in zip(a,b)),F(0))
A=[[F(1),F(1,4),F(1,2)],[F(1,4),F(1),F(1,2)]]
# Rectangular nonsymmetric LP: the leading square block happens to be symmetric;
# the reached final square basis is nonsymmetric.
c=[F(-4),F(-3),F(-7,2)];upper=[F(16)]*3+[F(2),F(3)];cost=c+[F(0)]*2
C=[A[0]+[F(-1),F(0)],A[1]+[F(0),F(-1)]]
basis=[3,4];x=[F(0)]*5;stages=[];steps=[]
for k in range(4):
 B=[[C[i][j] for j in basis] for i in range(2)]
 y=solve(list(map(list,zip(*B))),[cost[j] for j in basis])
 rc=[cost[j]-dot(y,[C[i][j] for i in range(2)]) for j in range(5)]
 rows=[];ptr=[1]
 for j in range(2):rows.extend(i+1 for i in range(2) if B[i][j]);ptr.append(len(rows)+1)
 stages.append(dict(basis=[j+1 for j in basis],x=x[:],B=B,dual=y,reduced_costs=rc,colptr=ptr,rowval=rows))
 improving=[]
 for j in range(5):
  if j in basis:continue
  assert x[j] in (0,upper[j])
  direction=1 if x[j]==0 else -1
  if rc[j]*direction<0:improving.append((abs(rc[j]),j,direction))
 if not improving:assert k==3;break
 improving.sort(reverse=True);assert len(improving)==1 or improving[0][0]>improving[1][0]
 _,j,direction=improving[0];d=solve(B,[C[i][j]*direction for i in range(2)])
 ratios=[(upper[j],-1)]
 for i,index in enumerate(basis):
  if d[i]>0:ratios.append((x[index]/d[i],i))
  elif d[i]<0:ratios.append(((upper[index]-x[index])/-d[i],i))
 ratios.sort();assert ratios[0][0]<ratios[1][0];theta,leaving=ratios[0];assert leaving>=0
 steps.append(dict(entering=j+1,leaving=basis[leaving]+1,leaving_row=leaving+1,direction=d,theta=theta,ratios=[[v,r+1] for v,r in ratios],improving=[[v,t+1,s] for v,t,s in improving]))
 for i,index in enumerate(basis):x[index]-=theta*d[i]
 x[j]+=theta*direction;basis[leaving]=j
 assert all(F(0)<=v<=u for v,u in zip(x,upper))
 assert all(dot(row,x)==0 for row in C)
y=stages[-1]['dual'];primal=x[:3];slack=[c[j]-dot(y,[A[i][j] for i in range(2)]) for j in range(3)]
checks={'three_unique_entering_and_ratio_choices':len(steps)==3,'basis_path': [s['basis'] for s in stages]==[[4,5],[1,5],[1,2],[3,2]],'all_finite_dyadic_input':all(v.denominator&(v.denominator-1)==0 for v in sum(A,[])+c+upper),'exact_original_feasible':all(F(0)<=v<=16 for v in primal) and [dot(row,primal) for row in A]==[F(2),F(3)],'dual_sign':all(v<=0 for v in y),'reduced_cost_nonnegative':all(v>=0 for v in slack),'complementarity':all(v*r==0 for v,r in zip(primal,slack)),'objective_agrees':dot(c,primal)==dot(y,[F(2),F(3)])==F(-47,3),'same_pattern_last_refactor':stages[2]['colptr']==stages[3]['colptr'] and stages[2]['rowval']==stages[3]['rowval'],'changed_final_basis_values':stages[2]['B']!=stages[3]['B'],'final_basis_nonsymmetric':stages[3]['B'][0][1]!=stages[3]['B'][1][0]}
inputs=dict(A=A,objective=c,objective_constant=F(0),row_lower=[F(0)]*2,row_upper=[F(2),F(3)],column_lower=[F(0)]*3,column_upper=[F(16)]*3)
def bits(v):
 if isinstance(v,list):return [bits(z) for z in v]
 z=float(v);assert F(z)==v;return struct.pack('>d',z).hex()
obj=dict(scope='Exact rational LP witness and conditional algebraic Dantzig path ONLY; no Julia/native trajectory or complete attempt budget',inputs=enc(inputs),binary64={k:bits(v) for k,v in inputs.items()},matrix_csc=dict(colptr=[1,3,5,7],rowval=[1,2,1,2,1,2],nzval_bits=bits([A[i][j] for j in range(3) for i in range(2)]),index_type='Int64'),stages=enc(stages),steps=enc(steps),witness=enc(dict(primal=primal,dual=y,reduced_cost=slack,objective=dot(c,primal))),checks=checks,all_passed=all(checks.values()),launch_supported=False)
dump('exact-lp.json',obj);print(json.dumps(dict(checks=checks,all_passed=obj['all_passed'])));assert obj['all_passed']
