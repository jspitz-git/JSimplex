"""UNEXECUTED. Explicit one-attempt launcher, never auto-seals or auto-retries."""
from control import *
import supervisor

def main(phase):
 os.chdir(R);cfg=config(phase);validate_environment();preparation();validate_sources();extra,groups=predecessor(phase);run=Path(cfg['run']);sp=run/'sealed.json';sealed=rd(sp);rp=run/'admission.json'
 require(sealed['phase']==phase and sealed['config']==cfg and rd(run/'config.json')==cfg,'Config drift')
 verify_review(rd(rp),sp,sealed['files']+[str(sp)],'block BG exact-stage admission',phase)
 require(guard.pins_match(sealed),'Seal changed');h=full_host(groups+sealed['groups'])
 require(not h['matches'] and all(h[k]==sealed[k] for k in ('head','master','boot_id')),'Actual host/ref drift')
 require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked changes')
 require(not Path(cfg['output']).exists(),'Existing output');save(run/'prehost.json',h)
 files=sorted(set(sealed['files'])|{str(sp),str(rp),str(run/'prehost.json')});pp=run/'launch-pins.json'
 save(pp,dict(files=files,trees=sealed['trees'],inventory=guard.inventory(files,sealed['trees']),inputs=[]))
 res=run/'reservation.json';save(res,dict(one_attempt=True,phase=phase,command=cfg['command'],pins_sha256=sha(pp),review_sha256=sha(rp),max_seconds=cfg['seconds']))
 started=time.monotonic();cmd=guard_command(cfg,pp,started);inv=dict(monotonic_start=started,command=cfg['command'],guard_command=cmd,python=sys.executable,pins_sha256=sha(pp),review_sha256=sha(rp),reservation_sha256=sha(res))
 try:
  with (run/'launcher.log').open('x') as log:inv['supervisor']=supervisor.run(cmd,log,cfg['output'],started,cfg['seconds'])
 finally:
  inv['elapsed_seconds']=time.monotonic()-started;save(run/'invocation.json',inv)
  if 'supervisor' in inv:groups += [inv['supervisor']['guard_identity'][k] for k in ('pgid','sid')]
  for n in ['current.json','process.json']:
   f=Path(cfg['output'])/n
   if f.exists():
    for role in ['runner','child']:
     o=rd(f)
     if role in o:groups += [o[role][k] for k in ('pgid','sid')]
  save(run/'posthost.json',full_host(groups+sealed['groups']))
 from audit import audit
 require(audit(phase)['all_passed'],'Failed attempt preserved; pure timeout may receive separately admitted600s, never automatic in launcher')
if __name__=='__main__':main(sys.argv[1])
