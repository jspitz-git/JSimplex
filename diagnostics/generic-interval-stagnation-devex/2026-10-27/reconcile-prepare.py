from pathlib import Path
import sys,shutil,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-interval-stagnation-devex/2026-10-27');Q=D/'comparison-2'
s=(Q/'audit.py').read_text()
a=s.index("p=c.read('output/process.json')");b=s.index("data=tomllib.loads",a)
s=s[:a]+'''p=c.read('output/process.json');s=c.read('supervisor.json');contract=c.read('contract.json');log=(D/'output/run.log').read_text()
qual=D.parent/'correctness-qualification';qa=json.loads((qual/'audit.json').read_text());qr=json.loads((qual/'result-review.json').read_text())
c.need(qa['accepted'] is True and qa['assertions']==15213 and qr['accepted'] is True and qr['findings']==[],'independently qualified corrected correctness')
for r in [qa,qr]:
 for path,h in r['bindings'].items():c.need(c.sha(path)==h,'qualification binding '+path)
c.need(p['returncode']==1 and p['pins_unchanged'] is True and s['accepted'] is False and s['returncode']==1 and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s,'original rejected run preserved')
c.need(not any(s.get(k,False) for k in ['child_kill','guard_kill','guard_term']),'no forced numerical termination')
c.need(s['elapsed_seconds']<=600 and p['command']==contract['command'] and p['pins_sha256']==c.sha(D/'pins.json'),'bounded command/pins')
gate=c.read('output/gate.json');cur=c.read('output/current.json');permit=c.read('output/permit.json');reservation=c.read('reservation.json')
c.need(s['guard_identity']==p['runner']==gate['parent']==cur['runner'] and gate['identity']==p['child']==cur['child'],'all complete entry identities')
c.need(gate['command']==permit['command']==cur['command']==contract['command'] and gate['parent_death_signal']==9,'all entry command/signal')
c.need(gate['current_sha256']==permit['current_sha256']==c.sha(D/'output/current.json') and gate['permit_sha256']==c.sha(D/'output/permit.json'),'entry links')
c.need(reservation['guard_deadline']==reservation['started_monotonic']+592 and reservation['outer_deadline']==reservation['started_monotonic']+600,'frozen shared deadlines')
root_summary=re.search(r'^Interval setup Devex whole-function comparison\\s*\\|\\s*(\\d+)\\s+(\\d+)\\s+(\\d+)\\s+',log,re.M)
c.need(root_summary and [int(root_summary[i]) for i in [1,2,3]]==[55982,360,56342],'exact original rejected ordinary summary')
from collections import Counter
failures=Counter(int(x) for x in re.findall(r'Test Failed at .*fixtures.jl:(\\d+)',log));c.need(dict(failures)=={127:60,248:60,249:60,251:60,252:120},'only diagnosed oracle sites')
c.need('Error During Test' not in log,'no unexpected Test errors')
errors=re.findall(r'^ERROR:.*$',log,re.M);c.need(errors==['ERROR: LoadError: Some tests did not pass: 55982 passed, 360 failed, 0 errored, 0 broken.'],'only normal aggregate Test failure')
c.need('INTERVAL_SETUP_DEVEX_COMPARISON_COMPLETE' not in log,'do not retroactively invent failed-run completion')
''' +s[b:]
s=s.replace("c.put('summary.json'","c.put('summary-reconciled.json'").replace("c.put('audit.json'","c.put('audit-reconciled.json'").replace("c.read('audit.json')","c.read('audit-reconciled.json')").replace("assertions=int(root_summary[1])","assertions=qa['assertions'],original_run_accepted=False,raw_original_passes=55982,raw_original_failures=360,qualification_assertions=15213,measurement_rerun=False").replace("done['elapsed_shared_seconds']","s['elapsed_seconds']").replace("'summary.json','audit.py'","'summary-reconciled.json','audit-reconciled.py'")
s=s.replace("str(D/n):c.sha(D/n) for n in", "str(D/n):c.sha(D/n) for n in")
# Add exact qualification linkage to the accepted cost-data record; no raw file changes.
s=s.replace("bindings={str(D/n):c.sha(D/n) for n in ['output/results.toml','output/run.log','output/process.json','pins.json','summary-reconciled.json','audit-reconciled.py']}","bindings={**{str(D/n):c.sha(D/n) for n in ['output/results.toml','output/run.log','output/process.json','pins.json','summary-reconciled.json','audit-reconciled.py']},**{str(qual/n):c.sha(qual/n) for n in ['audit.json','result-review.json','fixtures.jl','pins-reviewed.json']}}")
ast.parse(s);(Q/'audit-reconciled.py').write_text(s);shutil.copyfile(__file__,D/'reconcile-prepare.py');print('new post-exit costdata auditor prepared, unexecuted; not a launch pin')
