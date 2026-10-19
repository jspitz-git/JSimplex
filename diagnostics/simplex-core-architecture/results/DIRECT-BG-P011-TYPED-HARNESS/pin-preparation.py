from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3];Z=D.with_name('DIRECT-BG-ZERO-COUNTS-HARNESS');T=D.with_name('DIRECT-BG-P011-TYPED-REPAIR');C=D.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE');Q=D.with_name('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR');F=D.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
save('adapted-files.json',{n:dict(source=str(Z/n),original_sha256=sha(Z/n),prepared_sha256=sha(D/n)) for n in ('control.py','audit.py','seal.py','launch.py','outer.py')})
paths=set(p for p in D.iterdir() if p.is_file())
paths.update(p for root in [T,C,Q] for p in root.rglob('*') if p.is_file())
for root,key in [(C,'sha256'),(Q,'sha256'),(T,'reviewed_bindings')]:
 filename='independent-review.json' if root==T else 'review.json'
 for n in json.loads((root/filename).read_text())[key]:paths.add(Path(n) if Path(n).is_absolute() else R/n)
paths.update([R/'AGENTS.md',F/'panel-tests.jl',F/'recorder.jl'])
paths.update(Path(v['source']) for v in json.loads((D/'copied-files.json').read_text()).values())
paths.update(Z/n for n in ('control.py','audit.py','seal.py','launch.py','outer.py'))
# These are static inputs read by control validation, not old scripts to execute.
paths.update(Path(n) if Path(n).is_absolute() else R/n for n in json.loads((Q/'stage.json').read_text())['sha256'])
paths.add(D/'required-paths.json');save('required-paths.json',dict(paths=sorted(str(p) for p in paths)))
if not all(p.is_file() for p in paths):raise RuntimeError('missing required input')
save('preparation-pins.json',dict(scope='P011 typed harness preparation only; not launch pins',sha256={str(p):sha(p) for p in sorted(paths)}))
print('Preparation inputs',len(paths))
