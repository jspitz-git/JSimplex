"""New one-shot diagnostic-result closure. Never replays a numerical/audit script."""
from common import *
E=Q.parent/'NATIVE-PIVOT-INTEGRATION-ENVIRONMENT-AMENDMENT';run=E/'runs/integration';out=run/'output';P=Q.parent/'NATIVE-PIVOT-INTEGRATION-DRIVER-PREPARATION'
v=rd(Q/'result-review.json');a=rd(run/'audit.json')
require(v['accepted'] is True and v['qualification_accepted'] is False and v['scope']=='diagnostic result' and v['findings']==[],'Diagnostic review acceptance')
require(set(v['sha256'])==set(a['sha256'])|{str(run/'audit.json')},'Exact result review membership')
require(bindings(v) and bindings(a),'Result binding drift')
require(all(sha(path(n))==s for n,s in v['evidence_sha256'].items()),'Supplemental result evidence drift')
h=host();verify_host(h);save(Q/'closure-host.json',h)
require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'Tracked/index drift')
require(sha(STATUS)==sha(Q/'STATUS.md.before-integration-run') and sha(ROAD)==sha(Q/'roadmap.md.before-integration-run'),'Continuation preimage')
for m in rd(Q/'continuation-mappings.json')['mappings']:
 z=rd(R/m['record'])
 for pointer in m['pointer']:z=z[pointer]
 require(z==m['sha256']==sha(R/m['preserved_path']),'Explicit continuation mapping')
stage=Path(rd(run/'config.json')['stage']);manifest=rd(P/'overlay-manifest.json')['candidate']
stage_ok={str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()}=={e['destination'] for e in manifest} and all(sha(stage/e['destination'])==e['sha256']==sha(Path(e['source'])) for e in manifest)
text=(Q/'continuation-text.md').read_text().strip()+'\n';s=STATUS.read_text();start=s.index('## Exact next action\n');end=s.index('\n## ',start+1)
STATUS.write_text(s[:start]+'## Exact next action\n\n'+text+s[end:]);ROAD.write_text(ROAD.read_text().rstrip()+'\n\n## Native pivot integration timeout (2026-10-16)\n\n'+text)
names=rd(Q/'publication-names.json')['names'];expected={str(p.relative_to(R)) for p in Q.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in run.rglob('*') if p.is_file()}|{str(p.relative_to(R)) for p in [STATUS,ROAD,Q/'closure.json',Q/'publication.json']}
p=rd(out/'process.json');post=rd(Q/'timeout-postcheck.json')
checks=dict(review=True,qualification_rejected=v['qualification_accepted'] is False,audit_false=a['all_passed'] is False,no_raw=not (out/'raw.toml').exists(),timeout=p['reason']=='wall_time' and p['returncode']==-9,
 bound60=rd(run/'invocation.json')['elapsed_seconds']<=60,post_integrity=post['all_passed'] and bindings(post),host218=len(h['groups'])==218 and not h['matches'],actual520=all(sha(R/n)==s for n,s in rd(E/'actual-baseline.json')['sha256'].items()),stage76=stage_ok and len(manifest)==76,mappings12=len(rd(Q/'continuation-mappings.json')['mappings'])==12,exact_names=set(names)==expected and len(names)==len(expected))
files=[R/n for n in names if n not in [str((Q/'closure.json').relative_to(R)),str((Q/'publication.json').relative_to(R))]]
save(Q/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={str(p.relative_to(R)):sha(p) for p in files},scope='Diagnostic preservation closure ONLY; numerical attempt FAILED/CONSUMED, never qualification PASS'))
require(all(checks.values()),'Closure failed; preserve');print(dict(checks=len(checks),bindings=len(files),names=len(names)))
