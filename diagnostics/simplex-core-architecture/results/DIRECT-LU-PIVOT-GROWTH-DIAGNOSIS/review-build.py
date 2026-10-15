"""Bind this bounded review, without executing any previous scripts."""
from pathlib import Path
import json,hashlib
F=Path(__file__).resolve().parent; R=F.parents[3]
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
v=read(F/'independent-review-check-3.json'); a=read(F/'author-check.json')
assert v['all_passed'] and len(v['checks'])==33 and all(v['checks'].values())
assert all(digest(p)==h for p,h in v['sha256'].items())
assert all(digest(p)==h for p,h in a['sha256'].items())
assert read(F.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False
assert not list((F.parent/'DIRECT-LU-COST-PREPARATION').glob('cost2-*'))
paths=set(map(Path,v['sha256']))|set(map(Path,a['sha256']))
paths|={p for p in F.iterdir() if p.is_file() and p.name not in ('review.json','closure.json','publication.json','continuation.json','continuation-host.json','closure-host.json')}
paths.add(F.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')
result=dict(accepted=True,findings=[],scope='Offline saved-factor/source diagnosis only; no numerical qualification or continuation execution.',independent_check_count=33,baseline_count=514,work_memory='No unnecessary production work or memory found; unchanged baseline and bounded offline arithmetic only.',sha256={str(p):digest(p) for p in sorted(paths)})
with (F/'review.json').open('x') as h:json.dump(result,h,indent=2);h.write('\n')
print(json.dumps(dict(accepted=True,findings=[],checks=33,bindings=len(paths))))
