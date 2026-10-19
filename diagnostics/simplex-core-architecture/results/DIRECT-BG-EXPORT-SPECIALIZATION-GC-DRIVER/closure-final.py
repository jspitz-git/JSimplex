"""Separate final offline closure. Never launches Julia or re-executes old checks."""
from pathlib import Path
import sys,json
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import control as c
N=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-PREPARATION');D=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER');Q=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-RED');R=c.R
checks={}
def ck(n,v):checks[n]=bool(v)
m=P/'preparation-pins-final.json';j=c.rd(m);v=c.rd(P/'review.json')
c.verify_review(v,m,list(j['sha256'])+[str(m)],'BG specialization GC driver preparation');ck('independent_review_exact_canonical',True)
ck('canonical_manifest_bindings',c.bindings(j) and set(j['sha256'])==set(c.rd(P/'required-paths-final.json')['paths']))
old=c.rd(P/'preparation-pins.json');mapping=c.rd(P/'review-fix-source.json')['before_mapping']
ck('initial_2286_bindings_preserved',len(old['sha256'])==2286 and all(c.sha(mapping.get(p,p))==h for p,h in old['sha256'].items()))
intermediate=str(P/'control.py.before-outcome-fix')
ck('review_fix_bindings_preserved',all(c.sha(intermediate if p==str(P/'control.py') else p)==h for p,h in c.rd(P/'review-fix-source.json')['sha256'].items()))
ck('reviewed_2314_bindings_preserved',all(c.sha(intermediate if p==str(P/'control.py') else p)==h for p,h in c.rd(P/'preparation-pins-reviewed.json')['sha256'].items()))
ck('final_outcome_identity_fix',c.sha(P/'control.py')==c.rd(P/'outcome-fix.json')['after_sha256'])
for name,count in [('offline-tests-reviewed.json',438),('full-audit-tests-reviewed.json',22),('closure-tests-3.json',31)]:
 z=c.rd(P/name);ck(name,z['all_passed'] is True and len(z['checks'])==count and all(z['checks'].values()))
ck('initial_rejection_preserved',c.rd(P/'review-initial.json')['accepted'] is False)
ck('test_harness_failure_preserved',c.rd(P/'closure-tests-failure.json')['all_passed'] is False)
c.preparation();c.validate_environment();c.validate_sources();ck('preparation_source_stage_runtime_environment',True)
ck('copied_driver_helper_kernels',all(c.sha(P/n)==item['sha256']==c.sha(item['source']) for n,item in c.rd(P/'copied-files.json').items()))
ck('old_publications_unchanged',all(c.bindings(c.rd(p/'publication.json')) for p in [D,N,Q]))
ck('no_numerical_or_waiting_artifacts',all(not (P/n).exists() for n in ['runs','outers','sealed.json','admission.json','release.json','reservation.json','output','allowance.json']))
e=c.rd(P/'host-entry.json');h=c.full_host(e['groups']);h.update(memory=c.guard.memory(),remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'),branch=c.git('branch','--show-current'));c.save(P/'host-closure.json',h)
ck('fresh_full_groups_sessions_noJulia',c.host_safe(h) and set(h['groups'])==set(e['groups']) and len(h['groups'])==259 and h['boot_id']==e['boot_id'])
ck('refs_branch',h['head']==e['head']=='ff248544e8f89cc05aecff64806bf60d8b2bd9cf' and h['master']==c.MASTER and h['branch']=='codex/simplex-core-architecture')
ck('remote_refs',h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'])
ck('tracked_clean',not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'))
ck('prior_untracked_preserved',all(x in h['status'].splitlines() for x in e['status'].splitlines()))
names=c.rd(P/'publication-names.json')['names'];future={str((P/n).relative_to(R)) for n in ['closure.json','publication.json']};actual={str(p.relative_to(R)) for p in P.rglob('*') if p.is_file()}
ck('exact_publication_names',len(names)==len(set(names)) and actual==set(names)-future)
ck('diagnostic_only',all(n.startswith(str(P.relative_to(R))+'/') for n in names))
record=dict(all_passed=all(checks.values()),checks=checks,sha256={n:c.sha(R/n) for n in names if n not in future},scope='Reviewed offline GC admission/auditor only; no concrete numerical admission or runtime qualification')
c.save(P/'closure.json',record);print(json.dumps(dict(all_passed=record['all_passed'],checks=len(checks),bindings=len(record['sha256']),failed=[n for n,v in checks.items() if not v])))
c.require(record['all_passed'],'Closure failed; preserve and stop')
