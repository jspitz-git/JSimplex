"""Separate result closure, after fresh independent review and before publication."""
from pathlib import Path
import sys
E=Path(__file__).resolve().parent;D=E.parent/'NATIVE-PIVOT-MASTER-READINESS';sys.path.insert(0,str(D))
from control import *
phase=sys.argv[1];run=D/'runs'/phase;v=rd(E/'result-review.json');post=rd(E/(phase+'-postcheck.json'))
require(v.get('accepted') is True and v.get('findings')==[] and v.get('scope')=='actual-master result' and v.get('phase')==phase,'Result review')
require(bindings(v),'Result review bindings')
for n,h in v.get('evidence_sha256',{}).items():require(sha(path(n))==h,'Review evidence drift')
require(post['all_passed'] and bindings(post) and rd(run/'audit.json')['all_passed'],'Postcheck/audit')
preparation();validate_environment();validate_production();require(not git('diff','--cached','--name-only') and not git('diff','--name-only'),'Diagnostic dirty')
h=full_host(post['host']['groups']);require(not h['matches'],'Processes remain');save(E/'closure-host.json',h)
S=R/'diagnostics/simplex-core-architecture/STATUS.md';ROAD=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';maps=[]
for rec in [D/'closure.json',D/'publication.json']:
 for live,before in [(S,E/'STATUS.md.before-master-validation'),(ROAD,E/'roadmap.md.before-master-validation')]:
  n=str(live.relative_to(R));value=rd(rec)['sha256'][n];require(sha(live)==sha(before)==value,'Previous continuation drift')
  maps.append(dict(record=str(rec.relative_to(R)),key=n,sha256=value,preserved=str(before.relative_to(R))))
save(E/'continuation-mappings.json',maps)
text=(E/'continuation-text.md').read_text();s=S.read_text();marker='## Exact next action\n';require(s.count(marker)==1,'STATUS marker');i=s.index(marker)+len(marker)
S.write_text(s[:i]+'\n'+text+'\n### Historical prior continuation (superseded)\n'+s[i:]);ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## Native pivot actual-master validation (2026-10-16)\n\n'+text.rstrip()+'\n')
checks=dict(independent_result_accepted=True,all_result_bindings=True,original_audit_pass=True,postcheck_pass=True,actual_master_exact=True,remote_master_still_base=True,full_groups_sessions_closed=True,prior_continuation_maps4=len(maps)==4,readiness_preserved=True)
files=sorted([p for p in E.rglob('*') if p.is_file()]+[p for p in (D/'runs').rglob('*') if p.is_file()]+[S,ROAD])
save(E/'closure.json',dict(all_passed=all(checks.values()),checks=checks,phase=phase,master=git('rev-parse','master'),sha256={str(p.relative_to(R)):sha(p) for p in files}))
print('Actual master closure',len(checks),'PASS',len(files),'bindings')
