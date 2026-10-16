"""One-shot GREEN result closure after exact independent acceptance. No launch."""
from pathlib import Path
import sys,json
E=Path(__file__).resolve().parent;R=E.parents[3];D=E.parent/'DIRECT-LU-POLICY-ADAPTER-DRIVER-PREPARATION';A=E.parent/'DIRECT-LU-POLICY-ADAPTER-RED';sys.path.insert(0,str(D))
from control import preparation,result_review,validate_sources,full_host,require,sha,rd,save,bindings
run=D/'runs/green300';S=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
preparation();files,groups=result_review('green300','direct adapter GREEN result','result-review.json');validate_sources()
v=rd(run/'result-review.json');required={str(E/n) for n in ['REPORT.md','continuation-text.md','close.py','publication.py']}
require(required<=set(v.get('evidence_sha256',{})) and bindings(v,'evidence_sha256'),'Result review final draft bindings')
a=rd(run/'audit.json');require(a['all_passed'] is True and a['pure_timeout'] is False and a['result']['assertions']==30455,'GREEN not accepted')
require(rd(E/'postcheck-2.json')['all_passed'] is True,'Supplement')
h=full_host(groups);require(not h['matches'],'Live groups/Julia');save(E/'closure-host.json',h)
maps=[]
for rec in [A/'closure.json',A/'publication.json']:
 for live,before in [(S,E/'STATUS.md.before-GREEN'),(ROAD,E/'roadmap.md.before-GREEN')]:
  n=str(live.relative_to(R));v=rd(rec)['sha256'][n];require(sha(live)==sha(before)==v,'Continuation drift');maps.append(dict(record=str(rec.relative_to(R)),key=n,sha256=v,preserved=str(before.relative_to(R))))
save(E/'continuation-mappings.json',maps)
text=(E/'continuation-text.md').read_text();s=S.read_text();marker='## Exact next action\n';require(s.count(marker)==1,'STATUS marker');i=s.index(marker)+len(marker);S.write_text(s[:i]+'\n'+text+'\n### Historical prior continuation (superseded)\n'+s[i:]);ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## Direct LU policy adapter GREEN (2026-10-16)\n\n'+text)
paths=sorted(set(files)|{str(q) for q in E.iterdir() if q.is_file()}|{str(S),str(ROAD)})
save(E/'closure.json',dict(all_passed=True,checks=dict(exact_preparation_review=True,exact_result_review_and_drafts=True,accepted30455_audit=True,source_runtime_unchanged=True,master_remote_unchanged=True,full_groups_sessions_clear=True,previous_maps4=len(maps)==4,correctness_only=True),sha256={str(Path(n).relative_to(R)):sha(n) for n in paths}))
print('GREEN closure8PASS',len(paths),'bindings')
