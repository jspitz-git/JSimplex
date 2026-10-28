from pathlib import Path
import json,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');R=D.parents[2];B=D/'continuation-before-temporal-fix';B.mkdir();oldmap=json.loads((D/'historical-path-map.json').read_text())['continuation_before'];mapping={}
def need(v,m):
 if not v:raise RuntimeError(m)
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
for p in [R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']:
 s=p.read_bytes();old=Path(oldmap[str(p)]['before']).read_bytes();need(s.endswith(old),'preserved original suffix');prefix=s[:-len(old)];q=B/('STATUS.md' if p.name=='STATUS.md' else 'roadmap.md');q.write_bytes(s)
 a=b'residual pivot crash integrated; diagnostic closure pending, 2026-10-28';b=b'residual pivot crash integrated, 2026-10-28';need(prefix.count(a)==1,'temporal heading');prefix=prefix.replace(a,b)
 a=b'Final PASS closure and exact diagnostic publication are still pending; their eventual outcomes will be recorded separately.';b=b'At preparation of this prepublication record, closure and diagnostic publication remain pending; canonical outputs record subsequent outcomes.';need(prefix.count(a)==1,'temporal outcome description');prefix=prefix.replace(a,b)
 p.write_bytes(prefix+old);mapping[str(p)]=dict(before=str(q),sha256=sha(q),after_sha256=sha(p));need(p.read_bytes().endswith(old),'verbatim original suffix')
(D/'final-temporal-review-fix.json').write_text(json.dumps(dict(Julia_executed=False,production_unchanged=True,report_unchanged=True,historical_maps_unchanged=True,changes=mapping,reason='Truthful immutable prepublication snapshot before and after later accepted closure/publication; no postpublication rewrite'),indent=2,sort_keys=True)+'\n')
(D/'final-temporal-review-fix.py').write_bytes(Path(__file__).read_bytes());print('prepublication wording qualified by record time; all prior versions preserved')
