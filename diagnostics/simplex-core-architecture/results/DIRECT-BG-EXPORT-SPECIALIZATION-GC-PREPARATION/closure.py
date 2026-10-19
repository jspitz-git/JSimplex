"""Fresh closure for offline GC preparation only; no runtime acceptance."""
from pathlib import Path
import sys,json
N=Path(__file__).resolve().parent;D=N.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER');Q=N.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-RED');R=N.parents[3]
sys.path.insert(0,str(D));import control as c
checks={}
def ck(n,v):checks[n]=bool(v)
m=N/'preparation-pins-reviewed.json';v=c.rd(N/'review.json');required=list(c.rd(m)['sha256'])+[str(m)]
c.verify_review(v,m,required,'BG specialization fixed GC preparation');ck('exact_independent_review',True)
ck('canonical_preparation_pins',c.bindings(c.rd(m)))
old=c.rd(N/'preparation-pins.json');before=N/'PREPARATION.md.before-count-fix';report=N/'PREPARATION.md'
ck('initial_report_mapping_preserved',all(c.sha(before if p==str(report) else Path(p))==s for p,s in old['sha256'].items()))
ck('source_synthetic_check',c.rd(N/'offline-check.json')['all_passed'] and all(c.rd(N/'offline-check.json')['checks'].values()) and c.bindings(c.rd(N/'offline-check.json')))
ck('author_count_fix',c.rd(N/'count-fix.json')['all_passed'] and c.rd(N/'count-fix.json')['actual_schema_keys']==17)
c.preparation();c.validate_sources();ck('frozen_original_preparation_stage_runtime',True)
ck('old_publications_preserved',c.bindings(c.rd(D/'publication.json')) and c.bindings(c.rd(Q/'publication.json')))
ck('no_launch_artifacts',all(not (N/n).exists() for n in ['runs','launch.py','seal.py','sealed.json','reservation.json','output','allowance.json']))
h=c.full_host(c.rd(Q/'host-closure.json')['groups']);h.update(remote=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),status=c.git('status','--porcelain'),branch=c.git('branch','--show-current'));c.save(N/'host-closure.json',h)
e=c.rd(N/'host-entry.json');ck('fresh_groups_sessions',c.host_safe(h) and set(h['groups'])==set(e['groups']) and len(h['groups'])==259 and h['boot_id']==e['boot_id'])
ck('refs',h['head']==e['head']=='509fa509fdd8d3187e5aac6a4229bce707ffe227' and h['master']==c.MASTER and h['branch']=='codex/simplex-core-architecture')
ck('remotes',h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'])
ck('tracked_unchanged',not c.git('diff','HEAD','--name-only') and not c.git('diff','--cached','--name-only'))
ck('prior_untracked_preserved',all(x in h['status'].splitlines() for x in e['status'].splitlines()))
names=c.rd(N/'publication-names.json')['names'];future={str((N/n).relative_to(R)) for n in ['closure.json','publication.json']};actual={str(p.relative_to(R)) for p in N.rglob('*') if p.is_file()}
ck('exact_names',len(names)==len(set(names)) and actual==set(names)-future)
ck('diagnostic_scope',all(n.startswith(str(N.relative_to(R))+'/') for n in names))
out=dict(all_passed=all(checks.values()),checks=checks,sha256={n:c.sha(R/n) for n in names if n not in future},scope='Offline GC driver preparation only. Julia syntax/runtime/finalizer behavior/performance and numerical admission UNEXECUTED/unqualified.')
c.save(N/'closure.json',out);print(json.dumps(dict(all_passed=out['all_passed'],checks=len(checks),bindings=len(out['sha256']),failed=[k for k,v in checks.items() if not v])))
c.require(out['all_passed'],'Closure failed; preserve')
