from pathlib import Path
from fractions import Fraction as F
import json,hashlib,struct,itertools,subprocess
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S4-T';a=json.loads((E/'source-contract.json').read_text());q=json.loads((E/'exact-lp.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();checks={}
checks['full604_current_rehash']=len(a['sha256'])==604 and all(sha(p)==h for p,h in a['sha256'].items())
checks['recorded_source_gates17']=len(a['checks'])==17 and all(a['checks'].values())
def vals(x):return [vals(z) for z in x] if isinstance(x,list) else F(x)
def unpack(x):return [unpack(z) for z in x] if isinstance(x,list) else F(struct.unpack('>d',bytes.fromhex(x))[0])
v={k:vals(x) for k,x in q['inputs'].items()};checks['every_input_bit_exact']=all(v[k]==unpack(x) for k,x in q['binary64'].items())
A=[[F(1),F(1,4),F(1,2)],[F(1,4),F(1),F(1,2)]];c=[F(-4),F(-3),F(-7,2)];checks['independent_input_definition']=v['A']==A and v['objective']==c and v['row_upper']==[2,3] and v['column_upper']==[16]*3
ineq=[]
for i in range(3):
 row=[F(j==i) for j in range(3)];ineq.extend([(row,F(16)),([-z for z in row],F(0))])
for row,b in zip(A,[2,3]):ineq.extend([(row,F(b)),([-z for z in row],F(0))])
def intersection(rows):
 aug=[r[:]+[b] for r,b in rows]
 for j in range(3):
  pivot=next((i for i in range(j,3) if aug[i][j]),None)
  if pivot is None:return None
  aug[j],aug[pivot]=aug[pivot],aug[j];d=aug[j][j];aug[j]=[z/d for z in aug[j]]
  for i in range(3):
   if i!=j:
    d=aug[i][j];aug[i]=[z-d*w for z,w in zip(aug[i],aug[j])]
 return [row[3] for row in aug]
def dot(a,b):return sum((x*y for x,y in zip(a,b)),F(0))
vertices=set()
for combo in itertools.combinations(ineq,3):
 x=intersection(combo)
 if x is not None and all(dot(row,x)<=b for row,b in ineq):vertices.add(tuple(x))
opt=min(dot(c,x) for x in vertices);best=[x for x in vertices if dot(c,x)==opt]
checks['independent_exact_vertex_optimum']=opt==F(-47,3) and best==[(F(0),F(4,3),F(10,3))]
x=vals(q['witness']['primal']);y=vals(q['witness']['dual']);checks['independent_dual_identity']=y==[F(-16,3),F(-5,3)] and [c[j]-sum(y[i]*A[i][j] for i in range(2)) for j in range(3)]==[F(7,4),F(0),F(0)] and dot(c,x)==dot(y,[2,3])
checks['basis_path_and_steps']= [s['basis'] for s in q['stages']]==[[4,5],[1,5],[1,2],[3,2]] and [F(s['theta']) for s in q['steps']]==[2,F(8,3),F(10,3)]
checks['src_test_CI_no_diff']=not subprocess.check_output(['git','diff','master','--','src','test','.github'])
obj=dict(checks=checks,all_passed=all(checks.values()),vertex_count=len(vertices),exact_vertex_combinations=120,scope='Separate author full604 current hash check, all bit checks and exact vertex enumeration of the SAME frozen LP; no Julia/native/production solve')
with (E/'independent.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps(obj));assert obj['all_passed']
