import time
LAUNCH_STARTED=time.monotonic()
import sys
from common_ready2 import *
def main():
 start=LAUNCH_STARTED
 a=read('admission.json');need(a['accepted'] is True and a['findings']==[],'independent admission')
 for n,v in a['bindings'].items():need(sha(n)==v,'admission binding '+n)
 unchanged();put('launch-host.json',host())
 need(not (D/'output').exists() and not (D/'reservation.json').exists(),'exclusive attempt')
 sys.path.insert(0,str(D/'guard'));import supervisor_reviewed as supervisor
 c=read('contract-ready.json');deadline=start+592;need(time.monotonic()<deadline,'prelaunch budget exhausted')
 put('reservation.json',dict(attempt=1,started_monotonic=start,guard_deadline=deadline,outer_deadline=start+600,limit_seconds=600,pins_sha256=sha(D/'pins-ready2.json'),admission_sha256=sha(D/'admission.json')))
 unchanged();need(time.monotonic()<deadline,'prelaunch remaining budget')
 cmd=[sys.executable,'-B',str(D/'guard/guard_reviewed.py'),'run',str(D/'pins-ready2.json'),str(D/'output'),'--expected-exit',str(c['expected_exit']),'--seconds',str(deadline-time.monotonic()),'--deadline',str(deadline),'--',*c['command']]
 put('invocation.json',dict(command=cmd,Julia_command=c['command'],common_started=start,guard_deadline=deadline,outer_deadline=start+600))
 with (D/'guard.log').open('x') as log:r=supervisor.run(cmd,log,str(D/'output'),start,600)
 put('supervisor.json',r);need(r['accepted'] is True,'guard/supervisor failed; preserve records')
 p=read('output/process.json');extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']]
 put('host-after.json',host(extra));unchanged()
 elapsed=time.monotonic()-start;need(elapsed<=600,'inclusive600deadline')
 put('completed.json',dict(accepted=True,elapsed_shared_seconds=elapsed,limit_seconds=600,pins_unchanged=True))
 need(time.monotonic()-start<=600,'publication deadline')
 print(json.dumps(dict(accepted=True,elapsed=elapsed,child_exit=p['returncode'],pins_unchanged=p['pins_unchanged'])))
if __name__=='__main__':main()
