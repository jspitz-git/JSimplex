from control import *
import guard,supervisor,sys
phase=sys.argv[1];cfg=rd(D/(phase+'-config.json'));pins_path=D/(phase+'-launch-pins.json');pins=rd(pins_path)
review_path=D/(phase+'-admission.json');review=rd(review_path)
validate_review(review,sha(D/(phase+'-pins.json')),[Path(p) for p in cfg['required']])
base=rd(D/(phase+'-pins.json'))
req(set(pins['inventory'])==set(base['inventory'])|{str(D/(phase+'-pins.json')),str(review_path)},'exact launch addition')
req(all(pins['inventory'][p]==v for p,v in base['inventory'].items()),'base bindings');req(guard.pins_match(pins),'launch pins')
groups=rd(D/'host.json')['groups']
for p in D.glob('*-posthost.json'):groups+=rd(p)['groups']
h=host(groups);save(D/(phase+'-prehost.json'),h);entry=rd(D/'host.json')
req(not h['matches'] and all(h[k]==entry[k] for k in ('head','master','boot_id')),'fresh host')
out=D/(phase+'-run');req(not out.exists(),'prior output')
save(D/(phase+'-reservation.json'),dict(one_attempt=True,command=cfg['command'],pins_sha256=sha(pins_path),review_sha256=sha(review_path),max_seconds=120))
started=time.monotonic();command=[sys.executable,'-B',str(D/'guard.py'),'run',str(pins_path),str(out),'--seconds','114','--deadline',str(started+114),'--',*cfg['command']]
inv=dict(command=cfg['command'],guard_command=command,pins_sha256=sha(pins_path),review_sha256=sha(review_path),reservation_sha256=sha(D/(phase+'-reservation.json')),started=time.time())
try:
 with (D/(phase+'-launcher.log')).open('x') as log:inv['supervisor']=supervisor.run(command,log,out,started)
finally:
 inv['elapsed_seconds']=time.monotonic()-started;save(D/(phase+'-invocation.json'),inv)
 if 'supervisor' in inv:groups+=[inv['supervisor']['guard_identity'][k] for k in ('pgid','sid')]
 for n in ('current.json','process.json'):
  if (out/n).exists():
   rec=rd(out/n)
   for k in ('runner','child'):
    if k in rec:groups += [rec[k]['pgid'],rec[k]['sid']]
 post=host(groups);save(D/(phase+'-posthost.json'),post)
p=rd(out/'process.json');s=inv['supervisor'];raw=tomllib.loads((out/'raw.toml').read_text());expected=cfg['expected_returncode']
resources=[json.loads(l) for l in (out/'resources.jsonl').read_text().splitlines()]+[p['terminal_memory']]
checks={'no_processes':not post['matches'],'bounded':inv['elapsed_seconds']<=120 and not s['soft_timeout'] and not s['hard_timeout'] and 'cleanup_error' not in s,'exit':p['returncode']==expected and p['reason']=='exit'+str(expected) and s['returncode']==(0 if expected==0 else 1),'pins':p['pins_unchanged'] and guard.pins_match(pins) and rd(out/'pins.json')==pins,'command':p['command']==cfg['command'] and p['pins_sha256']==sha(pins_path),'resources':all(r['available_kib']>=6*1024**2 and r['swap_used_kib']<=1024**2 for r in resources),'loaded_path':raw['loaded_path']==str(Path(cfg['project'])/'src/JSimplex.jl') and raw['loaded_path'] in pins['inventory']}
checks['driver']=raw['correct'] and raw['preserved'] and raw['zero_conversions']==1 and raw['expected_red'] if expected==1 else raw['all_passed'] is True
save(D/(phase+'-audit.json'),dict(all_passed=all(checks.values()),checks=checks,expected_returncode=expected,scope='Expected RED is not numerical acceptance' if expected else 'Completed bounded run',sha256={str(q):sha(q) for q in out.rglob('*') if q.is_file()}));req(all(checks.values()),'audit failed; preserve/stop');print(phase,'PASS',inv['elapsed_seconds'])
