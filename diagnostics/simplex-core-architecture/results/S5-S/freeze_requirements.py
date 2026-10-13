"""Exclusive manifest requirements, assembled before review; no numerical calls."""
from common import *
old=read(H.parent/'S5-R/evidence.json')['sha256'];assert all(sha(p)==v for p,v in old.items())
files=set(map(Path,old))|set(essentials())|{p for p in H.iterdir() if p.is_file()}
files.discard(H/'required-paths.json')
files|={p for p in (H.parent/'S5-R').rglob('*') if p.is_file()}
files|={p for tree in ('src','test') for p in (R/tree).rglob('*') if p.is_file()}
previous=read(H.parent/'S5-O/master-1/pins.json')['inventory']
files|={Path(p) for p in previous if not Path(p).is_relative_to(R) and not Path(p).is_relative_to('/home/jspitz/JSimplex.jl/src') and not Path(p).is_relative_to('/home/jspitz/JSimplex.jl/test')}
files|={R/p for p in ('Project.toml','Manifest.toml','LocalPreferences.toml','.vscode/settings.json')}
dump(H/'required-paths.json',dict(sha256={str(p):sha(p) for p in sorted(files)},scope='Complete REQUIRED selected inventory; not loader closure or cache content proof.'))
print('required',len(files))
