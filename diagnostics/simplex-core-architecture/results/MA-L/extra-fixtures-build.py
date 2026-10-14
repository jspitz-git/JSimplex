"""Two explicit coverage supplements; original 220-case fixture output preserved."""
from pathlib import Path
from fractions import Fraction as F
from itertools import product
import json
D=Path(__file__).resolve().parent
base=json.loads((D/'fixtures.json').read_text())['fixtures'];out=[]
for id,parent in [('zero-coefficient','ordinary-unit'),('same-denominator-after-selection','target-160-8-1-0')]:
 f=json.loads(json.dumps(next(x for x in base if x['id']==parent)))
 f.update(id=id,group='ownership',cost='',alias='')
 if id=='zero-coefficient':f['co'][2]='0/1'
 else:
  den=F(f['co'][0]).denominator*F(f['co'][1]).denominator
  f['co'][2]='1/'+str(den)
  f['route'].update(adds=11)
 c=list(map(F,f['co']));lo=list(map(F,f['lo']));hi=list(map(F,f['hi']));p=f['pivot']-1;rhs=F(f['rhs'])
 verts=[sum(v,F(0)) for v in product(*[[c[j]*lo[j],c[j]*hi[j]] for j in range(len(c)) if j!=p])]
 pts=[(rhs-v)/c[p] for v in verts];f['expected']=min(pts)>=lo[p] and max(pts)<=hi[p]
 out.append(f)
def jl(v):
 if v is None:return 'nothing'
 if isinstance(v,bool):return 'true' if v else 'false'
 if isinstance(v,int):return str(v)
 if isinstance(v,str):return json.dumps(v)
 if isinstance(v,list):return '['+','.join(jl(x) for x in v)+']'
 raise TypeError(type(v))
lines=['# Two frozen MA-L coverage supplements. UNEXECUTED.','const MAL_EXTRA_FIXTURES = [']
for x in out:
 fields={k:v for k,v in x.items() if k!='route'};fields.update(route_position=x['route']['position'],route_count=x['route']['count'],route_adds=x['route']['adds'])
 lines.append('    ('+', '.join(k+'='+jl(v) for k,v in fields.items())+',),')
lines.append(']')
with (D/'extra-fixtures.json').open('x') as f:json.dump({'scope':'Additional direct-helper zero coefficient and active same-denominator ownership coverage; no new cost cases','fixtures':out},f,indent=2);f.write('\n')
with (D/'extra-fixtures.jl').open('x') as f:f.write('\n'.join(lines)+'\n')
print('2 extra correctness fixtures; 222 total, cost grid unchanged at76.')
