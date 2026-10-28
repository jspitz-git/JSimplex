from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');O=D.parents[1]/'generic-unit-perturb-residual/2026-10-28';sys.path.insert(0,str(D));import common as c
review=c.read('preparation-review.json');c.need(review['accepted'] is True and review['findings']==[],'independent preparation review')
for n,v in review['bindings'].items():c.need(c.sha(n)==v,'review binding '+n)
shutil.copyfile(__file__,D/'seal.py')
paths={n for n in c.read(str(O/'MASTER-run/pins.json'))['inventory'] if not Path(n).is_relative_to(c.R/'diagnostics')}
for root in [c.M/'src',c.M/'test',D/'baseline']:paths.update(str(p) for p in root.rglob('*') if p.is_file())
paths.update(str(c.M/n) for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.add(str(c.R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json'))
c.put('pins.json',dict(files=sorted(paths),trees=[str(c.M/'src'),str(c.M/'test'),str(D/'baseline')],inputs=[str(D/'grid.toml')],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}))
c.unchanged();c.put('author-host.json',c.host());print(json.dumps(dict(pins=len(paths),cells=c.read('contract.json')['cases'],noJulia=True)))
