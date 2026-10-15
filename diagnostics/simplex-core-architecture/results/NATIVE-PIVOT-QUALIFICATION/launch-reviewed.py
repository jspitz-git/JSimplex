"""UNEXECUTED single exact-stage launch. Does not auto-seal, review or continue."""
from control_reviewed import *
import guard,supervisor

def main(phase):
 os.chdir(R);cfg=config(phase);run=Path(cfg['run']);validate_environment();extra,groups=predecessor(phase)
 validate_stage(cfg);sp=run/'sealed.json';sealed=rd(sp);review=run/'admission.json'
 require(sealed['phase']==phase and sealed['config']==cfg,'Wrong sealed stage')
 verify_review(rd(review),sp,sealed['files']+[str(sp)],'exact-stage admission',phase)
 require(guard.pins_match(sealed),'Seal changed')
 h=full_host(groups+sealed['groups'])
 require(not h['matches'] and all(h[k]==sealed[k] for k in ('head','master','boot_id')),'Fresh host drift')
 require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked changes')
 save(run/'prehost.json',h)
 require(not Path(cfg['output']).exists(),'Output exists')
 files=sorted(set(sealed['files'])|{str(sp),str(review),str(run/'prehost.json')})
 pp=run/'launch-pins.json';pins=dict(files=files,trees=sealed['trees'],inventory=guard.inventory(files,sealed['trees']),inputs=[]);save(pp,pins)
 reservation=run/'reservation.json';save(reservation,dict(one_attempt=True,phase=phase,command=cfg['command'],pins_sha256=sha(pp),review_sha256=sha(review),max_seconds=cfg['seconds']))
 started=time.monotonic();command=guard_command(cfg,pp,started)
 inv=dict(monotonic_start=started,command=cfg['command'],guard_command=command,python=sys.executable,pins_sha256=sha(pp),review_sha256=sha(review),reservation_sha256=sha(reservation))
 try:
  with (run/'launcher.log').open('x') as log:inv['supervisor']=supervisor.run(command,log,cfg['output'],started,cfg['seconds'])
 finally:
  inv['elapsed_seconds']=time.monotonic()-started;save(run/'invocation.json',inv)
  if 'supervisor' in inv:groups += [inv['supervisor']['guard_identity'][k] for k in ('pgid','sid')]
  for name in ['current.json','process.json']:
   path=Path(cfg['output'])/name
   if path.exists():
    obj=rd(path)
    for role in ['runner','child']:
     if role in obj:groups += [obj[role][k] for k in ('pgid','sid')]
  save(run/'posthost.json',full_host(groups+sealed['groups']))
 from audit_reviewed import audit
 require(audit(phase)['all_passed'],'Stage failed: preserve all records and stop; no retry')
if __name__=='__main__':main(sys.argv[1])
