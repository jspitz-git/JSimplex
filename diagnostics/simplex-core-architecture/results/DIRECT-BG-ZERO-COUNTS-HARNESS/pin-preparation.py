from pathlib import Path
import json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');E=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-ZERO-COUNTS-HARNESS';P=E.with_name('DIRECT-BG-P011-HARNESS');C=E.with_name('DIRECT-BG-ZERO-COUNTS-CANDIDATE');F=E.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS');Q=E.with_name('DIRECT-BG-BLOCKED-UPDATE-STAGE-REPAIR')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
for src,dst in [('zero-counts-independent-review.py','independent-check.py'),('zero-counts-independent-review.json','independent-check.json'),('zero-counts-initial-review.json','review-initial.json')]:
 with (E/dst).open('xb') as f:f.write((Path('/tmp')/src).read_bytes())
with (E/'pin-preparation.py').open('x') as f:f.write(Path(__file__).read_text())
paths=set(p for p in E.iterdir() if p.is_file())
paths.update(p for p in C.iterdir() if p.is_file())
paths.update(Path(p) for p in json.loads((C/'review.json').read_text())['sha256'])
paths.update([R/'AGENTS.md',F/'recorder.jl',F/'panel-tests.jl'])
paths.update(p for p in Q.rglob('*') if p.is_file())
paths.update(Path(p) for p in json.loads((Q/'review.json').read_text())['sha256'])
paths.update(P/n for n in ['control.py','audit.py','oracle.py','outer.py','seal.py','launch.py','tests_reviewed.py','review.json','review.md','runs/p011-300/outer-closure.json'])
paths.update(Path(v['source']) for v in json.loads((E/'copied-files.json').read_text()).values())
# Every file read by stage/source control is additionally included in launch seal inventories.
js(E/'required-paths.json',dict(paths=sorted(str(p) for p in paths|{E/'required-paths.json'})))
paths.add(E/'required-paths.json')
js(E/'preparation-pins.json',dict(scope='Offline exact preparation inputs; not launch pins',sha256={str(p):sha(p) for p in sorted(paths)}))
print('preparation pins',len(paths))
