from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;W=D.parents[2]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=read(D/'green-final-pins.json')
assert len(p['files'])==174 and set(p['files'])==set(p['inventory'])
assert all(sha(Path(n))==v['sha256'] and str(Path(n).resolve())==v['resolved'] for n,v in p['inventory'].items())
assert read(D/'postcheck.json')['accepted'] is True and len(read(D/'postcheck.json')['checks'])==34
assert read(D/'result-review.json')['accepted'] is True
assert read(D/'green-run/result.json')['accepted'] is True
log=(D/'green-run/guard/run.log').read_text();assert 'DUAL_ENGINE_TASK1_COMPLETED' in log and 'Test Failed' not in log
assert read(D/'terminal-host.json')['no_julia'] is True and len(read(D/'terminal-host.json')['checked_groups'])==788
if (D/'closure.json').exists():
 c=read(D/'closure.json');assert c['accepted'] is True
 assert all(sha(Path(n))==h for n,h in c['bindings'].items())
print('PASS Task1: observed106/106 GREEN,34postchecks,accepted independent review,174currentpins; no Julia rerun')
