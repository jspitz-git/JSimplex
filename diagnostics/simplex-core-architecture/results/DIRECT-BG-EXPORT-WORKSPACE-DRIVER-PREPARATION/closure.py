"""Fresh offline publication closure; no Julia, launcher or old checker."""
from control import *
from pathlib import Path
import json
checks={}
def ck(v,n):checks[n]=bool(v)
# Publication names are an explicit fixed list authored after the final review.
names=rd(D/'publication-names.json')['names'];future={str((D/n).relative_to(R)) for n in ['closure.json','publication.json']}
h=full_host();h['branch']=git('branch','--show-current');h['remote']=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture');h['status']=git('status','--porcelain');save(D/'host-closure.json',h)
initial=rd(D/'host.json');v=rd(D/'review.json');fix=rd(D/'review-fix.json')
ck(host_safe(h) and h['boot_id']==initial['boot_id'] and len(h['groups'])==246,'fresh_full_groups_sessions_host')
ck(h['head']==ENTRY and h['master']==MASTER and h['branch']=='codex/simplex-core-architecture','refs')
ck(ENTRY+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and MASTER+'\trefs/heads/master' in h['remote'],'remote_refs')
ck(not git('diff','--name-only','HEAD') and not git('diff','--cached','--name-only'),'no_tracked_staged_edits')
ck(all(line in h['status'].splitlines() for line in initial['status'].splitlines()),'existing_untracked_preserved')
validate_sources();ck(True,'full_source_stage_runtime')
ck(bindings(rd(D/'entry.json')),'accepted_candidate_tests_plans_frozen')
ck(rd(D/'source-check.json')['all_passed'] and bindings(rd(D/'source-check.json')),'initial_author_evidence_preserved')
ck(fix['all_passed'] and all(fix['checks'].values()) and bindings(fix),'amendment_checks')
preparation();ck(True,'full_exact_preparation_review')
ck(v['accepted'] is True and v['findings']==[],'independent_review_accepted')
ck(not (D/'runs').exists(),'no_seal_reservation_output_or_Julia')
actual={str(p.relative_to(R)) for p in D.rglob('*') if p.is_file()}
ck(len(names)==len(set(names)) and actual==set(names)-future,'exact_publication_membership')
ck(all(n.startswith(str(D.relative_to(R))+'/') for n in names),'diagnostics_only')
ck(all(sha(R/p)==val for p,val in rd(D/'prepublication-inputs.json')['sha256'].items()),'reviewed_final_texts_unchanged')
out=dict(all_passed=all(checks.values()),checks=checks,sha256={p:sha(R/p) for p in names if p not in future},scope='Offline Task3 RED/GREEN preparation closure only; no runtime acceptance')
save(D/'closure.json',out);print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),bindings=len(out['sha256']),failed=[k for k,b in checks.items() if not b])))
require(out['all_passed'],'Closure failed; preserve')
