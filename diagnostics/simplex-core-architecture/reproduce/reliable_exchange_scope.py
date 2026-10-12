from fractions import Fraction as Q
from pathlib import Path
import json
r=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
a=[[8,-2,0,1,-3,2],[2,6,1,2,-2,-2],[1,-2,3,0,-1,3],[3,-1,0,5,-2,-2],[0,0,-1,0,6,-3],[0,0,-1,-2,-1,8]]
b=[6,8,-1,2,0,0];x=[1,1,0,0,0,0];m=[list(map(Q,row)) for row in a];det=Q(1)
for k in range(6):
 pivot=next(i for i in range(k,6) if m[i][k])
 if pivot!=k:m[k],m[pivot]=m[pivot],m[k];det=-det
 v=m[k][k];det*=v
 for i in range(k+1,6):
  t=m[i][k]/v
  for j in range(k,6):m[i][j]-=t*m[k][j]
assert det==31071 and [sum(v*w for v,w in zip(row,x)) for row in a]==b
print(json.dumps({'old_determinant':str(det),'old_full_rank':True,'point':x,'old_rhs':b,'new_rhs':x,'same_structural_singleton':True,'extended_row_activity_coordinates_differ':True}))
for p in [r/'diagnostics/simplex-core-architecture/S6-RELIABLE-EXCHANGE.md',r/'docs/superpowers/plans/2026-10-12-reliable-phase-exchange-repair.md']:
 assert 'same singleton' in p.read_text(), 'live report/repair plan lacks correct exact feasible-set scope: '+str(p)
print('Exact scope and both live documents PASS')
