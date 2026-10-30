"""Future one admitted cost phase; canonical failure auditing always attempted."""
import sys,os,time,traceback
from pathlib import Path
import common as C
import binding_checks as B
import audit
def main(phase,admission_path):
 C.phase_ok(phase);r=C.out(phase);seal=C.read(r/'seal.json');pins=C.read(r/'pins.json')
 B.interpreter(seal,pins,sys.executable)
 C.require(Path(audit.__file__).resolve()==(C.D/'audit.py').resolve(),'wrong auditor')
 C.ensure_unused(phase);ad=C.validate_admission(seal,pins,admission_path,C.git('rev-parse','HEAD'),phase)
 C.require(seal['environment']==C.environment(phase),'environment changed')
 used,facts=C.prior(phase);C.require(seal['used_seconds']==used and seal['previous']==facts and seal['remaining_seconds']==1800-used,'prior time/evidence changed')
 C.check_inventory(pins,C.required_paths(phase));C.driver_ready();h=C.host();B.head(seal,ad,h['refs']['HEAD']);C.fresh(r/'prelaunch-host.json',h)
 C.require(not os.environ.get('LD_PRELOAD') and not os.environ.get('LD_AUDIT'),'loader injection')
 for k in list(os.environ):
  if k.startswith('JULIA_'):del os.environ[k]
 os.environ.update(seal['environment'])
 sys.path.insert(0,str(C.D/'guard'));import supervisor_reviewed as S
 remaining=1800-used;C.require(remaining>20,'no cleanup budget')
 started=time.monotonic()
 C.fresh(r/'attempt.json',dict(phase=phase,started_monotonic=started,remaining_seconds=remaining,admission_path=str(Path(admission_path).resolve()),admission_sha256=C.sha(admission_path),seal_sha256=C.sha(r/'seal.json'),runner=C.identity(os.getpid())))
 command=C.guard_command(seal,started,phase);C.fresh(r/'invocation.json',dict(command=command,cwd=str(C.D),environment=seal['environment']))
 result=dict(accepted=False,error='supervisor did not return')
 try:
  with (r/'guard.log').open('x') as log:result=S.run(command,log,str(r/'guard'),started,remaining-4)
 except Exception:C.fresh(r/'launcher-error.json',dict(accepted=False,traceback=traceback.format_exc()))
 C.fresh(r/'supervisor.json',result)
 try:post=C.host();B.head(seal,ad,post['refs']['HEAD'])
 except Exception:post=dict(conflicts=['postflight failed'],error=traceback.format_exc())
 C.fresh(r/'postflight.json',post)
 elapsed=time.monotonic()-started;C.fresh(r/'completion.json',dict(elapsed_inclusive_seconds=elapsed,total_inclusive_seconds=used+elapsed,limit_seconds=1800,supervisor_accepted=result.get('accepted') is True))
 accepted=audit.main(phase)
 C.require(accepted and result.get('accepted') is True and used+elapsed<=1800,'cost phase rejected; audit/raw preserved')
 print('Completed and audited',phase,'standalone full closure still required')
if __name__=='__main__':
 C.require(len(sys.argv)==3,'phase and numerical admission required');os.chdir(C.D);main(sys.argv[1],sys.argv[2])
