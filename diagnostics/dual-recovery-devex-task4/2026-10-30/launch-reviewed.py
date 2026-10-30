"""One future reviewed phase; shared 1800s incl. guards. No import side effects."""
import sys,os,time,subprocess
from pathlib import Path
import common as C
import binding_checks as B
import audit_reviewed as audit

def main(phase,admission_path):
 C.phase_ok(phase);out=C.RUN/phase;seal=C.read(out/'seal.json');ad=C.read(admission_path)
 pins=C.read(out/'pins.json');B.interpreter(seal,pins,sys.executable)
 C.require(Path(audit.__file__).resolve()==(C.D/'audit_reviewed.py').resolve(),'wrong auditor source')
 C.require(ad.get('accepted') is True and ad.get('scope')=='numerical_admission' and ad.get('phase')==phase,'fresh concrete numerical admission required')
 C.require(ad.get('seal_sha256')==C.sha(out/'seal.json') and ad.get('pins_sha256')==C.sha(out/'pins.json'),'admission seal/pins')
 C.require(ad.get('head')==C.git('rev-parse','HEAD')==seal['head'] and ad.get('command')==C.command(phase)==seal['command'],'admission refs/command')
 C.require(C.sha(ad['review_report'])==ad['review_report_sha256'],'admission report binding')
 C.require(seal['environment']==C.environment(phase),'environment changed')
 C.require(not (out/'attempt.json').exists() and not (out/'guard').exists() and not (out/'result.toml').exists(),'attempt consumed/output exists')
 used,previous=C.previous(phase);C.require(previous==seal['previous'] and used==seal['used_seconds'],'prior phase/budget changed')
 h=C.host();C.fresh(out/'prelaunch-host.json',h);B.head(seal,ad,h['refs']['HEAD'])
 # Pure file verification here; guard verifies again under its ownership lock.
 C.require(all(C.sha(n)==v['sha256'] and str(Path(n).resolve(strict=True))==v['resolved'] for n,v in pins['inventory'].items()),'launch pins changed')
 C.require(not os.environ.get('LD_PRELOAD') and not os.environ.get('LD_AUDIT'),'unexpected loader injection')
 for key in list(os.environ):
  if key.startswith('JULIA_'):del os.environ[key]
 os.environ.update(seal['environment'])
 sys.path.insert(0,str(C.D/'guard'));import supervisor_reviewed as S
 remaining=1800-used;C.require(remaining>20,'no inclusive cleanup budget')
 started=time.monotonic();C.fresh(out/'attempt.json',dict(phase=phase,admission_path=str(Path(admission_path).resolve()),admission_sha256=C.sha(admission_path),seal_sha256=C.sha(out/'seal.json'),runner=C.identity(os.getpid()),remaining_seconds=remaining))
 command=[sys.executable,'-B',str(C.D/'guard/guard_reviewed.py'),'run',str(out/'pins.json'),str(out/'guard'),'--expected-exit',str(seal['expected_exit']),'--seconds',str(remaining-12),'--deadline',str(started+remaining-12),'--',*seal['command']]
 C.fresh(out/'invocation.json',dict(command=command,cwd=str(C.D),environment=seal['environment']))
 with (out/'guard.log').open('x') as log:result=S.run(command,log,str(out/'guard'),started,remaining-4)
 C.fresh(out/'supervisor.json',result)
 proc=C.read(out/'guard/process.json');extra=[proc[k][v] for k in ('runner','child') for v in ('pgid','sid') if k in proc]
 post=C.host(extra);C.fresh(out/'postflight.json',post);B.head(seal,ad,post['refs']['HEAD'])
 elapsed=time.monotonic()-started
 C.fresh(out/'completion.json',dict(elapsed_inclusive_seconds=elapsed,total_inclusive_seconds=used+elapsed,limit_seconds=1800,supervisor_accepted=result.get('accepted') is True))
 C.require(result.get('accepted') is True and used+elapsed<=1800,'supervisor/shared limit failed')
 audit.audit_phase(phase)
 print('Completed and audited',phase)
if __name__=='__main__':
 C.require(len(sys.argv)==3,'phase and numerical admission file required');os.chdir(C.D);main(sys.argv[1],sys.argv[2])
