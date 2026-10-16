"""One-shot closure after independent new-result review, never a numerical rerun."""
from common import *
N=Q.parent/'NATIVE-PIVOT-INTEGRATION-180-PREPARATION';A=Q.parent/'NATIVE-PIVOT-INTEGRATION-COMPILE-ANALYSIS';K=Q.parent/'NATIVE-PIVOT-INTEGRATION-QUALIFICATION';run=N/'runs/integration';out=run/'output'
v=rd(Q/'result-review.json');a=rd(run/'audit.json');post=rd(Q/'postcheck.json')
require(v['accepted'] is True and v['findings']==[] and v['qualification_accepted']==a['all_passed'],'Independent result acceptance')
require(set(v['sha256'])==set(a['sha256'])|{str(run/'audit.json')} and bindings(v) and bindings(a),'Exact result bindings')
require(all(sha(path(k))==h for k,h in v['evidence_sha256'].items()),'Result evidence bindings')
h=host();verify_host(h);save(Q/'closure-host.json',h)
require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked/index changes')
require(sha(STATUS)==sha(N/'STATUS.md.before-180') and sha(ROAD)==sha(N/'roadmap.md.before-180'),'Continuation preimage')
maps=[]
for rec,field,absolute,inventory in [(K/'closure.json','sha256',False,False),(K/'publication.json','sha256',False,False),(run/'sealed.json','inventory',True,True),(run/'admission.json','sha256',True,False),(run/'launch-pins.json','inventory',True,True),(out/'pins.json','inventory',True,True)]:
 z=rd(rec)
 for p,saved in [(STATUS,N/'STATUS.md.before-180'),(ROAD,N/'roadmap.md.before-180')]:
  key=str(p if absolute else p.relative_to(R));value=z[field][key];digest=value['sha256'] if inventory else value
  require(digest==sha(saved),'Continuation mapping')
  maps.append(dict(record=str(rec.relative_to(R)),pointer=[field,key]+(['sha256'] if inventory else []),sha256=digest,preserved_path=str(saved.relative_to(R))))
save(Q/'continuation-mappings.json',dict(mappings=maps,scope='These current continuation bindings map ONLY to N before180 copies; older mappings unchanged'))
text=(Q/'continuation-text.md').read_text().strip()+'\n';s=STATUS.read_text();start=s.index('## Exact next action\n');end=s.index('\n## ',start+1)
STATUS.write_text(s[:start]+'## Exact next action\n\n'+text+s[end:]);ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## Native pivot integration180 result (2026-10-16)\n\n'+text)
files={p for d in (A,N,Q) for p in d.rglob('*') if p.is_file()}|{STATUS,ROAD,Q/'publication-names.json',Q/'closure.json',Q/'publication.json'}
names=sorted(str(p.relative_to(R)) for p in files);save(Q/'publication-names.json',dict(names=names))
checks=dict(review=True,qualification_follows_original_audit=v['qualification_accepted']==a['all_passed'],consumed=post['summary']['allowance_consumed'],postcheck=post['all_passed'] and bindings(post),within180=rd(run/'invocation.json')['elapsed_seconds']<=180,host_closed=not h['matches'] and set(rd(run/'posthost.json')['groups'])<=set(h['groups']),actual520=bindings(rd(N.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT/actual-baseline.json')),old_failed=rd(K/'result-review.json')['qualification_accepted'] is False,mappings12=len(maps)==12,master=h['master']==MASTER,original_driver=sha(N.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION/driver.jl')==rd(N/'preparation-pins.json')['sha256'][str(N.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION/driver.jl')])
others=[R/x for x in names if x not in [str((Q/'closure.json').relative_to(R)),str((Q/'publication.json').relative_to(R))]]
save(Q/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in others},scope='New180s attempt preservation closure; acceptance exactly follows independently reviewed unchanged audit'))
require(all(checks.values()),'Closure failed; preserve');print(dict(checks=len(checks),bindings=len(others),names=len(names)))
