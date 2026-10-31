import os,sys,time,traceback
from pathlib import Path
import common as C
C.require(len(sys.argv)==2,'specific admission required');a=C.read(sys.argv[1]);c=C.read(C.D/'contract.json');seal=C.read(C.D/'seal.json')
C.require(a['accepted'] is True and a['scope']=='numerical_admission' and a['master']==c['master'] and a['seal_sha256']==C.sha(C.D/'seal.json') and a['pins_sha256']==C.sha(C.D/'pins.json'),'admission mismatch')
C.require(a['checks'] and all(v is True for v in a['checks'].values()),'admission checks');C.require(all(C.sha(p)==h for p,h in a['bindings'].items()),'review bindings changed');C.require(C.pins_ok(),'pins');C.require(not C.R.exists(),'attempt consumed')
C.R.mkdir();(C.R/'results').mkdir();C.fresh(C.R/'preflight.json',C.host());C.require(not os.environ.get('LD_PRELOAD') and not os.environ.get('LD_AUDIT'),'loader injection')
for name in list(os.environ):
 if name.startswith('JULIA_'):del os.environ[name]
os.environ.update(c['environment']);sys.path.insert(0,str(C.D/'guard'));import supervisor_reviewed as S
start=time.monotonic();C.fresh(C.R/'attempt.json',dict(runner=C.identity(os.getpid()),started_monotonic=start,admission=str(Path(sys.argv[1]).resolve()),admission_sha256=C.sha(sys.argv[1])))
cmd=[sys.executable,'-B',str(C.D/'guard/guard_reviewed.py'),'run',str(C.D/'pins.json'),str(C.R/'guard'),'--expected-exit','0','--seconds','1788','--deadline',str(start+1788),'--',*c['command']]
C.fresh(C.R/'invocation.json',dict(command=cmd,cwd=str(Path.cwd()),environment=c['environment']))
result=dict(accepted=False,error='supervisor did not return')
try:
 with open(C.R/'guard.log','x') as log:result=S.run(cmd,log,str(C.R/'guard'),start,1796)
except Exception:C.fresh(C.R/'launcher-error.json',dict(error=traceback.format_exc()))
C.fresh(C.R/'supervisor.json',result);C.fresh(C.R/'completion.json',dict(elapsed_inclusive_seconds=time.monotonic()-start,limit_seconds=1800,supervisor_accepted=result.get('accepted') is True))
try:C.fresh(C.R/'postflight.json',C.host(defer_self=True))
except Exception:C.fresh(C.R/'postflight-error.json',dict(error=traceback.format_exc()))
import audit
ok=audit.main();print('SAVED BASIS RUN ACCEPTED' if ok else 'SAVED BASIS RUN REJECTED; raw preserved')
raise SystemExit(0 if ok else 1)
