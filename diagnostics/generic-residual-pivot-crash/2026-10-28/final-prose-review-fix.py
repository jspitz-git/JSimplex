from pathlib import Path
import json,hashlib
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');R=D.parents[2]
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def need(v,msg):
 if not v:raise RuntimeError(msg)
report=D/'FINAL-REPORT.md';before=D/'FINAL-REPORT.md.before-final-review';need(not before.exists(),'exclusive report beforeimage');before.write_bytes(report.read_bytes())
s=report.read_text();needle='in inclusive 297.380s.';need(s.count(needle)==1,'supervisor elapsed correction')
s=s.replace(needle,'in supervisor elapsed 297.380s; the complete launcher elapsed was 297.660s (completed.json), including its final checks.')
needle='No native allocation/free balance or retained-native-memory gain is proved.'
need(s.count(needle)==1,'conditional result note');s=s.replace(needle,needle+' Negative B pivots show unchanged allocation counts and no established speedup; all-positive Rational{BigInt} C rows likewise show no allocation saving or established speedup. These controls remain included in the aggregate table above.')
report.write_text(s)
B=D/'continuation-after-finalizer-before-review';B.mkdir();mapping={str(report):dict(before=str(before),sha256=sha(before))};oldmap=json.loads((D/'historical-path-map.json').read_text())['continuation_before']
for p in [R/'diagnostics/simplex-core-architecture/STATUS.md',R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md']:
 content=p.read_bytes();old=Path(oldmap[str(p)]['before']).read_bytes();need(content.endswith(old),'exact original continuation suffix');prefix=content[:-len(old)]
 f=B/('STATUS.md' if p.name=='STATUS.md' else 'roadmap.md');f.write_bytes(content);mapping[str(p)]=dict(before=str(f),sha256=sha(f))
 a=b'# Current continuation \xe2\x80\x94 residual pivot crash candidates closed, 2026-10-28';b=b'# Current continuation \xe2\x80\x94 residual pivot crash integrated; diagnostic closure pending, 2026-10-28'
 need(prefix.count(a)==1,'unambiguous pending header');prefix=prefix.replace(a,b)
 a=b'Final PASS closure/exactdiagnosticpublication in canonical output records.';b=b'Final PASS closure and exact diagnostic publication are still pending; their eventual outcomes will be recorded separately.'
 need(prefix.count(a)==1,'unambiguous pending publication');prefix=prefix.replace(a,b);p.write_bytes(prefix+old);need(p.read_bytes().endswith(old),'preserved suffix after correction')
(D/'final-prose-review-fix.json').write_text(json.dumps(dict(Julia_executed=False,numerics_rerun=False,production_unchanged=True,beforeimages=mapping,corrections=['Distinguish supervisor297.379561 and complete launcher297.659991 elapsed','Explicit pending diagnostic closure and publication in both current prefixes','Explicit negative-pivot B and all-positive RationalBigInt C no-gain controls'],historical_continuation_maps_unchanged=True,after_sha256={p:sha(p) for p in mapping}),indent=2,sort_keys=True)+'\n')
(D/'final-prose-review-fix.py').write_bytes(Path(__file__).read_bytes());print('prose-only corrections; exact generated and original beforeimages retained, no numerical work')
