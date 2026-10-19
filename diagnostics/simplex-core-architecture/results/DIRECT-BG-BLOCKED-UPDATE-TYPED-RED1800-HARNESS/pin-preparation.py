"""New exact read-time preparation manifest, not launch admission."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3];P=D.with_name('DIRECT-BG-BLOCKED-UPDATE-TYPED-HARNESS')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text())
paths={str(p) for p in D.iterdir() if p.is_file()}
paths|=set(rd(P/'preparation-pins.json')['sha256'])|set(rd(D/'timeout-bindings.json')['sha256'])
paths|={str(P/'preparation-pins.json'),str(P/'review.json')}|set(rd(P/'review.json')['evidence_sha256'])
paths|={str(R/'AGENTS.md'),str(R/'docs/superpowers/plans/2026-10-19-direct-bg-blocked-update.md'),str(R/'docs/superpowers/specs/2026-10-19-direct-bg-blocked-update.md'),str(P/'MEMORY-WORK.md'),str(D/'required-paths.json')}
with (D/'required-paths.json').open('x') as f:json.dump(dict(paths=sorted(paths)),f,indent=2);f.write('\n')
if any(not Path(p).is_file() or Path(p).is_symlink() for p in paths):raise RuntimeError('Nonregular subject')
with (D/'preparation-pins.json').open('x') as f:json.dump(dict(scope='RED1800 offline preparation only; not launch',sha256={p:sha(p) for p in sorted(paths)}),f,indent=2);f.write('\n')
print(json.dumps(dict(subjects=len(paths),no_launch=True)))
