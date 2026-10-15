"""One-shot continuation publication after accepted offline package review."""
from control import *
pins=D/'preparation-pins.json'
verify_review(rd(D/'review.json'),pins,list(rd(pins)['sha256'])+[str(pins)],'offline preparation')
h=full_host();save(D/'continuation-host.json',h);verify_host(h)
text=(D/'continuation-text.md').read_text().strip()+'\n'
# Bind all preceding current continuation hashes; historical before-text mappings stay.
maps=[]
for n in ['closure.json','closure-final.json','publication-final.json','continuation.json']:
 record=PREV/n
 for key,digest in rd(record)['sha256'].items():
  p=path(key)
  if p in [STATUS,ROAD]:
   saved=D/('STATUS.md.before-qualification' if p==STATUS else 'roadmap.md.before-qualification')
   require(sha(saved)==digest==sha(p),'Preceding continuation mismatch')
   maps.append(dict(record=str(record.relative_to(R)),key=key,sha256=digest,preserved_path=str(saved.relative_to(R))))
s=STATUS.read_text();a=s.index('## Exact next action\n');b=s.index('\n## ',a+1)
STATUS.write_text(s[:a]+'## Exact next action\n\n'+text+s[b:])
s=ROAD.read_text();ROAD.write_text(s.rstrip()+'\n\n## Native pivot policy Task2 offline driver preparation (2026-10-15)\n\n'+text)
files=[Path(__file__),D/'continuation-text.md',D/'continuation-host.json',D/'STATUS.md.before-qualification',D/'roadmap.md.before-qualification',STATUS,ROAD]
save(D/'continuation.json',dict(all_passed=True,mappings=maps,sha256={str(p.relative_to(R)):sha(p) for p in files}))
print(dict(mappings=len(maps),julia_executed=False))
