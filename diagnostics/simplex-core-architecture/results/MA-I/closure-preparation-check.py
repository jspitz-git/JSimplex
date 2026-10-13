from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;F=D.parent/'MA-F-repair'
checks={}
a=(D/'whitespace.py').read_text();b=(D/'whitespace-2.py').read_text()
checks['only_exact_copy_and_fixed_list_change']=b==a.replace("'test-collector.jl','tests-instrumented.jl'","'test-collector.jl','tests-instrumented.jl','finite_oracle.py'").replace('publication-names.json','publication-names-final.json')
checks['oracle_byte_identical']=(D/'finite_oracle.py').read_bytes()==(F/'finite_oracle.py').read_bytes()
for n in ['closure','publication']:checks[n+'_only_new_fixed_list']=(D/(n+'-final.py')).read_text()==(D/(n+'.py')).read_text().replace('publication-names.json','publication-names-final.json')
checks['no_old_result_overwritten']=not (D/'closure.json').exists() and not (D/'publication.json').exists() and json.loads((D/'whitespace-failure.json').read_text())['exit_code']==1
checks['syntax']=all(compile((D/n).read_text(),str(D/n),'exec') is not None for n in ['whitespace-2.py','closure-final.py','publication-final.py'])
with (D/'closure-preparation-check.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,sha256={str(D/n):hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['whitespace.py','whitespace-2.py','whitespace-failure.json','finite_oracle.py','closure.py','closure-final.py','publication.py','publication-final.py','publication-names.json',Path(__file__).name]}),f,indent=2);f.write('\n')
print(checks)
if not all(checks.values()):raise SystemExit(1)
