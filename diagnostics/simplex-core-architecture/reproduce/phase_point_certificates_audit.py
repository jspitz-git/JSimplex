from pathlib import Path
from fractions import Fraction as Q
import json,tomllib,hashlib,sys,struct,importlib.util,shutil
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';out=d/'results/S6-Y';name=sys.argv[1];base=root/'.superpowers/simplex-core-architecture/S6-Y'/name
r=tomllib.loads((base/'report.toml').read_text());p=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());inputs=json.loads((out/'point-inputs.json').read_text());ti=tomllib.loads((out/'point-inputs.toml').read_text())
spec=importlib.util.spec_from_file_location('g',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks={'exit0':p['reason']=='exit0' and p['returncode']==0,'guard_pins':p['pins_unchanged'] and g.pins_match(pins),'independent_pins':all(sha(k)==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'actual_source':r['source']==str(root/'src/JSimplex.jl'),'input_hash':r['input_sha256']==sha(out/'point-inputs.toml'),'driver_hash':r['driver_sha256']==sha(d/'reproduce/phase_point_certificates.jl'),'threads':r['julia_threads']==r['blas_threads']==1,'globals':r['globals_preserved'],'model_preserved':r['model_preserved'],'three_cases':len(r['records'])==3,'six_component_calls':sum(c['quality_calls'] for c in r['records'])==sum(c['certificate_calls'] for c in r['records'])==3,'input_transcription':all(inputs[k]==ti[k] for k in ('matrix','rhs','costs','points')),'input_sources':all(sha(root/k)==v for k,v in inputs['sources'].items())}
paths=set(pins['files'])
for t in pins['trees']:paths.update(str(v) for v in Path(t).rglob('*') if v.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
old=tomllib.loads((d/'results/S6-X/census-1-report.toml').read_text());control=next(c for c in old['records'] if c['scalar']=='Float32' and c['manager']=='pfi' and c['max_refinements']==3)
checks['options_policy_identical']=r['options']==control['options'] and r['policy']==control['policy']
v=control['before_original'];model=r['model']
checks['matrix_identical']=all(model[k]==v[k] for k in ('colptr','rowval','nzval'))
checks['original_bounds_costs']=model['objective']==inputs['costs'] and model['row_lower']==model['row_upper']=={'finite':[True]*6,'values':inputs['rhs']} and model['column_lower']=={'finite':[True]*6,'values':[0.0]*6} and model['column_upper']['finite']==[False]*6
oldpins=json.loads((d/'results/S6-X/census-1-pins.json').read_text());shared=[k for k in oldpins['inventory'] if k in pins['inventory'] and ('/src/' in k or '/test/' in k or k.endswith(('Project.toml','Manifest.toml','LocalPreferences.toml','julia.sh','/bin/julia')))];checks['shared_pins']=all(oldpins['inventory'][k]==pins['inventory'][k] for k in shared)
checks['runtime_identical']=all(old[k]==r[k] for k in ('julia_version','arch','julia_threads','blas_threads'))
checks['exact_input_output_bits']=all(c['name']==i['name'] and c['input_bits']==c['output_bits']==i['bits'] for c,i in zip(r['records'],inputs['points']))
checks['test_summary']='12     12' in (base/'run.log').read_text()
A=inputs['matrix'];b=inputs['rhs'];tol=Q(r['primal_tolerance']);cases=[]
for c,i in zip(r['records'],inputs['points']):
 x=[Q(struct.unpack('!f',bytes.fromhex(h))[0]) for h in i['bits']]
 assert x==list(map(Q,c['point']))
 activity=[sum(Q(a)*v for a,v in zip(row,x)) for row in A];res=[a-z for a,z in zip(activity,b)]
 scale=[abs(Q(z))+sum(abs(Q(a)*v) for a,v in zip(row,x)) for row,z in zip(A,b)]
 ratios=[abs(v)/s if s else Q(0) for v,s in zip(res,scale)]
 cases.append({'name':c['name'],'residual_Ax_minus_rhs':list(map(str,res)),'scale':list(map(str,scale)),'max_exact_relative_indicator':str(max(ratios)),'exact_equations':not any(res),'exact_original_tolerance_feasible':max(map(abs,res))<=tol and min(x)>=-tol,'zero_dual_exact':not any(inputs['costs']),'quality_reliable':c['quality_reliable'],'quality_absolute':c['quality_absolute'],'quality_relative':c['quality_relative'],'original_primal_feasible':c['original_primal_feasible']})
checks['finite_quality']=all(c['quality_finite'] for c in r['records'])
checks['certificate_matches_exact_stored_inputs']=all(c['original_primal_feasible']==c['exact_original_tolerance_feasible'] for c in cases)
# Record, do not require, a favorable quality/certificate result.
audit={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'shared_count':len(shared),'shared_paths':shared,'cases':cases,'primal_tolerance_exact':str(tol),'solve_tolerance_exact':str(Q(r['solve_tolerance'])),'scope':'Three standalone stored-point evaluations; no private CI export state or backend/rejection-branch proof.'}
with (out/(name+'-audit.json')).open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
for n in ('report.toml','pins.json','process.json','run.log'):shutil.copyfile(base/n,out/(name+'-'+n))
shutil.copyfile(d/'reproduce/phase_point_certificates.jl',out/(name+'-driver.jl'))
print(json.dumps({k:v for k,v in audit.items() if k!='shared_paths'},indent=2));assert audit['all_passed']
