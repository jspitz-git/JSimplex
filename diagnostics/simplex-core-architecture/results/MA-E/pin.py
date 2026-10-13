"""Fresh readtime/admission pins; no Julia or launch or old script rerun."""
import sys
sys.dont_write_bytecode=True
from control import *
paths={p for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
for folder in ('src','test','.github'):
 paths.update(p for p in (R/folder).rglob('*') if p.is_file())
paths.update(R/n for n in ('Project.toml','Manifest.toml','LocalPreferences.toml','AGENTS.md'))
paths.update(p for p in (D.parent/'MA-D').rglob('*') if p.is_file())
paths.update([R/'docs/superpowers/plans/2026-10-13-ma-markowitz-upper-admission.md',R/'docs/superpowers/plans/2026-10-13-ma-markowitz-upper-qualification.md',R/'diagnostics/simplex-core-architecture/MA-MARKOWITZ-UPPER-ADMISSION.md',Path(sys.executable)])
old=read(D.parent/'MA-A/launch-pins.json')
# Fresh hashes of explicit installed runtime/dependency/launcher files; no old raw/audit rereads.
for name in old['files']:
 if name.startswith('/home/jspitz/.julia/') or name.startswith('/home/jspitz/.codex/worktrees/basis-update-chain-bench/') or name=='/bin/bash':paths.add(Path(name))
ma=Path('/home/jspitz/.julia/packages/MutableArithmetics/SaQfc');paths.update(p for p in (ma/'src').rglob('*') if p.is_file());paths.add(ma/'Project.toml')
paths.update(Path(p) for p in read(D/'host.json')['protected_sha256'])
required={str(p):sha(p) for p in sorted(paths)}
save(D/'required-paths.json',required)
paths.add(D/'required-paths.json')
inv={str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(paths)}
save(D/'admission-pins.json',dict(files=list(inv),trees=[],inputs=[],inventory=inv,scope='fresh readtime pins for future MA-F; not retroactive execution pins'))
print('fresh admission pins',len(inv),'listed bytes',sum(Path(p).stat().st_size for p in inv))
