"""One-shot first-cost diagnostic closure; no numerical or old auditor rerun."""
from pathlib import Path
import sys
Q=Path(__file__).resolve().parent;E=Q.parent/'DIRECT-BG-BLOCK-COST-PREPARATION';R=Q.parents[3];sys.path.insert(0,str(E))
import control as c
run=E/'runs/cost1-300';checks={}
def ok(v,k):
 checks[k]=bool(v)
 if not v:raise RuntimeError(k)
c.preparation();c.validate_sources();ok(True,'preparation_and_actual_sources_runtime')
f,groups=c.result_review('cost1-300','block BG matched cost result','result-review.json');ok(bool(f),'independent_exact_result_review')
v=c.rd(run/'result-review.json')
ok('evidence_sha256' in v and c.bindings(v,'evidence_sha256'),'result_supplementary_evidence')
a=c.rd(run/'audit.json');ok(a['all_passed'] is True and a['pure_timeout'] is False and c.bindings(a),'original_audit_integrity_accepted')
ok(not c.first_process_viable(a,c.rd(E/'inputs.json')['fixtures']),'cost_rejection_preserved_no_second_process')
ok({p.name for p in (E/'runs').iterdir()}=={'cost1-300'},'one_attempt')
p=c.rd(Q/'postcheck.json');ok(p['all_passed'] is True and c.bindings(p),'supplemental_postcheck')
h=c.full_host(groups);c.save(Q/'closure-host.json',h)
ok(not h['matches'] and len(h['groups'])==240,'fresh_full_groups_AND_sessions_noJulia')
ok(h['head']=='ffa005e219b2eb4b8f119a24f6c9953214cac8b9' and h['master']==c.MASTER,'refs')
ok(c.git('branch','--show-current')=='codex/simplex-core-architecture','branch')
ok(not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'),'no_tracked_or_staged_changes')
files=sorted([p for p in Q.iterdir() if p.is_file()]+[p for p in run.rglob('*') if p.is_file()]);names=[str(p.relative_to(R)) for p in files]
ok(not any(p.is_symlink() for p in files) and names==c.rd(Q/'closure-names.json')['names'],'explicit_exact_names')
c.save(Q/'closure.json',dict(all_passed=True,checks=checks,sha256={str(p.relative_to(R)):c.sha(p) for p in files},scope='One first cost result: integrity accepted, fixed design performance rejected and stopped; no promotion'))
print('Closure PASS',len(checks),'checks;',len(files),'bindings')
