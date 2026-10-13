"""Exclusive corrected read-time inventory; initial pins remain unchanged."""
from pathlib import Path
import json,hashlib
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent
old=json.loads((H/'pins.json').read_text())['sha256'];mp={str(D/'S5-CRASH-FALLBACK-OBSERVER-TEST-PREPARATION.md'):H/'S5-CRASH-FALLBACK-OBSERVER-TEST-PREPARATION.md.before-review',str(R/'docs/superpowers/plans/2026-10-13-crash-fallback-observer-test-integration.md'):H/'2026-10-13-crash-fallback-observer-test-integration.md.before-review'}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
assert all(sha(mp.get(k,k))==v for k,v in old.items())
files={Path(mp.get(k,k)) for k in old}|{Path(k) for k in mp}|{p for p in H.rglob('*') if p.is_file()}
with (H/'pins-reviewed.json').open('x') as f:json.dump(dict(scope='Fresh offline corrected read-time hashes; no Julia launch',count=len(files),old1398_preserved=True,sha256={str(p):sha(p) for p in sorted(files)}),f,indent=2);f.write('\n')
print('Reviewed inventory:',len(files))
