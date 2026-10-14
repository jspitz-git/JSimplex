from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
original=json.loads((D/'extra-fixtures.json').read_text());fixed=json.loads(json.dumps(original))
x=next(f for f in fixed['fixtures'] if f['id']=='zero-coefficient')
if x['route']['count']!=1:raise ValueError('unexpected original')
x['route']['count']=0
for a,b in zip(original['fixtures'],fixed['fixtures']):
 for key in a:
  if key!='route' and a[key]!=b[key]:raise ValueError('input changed')
with (D/'extra-fixtures-reviewed.json').open('x') as f:json.dump(fixed,f,indent=2);f.write('\n')
s=(D/'extra-fixtures.jl').read_text();lines=s.splitlines()
changed=0
for i,line in enumerate(lines):
 if 'id="zero-coefficient"' in line:
  if line.count('route_count=1')!=1:raise ValueError('literal original')
  lines[i]=line.replace('route_count=1','route_count=0');changed+=1
if changed!=1:raise ValueError('wrong fixture count')
with (D/'extra-fixtures-reviewed.jl').open('x') as f:f.write('\n'.join(lines)+'\n')
s=(D/'source-check.py').read_text().replace("D/'extra-fixtures.json'","D/'extra-fixtures-reviewed.json'").replace("('extra-fixtures.json','extra-fixtures.jl')","('extra-fixtures-reviewed.json','extra-fixtures-reviewed.jl')").replace("D/'source-check.json'","D/'source-check-final.json'")
with (D/'source-check-final.py').open('x') as f:f.write(s)
record=dict(cause='Extra zero-coefficient fixture copied the unit control route_count=1, but replacing its third coefficient by zero removes the sole qualifying addition. No candidate or input value changes.',checks={'original_gate_false':json.loads((D/'source-check.json').read_text())['checks']['all_route_expectations'] is False,'diagnosis_single_case':len(json.loads((D/'route-diagnosis.json').read_text())['differences'])==1,'one_metadata_count_fix':changed==1,'inputs_unchanged':all({k:v for k,v in a.items() if k!='route'}=={k:v for k,v in b.items() if k!='route'} for a,b in zip(original['fixtures'],fixed['fixtures']))},sha256={str(D/n):hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ('extra-fixtures.json','extra-fixtures.jl','extra-fixtures-reviewed.json','extra-fixtures-reviewed.jl','source-check.json','route-diagnosis.json','candidate.jl')})
with (D/'route-fix.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record['checks']))
