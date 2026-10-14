from pathlib import Path
from fractions import Fraction as F
import json
D=Path(__file__).resolve().parent
rows=json.loads((D/'fixtures.json').read_text())['fixtures']+json.loads((D/'extra-fixtures.json').read_text())['fixtures']
differences=[]
for f in rows:
 if f['scalar']!='Q' or f['container']!='vector' or len(f['co'])!=8:continue
 c=list(map(F,f['co']));l=[None if v is None else F(v) for v in f['lo']];h=[None if v is None else F(v) for v in f['hi']];k=f['pivot']-1
 v=[F(0) if (h[k] if c[k]>0 else l[k]) is not None else None,F(0) if (l[k] if c[k]>0 else h[k]) is not None else None]
 stop=None in v;pool=False;counter=at=adds=0;events=[]
 for j in range(8):
  if j==3:stop=True
  if j==k:continue
  a,b=(l[j],h[j]) if c[j]>0 else (h[j],l[j]);shared=v[0]==v[1]
  eligible=not stop and None not in v and a is not None and b is not None and a!=b
  for side,bound in enumerate((a,b)):
   if v[side] is None or bound is None:v[side]=None;continue
   if bound==0:continue
   term=c[j]*bound
   if v[side]==0:v[side]=term;continue
   if side==1 and shared and a==b:v[1]=v[0];continue
   if not pool and v[side].denominator!=term.denominator and eligible and not stop and term:
    counter+=1
    if counter==2:
     stop=True
     if (v[side]>0)==(term>0) and min(abs(v[side].numerator).bit_length(),abs(term.numerator).bit_length())>=129:pool=True;at=j+1
   if pool:adds+=1;events.append((j+1,side))
   v[side]+=term
 got=(at,counter,adds);wanted=tuple(f['route'][x] for x in ('position','count','adds'))
 if got!=wanted:differences.append(dict(id=f['id'],expected=wanted,source_order=got,events=events))
with (D/'route-diagnosis.json').open('x') as o:json.dump({'differences':differences},o,indent=2);o.write('\n')
print(json.dumps(differences,indent=2))
