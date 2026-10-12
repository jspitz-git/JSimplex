from pathlib import Path
import json,tomllib,hashlib,sys,importlib.util,shutil
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';out=d/'results/S6-Z';name=sys.argv[1];base=root/'.superpowers/simplex-core-architecture/S6-Z'/name
r=tomllib.loads((base/'report.toml').read_text());p=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());source=(root/'test/native_phase_transfer_tests.jl').read_text()
spec=importlib.util.spec_from_file_location('g',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
helper='function artificial_exchange_roundoff_fixture'+source.split('function artificial_exchange_roundoff_fixture',1)[1].split('\n@testset',1)[0]
oldmatrix='A=sparse(T[8 -2 0 1 -3 2; 2 6 1 2 -2 -2; 1 -2 3 0 -1 3;\n               3 -1 0 5 -2 -2; 0 0 -1 0 6 -3; 0 0 -1 -2 -1 8])'
newhelper=helper.replace('artificial_exchange_roundoff_fixture','reliable_exchange_fixture').replace(oldmatrix,'A=sparse(Matrix{T}(I,6,6))')
marker='@testset "Reliable artificial exchanges need no reconstruction recovery" begin';original=marker+source.split(marker,1)[1].split('\n@testset',1)[0]
expected=original.replace('artificial_exchange_roundoff_fixture','reliable_exchange_fixture').replace('JSimplex.SimplexDiagnostics()','JSimplex.SimplexDiagnostics(;kernel_timing=true)').replace('JSimplex.remove_artificials!','observed_remove!')
checks={'exit0':p['returncode']==0 and p['reason']=='exit0','guard_pins':p['pins_unchanged'] and g.pins_match(pins),'independent_pins':all(sha(k)==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'actual_source':r['source']==str(root/'src/JSimplex.jl'),'test_source':r['test_sha256']==sha(root/'test/native_phase_transfer_tests.jl'),'original_helper':r['helper']==helper,'only_helper_matrix_and_name_changed':r['qualified_helper']==newhelper,'original_four_assertions':r['original_oracle']==original,'only_target_call_and_count_routing':r['executed_oracle']==expected,'threads':r['julia_threads']==r['blas_threads']==1,'globals':r['globals_preserved']}
paths=set(pins['files'])
for t in pins['trees']:paths.update(str(v) for v in Path(t).rglob('*') if v.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
cs=r['records'];managers={'pfi','forrest_tomlin','suhl_suhl','bartels_golub'};checks['four_cases']=len(cs)==4 and {c['manager'] for c in cs}==managers
x=tomllib.loads((d/'results/S6-X/census-1-report.toml').read_text());controls={c['manager']:c for c in x['records'] if c['scalar']=='Float32' and c['max_refinements']==0}
checks['same_options_policy']=all(c['options']==controls[c['manager']]['options'] and c['policy']==controls[c['manager']]['policy'] for c in cs)
checks['identity_original_matrix']=all(c['before_original']['colptr']==list(range(1,8)) and c['before_original']['rowval']==list(range(1,7)) and c['before_original']['nzval']==[1]*6 for c in cs)
checks['identity_auxiliary_duplicate']=all(c['before_phase']['colptr']==list(range(1,9)) and c['before_phase']['rowval']==list(range(1,7))+[6] and c['before_phase']['nzval']==[1]*7 for c in cs)
checks['initial_basis_point_mapping']=all(c['before_phase']['basis']==[1,2,3,4,5,7] and c['before_phase']['primal']==[1,1,0,0,0,0,0,1,1,0,0,0,0] and c['original_to_phase']==[1,2,3,4,5,6,8,9,10,11,12,13] and c['phase_to_original']==[1,2,3,4,5,6,0,7,8,9,10,11,12] and c['artificials']==[7] for c in cs)
checks['all_accepted']=all(c['accepted'] for c in cs)
checks['exact_original_basis_point']=all(c['after_original']['basis']==list(range(1,7)) and c['after_original']['primal']==[1,1,0,0,0,0,1,1,0,0,0,0] for c in cs)
checks['original_certificates']=all(c['post_original_certificate'] for c in cs)
checks['one_exchange_no_correction']=all(c['after_original']['iterations']==1 and c['counts'].get('artificial_removed',0)==1 and c['counts'].get('correction_attempt',0)==0 for c in cs)
checks['test_summary']='29     29' in (base/'run.log').read_text()
oldpins=json.loads((d/'results/S6-Y/components-1-pins.json').read_text());shared=[k for k in oldpins['inventory'] if k in pins['inventory'] and ('/src/' in k or '/test/' in k or k.endswith(('Project.toml','Manifest.toml','LocalPreferences.toml','julia.sh','/bin/julia')))];checks['shared_pins']=all(oldpins['inventory'][k]==pins['inventory'][k] for k in shared)
audit={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'shared_count':len(shared),'shared_paths':shared,'cases':[{'manager':c['manager'],'accepted':c['accepted'],'kernels':{k:v for k,v in c['kernels'].items() if v},'events':{k:v for k,v in c['counts'].items() if v},'before_work':{k:c['before_phase'][k] for k in ('iterations','refactorizations')},'after_phase_work':{k:c['after_phase'][k] for k in ('iterations','refactorizations')},'after_original_work':{k:c['after_original'][k] for k in ('iterations','refactorizations')}} for c in cs],'scope':'New reliable zero-budget fixture only, no old native roundoff recovery qualification or historical CI cause/x64 proof.'}
with (out/(name+'-audit.json')).open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
for n in ('report.toml','pins.json','process.json','run.log'):shutil.copyfile(base/n,out/(name+'-'+n))
for src,dst in [(d/'reproduce/reliable_phase_exchange.jl','driver.jl'),(root/'test/native_phase_transfer_tests.jl','test.jl')]:shutil.copyfile(src,out/(name+'-'+dst))
print(json.dumps({k:v for k,v in audit.items() if k!='shared_paths'},indent=2));assert audit['all_passed']
