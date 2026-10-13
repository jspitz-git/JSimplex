from pathlib import Path
import json,hashlib,struct,subprocess
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/S2-D';C=D.parent/'S2-C'
def put(p,b):
 p=D/p;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b.encode() if isinstance(b,str) else b)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cl=json.loads((C/'closure-final.json').read_text());assert all(sha(Path(p))==h for p,h in cl['sha256'].items())
for p,n in [('diagnostics/simplex-core-architecture/STATUS.md','STATUS.md.before-S2-D'),('docs/superpowers/plans/2026-10-11-simplex-core-architecture.md','roadmap.md.before-S2-D')]:put(n,(R/p).read_bytes())
files=subprocess.check_output(['git','ls-files','src'],text=True).splitlines();mapping={}
for name in files+['Project.toml','Manifest.toml','LocalPreferences.toml']:
 src=C/'candidate-primal-updates.jl' if name=='src/primal_updates.jl' else R/name
 put('overlay/'+name,src.read_bytes());mapping[name]={'origin':str(src),'sha256':sha(src)}
put('overlay-map.json',json.dumps(mapping,indent=2)+'\n')
s=(C/'original-primal-updates.jl').read_text();start=s.index('function _primal_price_prediction_reliable(');ref=s[start:]
assert ref.count('function ')==1
ref=ref.replace('_primal_price_prediction_reliable','s2d_reference_price_audit').replace('::SimplexWorkspace{T}','::JSimplex.SimplexWorkspace{T}').replace('B = _PriceAuditMatrix','B = JSimplex._PriceAuditMatrix').replace('scratch = SolveQualityScratch','scratch = JSimplex.SolveQualityScratch').replace('return solve_quality!','return JSimplex.solve_quality!')
put('reference-audit.jl',ref)
put('guard.py',(D.parent/'S5-AA/guard.py').read_bytes())
fixtures=[]
for scalar,fmt in [('Float32','f'),('Float64','d')]:
 for m in [32,128]:
  n=2*m
  for density in ['sparse','dense']:
   rows=[];colptr=[1];values=[]
   for j in range(1,n+1):
    for i in range(1,m+1):
     if density=='sparse' and not (i==(j-1)%m+1 or i==j%m+1 or (i+3*j)%17==0):continue
     v=((3*i+5*j)%17-8)/16
     if v:rows.append(i);values.append(v)
    colptr.append(len(rows)+1)
   costs=[1+(j%7)/8 for j in range(1,n+1)]
   bits=lambda xs:[struct.pack('>'+fmt,x).hex() for x in xs]
   fixtures.append(dict(id=f'{scalar}-{density}-{m}',scalar=scalar,m=m,n=n,density=density,colptr=colptr,rowval=rows,nzval_bits=bits(values),cost_bits=bits(costs),nzval_sha256=hashlib.sha256(b''.join(struct.pack('<'+fmt,x) for x in values)).hexdigest()))
# TOML is generated without external packages and contains no non-dyadic decimals.
lines=['schema = 1','warm_pairs = 4','measured_pairs = 8','calls_per_window = 16']
for f in fixtures:
 lines+=['','[[fixtures]]']
 for k,v in f.items():lines.append(k+' = '+json.dumps(v,separators=(',',':')))
put('fixtures.toml','\n'.join(lines)+'\n')
put('budget.json',json.dumps({'scope':'prospective source entry counts, not complete hidden backend/import work','direct_quality_pairs':30,'direct_quality_calls':60,'alias_rejections':20,'integration_explicit_quality_calls':16,'integration_workspaces':11,'integration_explicit_recompute_calls':7,'integration_audit_calls':10,'integration_primal_iteration_calls':4,'cost_workspaces':8,'cost_windows':192,'warm_windows':64,'measured_windows':128,'cost_audits':3072,'candidate_cost_audits':1536,'reference_cost_audits':1536,'warm_pairs_per_fixture':4,'measured_pairs_per_fixture':8,'calls_per_window':16,'julia_processes_max':1,'attempts_max':1,'wall_seconds':180,'numerical_allowance_granted':False},indent=2)+'\n')
print('Prepared ordinary overlay',len(mapping),'files; eight exact dyadic cost fixtures; no Julia.')
