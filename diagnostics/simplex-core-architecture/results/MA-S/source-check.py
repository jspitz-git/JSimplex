from pathlib import Path
import ast,json,hashlib,tomllib
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/MA-S';RD=E.parent/'MA-R'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
driver=(E/'driver.jl').read_text();launcher=(E/'launcher.py').read_text();audit=(E/'audit.py').read_text();cmd=json.loads((E/'commands.json').read_text());spec=tomllib.loads((RD/'fixtures.toml').read_text());checks={}
for n in ['launcher.py','audit.py','guard.py','prepare-pins.py','offline-tests.py','source-check.py']:ast.parse((E/n).read_text())
checks['python_syntax_only']=True
checks['52cases_36targets_16controls']=len(spec['cost_cases'])==52 and sum(c['eligible'] for c in spec['cost_cases'])==36
checks['three_exact_commands']=len(cmd)==3 and all(c[-2:]==[str(i),str(E/f'run-{i}')] and '--project='+str(RD/'environment') in c and '--compiled-modules=existing' in c and c[-3]==str(E/'driver.jl') for i,c in ((i,cmd[str(i)]) for i in (1,2,3)))
checks['RED_before_candidate_include']=driver.index('raw["red"]=red()')<driver.index('Base.include(P,joinpath(RD,"candidate.jl"))')
checks['no_extra_cost_first_calls']='for _ in 1:4' in driver and 'for pair in 1:10' in driver and 'reference_smoke()' in driver and driver.count('TST.qualification()')==1 and 'f(x.dest,x.backend,x.rhs)' in driver
checks['exact_R_sources']=all(sha(p)==s for p,s in json.loads((RD/'publication.json').read_text())['sha256'].items() if '/results/MA-R/' in p)
checks['no_old_execution_import']='import audit' in launcher and 'MA-P' not in launcher and 'MA-P' not in driver and 'MA-P' not in audit
checks['separate_seal_required']='numerical-review.json' in launcher and 'launch-context.json' in launcher and launcher.index('validate_admission(pins,required,prep,seal,context)')<launcher.index("save(D/'sequence-reservation.json'")
checks['one_exclusive_sequence']="Path(p).open('x')" in launcher and "save(D/'sequence-reservation.json'" in launcher and 'total<=360' in launcher
checks['source_budget_arithmetic']=52*3*20*4==12480 and 160*3+2*3+2==488 and 162+52*3==318
checks['offline36_pass']=len(json.loads((E/'offline-tests.json').read_text())['checks'])==36 and json.loads((E/'offline-tests.json').read_text())['all_passed'] is True
checks['six_previous_bindings']=all(sha(x['preserved'])==x['sha256'] for x in json.loads((E/'continuation-map.json').read_text())['old_bindings'])
files=[E/n for n in ['driver.jl','launcher.py','audit.py','guard.py','commands.json','admission.md','pins.json','required-paths.json','offline-tests.json','preparation-check.json','source-check.py']]
obj=dict(checks=checks,all_passed=all(checks.values()),sha256={str(p):sha(p) for p in files},scope='Fresh Python AST/literal checks only. No Julia parser or numerical/launcher execution. Not proof of Julia runtime validity.')
with (E/'source-check.json').open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'bindings':len(files)}))
if not obj['all_passed']:raise SystemExit(1)
