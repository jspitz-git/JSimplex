"""One-shot RED diagnostic closure, no old auditor or numerical rerun."""
from pathlib import Path
import sys,json
E=Path(__file__).resolve().parent;D=E.parent/'DIRECT-BG-BLOCK-DRIVER-PREPARATION';R=E.parents[3];sys.path.insert(0,str(D))
import control as c
run=D/'runs/red300';checks={}
def ok(v,n):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
c.preparation();c.validate_sources();c.validate_environment();ok(True,'preparation_sources_runtime_environment')
f,groups=c.predecessor('green300');ok(bool(f),'accepted_RED_predecessor_readonly')
ok(c.rd(run/'audit.json')['all_passed'] is True,'saved_audit')
ok(c.rd(E/'postcheck.json')['all_passed'] and c.bindings(c.rd(E/'postcheck.json')),'supplemental_postcheck_bindings')
ok(c.rd(E/'independent-result-check.json')['all_passed'] is True,'independent_result_checks')
h=c.full_host(groups);c.save(E/'closure-host.json',h)
ok(not h['matches'],'fresh_no_Julia_full_groups_AND_sessions')
ok(len(h['groups'])==236,'all_prior_and_new_groups')
ok(h['head']=='c72bf6ee1fd2b17be803f020c1969bdc7f0f5a02' and h['master']==c.MASTER,'refs_unchanged')
ok(c.git('branch','--show-current')=='codex/simplex-core-architecture','branch')
ok(not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'),'no_tracked_or_staged_changes')
ok({p.name for p in (D/'runs').iterdir()}=={'red300'},'sole_phase')
files=sorted([p for p in E.iterdir() if p.is_file()]+[p for p in run.rglob('*') if p.is_file()])
ok(not any(p.is_symlink() for p in files),'no_evidence_symlinks')
names=[str(p.relative_to(R)) for p in files]
ok(names==c.rd(E/'closure-names.json')['names'],'explicit_exact_closure_names')
c.save(E/'closure.json',dict(all_passed=True,checks=checks,sha256={str(p.relative_to(R)):c.sha(p) for p in files},scope='One accepted expected RED result; no GREEN/cost admission'))
print('Closure PASS',len(checks),'checks;',len(files),'bindings')
