from pathlib import Path
from fractions import Fraction as F
import json,tomllib,hashlib,sys,importlib.util,shutil
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';base=root/'.superpowers/simplex-core-architecture/S6-R/replay-1';out=d/'results/S6-R'
r=tomllib.loads((base/'report.toml').read_text());proc=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());trace=tomllib.loads((d/'results/S6-Q/trace-1-report.toml').read_text());pre=json.loads((out/'preflight.json').read_text())
Q=lambda s:F(s.replace('//','/'))
mat=lambda v:[[Q(v[i+2*j]) for j in range(2)] for i in range(2)]
def mul(A,B):return [[sum(A[i][k]*B[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
def mv(A,b):return [sum(A[i][j]*b[j] for j in range(2)) for i in range(2)]
def solve(A,b):
 det=A[0][0]*A[1][1]-A[0][1]*A[1][0]
 return [(b[0]*A[1][1]-A[0][1]*b[1])/det,(A[0][0]*b[1]-b[0]*A[1][0])/det]
checks={};s=importlib.util.spec_from_file_location('g',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
checks['exit0']=proc['returncode']==0 and proc['reason']=='exit0' and proc['pins_unchanged']
checks['pins_guard']=g.pins_match(pins)
checks['pins_independent']=all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items())
paths=set(pins['files'])
for t in pins['trees']:paths.update(str(x) for x in Path(t).rglob('*') if x.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
checks['preflight']=pre['all_passed'] and pre['count']==517 and all(pre['checks'].values())
qpins=json.loads((d/'results/S6-Q/trace-1-pins.json').read_text())
checks['preflight_comparability']=all(pins['inventory'][k]==qpins['inventory'][k] for k in pre['checks'])
checks['actual_source']=r['source']==str(root/'src/JSimplex.jl')
checks['input_hash']=r['input_sha256']==hashlib.sha256((d/'results/S6-Q/trace-1-report.toml').read_bytes()).hexdigest()
checks['runtime_threads']=r['julia_version']==trace['julia_version'] and r['arch']==trace['arch'] and r['julia_threads']==r['blas_threads']==1
checks['options_policy']=r['options']==trace['options'] and r['source_policy']==trace['policy'] and r['source_policy']['hypersparse']==r['source_policy']['solve_refinement']=='false'
checks['globals_preserved']=r['globals_preserved'] and r['global_precision']==256 and r['global_rounding']=='RoundingMode{:Nearest}()'
checks['two_lifecycles']=[x['mode'] for x in r['records']]==['fresh','copy_refactor']
checks['four_component_solves']=sum(x['ftran_calls']+x['btran_calls'] for x in r['records'])==4 and all(x['ftran_calls']==x['btran_calls']==1 for x in r['records'])
checks['declared_lifecycle']=r['records'][0]['explicit_refactors']==r['records'][0]['copy_calls']==0 and r['records'][1]['explicit_refactors']==r['records'][1]['copy_calls']==1 and all(x['initial_factorizations']==1 for x in r['records'])
checks['immutable_inputs_control']=all(x['source_unchanged'] and x['control_before']==x['control_after'] and x['initial_copy_base_preserved'] for x in r['records'])
checks['no_eta_default_controls']=all(x['update_count']==0 and x['umfpack_refinement_steps']==0 and x['umfpack_scaling_mode']==1 for x in r['records'])
checks['matches_trace']=all(x['primal_matches_trace'] and x['dual_matches_recorded_scratch'] and x['primal']==trace['events'][-1]['scratch_row_solution'] and x['dual']==trace['events'][-1]['scratch_rho'] for x in r['records'])
summary=[]
for rec in r['records']:
 A=mat(rec['matrix']);L=mat(rec['L']);U=mat(rec['U']);rs=list(map(Q,rec['Rs']));p=[x-1 for x in rec['p']];q=[x-1 for x in rec['q']];b=list(map(Q,rec['rhs']));c=list(map(Q,rec['dual_rhs']));x=list(map(Q,rec['primal']));dual=list(map(Q,rec['dual']))
 assert sorted(p)==sorted(q)==[0,1]
 LU=mul(L,U);scaled=[[rs[i]*A[i][j] for j in range(2)] for i in range(2)];target=[[scaled[i][j] for j in q] for i in p]
 residual=[[LU[i][j]-target[i][j] for j in range(2)] for i in range(2)]
 # Exact application of stored factors and scale (not another floating solve).
 y=solve(L,[(rs[i]*b[i]) for i in p]);z=solve(U,y);xf=[F(0),F(0)]
 for j in range(2):xf[q[j]]=z[j]
 strict=solve(A,b);ar=[v-w for v,w in zip(mv(A,x),b)]
 dr=[sum(A[j][i]*dual[j] for j in range(2))-c[i] for i in range(2)]
 fg=-xf[1]+strict[1];ag=-x[1]+xf[1];gap=-x[1]+strict[1]
 assert fg+ag==gap
 assert ar==[0,F(1,2**27)] and gap==-F(1,16)
 assert residual==[[0,0],[0,-F(1,2**72)]]
 assert fg==-F(2**20,2**24-1) and ag==F(1,16*(2**24-1))
 assert strict==[-2**44-2**20,2**44]
 summary.append({'mode':rec['mode'],'strict_solution':list(map(str,strict)),'primal_residual':list(map(str,ar)),'dual_residual':list(map(str,dr)),'exact_LU_minus_scaled_permuted_B':[[str(v) for v in row] for row in residual],'exact_stored_factor_solution':list(map(str,xf)),'objective_factor_representation_contribution':str(fg),'objective_application_contribution':str(ag),'objective_total_gap':str(gap),'exact_identity_holds':all(v==0 for row in residual for v in row)})
checks['exact_residual_decomposition']=len(summary)==2
checks['rounded_factor_identity_not_misreported']=all(not x['exact_identity_holds'] for x in summary)
checks['lifecycle_metadata_equal']=all(r['records'][0][k]==r['records'][1][k] for k in ['matrix','L','U','p','q','Rs','primal','dual','control_before','control_after'])
checks['diagnostic_assertions']='12     12' in (base/'run.log').read_text() and 'Test Failed' not in (base/'run.log').read_text()
audit={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'summary':summary,'scope':'Exact rational decomposition of newly constructed local component factors. Not captured solver runtime internals, historical x64 cause, strict equality pass, performance or production repair.'}
with (out/'replay-1-audit.json').open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
for name in ['report.toml','run.log','pins.json','process.json']:shutil.copyfile(base/name,out/('replay-1-'+name))
shutil.copyfile(d/'reproduce/nearly_singular_factor_replay.jl',out/'replay-1-driver.jl')
print(json.dumps(audit,indent=2))
