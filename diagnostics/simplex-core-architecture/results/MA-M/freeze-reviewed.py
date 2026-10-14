from pathlib import Path
import json,hashlib,tomllib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-M'
roots=json.loads((D/'dependency-roots.json').read_text());trees={str(Path(p).resolve()) for values in roots['roots'].values() for p in values};trees.add('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base')
artifact_hashes=set()
def walk(v):
 if isinstance(v,dict):
  if 'git-tree-sha1' in v:artifact_hashes.add(v['git-tree-sha1'])
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
for root in tuple(trees):
 p=Path(root)/'Artifacts.toml'
 if p.exists():walk(tomllib.loads(p.read_text()))
for depot in roots['depots']:
 for h in artifact_hashes:
  p=Path(depot)/'artifacts'/h
  if p.is_dir():trees.add(str(p.resolve()))
old=json.loads((D/'pins.json').read_text());files={Path(p) for p in old['files']};files.update(p for p in D.rglob('*') if p.is_file())
for root in trees:
 for p in Path(root).rglob('*'):
  if p.is_symlink() and (p.is_dir() or not p.exists()):raise ValueError('unsupported tree symlink '+str(p))
  if p.is_file():files.add(p)
required=sorted(str(p) for p in files|{D/'required-paths-reviewed.json'})
with (D/'required-paths-reviewed.json').open('x') as f:json.dump(required,f,indent=2);f.write('\n')
files.add(D/'required-paths-reviewed.json')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
inv={str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(files)}
with (D/'pins-reviewed.json').open('x') as f:json.dump(dict(files=sorted(inv),trees=sorted(trees),inventory=inv,inputs=[]),f,indent=2);f.write('\n')
print('reviewed pins',len(inv),'trees',len(trees))
