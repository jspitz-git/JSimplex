"""Offline input generation only; never imports Julia or runs a historical script."""
from pathlib import Path
import json,struct,hashlib,shutil
D=Path(__file__).resolve().parent;R=D.parents[3]
def save(p,s):
 with p.open('x') as f:f.write(s)
def bits(x):return struct.pack('>d',x).hex()
def csc(B):
 n=len(B);ptr=[1];rows=[];vals=[]
 for j in range(n):
  for i in range(n):
   if B[i][j]!=0:rows.append(i+1);vals.append(bits(B[i][j]))
  ptr.append(len(rows)+1)
 return dict(n=n,colptr=ptr,rowval=rows,nzval=vals)
fixtures=[]
for n in (32,96):
 for kind in ('sparse','dense'):
  A=[[4. if i==j else ((-1. if (i+j)%2 else 1.)/16/n if kind=='dense' else (-.5 if i==j+1 else .25 if j==i+1 else 0.)) for j in range(n)] for i in range(n)]
  B=[[A[(i+3)%n][n-j-1] for j in range(n)] for i in range(n)]
  mats=[csc(B)];steps=[]
  for t in range(8):
   j=(7*t)%n;a=[row[j] for row in B];a[(j+1)%n]+=1/32
   e=[0.]*n;e[j]=1.
   steps.append(dict(j=j+1,a=list(map(bits,a)),dse=[bits(i/n) for i in range(1,n+1)],unit=list(map(bits,e))))
   for i in range(n):B[i][j]=a[i]
   mats.append(csc(B))
  fixtures.append(dict(name=f'{kind}{n}',n=n,matrices=mats,steps=steps))
# JSON and TOML carry the same canonical IEEE tokens. Julia does no fixture math.
save(D/'inputs.json',json.dumps(dict(fixtures=fixtures),indent=2)+'\n')
lines=[]
for f in fixtures:
 lines+=['[[fixtures]]',f'name = "{f["name"]}"',f'n = {f["n"]}']
 for m in f['matrices']:
  lines+=['[[fixtures.matrices]]',f'n = {m["n"]}']+[k+' = '+json.dumps(m[k]) for k in ('colptr','rowval','nzval')]
 for s in f['steps']:
  lines+=['[[fixtures.steps]]',f'j = {s["j"]}']+[k+' = '+json.dumps(s[k]) for k in ('a','dse','unit')]
save(D/'inputs.toml','\n'.join(lines)+'\n')
A=R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-GREEN-ADMISSION'
for name in ('guard.py','supervisor.py'):
 with (D/name).open('xb') as o:o.write((A/name).read_bytes())
# Reuse the qualified immutable ordinary overlay with explicit private factories.
# No copy of the tested implementation and no new production dispatch.
save(D/'source-lineage.json',json.dumps(dict(project=str(R/'.superpowers/direct-lu-markowitz-green-2/candidate'),
 implementation={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'diagnostics/direct-lu-markowitz/reproduce').glob('*.jl')},
 guard_sources={n:hashlib.sha256((A/n).read_bytes()).hexdigest() for n in ('guard.py','supervisor.py')}),indent=2)+'\n')
print(json.dumps(dict(fixtures=len(fixtures),matrices=sum(len(f['matrices']) for f in fixtures),steps=32,scalar_tokens=sum(len(m['nzval']) for f in fixtures for m in f['matrices'])+sum(3*f['n']*8 for f in fixtures))))
