from pathlib import Path
import json,hashlib,sys
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-M';L=D.parent/'MA-L'
old=json.loads((D.parent/'MA-J/pins-2.json').read_text())['inventory']
files={Path(p) for p in old if '/.julia/' in p or p.endswith('/julia.sh') or p=='/bin/bash'}
files.update(p for p in (R/'src').rglob('*') if p.is_file())
files.update(p for p in Path('/home/jspitz/.julia/packages/MutableArithmetics/SaQfc/src').rglob('*') if p.is_file())
files.update(p for p in L.rglob('*') if p.is_file())
files.update(p for p in D.rglob('*') if p.is_file())
files.update(R/n for n in ('Project.toml','Manifest.toml','LocalPreferences.toml','docs/superpowers/plans/2026-10-14-ma-presolve-selective-routing.md','docs/superpowers/specs/2026-10-14-ma-presolve-selective-routing-design.md'))
files.update(Path(p) for p in json.loads((D/'host.json').read_text())['protected']);files.add(Path(sys.executable))
base=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia')
files.update(p for p in (base/'stdlib/v1.13/Test').rglob('*') if p.is_file())
files.update(base/'base'/n for n in ('timing.jl','gmp.jl','rational.jl','mpfr.jl','loading.jl'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
required=sorted(str(p) for p in files)
with (D/'required-paths.json').open('x') as f:json.dump(required+[str(D/'required-paths.json')],f,indent=2);f.write('\n')
files.add(D/'required-paths.json')
inv={str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(files)}
with (D/'pins.json').open('x') as f:json.dump(dict(files=sorted(inv),trees=[],inventory=inv,inputs=[]),f,indent=2);f.write('\n')
print('pins',len(inv))
