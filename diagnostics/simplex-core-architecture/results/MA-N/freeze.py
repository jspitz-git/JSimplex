from pathlib import Path
import json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-N';M=D.parent/'MA-M'
old=json.loads((M/'pins-reviewed.json').read_text());trees=set(old['trees'])
base=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13')
trees.update(str(base/n) for n in ('FileWatching','Sockets'))
files={Path(p) for p in old['inventory']};files.update(p for p in M.rglob('*') if p.is_file());files.update(p for p in D.rglob('*') if p.is_file())
files.update(R/n for n in ('diagnostics/simplex-core-architecture/MA-PRESOLVE-HARNESS-REPAIR.md','diagnostics/simplex-core-architecture/MA-PRESOLVE-SELECTIVE-QUALIFICATION.md','docs/superpowers/plans/2026-10-14-ma-presolve-qualification-harness-repair.md'))
for root in trees:
 for p in Path(root).rglob('*'):
  if p.is_symlink() and (p.is_dir() or not p.exists()):raise ValueError('unsupported tree symlink')
  if p.is_file():files.add(p)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
if not all(sha(Path(p))==v['sha256'] and str(Path(p).resolve())==v['resolved'] for p,v in old['inventory'].items()):raise ValueError('old pins changed')
files.add(D/'required-paths.json')
with (D/'required-paths.json').open('x') as f:json.dump(sorted(str(p) for p in files),f,indent=2);f.write('\n')
inv={str(p):dict(resolved=str(p.resolve(strict=True)),sha256=sha(p)) for p in sorted(files)}
with (D/'pins.json').open('x') as f:json.dump(dict(files=sorted(inv),trees=sorted(trees),inventory=inv,inputs=[]),f,indent=2);f.write('\n')
print('new pins',len(inv),'trees',len(trees),'old inputs',len(old['inventory']))
