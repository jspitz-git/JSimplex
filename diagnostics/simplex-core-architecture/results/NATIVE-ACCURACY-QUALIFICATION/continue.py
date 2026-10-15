"""One-time reviewed continuation update with explicit old-pin preservation."""
from final_helpers import *
review=rd(Q/'result-review.json');require(review['accepted'] is True and not review['findings'],'Result review not accepted');require(bindings(review),'Changed review bindings')
require(review['sha256'].get(str(Q/'continuation-text.md'))==sha(Q/'continuation-text.md'),'Continuation not independently bound')
h=host();save(Q/'continuation-host.json',h);verify_host(h)
for live,before in [(STATUS,Q/'STATUS.md.before-qualification'),(ROAD,Q/'roadmap.md.before-qualification')]:require(live.read_bytes()==before.read_bytes(),'Continuation changed before preserving')
records=[(D/'closure.json','sha256'),(D/'publication.json','sha256'),(Q/'accuracy-sealed-pins.json','inventory'),(Q/'accuracy-launch-pins.json','inventory'),(Q/'accuracy-admission.json','sha256'),(Q/'accuracy-run/pins.json','inventory'),(Q/'portable/pins.json','inventory')]
maps=[]
for rec,field in records:
 z=rd(rec)[field]
 for live,before in [(STATUS,Q/'STATUS.md.before-qualification'),(ROAD,Q/'roadmap.md.before-qualification')]:
  keys=[k for k in z if path(k)==live];require(len(keys)==1,'Missing exact continuation key')
  key=keys[0];value=z[key];digest=value['sha256'] if isinstance(value,dict) else value
  require(digest==sha(before),'Historical digest mismatch')
  maps.append(dict(record=str(rec.relative_to(R)),field=field,key=key,sha256=digest,preserved_path=str(before.relative_to(R))))
require(len(maps)==14,'Expected fourteen mappings')
text=(Q/'continuation-text.md').read_text()
s=STATUS.read_text();start=s.index('## Exact next action\n');end=s.index('## Previous missing-zero experiment',start)
STATUS.write_text(s[:start]+'## Exact next action\n\n'+text+'\n'+s[end:])
with ROAD.open('a') as f:f.write('\n### Native Float64 accuracy-policy qualification and decision\n\nThis completed result supersedes the prospective preparation handoff above.\n\n'+text)
save(Q/'continuation.json',dict(all_passed=True,mappings=maps,scope='Only current preparation and exact-stage continuation keys map to preserved before-qualification bytes; all older mappings unchanged',sha256={str(p.relative_to(R)):sha(p) for p in [Path(__file__),Q/'final_helpers.py',Q/'continuation-host.json',Q/'continuation-text.md',Q/'STATUS.md.before-qualification',Q/'roadmap.md.before-qualification',STATUS,ROAD]}))
print(dict(all_passed=True,mappings=len(maps),groups=len(h['groups'])))
