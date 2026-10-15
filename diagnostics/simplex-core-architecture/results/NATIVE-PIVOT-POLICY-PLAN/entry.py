from common import *
import shutil
h=host();save(Q/'host.json',h);verify_host(h)
require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked changes exist')
for live,name in [(STATUS,'STATUS.md.before-policy-plan'),(ROAD,'roadmap.md.before-policy-plan')]:
 require(not (Q/name).exists(),'Before exists');shutil.copyfile(live,Q/name)
checks=dict(refs=h['head']==HEAD and h['master']==MASTER,groups208=len(h['groups'])==208 and not h['matches'],previous_review=rd(PREV/'result-review.json')['accepted'] is True and bindings(rd(PREV/'result-review.json')),previous_closure=rd(PREV/'closure.json')['all_passed'] is True and bindings(rd(PREV/'closure.json')),previous_publication=rd(PREV/'publication.json')['all_passed'] is True and bindings(rd(PREV/'publication.json')),before_bytes=STATUS.read_bytes()==(Q/'STATUS.md.before-policy-plan').read_bytes() and ROAD.read_bytes()==(Q/'roadmap.md.before-policy-plan').read_bytes())
save(Q/'entry.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in [Path(__file__),Q/'common.py',Q/'host.json',Q/'STATUS.md.before-policy-plan',Q/'roadmap.md.before-policy-plan']}))
require(all(checks.values()),'Entry failed; preserve');print(dict(all_passed=True,checks=len(checks),groups=len(h['groups'])))
