"""Future guarded execution only after exact independent stage admission."""
from control import *
import guard,supervisor,sys

def main(phase):
    cfg=phase_config(phase);sealed_path=D/(phase+'-sealed-pins.json');sealed=rd(sealed_path)
    req(sealed.get('phase')==phase,'Wrong sealed phase')
    review_path=D/(phase+'-admission.json');required=sealed['files']+[str(sealed_path)]
    validate_review(rd(review_path),sealed_path,required)
    req(guard.pins_match(sealed),'Sealed bindings changed')
    groups=rd(D/(phase+'-seal-host.json'))['groups'];fresh=host(groups)
    req(not fresh['matches'] and all(fresh[k]==sealed[k] for k in ('head','master','boot_id')),'Fresh host mismatch')
    save(D/(phase+'-prehost.json'),fresh)
    out=Path(cfg['output']);req(not out.exists(),'Prior output exists')
    files=sorted(set(sealed['files'])|{str(sealed_path),str(review_path)})
    pins=dict(files=files,trees=sealed['trees'],inventory=guard.inventory(files,sealed['trees']),inputs=[],created=time.time())
    pins_path=D/(phase+'-launch-pins.json');save(pins_path,pins)
    save(D/(phase+'-reservation.json'),dict(one_attempt=True,phase=phase,command=cfg['command'],pins_sha256=sha(pins_path),review_sha256=sha(review_path),max_seconds=cfg['seconds']))
    started=time.monotonic();limit=cfg['seconds']
    command=[sys.executable,'-B',str(D/'guard.py'),'run',str(pins_path),str(out),'--seconds',str(limit-6),'--deadline',str(started+limit-6),'--',*cfg['command']]
    inv=dict(command=cfg['command'],guard_command=command,pins_sha256=sha(pins_path),review_sha256=sha(review_path),reservation_sha256=sha(D/(phase+'-reservation.json')),started=time.time())
    try:
        with (D/(phase+'-launcher.log')).open('x') as log:inv['supervisor']=supervisor.run(command,log,out,started,limit)
    finally:
        inv['elapsed_seconds']=time.monotonic()-started;save(D/(phase+'-invocation.json'),inv)
        if 'supervisor' in inv:groups += [inv['supervisor']['guard_identity'][k] for k in ('pgid','sid')]
        for name in ('current.json','process.json'):
            if (out/name).exists():
                p=rd(out/name)
                for k in ('runner','child'):
                    if k in p:groups += [p[k]['pgid'],p[k]['sid']]
        save(D/(phase+'-posthost.json'),host(groups))
    from audit import audit
    result=audit(phase);req(result['all_passed'],'Audit failed; preserve and stop')
if __name__=='__main__':main(sys.argv[1])
