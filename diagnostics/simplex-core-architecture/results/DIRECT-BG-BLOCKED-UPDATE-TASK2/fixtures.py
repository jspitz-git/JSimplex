from pathlib import Path
import json,struct,hashlib,shutil,re
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,s):
 with p.open('x') as f:f.write(s)
def bits(x):return struct.pack('>d',x).hex()
def csc(B):
 n=len(B);ptr=[1];rows=[];vals=[]
 for j in range(n):
  for i in range(n):
   if B[i][j]!=0:rows.append(i+1);vals.append(bits(B[i][j]))
  ptr.append(len(rows)+1)
 return dict(n=n,colptr=ptr,rowval=rows,bits=vals)
def baseline(n,kind):
 A=[[4. if i==j else ((-1. if (i+j)%2 else 1.)/16/n if kind=='dense' else (-.5 if i==j+1 else .25 if j==i+1 else 0.)) for j in range(n)] for i in range(n)]
 return [[A[(i+3)%n][n-j-1] for j in range(n)] for i in range(n)]
def stream(name,B,count,scale=1.,agreement=False,panels=0,recipe=''):
 n=len(B);initial=csc(B);steps=[]
 for t in range(count):
  j=(7*t)%n;a=[row[j] for row in B];a[(j+1)%n]+=scale/32
  e=[0.]*n;e[j]=1.
  steps.append(dict(j=j+1,a=list(map(bits,a)),dse=[bits(i/n) for i in range(1,n+1)],unit=list(map(bits,e))))
  for i in range(n):B[i][j]=a[i]
 return dict(name=name,n=n,initial=initial,steps=steps,expected='success',pivot_agreement=agreement,minimum_panels=panels,recipe=recipe)
fixtures=[]
for n in (32,96,256):
 for kind in ('sparse','dense'):
  fixtures.append(stream(f'{kind}{n}',baseline(n,kind),8,panels=2 if kind=='dense' and n>=96 else 0,recipe='DIRECT-LU-COST-PREPARATION/prepare.py pure formula; n extended to256; independent original-column replacements'))
fixtures.append(stream('dense96-long32',baseline(96,'dense'),32,panels=2,recipe='same dense96 original generator;32 replacements'))
for kind in ('near-tie','cancellation-fill','large-scale','small-scale','near-singular','separated-exact'):
 n=32 if kind=='separated-exact' else 96
 B=[[1. if i==j else .125 if i<j else 0. for j in range(n)] for i in range(n)]
 scale=1.
 if kind=='near-tie':B[0][1]=1.+2**-52
 if kind=='cancellation-fill':B[0][1]=1.;B[0][2]=.5;B[1][2]=.5
 if kind in ('large-scale','small-scale'):
  scale=2.**(400 if kind=='large-scale' else -400);B=[[x*scale for x in row] for row in B]
 if kind=='near-singular':B[-1][-1]=2.**-30
 if kind=='separated-exact':B=[[4. if i==j else 0. for j in range(n)] for i in range(n)]
 fixtures.append(stream(kind,B,8,scale,agreement=kind=='separated-exact',recipe='upper triangular identity diagonal, strict upper1/8; named single parameter change; source exact IEEE bits. Label describes input stress, not promised backend pivot trajectory'))
old=R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION/inputs.json';oldj=json.loads(old.read_text())
checks=[]
for previous in oldj['fixtures']:
 f=next(f for f in fixtures if f['name']==previous['name']);m=previous['matrices'][0]
 checks.append(f['initial']==dict(n=m['n'],colptr=m['colptr'],rowval=m['rowval'],bits=m['nzval']) and f['steps']==previous['steps'])
if not all(checks):raise ValueError('Old recipe mismatch')
negative=[dict(name='zero-diagonal',kind='post-rotation H microcase',expected='ZeroPivotException',overrides={'1,1':bits(0.),'2,1':bits(0.)}),dict(name='overflow',kind='post-rotation H microcase',expected='private rejection then original scalar propagation; safe=false',overrides={'1,1':bits(1.),'2,1':bits(1.),'1,2':bits(-float.fromhex('0x1.fffffffffffffp1023')),'2,2':bits(float.fromhex('0x1.fffffffffffffp1023'))}),dict(name='explicit-zero',kind='stored zero row10col20 after panel1',expected='reject then scalar success',overrides={'10,20':bits(0.)}),dict(name='infinite',kind='post-rotation H microcase',expected='reject then original scalar, safe=false',overrides={'1,20':bits(float('inf'))}),dict(name='nan',kind='post-rotation H microcase',expected='reject then original scalar, safe=false',overrides={'1,20':bits(float('nan'))})]
j=dict(schema=1,scope='Frozen offline input bits; no generated candidate answer or Julia execution',fixtures=fixtures,negative_microcases=negative,residual_multiplier=128,unit_roundoff_denominator=2**52,old_input_sha256=sha(old))
put(C/'fixtures.json',json.dumps(j,indent=2)+'\n')
lines=['schema = 1']
for f in fixtures:
 lines+=['[[fixtures]]']
 for k in ['name','n','expected','pivot_agreement','minimum_panels','recipe']:lines.append(k+' = '+json.dumps(f[k]))
 lines+=['[fixtures.initial]']+[k+' = '+json.dumps(v) for k,v in f['initial'].items()]
 for s in f['steps']:lines+=['[[fixtures.steps]]']+[k+' = '+json.dumps(v) for k,v in s.items()]
put(C/'fixtures.toml','\n'.join(lines)+'\n')
# Ordinary isolated overlay. No cache/read-only/import-work assertion. No loader
# executes here. Bind every copied source and environment file explicitly.
stage=R/'.superpowers/sdd/2026-10-19-direct-bg-blocked-update/task2-stage'
if stage.exists():raise ValueError('Stage exists')
stage.mkdir()
originals={}
for p in sorted((R/'src').rglob('*')):
 if p.is_file():
  dest=stage/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);originals[str(p.relative_to(R))]=sha(p)
for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']:
 p=R/n
 if p.exists():shutil.copyfile(p,stage/n);originals[n]=sha(p)
ordinary=R/'diagnostics/direct-lu-policy-adapters/reproduce'
for n in ['factor-export.jl','direct-factor.jl']:shutil.copyfile(ordinary/n,stage/'src'/n)
root=stage/'src/JSimplex.jl';t=root.read_text();offset=t.rfind('\nend');insertion='\ninclude("factor-export.jl")\ninclude("direct-factor.jl")\n';root.write_text(t[:offset]+insertion+t[offset:])
manifest=dict(scope='Ordinary overlay prepared offline; NOT a launcher/admission or loading proof',stage=str(stage),original_sha256=originals,root_insertion=insertion,ordinary={n:sha(ordinary/n) for n in ['factor-export.jl','direct-factor.jl']},stage_sha256={str(p.relative_to(stage)):sha(p) for p in sorted(stage.rglob('*')) if p.is_file()},top_level_order=['load staged JSimplex by ordinary active project']+['include '+str(C/n) for n in ['panel.jl','factor.jl','panel-fault.jl','factor-fault.jl','numerical-tests.jl','lifecycle-tests.jl']])

put(C/'overlay-manifest.json',json.dumps(manifest,indent=2)+'\n')
put(Q/'fixture-preparation.json',json.dumps(dict(all_passed=True,old_recipe_matches=checks,fixtures=len(fixtures),updates_per_arm=sum(len(f['steps']) for f in fixtures),scalar_tokens=sum(len(f['initial']['bits'])+3*f['n']*len(f['steps']) for f in fixtures),sha256={str(C/n):sha(C/n) for n in ['fixtures.json','fixtures.toml','overlay-manifest.json']}),indent=2)+'\n')
with (Q/'fixtures.py').open('xb') as out:out.write(Path(__file__).read_bytes())
print('Frozen fixtures and ordinary overlay prepared, no Julia')
