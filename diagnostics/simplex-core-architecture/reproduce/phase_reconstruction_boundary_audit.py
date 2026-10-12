from pathlib import Path
import sys,json,tomllib,hashlib,importlib.util,shutil
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';name=sys.argv[1];base=root/'.superpowers/simplex-core-architecture/S6-AB'/name;out=d/'results/S6-AB'
r=tomllib.loads((base/'report.toml').read_text());p=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());log=(base/'run.log').read_text();cs=r['records'];source=(root/'test/native_phase_transfer_tests.jl').read_text()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('g',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
checks={'exit0':p['returncode']==0 and p['reason']=='exit0','guard_pins':p['pins_unchanged'] and g.pins_match(pins),'independent_pins':all(sha(k)==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'actual_source':r['source']==str(root/'src/JSimplex.jl'),'test_hash':r['test_sha256']==sha(root/'test/native_phase_transfer_tests.jl'),'test_unchanged':source==(d/'results/S6-AA/green-1-test.jl').read_text(),'helper_actual':r['helper']=='function reliable_artificial_exchange_fixture'+source.split('function reliable_artificial_exchange_fixture',1)[1].split('\n@testset',1)[0],'threads':r['julia_threads']==r['blas_threads']==1,'globals':r['globals_preserved']}
paths=set(pins['files'])
for t in pins['trees']:paths.update(str(v) for v in Path(t).rglob('*') if v.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
keys={(t,m,s) for t in ['Float32','Float64'] for m in ['pfi','forrest_tomlin','suhl_suhl','bartels_golub'] for s in [False,True]}
checks['sixteen_new_cases']=len(cs)==16 and {(c['scalar'],c['manager'],c['subject']) for c in cs}==keys
x=tomllib.loads((d/'results/S6-X/census-1-report.toml').read_text());controls={(c['scalar'],c['manager']):c for c in x['records'] if c['max_refinements']==3}
checks['same_options_policy']=all(c['options']==controls[c['scalar'],c['manager']]['options'] and c['policy']==controls[c['scalar'],c['manager']]['policy'] for c in cs)
checks['all_accepted']=all(c['accepted'] for c in cs)
checks['exact_points_basis']=all(c['original']['primal']==[1,1,0,0,0,0,1,1,0,0,0,0] and c['original']['basis']==list(range(1,7)) and c['original']['iterations']==1 for c in cs)
checks['certificates']=all(c.get('post_certificate',False) for c in cs)
checks['original_export_real']=all('PhaseBoundaryFactor' not in c['original']['factor'] and all(not e['wrapped'] for e in c['events'] if e['columns']==6) for c in cs)
checks['kernel_work']=all(c['kernels']['ftran']==(6 if c['subject'] else 5) and c['kernels']['btran']==4 and c['kernels']['refactorization']==2 for c in cs)
subjects=[c for c in cs if c['subject']]
expected={'ftran':4,'btran':2,'primal_rhs':1,'correction_rhs':1,'update':1,'refactor':1,'hit':1,'invalidations':5}
checks['complete_success_work']=all(c['work']==expected for c in subjects)
checks['event_order']=all([e['event'] for e in c['events'] if e['wrapped']]==['refactor_other','correction_attempt','artificial_removed'] for c in subjects)
checks['correction_counts']=all(c['event_counts']['correction_attempt']==int(c['subject']) for c in cs)
checks['one_declared_output']=all(len(c['calls'])==6 and sum(v['hit'] for v in c['calls'])==1 and all(v['real_output']==v['rhs'] and (v['output']==[1,1,2**-10,0,0,0] if v['hit'] else v['output']==v['real_output']) for v in c['calls']) for c in subjects)
checks['correction_rhs_and_output']=all(sum(v['rhs']==[0,0,-2**-10,0,0,0] and v['output']==v['rhs'] for v in c['calls'])==1 for c in subjects)
checks['negative_static_extra_attempt']=all(c['negative_rejected'] and c['negative_work']==dict(expected,ftran=5,primal_rhs=2) for c in subjects)
checks['selected_endpoints_equal']=all(all(c['original'][k]==next(z for z in cs if z['scalar']==c['scalar'] and z['manager']==c['manager'] and not z['subject'])['original'][k] for k in ['basis','states','primal','rho','iterations','refactorizations','factor']) for c in subjects)
checks['assertions_pass']='Test Failed' not in log and 'Error During Test' not in log and 'S6-AB phase reconstruction boundary' in log
old=json.loads((d/'results/S6-AA/green-1-pins.json').read_text());shared=[k for k in old['inventory'] if k in pins['inventory'] and ('/src/' in k or '/test/' in k or k.endswith(('Project.toml','Manifest.toml','LocalPreferences.toml','julia.sh','/bin/julia')))];checks['source_runtime_environment_comparable']=all(old['inventory'][k]==pins['inventory'][k] for k in shared)
checks['user_hashes']=all(sha(Path('/home/jspitz/JSimplex.jl')/k)==v for k,v in json.loads(Path('/tmp/jsimplex-main-preserved.json').read_text()).items())
audit={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'shared_count':len(shared),'shared_paths':shared,'summary':log.splitlines()[-2:],'scope':'Declared phase-only output boundary on identity fixtures; successful forwarded calls logged. Copy unsupported. No historical CI private state/backend cause, exception-attempt accounting, hidden trajectory, observer neutrality, x64 or fullsuite proof.'}
with (out/(name+'-audit.json')).open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
for n in ('report.toml','process.json','pins.json','run.log'):shutil.copyfile(base/n,out/(name+'-'+n))
shutil.copyfile(d/'reproduce/phase_reconstruction_boundary.jl',out/(name+'-driver.jl'))
print(json.dumps({k:v for k,v in audit.items() if k!='shared_paths'},indent=2));assert audit['all_passed']
