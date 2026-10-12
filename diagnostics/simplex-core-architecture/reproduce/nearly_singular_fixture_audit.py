from pathlib import Path
import sys,json,tomllib,hashlib,importlib.util,re,shutil
sys.dont_write_bytecode=True
root=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');d=root/'diagnostics/simplex-core-architecture';name=sys.argv[1];project=Path(sys.argv[2]) if len(sys.argv)>2 else root;base=root/'.superpowers/simplex-core-architecture/S6-T'/name;out=d/'results/S6-T';out.mkdir(parents=True,exist_ok=True)
r=tomllib.loads((base/'report.toml').read_text());p=json.loads((base/'process.json').read_text());pins=json.loads((base/'pins.json').read_text());log=(base/'run.log').read_text();selected=r['selected_source'];mode=r['mode']
s=importlib.util.spec_from_file_location('g',d/'reproduce/guarded_run.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
checks={'process_exit':p['returncode']==(1 if mode=='red' else 0) and p['reason']==('exit1' if mode=='red' else 'exit0') and p['pins_unchanged'],'pins_guard':g.pins_match(pins),'pins_independent':all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()),'actual_source':r['source']==str(project/'src/JSimplex.jl'),'test_hash':r['test_sha256']==hashlib.sha256((project/'test/solver_tests.jl').read_bytes()).hexdigest(),'selected_hash':r['selected_sha256']==hashlib.sha256(selected.encode()).hexdigest(),'one_thread':r['julia_threads']==r['blas_threads']==1,'globals_preserved':r['globals_preserved']}
paths=set(pins['files'])
for t in pins['trees']:paths.update(str(v) for v in Path(t).rglob('*') if v.is_file())
checks['inventory_membership']=paths==set(pins['inventory'])
source=(project/'test/solver_tests.jl').read_text()
def extract(title):
 marker='@testset "'+title+'" begin'
 return marker+source.split(marker,1)[1].split('\n@testset',1)[0]
expected='\n'.join(extract(t) for t in r['titles'])
if mode=='red':expected=expected.split('    for T in (Float32, Float64, BigFloat, Rational{BigInt})',1)[0]+'end\n'
checks['exact_selected_source']=expected==selected
checks['no_test_errors']='Error During Test' not in log
if mode=='red':
 checks['no_solve']='solve(' not in selected and 'Loaded problem:' not in log
 checks['expected_structural_failures']=len(re.findall(r'Test Failed at',log))==4 and re.search(r'\|\s+2\s+4\s+6\s+',log) is not None and all(t in log for t in ['det(exact_coefficients)','sum(exact_coefficients','row_limits ==','exact_coefficients * exact_primal'])
else:
 checks['all_pass']='Test Failed' not in log and all(re.search(re.escape(t)+r'\s+\|\s+(\d+)\s+\1\s+',log) for t in r['titles'])
 checks['original_oracle_preserved']=all(t in selected for t in ['result = @inferred solve(problem)','@test result isa Solution{T}','@test result.status in (OPTIMAL, NUMERICAL_ERROR)','T <: Rational && @test result.status == OPTIMAL','@test result.objective_value == -T(big(2)^44)','@test isnothing(result.primal)','@test isnothing(result.objective_value)'])
 checks['six_structural_assertions']=all(t in selected for t in ['@test size(coefficients)','@test all(!iszero, coefficients)','@test det(exact_coefficients)','@test sum(exact_coefficients','@test row_limits ==','@test exact_coefficients * exact_primal'])
 if mode=='master':
  green=tomllib.loads((out/'green-1-report.toml').read_text());marker='@testset "'+r['titles'][0]+'" begin';body=marker+green['selected_source'].split(marker,1)[1].split('\n@testset',1)[0];checks['exact_green_testset']=body==selected
summary=[line for line in log.splitlines() if re.search(r'\|\s+\d',line)]
audit={'checks':checks,'all_passed':all(checks.values()),'pin_count':len(pins['inventory']),'summary':summary,'mode':mode,'scope':'Bounded new-source test repair checks; not full-suite/x64 proof or performance evidence.'}
with (out/(name+'-audit.json')).open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
for n in ['report.toml','process.json','pins.json','run.log']:shutil.copyfile(base/n,out/(name+'-'+n))
shutil.copyfile(project/'test/solver_tests.jl',out/(name+'-solver_tests.jl'))
shutil.copyfile(d/'reproduce/nearly_singular_fixture_repair.jl',out/(name+'-driver.jl'))
print(json.dumps(audit,indent=2));assert audit['all_passed']
