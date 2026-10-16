"""One-shot planning closure after exact independent review. No Julia."""
from pathlib import Path
import json,sys,hashlib
E=Path(__file__).resolve().parent;R=E.parents[3];D=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST-PREPARATION';C=E.parent/'DIRECT-LU-POLICY-ADAPTER-COST1';sys.path.insert(0,str(D))
from control import full_host,rd,sha,save,require,bindings,git,W,MASTER
S=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';SPEC=R/'docs/superpowers/specs/2026-10-16-direct-bg-dynamic-upper.md';PLAN=R/'docs/superpowers/plans/2026-10-16-direct-bg-dynamic-upper.md'
review=rd(E/'review.json');required={str(q) for q in E.iterdir() if q.is_file() and q.name!='review.json'}|{str(SPEC),str(PLAN)}
require(review.get('accepted') is True and review.get('findings')==[] and review.get('scope')=='direct BG dynamic U planning','Review acceptance')
require(set(review['sha256'])==required and bindings(review),'Exact review membership/hashes')
require(bindings(rd(E/'source-pins.json')) and bindings(rd(E/'helper-pins.json')),'Bounded readtime/helper drift')
require(git('rev-parse','HEAD')=='47ec2fc41fa3d21df9569e64a3b5a3e4ec7fa184','Diagnostic ref drift')
require(git('rev-parse','master')==MASTER and git('rev-parse','HEAD',cwd=W)==MASTER,'Master refs drift')
require(MASTER+'\trefs/heads/master' in git('ls-remote','origin','refs/heads/master'),'Remote master drift')
for root in (R,W):
 require(not git('diff','HEAD','--name-only','--','src','test','.github','Project.toml',cwd=root),'Tracked source/test/CI/project drift')
# No runtime inventory or environment requalification: planning uses 15 selected readtime pins only.
h=full_host(rd(E/'host.json')['groups']);require(not h['matches'],'Live groups/Julia');save(E/'closure-host.json',h)
maps=[]
for rec in [C/'closure.json',C/'publication.json']:
 for live,before in [(S,E/'STATUS.md.before-dynamic-U'),(ROAD,E/'roadmap.md.before-dynamic-U')]:
  n=str(live.relative_to(R));v=rd(rec)['sha256'][n];require(sha(live)==sha(before)==v,'Continuation drift');maps.append(dict(record=str(rec.relative_to(R)),key=n,sha256=v,preserved=str(before.relative_to(R))))
save(E/'continuation-mappings.json',maps)
text=(E/'continuation-text.md').read_text();s=S.read_text();marker='## Exact next action\n';require(s.count(marker)==1,'Marker');i=s.index(marker)+len(marker);S.write_text(s[:i]+'\n'+text+'\n### Historical prior continuation (superseded)\n'+s[i:]);ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## Direct BG dynamic U planning (2026-10-16)\n\n'+text)
paths=sorted([q for q in E.iterdir() if q.is_file()]+[S,ROAD,SPEC,PLAN]);save(E/'closure.json',dict(all_passed=True,checks=dict(exact_review=True,selected15_sources_and_helpers_unchanged=True,master_remote_unchanged=True,full_groups_sessions_clear=True,prior_maps4=len(maps)==4,planning_only=True),sha256={str(q.relative_to(R)):sha(q) for q in paths}));print('Planning closure6PASS',len(paths),'bindings')
