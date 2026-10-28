from pathlib import Path
import sys,json,shutil,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');sys.path.insert(0,str(D));import common_qualified as c
p=c.read('output/process.json');extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];c.put('failed-close-host.json',c.host(extra));c.unchanged()
s=(D/'audit-qualified.py').read_text().replace("put('audit-invoker.json'","put('prefix-audit-invoker.json'")
s=s.replace("con=read('contract-qualified.json');p=", "con=dict(read('contract-qualified.json'),cases=1196,measured_windows=21528);p=")
s=s.replace("need(p['returncode']==0 and p['pins_unchanged'] is True,'successful child and pins')","need(p['returncode']==1 and p['pins_unchanged'] is True,'preserved failed child and unchanged pins')")
s=s.replace("need(sup['accepted'] is True and sup['returncode']==0 and not sup['soft_timeout'] and not sup['hard_timeout'] and 'cleanup_error' not in sup,'successful guard supervisor')","need(sup['accepted'] is False and sup['returncode']==1 and not sup['soft_timeout'] and not sup['hard_timeout'] and 'cleanup_error' not in sup,'failed Test exit, no timeout or cleanup error')")
s=s.replace("need(sup['elapsed_seconds']<=900 and read('completed.json')['accepted'] is True,'inclusive900completed')","need(sup['elapsed_seconds']<=900 and not (D/'completed.json').exists(),'failed attempt remains incomplete')")
a=s.index(" need(not re.search(r'Test Failed");b=s.index(" raw=tomllib.loads",a)
s=s[:a]+''' need(log.count('Test Failed at ')==1 and log.count('Error During Test at ')==2,'exact preserved failure/error counts')
 need('fixtures.jl:162' in log and 'precision(::Type{Rational{BigInt}})' in log,'unsupported baseline rational route')
 header=next(x for x in log.splitlines() if x.startswith('Test Summary:') and '|' in x);need(header.split('|',1)[1].split()==['Pass','Fail','Error','Total','Time'],'failed root schema')
 line=next(x for x in log.splitlines() if x.startswith('Epsilon bound auxiliary whole-function comparison') and '|' in x);cols=line.split('|',1)[1].split()
 need(cols[:4]==['55626','1','2','55629'] and len(cols)==5,'exact failed original counts');assertions=55629
 need('EPSILON_BOUND_AUXILIARY_COMPLETE' not in log,'no successful completion claim')
'''+s[b:]
s=s.replace("grid=read('expected-cases.json');","grid=read('expected-cases.json')[:1196];")
s=s.replace('len(grid)+38','len(grid)+36').replace('len(contexts)==19','len(contexts)==18')
s=s.replace("put('audit-host.json'","put('prefix-audit-host.json'").replace("put('summary.json'","put('summary-prefix.json'").replace("put('audit.json'","put('audit-prefix.json'").replace("read('audit.json')","read('audit-prefix.json')")
s=s.replace("dict(accepted=True,assertions=assertions", "dict(accepted=True,scope='completed-prefix-only; original attempt remains failed',original_root_passed=55626,original_root_failed=1,original_root_errors=2,original_attempt_accepted=False,assertions=assertions")
s=s.replace("elapsed_shared_seconds=read('completed.json')['elapsed_shared_seconds']","failed_supervisor_elapsed_seconds=sup['elapsed_seconds']")
s=s.replace("['audit-qualified.py','contract-qualified.json','pins-qualified.json','output/results.toml','output/run.log','output/process.json','summary.json','audit-invoker.json']","['audit-prefix.py','audit-qualified.py','contract-qualified.json','pins-qualified.json','output/results.toml','output/run.log','output/process.json','summary-prefix.json','prefix-audit-invoker.json','supervisor.json']")
ast.parse(s);(D/'audit-prefix.py').write_text(s);shutil.copyfile(__file__,D/'prefix-prepare.py')
print('Fresh677groups+sessions/noJulia and unchanged1273 pins; strict completed-prefix auditor prepared')
