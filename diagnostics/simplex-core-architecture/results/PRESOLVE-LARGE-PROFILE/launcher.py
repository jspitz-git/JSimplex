from control import *
import sys,time,tomllib
import guard,supervisor

def audit(index,pins):
 out=D/f'run-{index}';p=rd(out/'process.json');inv=rd(D/f'invocation-{index}.json')
 checks={'exit0':p['reason']=='exit0' and p['returncode']==0 and p['pins_unchanged'] is True,'supervisor':inv['supervisor']['accepted'] is True,'command':p['command']==rd(D/'commands.json')[str(index)]==inv['command'],'pins':p['pins_sha256']==sha(D/'launch-pins.json') and rd(out/'pins.json')==pins,'inventory':guard.pins_match(pins)}
 raw=tomllib.loads((out/'raw.toml').read_text());checks['driver']=raw['model']==('runtime','medium','test')[index-1] and raw['all_passed'] is True and not raw['errors'] and all(v is True for v in raw['checks'].values())
 checks['loaded_paths']=all(v in pins['inventory'] for v in raw['loaded_paths'].values())
 starts={p.name.removeprefix('start-'):tomllib.loads(p.read_text()) for p in out.glob('start-*.toml')};ends={p.name.removeprefix('finish-'):tomllib.loads(p.read_text()) for p in out.glob('finish-*.toml')}
 checks['calls']=set(starts)==set(ends) and 0<len(ends)<=324 and all(all(e[k]==starts[n][k] for k in ('rep','serial','round','index','input_dimensions')) and metric_ok(e) and 1<=e['rep']<=3 and 1<=e['round']<=12 and 1<=e['index']<=9 for n,e in ends.items())
 profiles=[tomllib.loads(q.read_text()) for q in out.glob('profile-*.toml')]
 checks['profiles']=len(profiles)==raw['completed_profiles'] and all(q['output_equal'] and q['input_preserved'] and q['calls']==sum(e['rep']==q['rep'] for e in ends.values()) for q in profiles)
 checks['public']=raw['public_control_completed']==(out/'public.toml').exists()
 if checks['public'] and raw['public_control_completed']:
  v=tomllib.loads((out/'public.toml').read_text());checks['public_match']=v['output_equal'] and v['input_preserved'] and all(v['signature']==q['signature'] for q in profiles)
 resources=[json.loads(l) for l in (out/'resources.jsonl').read_text().splitlines()]+[p['terminal_memory']]
 checks['resources']=all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in resources)
 return dict(all_passed=all(checks.values()),checks=checks,completed_profiles=len(profiles),public_control=raw['public_control_completed'],cooperative_stop=raw['cooperative_stop'],min_available_kib=min(s['available_kib'] for s in resources),max_swap_kib=max(s['swap_used_kib'] for s in resources),sha256={str(q):sha(q) for q in out.iterdir() if q.is_file()})

def main():
 base=rd(D/'pins.json');review=rd(D/'admission.json');required=[Path(p) for p in rd(D/'required.json')]
 validate_review(review,sha(D/'pins.json'),required);req(guard.pins_match(base),'base inventory')
 pins=rd(D/'launch-pins.json');req(set(pins['inventory'])==set(base['inventory'])|{str(D/'pins.json'),str(D/'admission.json')},'launch additions');req(all(pins['inventory'][p]==v for p,v in base['inventory'].items()),'base unchanged');req(guard.pins_match(pins),'launch inventory')
 entry=rd(D/'host.json');groups=entry['groups'];commands=rd(D/'commands.json');total=0.
 save(D/'reservation.json',dict(one_attempt=True,max_processes=3,max_seconds=360,pins_sha256=sha(D/'launch-pins.json'),review_sha256=sha(D/'admission.json'),commands_sha256=sha(D/'commands.json')))
 for i in range(1,4):
  req(guard.pins_match(pins),'prelaunch pins');h=host(groups);save(D/f'prehost-{i}.json',h)
  req(not h['matches'] and all(h[k]==entry[k] for k in ('boot_id','head','master')),'host changed');req(total+120<=360,'total budget')
  command=commands[str(i)];out=D/f'run-{i}';req(not out.exists(),'output exists');started=time.monotonic()
  gc=[sys.executable,'-B',str(D/'guard.py'),'run',str(D/'launch-pins.json'),str(out),'--seconds','114','--deadline',str(started+114),'--',*command]
  inv=dict(command=command,guard_command=gc,pins_sha256=sha(D/'launch-pins.json'),review_sha256=sha(D/'admission.json'),prehost_sha256=sha(D/f'prehost-{i}.json'),reservation_sha256=sha(D/'reservation.json'),started=time.time())
  try:
   with (D/f'launcher-{i}.log').open('x') as log:inv['supervisor']=supervisor.run(gc,log,out,started)
  finally:
   inv['elapsed_seconds']=time.monotonic()-started;total+=inv['elapsed_seconds'];inv['cumulative_seconds']=total;save(D/f'invocation-{i}.json',inv)
   if 'supervisor' in inv:groups += [inv['supervisor']['guard_identity']['pgid'],inv['supervisor']['guard_identity']['sid']]
   for n in ('current.json','process.json'):
    if (out/n).exists():
     p=rd(out/n)
     for k in ('runner','child'):
      if k in p:groups += [p[k]['pgid'],p[k]['sid']]
   post=host(groups);save(D/f'posthost-{i}.json',post)
  req(not post['matches'] and total<=360 and guard.pins_match(pins),'post host/time/pins')
  if not inv['supervisor']['accepted']:
   # Only a fully recorded timeout may leave partial data and allow the next
   # independently admitted input. All other errors/resources stop the sequence.
   p=rd(out/'process.json');rs=[json.loads(l) for l in (out/'resources.jsonl').read_text().splitlines()]+[p['terminal_memory']]
   req(p['reason'] in ('wall_time','interrupted') and p['pins_unchanged'] is True and inv['supervisor']['elapsed_seconds']<=120 and 'cleanup_error' not in inv['supervisor'] and all(s['available_kib']>=6*1024**2 and s['swap_used_kib']<=1024**2 for s in rs),'non-timeout failure')
   save(D/f'partial-{i}.json',dict(accepted_complete=False,reason=p['reason'],no_retry=True));print('Partial timeout',i,flush=True);continue
  a=audit(i,pins);save(D/f'audit-{i}.json',a);req(a['all_passed'],'audit failed; no retry')
  print(f'Model {i}/3 complete; cumulative {total:.3f}s',flush=True)
 save(D/'posthost.json',host(groups))
if __name__=='__main__':main()
