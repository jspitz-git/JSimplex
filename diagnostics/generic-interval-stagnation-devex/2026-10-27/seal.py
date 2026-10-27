from pathlib import Path
import sys,json,shutil,datetime
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-interval-stagnation-devex/2026-10-27');O=D.parents[1]/'generic-stagnation-unit-seed/2026-10-27';sys.path.insert(0,str(D));import common as c
# The same named binaries are freshly read at this case's prospective seal.
r=json.loads((O/'runtime-readtime-pins.json').read_text());r=dict(provenance='Prospective fresh read at this case; named bundle scope inherited, no transitive loader/runtime-selection proof',time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),inherited_manifest=str(O/'runtime-readtime-pins.json'),inherited_manifest_sha256=c.sha(O/'runtime-readtime-pins.json'),named_scope=r)
c.put('runtime-readtime-pins.json',r)
shutil.copyfile(__file__,D/'seal.py')
paths={n for n in json.loads((O/'MASTER-run/pins.json').read_text())['inventory'] if not Path(n).is_relative_to(c.R/'diagnostics')};paths.update(str(p) for root in [c.M/'src',c.M/'test',D/'baseline'] for p in root.rglob('*') if p.is_file());paths.update(str(c.M/n) for n in ['Project.toml','Manifest.toml','LocalPreferences.toml']);paths.update(str(p) for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.add(str(c.R/'diagnostics/generic-quality-local/2026-10-27/host-identity-allowance.json'));paths.add(str(c.R/'diagnostics/dual-finite-validity/terminal-primal-repair/green-2/output/process.json'))
c.put('pins.json',dict(files=sorted(paths),trees=[str(c.M/'src'),str(c.M/'test'),str(D/'baseline')],inputs=[],inventory={n:dict(resolved=str(Path(n).resolve(strict=True)),sha256=c.sha(n)) for n in sorted(paths)}));c.unchanged();c.put('author-host.json',c.host());print('sealed',len(paths),'pins; noJulia')
