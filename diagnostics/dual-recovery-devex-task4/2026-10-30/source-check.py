from pathlib import Path
import hashlib,json,ast,subprocess,re
D=Path(__file__).resolve().parent;W=D.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def req(v,m):
 if not v:raise RuntimeError(m)
s=json.loads((D/'staging.json').read_text());checks={}
checks['all165_copies_exact']=len(s['bindings'])==165 and all(sha(Path(n))==v['sha256']==sha(Path(v['source'])) for n,v in s['bindings'].items())
checks['reference_source_exact_master']=all((D/'overlays/reference'/p.relative_to(W)).read_bytes()==subprocess.check_output(['git','-C',str(W),'show','c0fa748ffa61ccb7c1caaf248c40324f60bc737b:'+str(p.relative_to(W))]) for p in (W/'src').rglob('*.jl'))
a=D/'overlays/reference/src';b=D/'overlays/candidate/src';changed=sorted(p.name for p in a.rglob('*.jl') if p.read_bytes()!=(b/p.relative_to(a)).read_bytes());checks['exact_three_candidate_source_files']=changed==['simplex_numerics.jl','simplex_pivot.jl','simplex_recovery.jl']
checks['seven_regressions_exact_master']=all((D/'tests'/n).read_bytes()==subprocess.check_output(['git','-C',str(W),'show','c0fa748ffa61ccb7c1caaf248c40324f60bc737b:test/'+n]) for n in s['regressions'])
checks['python_syntax']=True
for n in ('common.py','seal.py','launch.py','audit.py','offline_tests.py'):ast.parse((D/n).read_text(),filename=n)
c=json.loads((D/'contract.json').read_text());checks['four_phases_1800']=len(c['phases'])==c['maximum_processes']==4 and c['total_seconds']==1800
checks['red8_with_sole_behavioral_failure']=len(re.findall(r'^\s*@test(?!set)',(D/'red.jl').read_text(),re.M))==8 and 'recovery_ready === true # EXPECTED_RED' in (D/'red.jl').read_text()
checks['no_custom_Test_recorder']=all(x not in (D/'green.jl').read_text()+(D/'red.jl').read_text() for x in ('record(','push_testset','pop_testset','get_test_counts'))
checks['ordinary_exact_include_order']=re.findall(r'^    include\("([^\"]+)"\)',(D/'green.jl').read_text(),re.M)==c['green_includes']
checks['endpoint46_assertions']=len(re.findall(r'^\s*@test(?!set)',(D/'endpoint.jl').read_text().split('function run_case',1)[1].split('\nfunction run(path)',1)[0],re.M))*2==c['green']['endpoint_assertions']==46
checks['cost80_calls_272_assertions']=c['cost']['api_calls_per_side']==8*(3+7) and c['cost']['assertions_per_side']==8*(3*2+7*4)==272
checks['no_numerical_output_or_admission']=not (W/'.superpowers/dual-recovery-devex-task4/qualification-1').exists() and not (D/'numerical-admission.json').exists()
f=json.loads((D/'offline-final.json').read_text());checks['offline_tests_accepted_and_bound']=f['accepted'] and all(sha(Path(n))==h for n,h in f['bindings'].items())
pins=json.loads((D/'source-pins.json').read_text());checks['all81_preparation_pins']=all(sha(Path(n))==h for n,h in pins['bindings'].items())
checks['actual_src_test_unchanged']=not subprocess.check_output(['git','-C',str(W),'diff','HEAD','--','src','test','Project.toml','.github'],text=True).strip()
checks['scope_preparation_only']='PREPARATION ONLY' in (D/'ADMISSION-PREPARATION.md').read_text()
bindings=dict(pins['bindings']);bindings.update({str(p):sha(p) for p in D.rglob('*') if p.is_file() and p.name!='source-check.json'})
r=dict(accepted=all(checks.values()),scope='offline source/copy/budget checks only, no Julia/guard/launcher',checks=checks,bindings=bindings)
with (D/'source-check.json').open('x') as out:json.dump(r,out,indent=2);out.write('\n')
print(json.dumps(dict(accepted=r['accepted'],checks=checks,bindings=len(bindings))))
req(r['accepted'],'source check failed')
