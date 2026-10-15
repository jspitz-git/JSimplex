"""One-time publication continuation, after independent plan acceptance."""
from common import *
review=rd(Q/'review-final.json');require(review['accepted'] is True and not review['findings'],'Plan review not accepted');require(bindings(review),'Review binding changed')
require(review['sha256'].get(str(Q/'continuation-text.md'))==sha(Q/'continuation-text.md'),'Continuation not reviewed')
h=host();save(Q/'continuation-host.json',h);verify_host(h)
for live,before in [(STATUS,Q/'STATUS.md.before-preparation'),(ROAD,Q/'roadmap.md.before-preparation')]:require(live.read_bytes()==before.read_bytes(),'Current text changed since entry')
maps=[]
for filename in ['closure.json','publication.json','continuation.json']:
 rec=PREV/filename;z=rd(rec)['sha256']
 for live,before in [(STATUS,Q/'STATUS.md.before-preparation'),(ROAD,Q/'roadmap.md.before-preparation')]:
  keys=[n for n in z if path(n)==live];require(len(keys)==1,'Missing exact historical continuation key')
  key=keys[0];require(z[key]==sha(before),'Wrong historical text bytes')
  maps.append(dict(record=str(rec.relative_to(R)),key=key,sha256=z[key],preserved_path=str(before.relative_to(R))))
text=(Q/'continuation-text.md').read_text();s=STATUS.read_text();a=s.index('## Exact next action\n');b=s.index('## Previous missing-zero experiment',a)
STATUS.write_text(s[:a]+'## Exact next action\n\n'+text+'\n'+s[b:])
with ROAD.open('a') as f:f.write('\n### Optional native pivot policy offline candidate preparation\n\n'+text)
save(Q/'continuation.json',dict(all_passed=True,mappings=maps,scope='Six current policy-plan continuation keys preserved; all older policy-plan and qualification maps unchanged',sha256={str(p.relative_to(R)):sha(p) for p in [Path(__file__),Q/'common.py',Q/'continuation-host.json',Q/'continuation-text.md',Q/'STATUS.md.before-preparation',Q/'roadmap.md.before-preparation',STATUS,ROAD]}))
print(dict(all_passed=True,mappings=len(maps),groups=len(h['groups'])))
