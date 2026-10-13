"""Exclusive fresh read-time inventory and supplemental required membership."""
from pathlib import Path
import json,hashlib
R=Path.cwd();H=Path(__file__).resolve().parent;Y=H.parent/'S5-Y';D=H.parent.parent;S=D/'STATUS.md';P=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
mp={str(S):Y/'STATUS.md.before-Y',str(P):Y/'2026-10-11-simplex-core-architecture.md.before-Y'}
a=read(Y/'pins.json')['inventory'];required=read(Y/'required-paths.json')['sha256'];assert len(required)==338 and all(k in a and v==a[k]['sha256'] and sha(mp.get(k,k))==v for k,v in required.items())
files={Path(mp.get(k,k)) for k in a}|{S,P}|{p for p in Y.rglob('*') if p.is_file()}|{p for p in H.rglob('*') if p.is_file()}|{D/'S5-CRASH-FALLBACK-OBSERVER-TEST-PREPARATION.md',D/'S5-CRASH-FALLBACK-OBSERVER-QUALIFICATION.md',D/'S5-CRASH-FALLBACK-OBSERVER-QUALIFICATION-REVIEW.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-test-preparation.md',R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-test-integration.md'}
with (H/'pins.json').open('x') as f:json.dump(dict(scope='Fresh offline read-time hashes; no Julia launch',required338=True,sha256={str(p):sha(p) for p in sorted(files)}),f,indent=2);f.write('\n')
print('Fresh read-time pins:',len(files),'required338 PASS')
