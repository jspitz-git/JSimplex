"""Supplementary one-use post-exit preservation; not a launch input."""
from common import *
import tomllib
p=read(OUT/'process.json');pins=read(D/'launch-pins.json');audit=read(D/'audit.json');inv=read(D/'invocation.json');a=read(D/'allowance.json')
h=absent([p[k]['pgid'] for k in ('runner','child') if k in p])
checks={
 'full_launch_inventory':manifest_ok(pins,read(D/'required-paths.json')),
 'admitted_audit':audit['all_passed'] is True and all(v is True for v in audit['checks'].values()),
 'process_and_launcher':terminal_ok(p) and inv.get('returncode')==0 and 'error' not in inv,
 'refs_unchanged':refs()==a['refs'],
 'full_groups_ANDsessions_noJulia':not h['matches'] and len(h['groups'])==32,
 'production_test_CI_unchanged':not subprocess.check_output(['git','diff','master','--','src','test','.github'])}
portable=D/'qualification-1';portable.mkdir(exist_ok=False)
for q in OUT.iterdir():
 require(q.is_file() and not q.is_symlink(),'unexpected raw object')
 with (portable/q.name).open('xb') as f:f.write(q.read_bytes())
checks['portable_byteidentical']=all(sha(q)==sha(OUT/q.name) for q in portable.iterdir())
raw=tomllib.loads((OUT/'measurement.toml').read_text()) if (OUT/'measurement.toml').exists() else {}
resources=[json.loads(s) for s in (OUT/'resources.jsonl').read_text().splitlines()]
paths=list(portable.iterdir())+[D/n for n in ('allowance.json','numerical-review.md','launch-pins.json','attempt-reserved.json','launcher.log','invocation.json','audit.json','postcheck.py')]
result={'all_passed':all(checks.values()),'checks':checks,'host':h,'sha256':{str(q):sha(q) for q in paths},'raw_errors':raw.get('errors'),'resources':{'samples':len(resources),'minimum_available_kib':min((s['available_kib'] for s in resources),default=None),'maximum_swap_kib':max((s['swap_used_kib'] for s in resources),default=None),'terminal_memory':p.get('terminal_memory'),'elapsed_including_launch':p.get('elapsed_including_launch')},'note':'Post-exit supplement, not launch pin; inclusive duration not benchmark.'}
dump(D/'postcheck.json',result)
print(json.dumps({'checks':checks,'resources':result['resources']}))
require(result['all_passed'],'postcheck failed')
