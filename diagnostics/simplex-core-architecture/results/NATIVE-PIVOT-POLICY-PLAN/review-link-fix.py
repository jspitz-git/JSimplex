"""Separate one-time final review link correction; original amendment preserved."""
from common import *
p=Q/'continuation-text.md';before=Q/'continuation.before-final-link.md';old=p.read_bytes()
a=b'results/NATIVE-PIVOT-POLICY-PLAN/review.md';b=b'results/NATIVE-PIVOT-POLICY-PLAN/review-final.md'
require(old.count(a)==1 and b not in old,'Unexpected old review link')
require(rd(Q/'review-fix.json')['sha256'][str(p)]==sha(p),'Initial amendment linkage changed')
with before.open('xb') as f:f.write(old)
p.write_bytes(old.replace(a,b))
checks=dict(original_preserved=before.read_bytes()==old,exact_inverse=p.read_bytes().replace(b,a)==old,final_link=p.read_bytes().count(b)==1,initial_amendment_old_binding=rd(Q/'review-fix.json')['sha256'][str(p)]==sha(before))
save(Q/'review-link-fix.json',dict(all_passed=all(checks.values()),checks=checks,mapping=dict(record=str(Q/'review-fix.json'),key=str(p),sha256=sha(before),preserved=str(before)),sha256={str(f):sha(f) for f in [Path(__file__),Q/'review-fix.json',before,p]},scope='Only final accepted review link; initial rejected review and first amendment stay unchanged'))
require(all(checks.values()),'Link correction failed');print(dict(all_passed=True,checks=len(checks)))
