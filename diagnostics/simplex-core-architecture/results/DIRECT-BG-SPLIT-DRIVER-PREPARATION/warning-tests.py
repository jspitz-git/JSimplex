from pathlib import Path
import json
from oracle import warning_log,timeout_only
import control as c
D=Path(__file__).resolve().parent;checks={};phase='green300';loaded=c.loaded_for(c.config(phase));p=dict(reason='wall_time',returncode=-15,pins_unchanged=True);sup=dict(returncode=1,hard_timeout=False)
for i,token in enumerate(['Warning: bad','WARNING: bad','\x1b[33m┌ Warning: new binding\x1b[0m','world age mismatch','world-age mismatch']):
 log='BEGIN split BG driver '+phase+'\n'+token
 checks['warning_'+str(i)]=warning_log(log)
 checks['timeout_reject_'+str(i)]=not timeout_only(p,sup,None,log,299.,300,loaded,phase)
checks['clean_log']=not warning_log('BEGIN split BG driver green300\nEND lifecycles')
a=(D/'audit.py').read_text();checks['audit_warning_before_accept_or_timeout']=a.index("require(not warning_log(log)")<a.index('if pure:return')<a.index('result=test_results')
checks['no_runs']=not (D/'runs').exists()
with (D/'warning-tests.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,scope='New pure synthetic log tests, no process/Julia'),f,indent=2);f.write('\n')
if not all(checks.values()):raise RuntimeError(checks)
print('Warning/world-age controls PASS',len(checks))
