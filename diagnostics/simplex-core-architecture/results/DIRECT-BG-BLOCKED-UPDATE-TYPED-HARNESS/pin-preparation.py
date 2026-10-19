"""New offline preparation manifest, not execution admission."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3];P=D.with_name('DIRECT-BG-P011-TYPED-HARNESS');F=D.with_name('DIRECT-BG-BLOCKED-UPDATE-HARNESS')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
def save(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
paths={p for p in D.iterdir() if p.is_file()}
for root,manifest in [(P,'preparation-pins.json'),(F,'preparation-pins-reviewed.json')]:
 paths.add(root/manifest);paths.update(Path(n) if Path(n).is_absolute() else R/n for n in rd(root/manifest)['sha256'])
 paths.add(root/'review.json')
 for key in ['sha256','evidence_sha256']:paths.update(Path(n) if Path(n).is_absolute() else R/n for n in rd(root/'review.json').get(key,{}))
paths.update(Path(n) for n in rd(D/'qualification-bindings.json')['sha256'])
for n in rd(D/'qualification-bindings.json')['accepted_receipts']:
 p=Path(n);paths.add(p)
 for key in ['sha256','evidence_sha256']:paths.update(Path(n) if Path(n).is_absolute() else R/n for n in rd(p).get(key,{}))
paths.update(Path(v['source']) for v in rd(D/'copied-files.json').values());paths.add(Path(rd(D/'fault-transform.json')['source']))
paths.update(R/n for n in ['AGENTS.md','docs/superpowers/plans/2026-10-19-direct-bg-blocked-update.md','docs/superpowers/specs/2026-10-19-direct-bg-blocked-update.md'])
paths.update(P/n for n in ['control.py','audit.py','seal.py','outer.py','launch.py']);paths.update(F/n for n in ['driver.jl','oracle.py','MEMORY-WORK.md'])
paths.add(D/'required-paths.json');save('required-paths.json',{'paths':sorted(str(p) for p in paths)})
if not all(p.is_file() and not p.is_symlink() for p in paths):raise RuntimeError('Missing/symlink preparation input')
save('preparation-pins.json',{'scope':'BG blocked typed harness preparation only; not launch admission','sha256':{str(p):sha(p) for p in sorted(paths)}})
print(json.dumps({'preparation_subjects':len(paths)}))
