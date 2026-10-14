from pathlib import Path
import json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-J'
old=json.loads((R/'diagnostics/simplex-core-architecture/results/MA-I/admission-pins-reviewed.json').read_text())['inventory']
files={Path(p) for p in old if '/.julia/' in p or p.endswith('/julia.sh')}
files.update(p for p in (R/'src').rglob('*') if p.is_file())
files.update(p for p in Path('/home/jspitz/.julia/packages/MutableArithmetics/SaQfc/src').rglob('*') if p.is_file())
files.update(p for p in D.rglob('*') if p.is_file())
files.update(R/n for n in ('Project.toml','Manifest.toml','LocalPreferences.toml'))
files.update(Path(p) for p in json.loads((D/'host.json').read_text())['protected'])
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
inv={str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(files)}
with (D/'pins.json').open('x') as f:json.dump(dict(files=sorted(inv),trees=[],inventory=inv,inputs=[]),f,indent=2);f.write('\n')
print('pins',len(inv))
