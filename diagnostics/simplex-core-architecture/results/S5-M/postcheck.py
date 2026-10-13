"""New exclusive post-attempt independent evidence check; no numerical calls."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=Path(__file__).resolve().parent;O=R/'.superpowers/simplex-core-architecture/S5-M/qualification-1'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
p=json.loads((O/'process.json').read_text());pins=json.loads((O/'pins.json').read_text());l=json.loads((H.parent/'S5-L/evidence.json').read_text());a=json.loads((H/'audit.json').read_text())
checks={'full_current_launch_inventory':all(sha(f)==x['sha256'] and str(Path(f).resolve())==x['resolved'] for f,x in pins['inventory'].items()),'L141_unchanged':all(sha(f)==x for f,x in l['sha256'].items()),'raw_bindings':all(sha(O/f)==x for f,x in a['raw_sha256'].items()),'source_test_CI_master':subprocess.check_output(['git','diff','master','--','src','test','.github'],cwd=R)==b'','master_unchanged':subprocess.check_output(['git','rev-parse','master'],cwd=R,text=True).strip()=='513c05388a82531e4d8fbcfb383e8897fad14ba2','user6':all(sha(f)==x for f,x in json.loads((H/'host-before.json').read_text())['user_hashes'].items()),'reviewed_manifest':sha(O/'pins.json')==json.loads((H/'prelaunch-acceptance.json').read_text())['pins_sha256'],'audit_gate_consistent':a['all_passed']==all(a['checks'].values())}
x={'checks':checks,'all_passed':all(checks.values()),'qualification_accepted':a['all_passed'],'sha256':{str(f):sha(f) for f in [H/'audit.json',H/'prelaunch-review.md',H/'prelaunch-acceptance.json',H/'postcheck.py',O/'process.json',O/'pins.json']},'time_ns':time.time_ns()}
with (H/'postcheck.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x));raise SystemExit(0 if x['all_passed'] else 1)
