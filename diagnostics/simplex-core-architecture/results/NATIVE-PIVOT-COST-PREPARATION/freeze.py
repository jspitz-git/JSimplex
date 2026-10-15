"""One-shot cost preparation inventory only; no stage or numerical launch."""
from pathlib import Path
import json,hashlib,sys
D=Path(__file__).resolve().parent;R=D.parents[3];Q=D.parent/'NATIVE-PIVOT-QUALIFICATION';F=D.parent/'NATIVE-PIVOT-OBSERVER-FIX';P=D.parent/'NATIVE-PIVOT-PREPARATION'
sys.path.insert(0,str(D));from control import predecessor
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
files,groups=predecessor('cost');files=set(files)
runtime=rd(Q/'runtime-pins.json')['sha256']
if not all(sha(n)==v for n,v in runtime.items()):raise RuntimeError('Runtime/source/environment differs')
files|={Path(n) for n in runtime}
files|={Path(e['source']) for arm in ['candidate','reference'] for e in rd(P/'overlay-manifest.json')[arm]}
files|={Q/'runtime-pins.json',P/'overlay-manifest.json',Q/'tests-observed.jl',Q/'neighbors-observed.jl',Q/'control_reviewed.py',Q/'common.py',Q/'audit_reviewed.py',Q/'oracle.py',Q/'cost-driver.jl',Q/'inputs.json',Q/'inputs.toml'}
files|={R/'docs/superpowers/plans/2026-10-15-native-pivot-policy.md',R/'docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md'}
files|={p for p in D.iterdir() if p.is_file()}
# Live continuation is sealed only after publication; immutable before copies are preparation inputs.
files-={R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'}
files.add(D/'required-paths.json')
save(D/'required-paths.json',dict(paths=sorted(map(str,files)),scope='Exact required preparation membership, including this list; no launch seal'))
save(D/'preparation-pins.json',dict(sha256={str(p):sha(p) for p in sorted(files)},scope='Fresh read-time preparation pins; no retroactive or numerical launch acceptance'))
print(dict(files=len(files),runtime=len(runtime),all_read=True))
