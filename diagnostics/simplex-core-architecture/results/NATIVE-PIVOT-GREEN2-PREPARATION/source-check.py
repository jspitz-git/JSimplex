"""One-shot bounded source/integrity checks; no Julia, seal, launch or old audit."""
from pathlib import Path
import json,hashlib,sys,ast,difflib
D=Path(__file__).resolve().parent;R=D.parents[3];Q=D.parent/'NATIVE-PIVOT-QUALIFICATION';F=D.parent/'NATIVE-PIVOT-OBSERVER-FIX';P=D.parent/'NATIVE-PIVOT-PREPARATION'
sys.path.insert(0,str(D));from control import predecessor,config,validate_environment
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,z):
 with (D/n).open('x') as f:json.dump(z,f,indent=2);f.write('\n')
checks={};m=rd(D/'source-map.json')
checks['seven_identical_dependencies']=all((D/n).read_bytes()==Path(p).read_bytes() for n,p in m['byte_identical'].items())
driver=(D/'test-driver.jl').read_text();old=(F/'test-driver-fixed.jl').read_text()
reverse=driver.replace('include(joinpath(@__DIR__,"regression-reviewed.jl"))\n','').replace('root=RecordedTests.Capture("root")\n    regression=RecordedTests.Capture("regression")\n    helper_calls=Ref(0)','root=RecordedTests.Capture("root")')
insert='''        raw["regression_counts_before"]=copy(NP.counts)
        Test.@with_testset regression begin
            DenseTokenRegression.run((format,v)->begin
                helper_calls[]+=1
                NP.dense_tokens(format,v)
            end,NP.scalar,NP.token)
        end
        raw["regression_counts_after"]=copy(NP.counts)
'''
reverse=reverse.replace(insert,'').replace('if phase=="green2"','if phase=="red"\n            include(joinpath(@__DIR__,"..","NATIVE-PIVOT-QUALIFICATION","red-contract.jl"))\n        elseif phase=="green"').replace('\n        raw["regression_tests"]=RecordedTests.dictionary(regression)\n        raw["regression_helper_calls"]=helper_calls[]','').replace('failed(root)==0 && failed(regression)==0 ? 0 : 1','failed(root)==0 ? 0 : 1')
checks['whole_driver_inverse']=reverse==old
checks['top_level_regression']=driver.index('include(joinpath(@__DIR__,"regression-reviewed.jl"))')<driver.index('function main()')
checks['119_separate_from6858']=rd(D/'budget.json')==rd(Q/'budget.json') and rd(D/'regression-budget.json')['total_assertions']==6977
checks['regression_counts_in_raw']=all(s in driver for s in ['"regression_tests"','"regression_helper_calls"','"regression_counts_before"','"regression_counts_after"'])
files,groups=predecessor('green2');checks['distinct_verified_predecessors']=len(groups)==212
manifest=rd(P/'overlay-manifest.json');entries=[e for arm in ['candidate','reference'] for e in manifest[arm]]
checks['candidate75_reference73_unchanged']=len(entries)==148 and all(sha(e['source'])==e['sha256'] for e in entries)
checks['no_new_stage_run']=not Path(config('green2')['stage']).exists() and not (D/'runs').exists()
validate_environment();checks['environment']=True
for p in D.glob('*.py'):ast.parse(p.read_text())
checks['python_syntax_only']=True
checks['new_python_RED_preserved']=rd(D/'offline-RED.json')['all_passed'] is False
checks['new_python_GREEN']=rd(D/'offline-GREEN.json')['all_passed'] is True
checks['seal_required_membership']="set(z['sha256'])==set(rd(D/'required-paths.json')['paths'])" in (D/'seal.py').read_text()
checks['unchanged_guard_caps']=config('green2')['seconds']==60 and (D/'guard.py').read_bytes()==(Q/'guard.py').read_bytes() and (D/'supervisor.py').read_bytes()==(Q/'supervisor.py').read_bytes()
checks['no_production_diff']=__import__('subprocess').check_output(['git','diff','--name-only','--','src','test','Project.toml','.github','diagnostics/direct-lu-markowitz/reproduce'],cwd=R)==b''
# Final delta replaces the initial unpinned preparation delta to include the required-list seal gate.
(D/'changes.diff').write_text(''.join(''.join(difflib.unified_diff(Path(p).read_text().splitlines(True),(D/n).read_text().splitlines(True),fromfile=p,tofile=str(D/n))) for n,p in m['originals'].items()))
put('config-preview.json',config('green2'))
inputs={D/n for n in ['source-check.py','source-map.json','changes.diff','test-driver.jl','test-support-fixed.jl','regression-reviewed.jl','budget.json','regression-budget.json','control.py','seal.py','launch.py','audit.py','oracle.py','common.py','offline-tests.py','offline-RED.json','offline-GREEN.json','ADMISSION.md','finalize.py','publication.py','continuation-text.md','config-preview.json']}|{Path(p) for p in m['originals'].values()}|{P/'overlay-manifest.json'}
put('source-check.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p):sha(p) for p in sorted(inputs)},scope='Offline source/schema integrity only; no Julia correctness or launch acceptance'))
if not all(checks.values()):raise RuntimeError(checks)
print(dict(checks=len(checks),bindings=len(inputs),all_passed=True))
