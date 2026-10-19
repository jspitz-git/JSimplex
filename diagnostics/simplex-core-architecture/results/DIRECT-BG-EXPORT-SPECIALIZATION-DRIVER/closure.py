"""Fresh offline Task2 closure. No Julia or frozen checker execution."""
from pathlib import Path
import json
import control as c
D=Path(__file__).resolve().parent;R=D.parents[3];T=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-TASK1')
checks={}
def ck(n,v):checks[n]=bool(v)
rv=c.rd(D/'review.json');s=c.rd(D/'source-check.json')
ck('review_accepted',rv.get('accepted') is True and rv.get('findings')==[] and rv.get('scope')=='BG specialization driver preparation')
ck('red_expectation_supported',rv.get('red_expectation_supported') is True)
ck('review_bindings',bool(rv.get('sha256')) and c.bindings(rv) and c.bindings(rv,'evidence_sha256'))
ck('author_check',s['all_passed'] and all(s['checks'].values()) and c.bindings(s))
ind=c.rd(D/'independent-check2.json')
original=c.rd(D/'independent-check.json')
ck('original_reviewer_failure_preserved',original['all_passed'] is False and c.bindings(original))
ck('independent_check',ind['all_passed'] and all(ind['checks'].values()) and c.bindings(ind))
ck('synthetic_check',c.rd(D/'offline-tests.json')['all_passed'] and all(c.rd(D/'offline-tests.json')['checks'].values()))
c.preparation();ck('exact_review_preparation_membership',True)
c.validate_sources();c.validate_environment();ck('sources_runtime_stage_environment',True)
ck('Task1_frozen',c.bindings(c.rd(T/'publication.json')))
ck('no_runtime_outputs',not (D/'runs').exists())
h=c.full_host(c.rd(D/'host.json')['groups']);h.update(remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'),branch=c.git('branch','--show-current'));c.save(D/'host-closure.json',h)
e=c.rd(D/'host.json')
ck('fresh_groups_sessions',c.host_safe(h) and set(e['groups'])<=set(h['groups']) and h['boot_id']==e['boot_id'])
ck('refs',h['head']==e['head']==c.ENTRY and h['master']==c.MASTER and h['branch']=='codex/simplex-core-architecture')
ck('remotes',h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'])
ck('tracked_unchanged',not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'))
ck('prior_untracked',all(x in h['status'].splitlines() for x in e['status'].splitlines()))
names=c.rd(D/'publication-names.json')['names'];future={str((D/n).relative_to(R)) for n in ['closure.json','publication.json']};actual={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}
ck('exact_files',len(names)==len(set(names)) and actual==set(names)-future)
ck('diagnostic_scope',all(n.startswith(str(D.relative_to(R))+'/') for n in names))
out=dict(all_passed=all(checks.values()),checks=checks,sha256={n:c.sha(R/n) for n in names if n not in future},scope='Task2 concrete offline driver preparation only; no numerical admission/execution or performance acceptance')
c.save(D/'closure.json',out);print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),bindings=len(out['sha256']),failed=[k for k,v in checks.items() if not v])))
c.require(out['all_passed'],'Closure failed; preserve')
