from pathlib import Path
import sys,time
from control import *
import guard,supervisor

def main():
 base=rd(D/'pins.json');review=rd(D/'admission.json');required=[Path(p) for p in rd(D/'required.json')]
 validate_review(review,sha(D/'pins.json'),required)
 req(guard.pins_match(base),'base inventory')
 pins=rd(D/'launch-pins.json')
 req(set(pins['inventory'])==set(base['inventory'])|{str(D/'pins.json'),str(D/'admission.json')},'launch additions')
 req(all(pins['inventory'][p]==v for p,v in base['inventory'].items()),'base unchanged in launch')
 req(guard.pins_match(pins),'launch inventory')
 entry=rd(D/'host.json');groups=entry['groups'];commands=rd(D/'commands.json');cumulative=0.
 save(D/'reservation.json',dict(one_attempt=True,max_processes=4,max_seconds=280,pins_sha256=sha(D/'launch-pins.json'),review_sha256=sha(D/'admission.json'),commands_sha256=sha(D/'commands.json')))
 for index in range(1,5):
  req(guard.pins_match(pins),'prelaunch pins')
  h=host(groups);save(D/f'prehost-{index}.json',h)
  req(not h['matches'] and h['boot_id']==entry['boot_id'] and h['head']==entry['head'] and h['master']==entry['master'],'host changed')
  req(cumulative+70<=280,'cumulative budget')
  command=commands[str(index)];out=D/f'run-{index}'
  req(not out.exists(),'output already exists')
  started=time.monotonic();gc=[sys.executable,'-B',str(D/'guard.py'),'run',str(D/'launch-pins.json'),str(out),'--seconds','64','--deadline',str(started+64),'--',*command]
  invocation=dict(command=command,guard_command=gc,pins_sha256=sha(D/'launch-pins.json'),review_sha256=sha(D/'admission.json'),prehost_sha256=sha(D/f'prehost-{index}.json'),reservation_sha256=sha(D/'reservation.json'),started=time.time())
  try:
   with (D/f'launcher-{index}.log').open('x') as log:invocation['supervisor']=supervisor.run(gc,log,out,started)
  finally:
   invocation['elapsed_seconds']=time.monotonic()-started;cumulative+=invocation['elapsed_seconds'];invocation['cumulative_seconds']=cumulative;save(D/f'invocation-{index}.json',invocation)
   if 'supervisor' in invocation:groups=groups+[invocation['supervisor']['guard_identity']['pgid'],invocation['supervisor']['guard_identity']['sid']]
   for n in ('current.json','process.json'):
    if (out/n).exists():
     p=rd(out/n)
     for k in ('runner','child'):
      if k in p:groups=groups+[p[k]['pgid'],p[k]['sid']]
   post=host(groups);save(D/f'posthost-{index}.json',post)
  req(not post['matches'],'process groups remain')
  req(invocation['supervisor']['accepted'] and cumulative<=280,'process failed; stop without retry')
  a=stage_audit(index,pins);save(D/f'audit-{index}.json',a);req(a['all_passed'],'audit failed; stop without retry')
  print(f'Process {index}/4 PASS; cumulative {cumulative:.3f}s',flush=True)
 save(D/'posthost.json',host(groups))
if __name__=='__main__':main()
