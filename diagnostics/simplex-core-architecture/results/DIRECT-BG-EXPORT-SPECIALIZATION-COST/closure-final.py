"""Separate offline Task3 closure; no old checker, auditor, outer or Julia execution."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import control as c
checks={}
def ck(n,v):checks[n]=bool(v)
m=D/'preparation-pins-reviewed.json';j=c.rd(m);v=c.rd(D/'review-final.json')
c.verify_review(v,m,list(j['sha256'])+[str(m)],'BG specialized export cost preparation');ck('independent_review_exact',True);ck('no_launch_admission',v.get('launch_admitted') is False)
ck('exact_manifest',c.bindings(j) and set(j['sha256'])==set(c.rd(D/'required-paths-reviewed.json')['paths']))
mapping=c.rd(D/'review-fix-map.json')['mapping']
def initial_bindings(z):
 return all(c.sha(mapping[n]['preserved'] if n in mapping else n)==h for n,h in z['sha256'].items())
ck('initial_manifest_before_mapping',initial_bindings(c.rd(D/'preparation-pins.json')))
ck('initial_rejection_preserved',c.rd(D/'review.json')['accepted'] is False and len(c.rd(D/'review.json')['findings'])==2 and c.sha(D/'review.json')==c.sha(D/'review.json.initial'))
for n,num in [('source-check.json',132),('offline-tests-2.json',223)]:
 z=c.rd(D/n);ck(n,z['all_passed'] is True and len(z['checks'])==num and all(z['checks'].values()) and initial_bindings(z))
z=c.rd(D/'review-fix-check.json');ck('new_correction_checks',z['all_passed'] is True and len(z['checks'])==2922 and all(z['checks'].values()) and c.bindings(z))
ck('original_synthetic_failure_preserved',c.rd(D/'offline-tests-failure.json')['returncode']==1 and c.sha(D/'offline-tests.py')==c.rd(D/'offline-tests-failure.json')['source_sha256'])
c.preparation();c.validate_environment();c.validate_sources();files,groups=c.predecessor('cost1-300');ck('preparation_stage_runtime_GREEN_predecessor',bool(files) and len(groups)==265)
for p in [c.G,c.G.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-RED'),c.G.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-GREEN')]:ck('old_publication_'+p.name,c.bindings(c.rd(p/'publication.json')))
ck('no_runtime_artifacts',all(not (D/n).exists() for n in ['runs','outers','sealed.json','admission.json','release.json','reservation.json','output','allowance.json']))
e=c.rd(D/'host-entry.json');h=c.full_host(groups);h.update(memory=c.guard.memory(),remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'),branch=c.git('branch','--show-current'));c.save(D/'host-closure.json',h)
ck('fresh_groups_sessions_noJulia',c.host_safe(h) and h['groups']==e['groups'] and len(h['groups'])==265 and h['boot_id']==e['boot_id'])
ck('refs',h['head']==e['head']=='7fd611127d3e3366c25ddb531768c3610548f303' and h['master']==c.MASTER and h['branch']=='codex/simplex-core-architecture')
ck('remote',h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'])
ck('tracked_clean',not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'))
ck('prior_untracked_preserved',all(x in h['status'].splitlines() for x in e['status'].splitlines()))
names=c.rd(D/'publication-names.json')['names'];future={str((D/n).relative_to(c.R)) for n in ['closure.json','publication.json']};actual={str(p.relative_to(c.R)) for p in D.rglob('*') if p.is_file()}
ck('exact_publication',len(names)==len(set(names)) and actual==set(names)-future)
ck('diagnostic_scope',all(n.startswith(str(D.relative_to(c.R))+'/') for n in names))
c.save(D/'closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={n:c.sha(c.R/n) for n in names if n not in future},scope='Offline preparation acceptance only; no Julia, runtime qualification or concrete launch admission'))
print(json.dumps(dict(all_passed=all(checks.values()),checks=len(checks),bindings=len(names)-2,failed=[k for k,v in checks.items() if not v])));c.require(all(checks.values()),'Closure failed; preserve and stop')
