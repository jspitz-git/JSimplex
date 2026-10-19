"""One explicit RED300 invocation after exact admission and release. No auto retry."""
from pathlib import Path
import sys,os,time,runpy,traceback
Q=Path(__file__).resolve().parent
D=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER');sys.path.insert(0,str(D))
import control as c
PHASE='red300';RUN=D/'runs'/PHASE

def valid_release(v,seal_sha,review_sha,identity_sha):
 return type(v) is dict and v==dict(phase=PHASE,sealed_sha256=seal_sha,admission_sha256=review_sha,outer_ready_sha256=identity_sha,one_attempt=True)

def main():
 os.chdir(c.R)
 identity=c.guard.process_identity(os.getpid())
 c.require(identity['pid']==identity['pgid']==identity['sid'],'Outer must own isolated group/session')
 c.require(not (Q/'release.json').exists() and not (Q/'outer-ready.json').exists(),'Existing outer run/release')
 c.save(Q/'outer-ready.json',dict(identity=identity,script_sha256=c.sha(__file__),waiting_only=True,phase=PHASE,expected_launcher=str(D/'launch.py'),ready_time=time.time()))
 print('OUTER READY: waiting for independently accepted exact admission and explicit release',flush=True)
 deadline=time.monotonic()+1200
 while not (Q/'release.json').exists():
  if time.monotonic()>=deadline:
   c.save(Q/'outer-outcome.json',dict(launched=False,reason='admission wait expired',identity=identity));return 2
  time.sleep(.2)
 sp=RUN/'sealed.json';rp=RUN/'admission.json';s=c.rd(sp);v=c.rd(rp)
 c.require(valid_release(c.rd(Q/'release.json'),c.sha(sp),c.sha(rp),c.sha(Q/'outer-ready.json')),'Release binding')
 c.verify_review(v,sp,s['files']+[str(sp)],'BG specialization exact-stage admission',PHASE)
 c.require(c.guard.process_identity(os.getpid())==identity and s['outer_identity']==identity,'Outer identity drift')
 c.require(c.guard.pins_match(s),'Sealed inputs changed')
 c.save(Q/'outer-invocation.json',dict(identity=identity,phase=PHASE,seal_sha256=c.sha(sp),review_sha256=c.sha(rp),release_sha256=c.sha(Q/'release.json'),launcher_sha256=c.sha(D/'launch.py'),method='runpy.run_path unchanged launch.py as __main__ in this outer process'))
 started=time.monotonic();code=0;error=''
 try:
  sys.argv=[str(D/'launch.py'),PHASE]
  runpy.run_path(str(D/'launch.py'),run_name='__main__')
 except BaseException as e:
  code=e.code if isinstance(e,SystemExit) and isinstance(e.code,int) else 2
  error=''.join(traceback.format_exception(e));print(error,flush=True)
 finally:
  c.save(Q/'outer-outcome.json',dict(identity=identity,launched=True,returncode=code,error=error,elapsed_with_checks_seconds=time.monotonic()-started,scope='Outer time includes immutable pre/post checks and auditor; not benchmark or numerical guard duration'))
 return code
if __name__=='__main__':sys.exit(main())
