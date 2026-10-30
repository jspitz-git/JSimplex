import sys,os,time,traceback
from pathlib import Path
import common as C
import audit
C.require(len(sys.argv)==2,'admission required');c=C.read(C.D/'contract.json');seal=C.read(C.R/'seal.json');pins=C.read(C.R/'pins.json');C.unused();C.require(C.prior_time()==c['previous_seconds'],'actual prior time');C.verify_pins(pins);C.require(set(pins['files'])==set(C.paths()),'full source pin membership');C.require(Path(sys.executable).absolute()==Path(seal['guard_python']) and str(Path(sys.executable).resolve(strict=True))==pins['inventory'][str(Path(sys.executable).absolute())]['resolved'],'guard interpreter');a=C.admit(sys.argv[1],seal,pins);C.require(Path(audit.__file__).resolve()==(C.D/'audit.py').resolve(),'wrong auditor');C.fresh(C.R/'prelaunch-host.json',C.host());C.require(not os.environ.get('LD_PRELOAD') and not os.environ.get('LD_AUDIT'),'loader injection')
for k in list(os.environ):
 if k.startswith('JULIA_'):del os.environ[k]
os.environ.update(c['environment']);sys.path.insert(0,str(C.D/'guard'));import supervisor_reviewed as S
started=time.monotonic();C.fresh(C.R/'attempt.json',dict(started_monotonic=started,admission_path=str(Path(sys.argv[1]).resolve()),admission_sha256=C.sha(sys.argv[1]),seal_sha256=C.sha(C.R/'seal.json'),runner=C.identity(os.getpid())));cmd=C.guard_command(started);C.fresh(C.R/'invocation.json',dict(command=cmd,cwd=str(C.D),environment=c['environment']));result=dict(accepted=False,error='supervisor did not return')
try:
 with (C.R/'guard.log').open('x') as log:result=S.run(cmd,log,str(C.R/'guard'),started,c['remaining_seconds']-4)
except Exception:C.fresh(C.R/'launcher-error.json',dict(error=traceback.format_exc()))
C.fresh(C.R/'supervisor.json',result)
try:post=C.host()
except Exception:post=dict(conflicts=['postflight failed'],error=traceback.format_exc())
C.fresh(C.R/'postflight.json',post);elapsed=time.monotonic()-started;C.fresh(C.R/'completion.json',dict(elapsed_inclusive_seconds=elapsed,total_inclusive_seconds=c['previous_seconds']+elapsed,limit_seconds=1800,supervisor_accepted=result.get('accepted') is True));accepted=audit.main();C.require(accepted,'master verification rejected; raw preserved');print('MASTER VERIFIED AND AUDITED; standalone postexit closure required')
