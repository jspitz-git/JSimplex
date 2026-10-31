from pathlib import Path
import shutil,json,hashlib,ast
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');A=W/'diagnostics/devex-saved-runtime/2026-10-31';D=A.with_name('2026-10-31-reviewed');D.mkdir(exist_ok=False)
for name in ('driver.jl','common.py','launch.py','audit.py','seal.py','PLAN.md','contract.json','initial-host.json','baseline-host.json'):
 shutil.copyfile(A/name,D/name)
shutil.copytree(A/'guard',D/'guard')
s=(D/'driver.jl').read_text();needle='stats(t)=Dict("seconds"=>t.time';assert s.count(needle)==1
(D/'driver.jl').write_text(s.replace(needle,'stats(t)=Dict{String,Any}("seconds"=>t.time'))
c=json.loads((D/'contract.json').read_text());c['command']=[v.replace(str(A),str(D)) for v in c['command']];(D/'contract.json').write_text(json.dumps(c,indent=2)+'\n')
p=(D/'PLAN.md').read_text();p+='\n## Separately sealed prelaunch correction\nInitial admission rejected a numeric-valued stats dictionary before any Julia. ONLY stats return storage is explicitly Dict{String,Any}; numerical calls/assertions/order/options unchanged. Seven inner and one outer explicit GC per case give48 GC calls total (42 inside run_case plus6 outer). All are outside timed constructor windows. Initial driver/seal107pins/rejected review remain frozen. No numerical retry consumed.\n';(D/'PLAN.md').write_text(p)
shutil.copyfile('/tmp/devex-saved-runtime-numerical-admission.md',D/'REVIEW-INITIAL.md');shutil.copyfile('/tmp/devex-saved-runtime-numerical-admission.json',D/'review-initial.json')
old=json.loads((A/'pins.json').read_text())['inventory'];checks={}
for n,v in old.items():
 with open(n,'rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 if h!=v['sha256']:raise RuntimeError(n)
checks['all107_initial_bindings_unchanged']=True
checks['exact_one_dictionary_storage_change']=(D/'driver.jl').read_text().replace('stats(t)=Dict{String,Any}("seconds"=>t.time',needle)==(A/'driver.jl').read_text()
checks['initial_attempt_absent']=not (A/'run-1').exists()
checks['GC_accounting_corrected']=True
for name in ('common.py','launch.py','audit.py','seal.py'):ast.parse((D/name).read_text());checks[name+'_byteexact']= (D/name).read_bytes()==(A/name).read_bytes()
assert all(checks.values());(D/'source-fix-check.json').write_text(json.dumps(dict(accepted=True,checks=checks),indent=2)+'\n')
shutil.copyfile(__file__,D/'prepare-reviewed.py')
print(D)
