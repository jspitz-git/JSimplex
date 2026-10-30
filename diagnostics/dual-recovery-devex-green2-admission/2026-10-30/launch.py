"""Future single GREEN2 process; admission/guard/auditor are fail closed."""
import os,sys,time,traceback
from pathlib import Path
import common as C
import binding_checks as B
import audit # intended local module loaded BEFORE guard sys.path insertion
def main(admission_path):
 out=C.OUT;seal=C.read(out/'seal.json');pins=C.read(out/'pins.json')
 B.interpreter(seal,pins,sys.executable)
 C.require(Path(audit.__file__).resolve()==(C.D/'audit.py').resolve(),'wrong auditor source')
 C.ensure_unused(out);ad=C.validate_admission(seal,pins,admission_path,C.git('rev-parse','HEAD'))
 C.require(seal['environment']==C.environment() and seal['remaining_seconds']==C.TOTAL-seal['used_seconds'],'environment/remaining')
 used,facts=C.prior();C.require(seal['used_seconds']==used==C.USED and seal['previous']==facts,'prior changed/reset')
 C.check_inventory(pins,C.required_paths(),C.expected_inputs());C.fixtures()
 h=C.host();B.head(seal,ad,h['refs']['HEAD']);C.fresh(out/'prelaunch-host.json',h)
 C.require(not os.environ.get('LD_PRELOAD') and not os.environ.get('LD_AUDIT'),'unexpected loader injection')
 for key in list(os.environ):
  if key.startswith('JULIA_'):del os.environ[key]
 os.environ.update(seal['environment'])
 sys.path.insert(0,str(C.D/'guard'));import supervisor_reviewed as S
 remaining=C.TOTAL-used;C.require(remaining>20,'inclusive cleanup budget')
 started=time.monotonic()
 C.fresh(out/'attempt.json',dict(phase='green2',started_monotonic=started,remaining_seconds=remaining,admission_path=str(Path(admission_path).resolve()),admission_sha256=C.sha(admission_path),seal_sha256=C.sha(out/'seal.json'),runner=C.identity(os.getpid())))
 command=C.guard_command(seal,started)
 C.fresh(out/'invocation.json',dict(command=command,cwd=str(C.D),environment=seal['environment']))
 result=dict(accepted=False,error='supervisor did not return')
 try:
  with (out/'guard.log').open('x') as log:result=S.run(command,log,str(out/'guard'),started,remaining-4)
 except Exception:
  C.fresh(out/'launcher-error.json',dict(accepted=False,traceback=traceback.format_exc()))
 C.fresh(out/'supervisor.json',result)
 try:post=C.host();B.head(seal,ad,post['refs']['HEAD'])
 except Exception:post=dict(conflicts=['postflight failed'],error=traceback.format_exc())
 C.fresh(out/'postflight.json',post)
 elapsed=time.monotonic()-started
 C.fresh(out/'completion.json',dict(elapsed_inclusive_seconds=elapsed,total_inclusive_seconds=used+elapsed,limit_seconds=1800,supervisor_accepted=result.get('accepted') is True))
 # Always attempt a canonical REJECTION record on failure; never bypass checks.
 accepted=audit.main()
 C.require(accepted and result.get('accepted') is True and used+elapsed<=1800,'GREEN2 rejected; preserved audit/raw')
 print('Completed and audited GREEN2; independent postexit result review still required')
if __name__=='__main__':
 C.require(len(sys.argv)==2,'one numerical admission file required');os.chdir(C.D);main(sys.argv[1])
