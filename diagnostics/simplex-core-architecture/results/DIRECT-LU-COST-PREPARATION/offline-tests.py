"""New synthetic failures only; no Julia or launch. Executable before controls."""
from pathlib import Path
import json,math,copy,struct,tomllib
from analysis import *
D=Path(__file__).resolve().parent
checks={}
def check(name,v):
 checks[name]=bool(v)
 if not v:raise RuntimeError(name)
def refuses(name,fn):
 try:fn()
 except (ValueError,KeyError,TypeError):check(name,True)
 else:check(name,False)
def tok(x):return struct.pack('>d',x).hex()
I=dict(n=2,colptr=[1,2,3],rowval=[1,2],nzval=[tok(1.),tok(1.)]);M=matrix(I)
check('exact_identity',residual(M,[tok(1.),tok(2.)],[tok(1.),tok(2.)]))
check('wrong_solution_rejected',not residual(M,[tok(1.),tok(3.)],[tok(1.),tok(2.)]))
refuses('nan_token',lambda:number(tok(float('nan'))));refuses('bad_token',lambda:number('bad'))
check('reversed_order',all(schedule(1,p)==schedule(2,p)[::-1] for p in range(1,11)))
fixtures=json.loads((D/'inputs.json').read_text())
check('toml_json_identical',tomllib.loads((D/'inputs.toml').read_text())==fixtures)
check('four_fixtures',[(f['name'],f['n']) for f in fixtures['fixtures']]==[('sparse32',32),('dense32',32),('sparse96',96),('dense96',96)])
for f in fixtures['fixtures']:
 n=f['n'];dense=[]
 for m in f['matrices']:
  rows,e,_=matrix(m);dense.append([[0.]*n for _ in range(n)])
  for i,row in enumerate(rows):
   for j,v in row:dense[-1][i][j]=float(Q(v,2**e))
 base=dense[0]
 for i in range(n):
  for j in range(n):
   ii=(i+3)%n;jj=n-j-1
   want=4. if ii==jj else ((-1. if (ii+jj)%2 else 1.)/16/n if f['name'].startswith('dense') else (-.5 if ii==jj+1 else .25 if jj==ii+1 else 0.))
   if tok(base[i][j])!=tok(want):raise RuntimeError('base bits')
 for k,s in enumerate(f['steps']):
  j=(7*k)%n;a=[row[j] for row in dense[k]];a[(j+1)%n]+=1/32
  check(f'{f["name"]}_step{k}',s['j']==j+1 and s['a']==list(map(tok,a)) and s['dse']==[tok(i/n) for i in range(1,n+1)] and s['unit']==[tok(float(i==j)) for i in range(n)] and all(dense[k+1][i][c]==(a[i] if c==j else dense[k][i][c]) for i in range(n) for c in range(n)))
 check(f'{f["name"]}_diagonal_margin',all(abs(base[i][n-1-((i+3)%n)])>sum(abs(x) for j,x in enumerate(base[i]) if j!=n-1-((i+3)%n)) for i in range(n)))
# Pure result-gate boundaries; no solver results invented.
a=dict(time_median_gate=True,allocation_gate=True,memory_gate=True,faster_pairs=5)
check('qualification_positive',qualify(a,a))
for field in ('time_median_gate','allocation_gate','memory_gate'):
 b=dict(a);b[field]=False;check('reject_'+field,not qualify(a,b))
b=dict(a,faster_pairs=4);check('reject_nine_faster',not qualify(a,b))
with (D/'offline-tests.json').open('x') as o:json.dump(dict(all_passed=all(checks.values()),checks=checks),o,indent=2)
print(json.dumps(dict(all_passed=True,checks=len(checks))))
