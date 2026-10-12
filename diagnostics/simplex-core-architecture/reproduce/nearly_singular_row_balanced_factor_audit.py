from pathlib import Path
from fractions import Fraction as F
import json,tomllib,hashlib,sys,importlib.util,shutil
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';base=root/'.superpowers/simplex-core-architecture/S6-S/factor-1';out=d/'results/S6-S'
r=tomllib.loads((base/'report.toml').read_text());proc=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());source=out/'qualify-1-report.toml';previous=tomllib.loads(source.read_text());control=next(x for x in previous['records'] if x['type']=='Float64');x=r['record']
Q=lambda s:F(s.replace('//','/'))
mat=lambda v:[[Q(v[i+2*j]) for j in range(2)] for i in range(2)]
def mul(A,B):return [[sum(A[i][k]*B[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
def mv(A,b):return [sum(A[i][j]*b[j] for j in range(2)) for i in range(2)]
checks={};s=importlib.util.spec_from_file_location('g',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
checks['exit0']=proc['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged']
checks['pins_guard']=g.pins_match(pins)
checks['pins_independent']=all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items())
paths=set(pins['files'])
for t in pins['trees']:paths.update(str(x) for x in Path(t).rglob('*') if x.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
checks['actual_source']=r['source']==str(root/'src/JSimplex.jl')
checks['input_hash']=r['input_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
checks['runtime_threads']=r['julia_version']==previous['julia_version'] and r['arch']==previous['arch'] and r['julia_threads']==r['blas_threads']==1
checks['options_globals']=r['options']==control['options'] and r['globals_preserved']
checks['one_factor_two_solves']=x['factorizations']==x['ftran_calls']==x['btran_calls']==1 and x['updates']==0
checks['immutable_inputs_controls']=x['input_unchanged'] and x['control_before']==x['control_after']
checks['default_controls']=x['refinement_steps']==0 and x['scaling_mode']==1
A=mat(x['matrix']);L=mat(x['L']);U=mat(x['U']);rs=list(map(Q,x['Rs']));p=[v-1 for v in x['p']];q=[v-1 for v in x['q']];b=list(map(Q,x['rhs']));c=list(map(Q,x['dual_rhs']));point=list(map(Q,x['primal']));dual=list(map(Q,x['dual']))
checks['valid_permutations']=sorted(p)==sorted(q)==[0,1]
LU=mul(L,U);scaled=[[rs[i]*A[i][j] for j in range(2)] for i in range(2)];target=[[scaled[i][j] for j in q] for i in p]
residual=[[LU[i][j]-target[i][j] for j in range(2)] for i in range(2)]
pr=[v-w for v,w in zip(mv(A,point),b)];dr=[sum(A[j][i]*dual[j] for j in range(2))-c[i] for i in range(2)]
e=F(1,2**23);s0=F(1,2**21);d0=F(1,2**44)
checks['new_source_matrix']=mat(x['original_matrix'])==[[s0,s0],[s0-d0,s0+d0]]==mat([v['exact'] for v in control['model_before']['matrix']])
checks['production_scaling']=list(map(Q,x['row_scaling']))==[s0,s0] and list(map(Q,x['column_scaling']))==[1,1] and A==[[1,1],[1-e,1+e]] and b==[-2**21,2**21*(1+e)] and c==[0,-1]
checks['actual_dyadic_metadata']=p==q==[0,1] and rs==[F(1,2),F(1,2)] and L==[[1,0],[1-e,1]] and U==[[F(1,2),F(1,2)],[0,e]]
checks['exact_factor_identity']=all(v==0 for row in residual for v in row)
checks['exact_primal_dual_residuals']=pr==dr==[0,0]
checks['endpoint_equals_new_public']=point==[-2**44-2**21,2**44]==[Q(v['exact']) for v in control['primal']]
checks['six_assertions']='6      6' in (base/'run.log').read_text() and 'Test Failed' not in (base/'run.log').read_text()
audit={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'summary':{'exact_LU_residual':[[str(v) for v in row] for row in residual],'primal_residual':list(map(str,pr)),'dual_residual':list(map(str,dr)),'primal':list(map(str,point))},'scope':'One newly constructed local Float64 component, not hidden public-solve factor identity or x64/full-suite proof. No performance comparison.'}
with (out/'factor-1-audit.json').open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
for name in ['report.toml','run.log','pins.json','process.json']:shutil.copyfile(base/name,out/('factor-1-'+name))
shutil.copyfile(d/'reproduce/nearly_singular_row_balanced_factor.jl',out/'factor-1-driver.jl')
print(json.dumps(audit,indent=2))
